PROFILE = 'collective.megaphone:default'

def to_1_1(context):
    context.runImportStepFromProfile(PROFILE, 'types', run_dependencies=False, purge_old=False)
