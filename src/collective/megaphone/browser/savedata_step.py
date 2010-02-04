from collective.megaphone import DOMAIN, MegaphoneMessageFactory as _
from collective.megaphone.config import SAVEDATA_ID, RECIPIENT_MAILER_ID, RENDERED_LETTER_ID, \
    SF_LEAD_ID, SF_CAMPAIGNMEMBER_ID, CAMPAIGN_ID_FIELD_ID, ORG_FIELD_ID
from collective.megaphone.browser.recipient_multiplexer import IMultiplexedActionAdapter
from collective.z3cform.wizard import wizard
from z3c.form import field
from zope import schema
from zope.app.component.hooks import getSite
from zope.interface import Interface, alsoProvides
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.i18nl10n import utranslate
from Products.CMFPlone.utils import safe_unicode

class ISaveDataStep(Interface):
    
    email = schema.Bool(
        title = _(u'Send the letter by e-mail to each recipient.'),
        description = _(u'The letters will be sent to the e-mail addresses you entered in the Recipients step.'),
        default = True,
        )

    savedata = schema.Bool(
        title = _(u'Save a copy of each submitted letter.'),
        description = _(u'The letters will be stored in a PloneFormGen Save Data Adapter.'),
        default = False,
        )

def salesforce_is_configured():
    site = getSite()
    
    sfbc = getToolByName(site, 'portal_salesforcebaseconnector', default=None)
    ttool = getToolByName(site, 'portal_types')
    
    if sfbc is not None and 'SalesforcePFGAdapter' in ttool.objectIds():
        return True
    else:
        return False

class ISalesforceSettings(Interface):
    
    save_lead = schema.Bool(
        title = _(u"Save the sender's contact information as a Lead in Salesforce.com"),
        description = _(u'A PloneFormGen-Salesforce Adapter will be created to add a new Lead in Salesforce.  If you want to create something other than a Lead, select this here and then go change the object type setting of the adapter that will be created when you complete the wizard.'),
        default = False,
        )

    campaign_id = schema.TextLine(
        title = _(u'Salesforce.com Campaign ID'),
        description = _(u"Enter the ID of a Salesforce campaign (which can be found by looking " +
                        u"at the campaign's URL in the Salesforce.com UI).  If this is configured, " +
                        u"the new Lead will be associated with this campaign."),
        required = False,
        )

