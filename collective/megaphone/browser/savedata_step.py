from collective.megaphone.config import SAVEDATA_ID, RENDERED_LETTER_ID
from collective.megaphone.browser.recipient_multiplexer import IMultiplexedActionAdapter
from collective.z3cform.wizard import wizard
from z3c.form import field
from zope import schema
from zope.interface import Interface, alsoProvides

class ISaveDataStep(Interface):
    savedata = schema.Bool(
        title = u'I want to save a copy of each submitted letter.',
        description = u'The letters will be stored in a PloneFormGen Save Data Adapter.',
        default = False,
        )

class SaveDataStep(wizard.Step):
    prefix = 'savedata'
    label = 'Letter Storage'
    description = u"This step allows you to configure what happens to the letters after they are submitted."
    fields = field.Fields(ISaveDataStep)

    def apply(self, pfg, initial_finish=True):
        data = self.getContent()
        
        if SAVEDATA_ID not in pfg.objectIds():
            pfg.invokeFactory(id=SAVEDATA_ID, type_name="FormSaveDataAdapter")
            sda = getattr(pfg, SAVEDATA_ID)
            alsoProvides(sda, IMultiplexedActionAdapter)
            sda.setTitle('Saved Letters')
        sda = getattr(pfg, SAVEDATA_ID)
        adapters = list(pfg.actionAdapter)
        if SAVEDATA_ID in adapters:
            adapters.remove(SAVEDATA_ID)
            pfg.setActionAdapter(adapters)
        sda.setExecCondition(data['savedata'] and 'python:True' or 'python:False')
        
        if RENDERED_LETTER_ID not in pfg.objectIds():
            pfg.invokeFactory(id=RENDERED_LETTER_ID, type_name='FormStringField')
            f = getattr(pfg, RENDERED_LETTER_ID)
            f.setServerSide(True)
            f.setTitle('Rendered Letter')
            f.setDescription('This hidden field is used to provide the rendered letter to the mailer and save data adapters.')

    def load(self, pfg):
        data = self.getContent()
        sda = getattr(pfg, SAVEDATA_ID, None)
        if sda is not None:
            data['savedata'] = (sda.getRawExecCondition() == 'python:True')
