from collective.megaphone.tests.base import MegaphoneTestCase

class TestSignersStep(MegaphoneTestCase):

    def afterSetUp(self):
        from collective.megaphone.browser.letter import ActionLetterWizard
        from collective.megaphone.browser.signers_step import SignersStep
        
        self.form = self.folder[self.folder.invokeFactory('FormFolder', 'form')]
        wizard = ActionLetterWizard(self.form, self.app.REQUEST)
        self.session = self.app.REQUEST.SESSION[wizard.sessionKey] = {}
        self.step = SignersStep(self.form, self.app.REQUEST, wizard)
    
    def testLoad(self):
        self.form.__annotations__['collective.megaphone'] = {
            'signers': {
                'show_signers': False,
                'batch_size': 50,
                'template': u'bar',
                },
            }
        self.step.load(self.form)
        self.assertEqual(self.session['signers'], self.form.__annotations__['collective.megaphone']['signers'])
    
    def testApply(self):
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
