from collective.megaphone.tests.base import MegaphoneTestCase
from Products.Five.testbrowser import Browser

from collective.megaphone.interfaces import IMegaphone

class TestPetition(MegaphoneTestCase):

    def test_petition_factory(self):
        pass
    
    def test_petition_wizard(self):
        # log in
        browser = Browser()
        browser.handleErrors = False
        self.app.acl_users.userFolderAddUser('root', 'secret', ['Manager'], [])
        browser.addHeader('Authorization', 'Basic root:secret')
        browser.open('http://nohost/plone')

        # make sure we get the right steps for configuring a petition
        browser.getLink('Megaphone Action').click()
        browser.getControl(name='intro.widgets.megaphone_type:list').value = ['petition']
        browser.getControl('Continue').click()
        
        self.failUnless('General Settings' in browser.contents)
        browser.getControl('Title').value = 'Petition'
        browser.getControl('Continue').click()
        
        self.failUnless('Form Fields' in browser.contents)
        # remove captcha field
        browser.getControl(name='crud-edit.captcha.widgets.select:list').value = ['true']
        browser.getControl('Delete').click()
        browser.getControl('Continue').click()
        
        self.failUnless('Thank You to Activist' in browser.contents)
        browser.getControl('Continue').click()
        self.failUnless('Delivery' in browser.contents)
        browser.getControl('Continue').click()
        self.failUnless('List of Signatures' in browser.contents)
        browser.getControl('Finish').click()
        self.failUnless('Megaphone Action Wizard Summary' in browser.contents)

        browser.getLink('View').click()
        self.assertEqual('http://nohost/plone/petition', browser.url)
        self.failUnless(IMegaphone.providedBy(self.portal.petition))

def test_suite():
    import unittest
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