class SaveDataStep(wizard.Step):
    prefix = 'savedata'
    label = _(u'Delivery')
    description = _(u"This step allows you to configure what happens to the letters after they are submitted.")
    
    @property
    def fields(self):
        fields = field.Fields(ISaveDataStep)
        if salesforce_is_configured():
            fields += field.Fields(ISalesforceSettings)
        return fields

    def apply(self, pfg, initial_finish=True):
        data = self.getContent()
        existing_ids = pfg.objectIds()
        
        mailer = getattr(pfg, RECIPIENT_MAILER_ID, None)
        if mailer is not None:
            execCondition = mailer.getRawExecCondition()
            if not execCondition or execCondition in ('request/form/recip_email|nothing', 'python:False'):
                mailer.setExecCondition(data['email'] and 'request/form/recip_email|nothing' or 'python:False')

        if SAVEDATA_ID not in existing_ids:
            pfg.invokeFactory(id=SAVEDATA_ID, type_name="FormSaveDataAdapter")
            sda = getattr(pfg, SAVEDATA_ID)
            alsoProvides(sda, IMultiplexedActionAdapter)
            sda.setTitle(utranslate(DOMAIN, _(u'Saved Letters'), context=self.request))
        sda = getattr(pfg, SAVEDATA_ID)
        adapters = list(pfg.actionAdapter)
        if SAVEDATA_ID in adapters:
            adapters.remove(SAVEDATA_ID)
            pfg.setActionAdapter(adapters)
        execCondition = sda.getRawExecCondition()
        if not execCondition or execCondition in ('python:True', 'python:False'):
            sda.setExecCondition(data['savedata'] and 'python:True' or 'python:False')

        if RENDERED_LETTER_ID not in existing_ids:
            pfg.invokeFactory(id=RENDERED_LETTER_ID, type_name='FormStringField')
            f = getattr(pfg, RENDERED_LETTER_ID)
            f.setServerSide(True)
            f.setTitle(utranslate(DOMAIN, _(u'Rendered Letter'), context=self.request))
            f.setDescription(utranslate(DOMAIN, _(u'This hidden field is used to provide the rendered letter to the mailer and save data adapters.'), context=self.request))
        
        if salesforce_is_configured() and data['save_lead']:
            if ORG_FIELD_ID not in existing_ids:
                pfg.invokeFactory(id=ORG_FIELD_ID, type_name='FormStringField')
                f = getattr(pfg, ORG_FIELD_ID)
                f.setTitle(utranslate(DOMAIN, _(u'Organization'), context=self.request))
                f.setDescription(utranslate(DOMAIN, _(u"This field is used internally to provide the required 'Company' value to Salesforce.com"), context=self.request))
                f.setServerSide(True)
                if not f.getFgDefault():
                    f.setFgDefault(utranslate(DOMAIN, _(u'[not provided]'), context=self.request))
                f.reindexObject()

            if SF_LEAD_ID not in existing_ids:
                pfg.invokeFactory(id=SF_LEAD_ID, type_name='SalesforcePFGAdapter')
                a = getattr(pfg, SF_LEAD_ID)
                a.setTitle(utranslate(DOMAIN, _(u'Salesforce.com Lead Adapter'), context=self.request))
                a.setSFObjectType('Lead')
                a.setFieldMap((
                    dict(field_path='first', form_field=utranslate(DOMAIN, _(u'First Name'), context=self.request), sf_field='FirstName'),
                    dict(field_path='last', form_field=utranslate(DOMAIN, _(u'Last Name'), context=self.request), sf_field='LastName'),
                    dict(field_path='email', form_field=utranslate(DOMAIN, _(u'E-mail Address'), context=self.request), sf_field='Email'),
                    dict(field_path='street', form_field=utranslate(DOMAIN, _(u'Street Address'), context=self.request), sf_field='Street'),
                    dict(field_path='city', form_field=utranslate(DOMAIN, _(u'City'), context=self.request), sf_field='City'),
                    dict(field_path='state', form_field=utranslate(DOMAIN, _(u'State'), context=self.request), sf_field='State'),
                    dict(field_path='zip', form_field=utranslate(DOMAIN, _(u'Postal Code'), context=self.request), sf_field='PostalCode'),
                    dict(field_path=ORG_FIELD_ID, form_field=utranslate(DOMAIN, _(u'Organization'), context=self.request), sf_field='Company'),
                    ))
                if hasattr(a, 'setPresetValueMap'): # BBB for salesforcepfgadapter < 1.6b2
                    a.setPresetValueMap((
                        dict(value='Web', sf_field='LeadSource'),
                        ))
                a.reindexObject()

            if data['campaign_id']:
                if CAMPAIGN_ID_FIELD_ID not in existing_ids:
                    pfg.invokeFactory(id=CAMPAIGN_ID_FIELD_ID, type_name='FormStringField')
                    f = getattr(pfg, CAMPAIGN_ID_FIELD_ID)
                    f.setTitle(utranslate(DOMAIN, _(u'Salesforce.com Campaign ID'), context=self.request))
                    f.setDescription(utranslate(DOMAIN, _(u'This field is used to supply the ID of a Salesforce.com Campaign to the CampaignMember adapter.'), context=self.request))
                    f.setServerSide(True)
                    f.reindexObject()
                else:
                    f = getattr(pfg, CAMPAIGN_ID_FIELD_ID)
                f.setFgDefault(data['campaign_id'])

                if SF_CAMPAIGNMEMBER_ID not in existing_ids:
                    pfg.invokeFactory(id=SF_CAMPAIGNMEMBER_ID, type_name='SalesforcePFGAdapter')
                    a = getattr(pfg, SF_CAMPAIGNMEMBER_ID)
                    a.setTitle(utranslate(DOMAIN, _(u'Salesforce.com CampaignMember Adapter'), context=self.request))
                    a.setSFObjectType('CampaignMember')
                    a.setFieldMap((
                        dict(field_path=CAMPAIGN_ID_FIELD_ID, form_field=utranslate(DOMAIN, _(u'Campaign ID'), context=self.request), sf_field='CampaignId'),
                        ))
                    a.setDependencyMap((
                        dict(adapter_id=SF_LEAD_ID, adapter_name=utranslate(DOMAIN, _(u'Salesforce.com Lead Adapter'), context=self.request), sf_field='LeadId'),
                        ))
                    a.reindexObject()
            else:
                objs_to_delete = []
                if SF_CAMPAIGNMEMBER_ID in existing_ids:
                    objs_to_delete.append(SF_CAMPAIGNMEMBER_ID)
                if CAMPAIGN_ID_FIELD_ID in existing_ids:
                    objs_to_delete.append(CAMPAIGN_ID_FIELD_ID)
                pfg.manage_delObjects(objs_to_delete)
        else:
            objs_to_delete = []
            if SF_LEAD_ID in existing_ids:
                objs_to_delete.append(SF_LEAD_ID)
            if SF_CAMPAIGNMEMBER_ID in existing_ids:
                objs_to_delete.append(SF_CAMPAIGNMEMBER_ID)
            if CAMPAIGN_ID_FIELD_ID in existing_ids:
                objs_to_delete.append(CAMPAIGN_ID_FIELD_ID)
            if objs_to_delete:
                pfg.manage_delObjects(objs_to_delete)
                adapters = list(pfg.actionAdapter)
                for id in objs_to_delete:
                    if id in adapters:
                        adapters.remove(id)
                pfg.actionAdapter = adapters

    def load(self, pfg):
        data = self.getContent()

        sda = getattr(pfg, SAVEDATA_ID, None)
        data['savedata'] = False
        if sda is not None:
            data['savedata'] = (sda.getRawExecCondition() != 'python:False')

        mailer = getattr(pfg, RECIPIENT_MAILER_ID, None)
        data['email'] = False
        if mailer is not None:
            data['email'] = (mailer.getRawExecCondition() != 'python:False')

        data['save_lead'] = False
        sfa = getattr(pfg, SF_LEAD_ID, None)
        if sfa is not None:
            data['save_lead'] = True
        campaign_id_field = getattr(pfg, CAMPAIGN_ID_FIELD_ID, None)
        data['campaign_id'] = ''
        if campaign_id_field is not None:
            data['campaign_id'] = safe_unicode(campaign_id_field.getFgDefault())
