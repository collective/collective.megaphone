from collective.megaphone.utils import DOMAIN, MegaphoneMessageFactory as _
from collective.megaphone.config import \
    SF_LEAD_ID, SF_CAMPAIGNMEMBER_ID, CAMPAIGN_ID_FIELD_ID, ORG_FIELD_ID, \
    SF_CONTACT_FIELDMAPPING, SF_LEAD_FIELDMAPPING
from collective.z3cform.wizard import wizard
from z3c.form import field
from zope import schema
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
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
        title = _(u"Save the sender's contact information to Salesforce.com"),
        description = _(u'A PloneFormGen-Salesforce Adapter will be created.'),
        default = False,
        )
        
    sfobj_type = schema.Choice(
        title = _(u'Salesforce Object'),
        description = _(u'Select the type of object that will be created.'),
        vocabulary = SimpleVocabulary([
            SimpleTerm(value=u'Lead', title=_(u'Lead')),
            SimpleTerm(value=u'Contact', title=_(u'Contact')),]),
        default = u'Lead',
        required = True,
        )
    
    lead_source = schema.ASCIILine(
        title = _(u'Salesforce.com Lead Source'),
        description = _(u'Lead Source to set for Leads created via this Megaphone.'),
        default = 'Web',
        required = False,
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
    
    def _getFieldMap(self, sfobj_type):
        """
        Returns the field mapping that gets set with setFieldMap.
        """
        
        if sfobj_type == u'Contact':
            field_source = SF_CONTACT_FIELDMAPPING
        else:
            field_source = SF_LEAD_FIELDMAPPING
            
        return tuple([dict(field_path=p, form_field=utranslate(DOMAIN, _(l),
            context=self.request), sf_field=s) for (p, s, l) in field_source])

    def apply(self, pfg, initial_finish=True):
        data = self.getContent()
        existing_ids = pfg.objectIds()
        sfobj_type = data['sfobj_type']
        obj_adapter_title = u'Salesforce.com %s Adapter' % sfobj_type
        lead_source = data['lead_source'] or u'Web'
        
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
                new_adapter = True
            else:
                a = getattr(pfg, SF_LEAD_ID)
                new_adapter = False
            if new_adapter or not a.getSFObjectType() == sfobj_type:
                a.setTitle(utranslate(DOMAIN, _(obj_adapter_title), context=self.request))
                a.setSFObjectType(sfobj_type)
                a.setFieldMap(self._getFieldMap(sfobj_type))
                a.reindexObject()
            if hasattr(a, 'setPresetValueMap'): # BBB for salesforcepfgadapter < 1.6b2
                preset_map = list(a.getPresetValueMap())
                found = False
                for entry in preset_map:
                    if entry['sf_field'] == 'LeadSource':
                        entry['value'] = lead_source
                        found = True
                if not found:
                    preset_map.append({'value': lead_source, 'sf_field': 'LeadSource'})
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
                    a.reindexObject()
                else:
                    a = getattr(pfg, SF_CAMPAIGNMEMBER_ID)
                a.setDependencyMap((
                    dict(adapter_id=SF_LEAD_ID, adapter_name=utranslate(DOMAIN, _(obj_adapter_title), context=self.request), sf_field='%sId' % sfobj_type),
                    ))
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
            if sfa.getSFObjectType() in [u'Contact', u'Lead']:
                data['sfobj_type'] = sfa.getSFObjectType()
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
