from collective.megaphone.tests.base import MegaphoneTestCase
from Testing.ZopeTestCase.utils import makerequest

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
            'signers.widgets.template': u'${foobar}',
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

def test_suite():
    import unittest
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
