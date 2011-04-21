from collective.megaphone.utils import DOMAIN, MegaphoneMessageFactory as _
from collective.megaphone.config import \
    SF_LEAD_ID, SF_CAMPAIGNMEMBER_ID, CAMPAIGN_ID_FIELD_ID, ORG_FIELD_ID
from collective.z3cform.wizard import wizard
from z3c.form import field
from zope import schema
from zope.app.component.hooks import getSite
from zope.interface import Interface
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from Products.CMFPlone.i18nl10n import utranslate

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
        description = _(u'A PloneFormGen-Salesforce Adapter will be created to add a new Lead in Salesforce. '
                        u'If you want to create something other than a Lead, select this here and then go '
                        u'change the object type setting of the adapter that will be created when you complete '
                        u'the wizard.'),
        default = False,
        )
    
    lead_source = schema.ASCIILine(
        title = _(u'Salesforce.com Lead Source'),
        description = _(u'Lead Source to set for Leads created via this Megaphone.'),
        default = 'Web',
        required = True,
        )

    campaign_id = schema.TextLine(
        title = _(u'Salesforce.com Campaign ID'),
        description = _(u"Enter the ID of a Salesforce campaign (which can be found by looking " +
                        u"at the campaign's URL in the Salesforce.com UI).  If this is configured, " +
                        u"the new Lead will be associated with this campaign."),
        required = False,
        )
    
    campaign_status = schema.ASCIILine(
        title = _(u'Salesforce.com Campaign Status'),
        description = _(u'The campaign status of new campaign members will be set to this string.'),
        default = 'Responded',
        required = False,
        )

class SalesforceStep(wizard.Step):
    prefix = 'salesforce'
    label = _(u'Save to Salesforce')
    description = _(u"This step allows you to record info about signers in Salesforce.com.")
    
    fields = field.Fields(ISalesforceSettings)

    def apply(self, pfg, initial_finish=True):
        data = self.getContent()
        existing_ids = pfg.objectIds()
        
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
                a.reindexObject()
            else:
                a = getattr(pfg, SF_LEAD_ID)
            if hasattr(a, 'setPresetValueMap'): # BBB for salesforcepfgadapter < 1.6b2
                preset_map = list(a.getPresetValueMap())
                found = False
                for entry in preset_map:
                    if entry['sf_field'] == 'LeadSource':
                        entry['value'] = data['lead_source']
                        found = True
                if not found:
                    preset_map.append({'value': data['lead_source'], 'sf_field': 'LeadSource'})
                a.setPresetValueMap(tuple(preset_map))

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
            
            if data['campaign_status']:
                a = getattr(pfg, SF_CAMPAIGNMEMBER_ID, None)
                if a is not None:
                    preset_map = list(a.getPresetValueMap())
                    found = False
                    for entry in preset_map:
                        if entry['sf_field'] == 'Status':
                            entry['value'] = data['campaign_status']
                            found = True
                    if not found:
                        preset_map.append({'value': data['campaign_status'], 'sf_field': 'Status'})
                    a.setPresetValueMap(tuple(preset_map))
            else:
                a = getattr(pfg, SF_CAMPAIGNMEMBER_ID, None)
                if a is not None:
                    preset_map = a.getPresetValueMap()
                    preset_map = [entry for entry in preset_map if entry['sf_field'] != 'Status']
                    a.setPresetValueMap(tuple(preset_map))
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

        data['save_lead'] = False
        sfa = getattr(pfg, SF_LEAD_ID, None)
        if sfa is not None:
            data['save_lead'] = True
            data['lead_source'] = 'Web'
            preset_map = sfa.getPresetValueMap()
            for entry in preset_map:
                if entry['sf_field'] == 'LeadSource':
                    data['lead_source'] = entry['value']
        campaign_id_field = getattr(pfg, CAMPAIGN_ID_FIELD_ID, None)
        data['campaign_id'] = ''
        if campaign_id_field is not None:
            data['campaign_id'] = safe_unicode(campaign_id_field.getFgDefault())
        data['campaign_status'] = ''
        a = getattr(pfg, SF_CAMPAIGNMEMBER_ID, None)
        if a is not None:
            preset_map = a.getPresetValueMap()
            for entry in preset_map:
                if entry['sf_field'] == 'Status':
                    data['campaign_status'] = entry['value']
