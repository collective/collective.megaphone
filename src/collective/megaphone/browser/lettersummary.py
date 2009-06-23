from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName
from collective.megaphone.config import THANK_YOU_EMAIL_ID, SAVEDATA_ID

class LetterSummary(BrowserView):

    template = ViewPageTemplateFile('lettersummary.pt')

    def __call__(self):
        return self.template()

    def letterJustCreated(self):
        """Return True if the user just created the letter and should therefore be congratulated"""
        return self.request.get('new', False) is not False

    def getThankYouEmailUrl(self):
        """Get the full url for the Mailer Adapter that's used for thanking the letter-writer.
        (None means there isn't one)
        """
        if THANK_YOU_EMAIL_ID in self.context.objectIds():
            return getattr(self.context, THANK_YOU_EMAIL_ID).absolute_url()
        return None

    def getThankYouPageUrl(self):
        """Get the full url for the thank you page the letter-writer sees after filling out the letter form
        (None means there isn't one)
        """
        # this id is the one given by PFG when it creates a form
        thanks_page_id = "thank-you"
        if thanks_page_id in self.context.objectIds():
            return getattr(self.context, thanks_page_id).absolute_url()
        return None

    def getSaveDataUrl(self):
        """
        Get the URL for the save data adapter, if present.
        """
        sda = getattr(self.context, SAVEDATA_ID, None)
        if sda is not None:
            return sda.absolute_url()

    def getSFPFGUrls(self):
        """Return a list of the full urls and titles of the SalesforcePFGAdapters in the form (we support multiple because
        they can be chained. But the wizard only would create at most one.)
        """
        pc = getToolByName(self.context, "portal_catalog")
        return [{'url':b.getURL(), 'title':b.Title,} for b in pc(portal_type="SalesforcePFGAdapter", path='/'.join(self.context.getPhysicalPath()))]
