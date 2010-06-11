from collective.megaphone.tests.base import MegaphoneTestCase
from Testing.ZopeTestCase.utils import makerequest
from Products.Five.testbrowser import Browser

from collective.z3cform.wizard import wizard
from collective.megaphone.browser.signers_step import SignersStep

class DummyStep(wizard.Step):
    prefix = 'dummy'

class DummyWizard(wizard.Wizard):
    steps = SignersStep, DummyStep

class TestSignersStep(MegaphoneTestCase):

    def afterSetUp(self):
        from zope.interface import alsoProvides
        from z3c.form.interfaces import IFormLayer
        
        self.form = self.folder[self.folder.invokeFactory('FormFolder', 'form')]
        self.request = makerequest(self.app).REQUEST
        alsoProvides(self.request, IFormLayer)
        self.wizard = DummyWizard(self.form, self.request)
        self.session = self.request.SESSION[self.wizard.sessionKey] = {}
        self.step = SignersStep(self.form, self.request, self.wizard)
    
    def test_load(self):
        self.form.__annotations__['collective.megaphone'] = {
            'signers': {
                'show_signers': False,
                'batch_size': 50,
                'template': u'bar',
                },
            }
        self.step.load(self.form)
        self.assertEqual(self.session['signers'], self.form.__annotations__['collective.megaphone']['signers'])
    
    def test_continue(self):
        data = {
            'signers.widgets.show_signers': u'true',
            'signers.widgets.batch_size': u'20',
            'signers.widgets.template': u'baz',
            'form.buttons.continue': 1,
        }
        self.request.form.update(data)
        self.wizard.update()
        self.assertEqual({'show_signers': True, 'batch_size': 20, 'template': u'baz'}, self.session['signers'])

    def test_continue_accepts_non_ascii_template(self):
        data = {
            'signers.widgets.show_signers': u'true',
            'signers.widgets.batch_size': u'20',
            'signers.widgets.template': u'\u9731',
            'form.buttons.continue': 1,
        }
        self.request.form.update(data)
        self.wizard.update()
        self.assertEqual({'show_signers': True, 'batch_size': 20, 'template': u'\u9731'}, self.session['signers'])

    def test_continue_accepts_valid_template_variable(self):
        self.session['formfields'] = {'fields': {'foobar': ()}}
        data = {
            'signers.widgets.show_signers': u'true',
            'signers.widgets.batch_size': u'20',
            'signers.widgets.template': u'${sender_foobar}',
            'form.buttons.continue': 1,
        }
        self.request.form.update(data)
        self.wizard.update()
        self.failIf(self.wizard.currentStep.widgets.errors)
    
    def test_continue_blocks_invalid_template_variable(self):
        data = {
            'signers.widgets.show_signers': u'true',
            'signers.widgets.batch_size': u'20',
            'signers.widgets.template': u'${foobar}',
            'form.buttons.continue': 1,
        }
        self.request.form.update(data)
        self.wizard.update()
        self.failUnless(self.wizard.currentStep.widgets.errors)
    
    def test_apply(self):
        self.session['signers'] = {
            'show_signers': True,
            'batch_size': 30,
            'template': u'foo',
            }
        self.step.apply(self.form)
        self.assertEqual(self.session['signers'], self.form.__annotations__['collective.megaphone']['signers'])

class TestSignersViewlet(MegaphoneTestCase):

    def afterSetUp(self):
        self._create_megaphone()
        # enable savedata adapter
        self.portal.megaphone['saved-letters'].setExecCondition('python:True')
        
        self.browser = Browser()
        self._submit_response()

    def _submit_response(self):
        self.browser.open('http://nohost/plone/megaphone')
        self.browser.getControl('First Name').value = 'Harvey'
        self.browser.getControl('Last Name').value = 'Frank'
        self.browser.getControl('E-mail Address').value = 'harvey@example.com'
        self.browser.getControl('City').value = 'Seattle'
        self.browser.getControl('State').value = ['WA']
        self.browser.getControl('Letter Body').value = 'body'
        self.browser.getControl('Send').click()

    def test_viewlet_appears_when_enabled(self):
        self.browser.open('http://nohost/plone/megaphone')
        self.failIf('Recent signers' in self.browser.contents)
        
        # turn on signer list
        self.portal.megaphone.__annotations__['collective.megaphone']['signers']['show_signers'] = True
        
        self.browser.open('http://nohost/plone/megaphone')
        self.failUnless('Recent signers' in self.browser.contents)
    
    def test_viewlet_shows_signers_in_table(self):
        # turn on signer list
        self.portal.megaphone.__annotations__['collective.megaphone']['signers']['show_signers'] = True
        # the default template uses a table layout
        self.browser.open('http://nohost/plone/megaphone')
        expected = "<td>Harvey</td><td>Seattle, WA</td><td>body</td>"
        self.failUnless(expected in self.browser.contents)

    def test_viewlet_shows_signers_in_list(self):
        # turn on signer list
        self.portal.megaphone.__annotations__['collective.megaphone']['signers']['show_signers'] = True
        # adjust template
        self.portal.megaphone.__annotations__['collective.megaphone']['signers']['template'] = \
            u'${sender_first}, ${sender_city}, ${sender_state}: ${sender_body}'
        
        self.browser.open('http://nohost/plone/megaphone')
        expected = "Harvey, Seattle, WA: body"
        self.failUnless(expected in self.browser.contents)

def test_suite():
    import unittest
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
