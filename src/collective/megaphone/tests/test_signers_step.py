from collective.megaphone.tests.base import MegaphoneTestCase
from Testing.ZopeTestCase.utils import makerequest
from Products.Five.testbrowser import Browser

from collective.z3cform.wizard import wizard
from collective.megaphone.browser.signers_step import SignersStep, assign_megaphone_portlet

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
                'show_sig_portlet': False,
                'batch_size': 50,
                'sig_portlet_template': u'bar',
                },
            }
        self.step.load(self.form)
        self.assertEqual(self.session['signers'], self.form.__annotations__['collective.megaphone']['signers'])
    
    _form_data = {
        'signers.widgets.show_sig_portlet': u'true',
        'signers.widgets.batch_size': u'20',
        'signers.widgets.sig_portlet_template': u'baz',
        'signers.widgets.sig_portlet_title': u'Title',
        'signers.widgets.sig_portlet_text': u'Text',
        'signers.widgets.sig_portlet_min_count': u'20',
        'signers.widgets.goose_factor': u'0',
        'signers.widgets.sig_portlet_batch_size': u'3',
        'signers.widgets.show_full_listing': u'true',
        'signers.widgets.full_template': u'baz',
        'form.buttons.continue': 1,
        }
    
    def test_continue(self):
        self.request.form.update(self._form_data)
        self.wizard.update()
        self.assertEqual({'show_sig_portlet': True, 'batch_size': 20, 'sig_portlet_template': u'baz',
                          'sig_portlet_title': u'Title', 'sig_portlet_text': u'Text', 'sig_portlet_min_count': 20,
                          'goose_factor': 0, 'sig_portlet_batch_size': 3, 'sig_portlet_button': None,
                          'sig_portlet_link': None, 'show_full_listing': True, 'full_template': u'baz'}, self.session['signers'])

    def test_continue_accepts_non_ascii_template(self):
        data = self._form_data.copy()
        data['signers.widgets.sig_portlet_template'] = u'\u9731'
        self.request.form.update(data)
        self.wizard.update()
        self.assertEqual({'show_sig_portlet': True, 'batch_size': 20, 'sig_portlet_template': u'\u9731',
                          'sig_portlet_title': u'Title', 'sig_portlet_text': u'Text', 'sig_portlet_min_count': 20,
                          'goose_factor': 0, 'sig_portlet_batch_size': 3, 'sig_portlet_button': None,
                          'sig_portlet_link': None, 'show_full_listing': True, 'full_template': u'baz'}, self.session['signers'])

    def test_continue_accepts_valid_template_variable(self):
        self.session['formfields'] = {'fields': {'foobar': ()}}
        data = self._form_data.copy()
        data['signers.widgets.sig_portlet_template'] = u'${sender_foobar}'
        self.request.form.update(data)
        self.wizard.update()
        self.failIf(self.wizard.currentStep.widgets.errors)
    
    def test_continue_blocks_invalid_template_variable(self):
        data = self._form_data.copy()
        data['signers.widgets.sig_portlet_template'] = u'${foobar}'
        self.request.form.update(data)
        self.wizard.update()
        self.failUnless(self.wizard.currentStep.widgets.errors)
    
    def test_apply(self):
        self.session['signers'] = {
            'show_sig_portlet': True,
            'batch_size': 30,
            'sig_portlet_template': u'foo',
            }
        self.step.apply(self.form)
        self.assertEqual(self.session['signers'], self.form.__annotations__['collective.megaphone']['signers'])

    def test_apply_forces_savedata_on_when_necessary(self):
        self._create_megaphone()
        self.session['signers'] = {
            'show_sig_portlet': True,
            'batch_size': 30,
            'sig_portlet_template': u'foo',
            }
        self.step.apply(self.portal.megaphone)
        self.assertEqual('python:True', self.portal.megaphone['saved-letters'].getRawExecCondition())

class TestCallToActionPortlet(MegaphoneTestCase):

    def afterSetUp(self):
        self._create_megaphone()
        # turn on signer portlet
        assign_megaphone_portlet(self.portal.megaphone, True)
        
        self.browser = Browser()
        self.browser.handleErrors = False
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

    def test_portlet_appears_when_enabled(self):
        self.browser.open('http://nohost/plone/megaphone')
        self.failUnless('Latest signers' in self.browser.contents)
        
        # turn off signer portlet
        assign_megaphone_portlet(self.portal.megaphone, False)
        
        self.browser.open('http://nohost/plone/megaphone')
        self.failIf('Latest signers' in self.browser.contents)
    
    def test_portlet_shows_signers_in_list(self):
        # adjust template
        self.portal.megaphone.__annotations__['collective.megaphone']['signers']['sig_portlet_template'] = \
            u'${sender_first}, ${sender_city}, ${sender_state}: ${sender_body}'
        
        self.browser.open('http://nohost/plone/megaphone')
        expected = "Harvey, Seattle, WA"
        self.failUnless(expected in self.browser.contents)

    def test_view_shows_signers_in_list(self):
        # adjust template
        self.portal.megaphone.__annotations__['collective.megaphone']['signers']['full_template'] = \
            u'${sender_first}, ${sender_city}, ${sender_state}: ${sender_body}'
        
        self.browser.open('http://nohost/plone/megaphone/signers')
        expected = "Harvey, Seattle, WA: body"
        self.failUnless(expected in self.browser.contents)

    def test_view_shows_signers_in_table(self):
        self.browser.open('http://nohost/plone/megaphone/signers')
        expected = "<td>Harvey</td><td>Seattle, WA</td><td>body</td>"
        self.failUnless(expected in self.browser.contents)

    def test_signers_view_batching(self):
        # fabricate a bunch of responses
        row = self.portal.megaphone['saved-letters']._inputStorage.values()[0]
        for x in xrange(50):
            new_row = row[:]
            new_row[1] = 'row_%s' % x
            self.portal.megaphone['saved-letters'].addDataRow(new_row)
        
        # make sure we see the most recent items
        self.browser.open('http://nohost/plone/megaphone/signers')
        self.failUnless('row_49' in self.browser.contents)
        self.failUnless('row_20' in self.browser.contents)
        self.failIf('row_19' in self.browser.contents)
        # make sure we can navigate to page 2
        self.browser.getLink('Next').click()
        self.failUnless('row_19' in self.browser.contents)
        self.failUnless('row_0' in self.browser.contents)
        self.failIf('row_20' in self.browser.contents)

def test_suite():
    import unittest
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
