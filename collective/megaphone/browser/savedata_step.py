from collective.megaphone.config import SAVEDATA_ID, RECIPIENT_MAILER_ID, RENDERED_LETTER_ID, \
    SF_LEAD_ID, SF_CAMPAIGNMEMBER_ID
from collective.megaphone.browser.recipient_multiplexer import IMultiplexedActionAdapter
from collective.z3cform.wizard import wizard
from z3c.form import field
from zope import schema
from zope.app.component.hooks import getSite
from zope.interface import Interface, alsoProvides
from Products.CMFCore.utils import getToolByName

class ISaveDataStep(Interface):
    
    email = schema.Bool(
        title = u'Send the letter by e-mail to each recipient.',
        description = u'The letters will be sent to the e-mail addresses you entered in the Recipients step.',
        default = True,
        )

    savedata = schema.Bool(
        title = u'Save a copy of each submitted letter.',
        description = u'The letters will be stored in a PloneFormGen Save Data Adapter.',
        default = False,
        )

def salesforce_is_configured():
    site = getSite()
    
    sfbc = getToolByName(site, 'portal_salesforcebaseconnector')
    ttool = getToolByName(site, 'portal_types')
    
    if sfbc is not None and 'SalesforcePFGAdapter' in ttool.objectIds():
        return True
    else:
        return False

class ISalesforceSettings(Interface):
    
    save_lead = schema.Bool(
        title = u"Save the sender's contact information as a Lead in Salesforce.com",
        description = u'A PloneFormGen-Salesforce Adapter will be created to add a new Lead in Salesforce.',
        default = False,
        )

    campaign_id = schema.TextLine(
        title = u'Salesforce.com Campaign ID',
        description = u"Enter the ID of a Salesforce campaign (which can be found by looking " + \
                      u"at the campaign's URL in the Salesforce.com UI).  If this is configured, " + \
                      u"the new Lead will be associated with this campaign.",
        required = False,
        )

class SaveDataStep(wizard.Step):
    prefix = 'savedata'
    label = 'Delivery'
    description = u"This step allows you to configure what happens to the letters after they are submitted."
    
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
            sda.setTitle('Saved Letters')
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
            f.setTitle('Rendered Letter')
            f.setDescription('This hidden field is used to provide the rendered letter to the mailer and save data adapters.')
        
        if salesforce_is_configured() and data['save_lead']:
            if SF_LEAD_ID not in existing_ids:
                pfg.invokeFactory(id=SF_LEAD_ID, type_name='SalesforcePFGAdapter')
                a = getattr(pfg, SF_LEAD_ID)
                a.setTitle('Salesforce.com Lead Adapter')
                a.setSFObjectType('Lead')
                # XXX object type
                # XXX field mapping
                # TTT make sure action adapter is enabled/disabled correctly

            if data['campaign_id']:
                if SF_CAMPAIGNMEMBER_ID not in existing_ids:
                    pfg.invokeFactory(id=SF_CAMPAIGNMEMBER_ID, type_name='SalesforcePFGAdapter')
                    a = getattr(pfg, SF_CAMPAIGNMEMBER_ID)
                    a.setTitle('Salesforce.com CampaignMember Adapter')
                    a.setSFObjectType('CampaignMember')
                    # XXX object type, field mapping
            else:
                if SF_CAMPAIGNMEMBER_ID in existing_ids:
                    pfg.manage_delObjects([SF_CAMPAIGNMEMBER_ID])
        else:
            objs_to_delete = []
            if SF_LEAD_ID in existing_ids:
                objs_to_delete.append(SF_LEAD_ID)
            if SF_CAMPAIGNMEMBER_ID in existing_ids:
                objs_to_delete.append(SF_CAMPAIGNMEMBER_ID)
            if objs_to_delete:
                pfg.manage_delObjects(objs_to_delete)
            # XXX adjust active action adapters

    def load(self, pfg):
        data = self.getContent()
        sda = getattr(pfg, SAVEDATA_ID, None)
        if sda is not None:
            data['savedata'] = (sda.getRawExecCondition() != 'python:False')
        mailer = getattr(pfg, RECIPIENT_MAILER_ID, None)
        if mailer is not None:
            data['email'] = (mailer.getRawExecCondition() != 'python:False')

        # XXX load SF settings