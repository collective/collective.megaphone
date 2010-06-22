from zope.interface import implements
from zope.component import getMultiAdapter
from zope.cachedescriptors.property import Lazy as lazy_property

from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base

from zope import schema
from zope.formlib import form

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.vocabularies.catalog import SearchableTextSourceBinder
from plone.app.form.widgets.uberselectionwidget import UberSelectionWidget

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

    @property
    def available(self):
        return self.megaphone is not None


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
