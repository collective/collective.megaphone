from zope.interface import implements
from zope.component import getMultiAdapter
from zope.cachedescriptors.property import Lazy as lazy_property
from zope.annotation.interfaces import IAnnotations

from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base

from zope import schema
from zope.formlib import form

from Products.CMFCore.utils import _checkPermission
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.vocabularies.catalog import SearchableTextSourceBinder
from plone.app.form.widgets.uberselectionwidget import UberSelectionWidget

from collective.megaphone.config import ANNOTATION_KEY, VIEW_SIGNATURES_PERMISSION
from collective.megaphone.interfaces import IMegaphone
from collective.megaphone import MegaphoneMessageFactory as _


class ICallToActionPortlet(IPortletDataProvider):
    """A portlet which prompts the user to sign a Megaphone letter or petition.
    """

    megaphone_path = schema.Choice(
        title=_(u"Megaphone"),
        description=_(u"Find the Megaphone you want to display a call to action for."),
        required=True,
        source=SearchableTextSourceBinder({'object_provides' : IMegaphone.__identifier__},
                                           default_query='path:'))


class Assignment(base.Assignment):
    implements(ICallToActionPortlet)

    megaphone_path = None

    def __init__(self, megaphone_path=None):
        self.megaphone_path = megaphone_path

    @property
    def title(self):
        return 'Megaphone: /%s' % (self.megaphone_path or '')

class Renderer(base.Renderer):
    render = ViewPageTemplateFile('calltoaction.pt')
    
    @lazy_property
    def megaphone(self):
        path = self.data.megaphone_path or ''
        if path.startswith('/'):
            path = path[1:]
        if not path:
            return None

        portal_state = getMultiAdapter((self.context, self.request), name=u'plone_portal_state')
        portal = portal_state.portal()
        return portal.restrictedTraverse(path, default=None)

    @lazy_property
    def settings(self):
        return IAnnotations(self.megaphone).get(ANNOTATION_KEY, {}).get('signers', {})

    @lazy_property
    def signers_listing(self):
        return self.megaphone.restrictedTraverse('@@signers')

    def rendered_signers(self):
        batch_size = self.settings.get('sig_portlet_batch_size', 3)
        return self.signers_listing.rendered_signers(template_id='sig_portlet_template', limit=batch_size)

    @property
    def megaphone_url(self):
        return self.megaphone.absolute_url()

    @property
    def at_megaphone(self):
        return self.request['ACTUAL_URL'].startswith(self.megaphone_url)

    @property
    def has_min_count(self):
        return self.signers_listing.count > self.settings.get('sig_portlet_min_count', 20)

    def render_text(self):
        return self.settings.get('sig_portlet_text', '').replace('\n', '<br/>')

    @property
    def available(self):
        context_state = getMultiAdapter((self.context, self.request), name=u'plone_context_state')
        if not context_state.is_view_template():
            return False
        
        if self.megaphone is None:
            return False
        
        if not self.has_min_count:
            return False
        
        return True
    
    @property
    def can_view_signatures(self):
        return _checkPermission(VIEW_SIGNATURES_PERMISSION, self.megaphone)


class AddForm(base.AddForm):
    form_fields = form.Fields(ICallToActionPortlet)
    form_fields['megaphone_path'].custom_widget = UberSelectionWidget
    
    label = _(u"Add Megaphone Portlet")
    description = _(u"This portlet promotes a Megaphone action letter or petition.")

    def create(self, data):
        return Assignment(**data)

class EditForm(base.EditForm):
    form_fields = form.Fields(ICallToActionPortlet)
    form_fields['megaphone_path'].custom_widget = UberSelectionWidget

    label = _(u"Edit Megaphone Portlet")
    description = _(u"This portlet promotes a Megaphone action letter or petition.")
