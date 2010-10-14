from Products.PloneTestCase import PloneTestCase as ptc
from Products.Five.testbrowser import Browser
from collective.megaphone.tests.layer import MegaphoneLayer

ptc.setupPloneSite()


class MegaphoneTestCase(ptc.FunctionalTestCase):
    """Base class for functional integration tests for collective.megaphone.
    """

    layer = MegaphoneLayer

    @property
    def mailhost(self):
        return self.portal.MailHost

    def _create_megaphone(self, type='letter'):
        browser = Browser()
        browser.handleErrors = False
        browser.addHeader('Authorization', 'Basic root:secret')
        browser.open('http://nohost/plone')
        browser.getLink('Megaphone Action').click()
        browser.getControl(name='intro.widgets.megaphone_type:list').value = [type]
        browser.getControl('Continue').click()
        browser.getControl('Title').value = 'Megaphone'
        browser.getControl('Continue').click()
        browser.getControl(name='crud-edit.captcha.widgets.select:list').value = ['true']
        browser.getControl('Delete').click()
        while 1:
            try:
                browser.getControl('Continue').click()
            except LookupError:
                break
        browser.getControl('Finish').click()
        browser.open('http://nohost/plone/megaphone')
        browser.getLink('Publish').click()

class MegaphoneFunctionalTestCase(MegaphoneTestCase):
    # We need a separate class for use with FunctionalDocFileSuite, or else
    # the default test loader finds the dummy runTest method it adds
    # when the case is subsequently used by another sort of test suite. o.O
    pass
