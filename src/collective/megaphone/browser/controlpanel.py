from collective.megaphone.utils import MegaphoneMessageFactory as _
from collective.megaphone.utils import get_megaphone_defaults, set_megaphone_defaults
from collective.megaphone.browser.megaphone import MegaphoneActionWizard, MegaphoneActionWizardView


class MegaphoneDefaultsWizard(MegaphoneActionWizard):
    label = _(u'Megaphone Defaults')
    description = _(u'You are editing the default values that will be used for all '
                    u'new Megaphone Actions added in this site.')
    successMessage = _(u'Your Megaphone defaults have been saved.')
    
    def initialize(self):
        defaults = get_megaphone_defaults()
        self.session.update(defaults)
        
        for step in self.activeSteps:
            if hasattr(step, 'initialize'):
                step.initialize()
        
        self.sync()

    def finish(self):
        set_megaphone_defaults(self.session)


class MegaphoneDefaultsWizardView(MegaphoneActionWizardView):
    form = MegaphoneDefaultsWizard
