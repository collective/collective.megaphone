from Products.Five import BrowserView
from collective.megaphone.browser.recipient_multiplexer import recipient_multiplexer

class ThanksPage(BrowserView):
    
    def renderedLetters(self):
        letters = []
        form = self.context.aq_inner.aq_parent
        for request in recipient_multiplexer(form, self.request):
            letters.append(form.restrictedTraverse('@@letter-renderer').render_letter())
        return letters
