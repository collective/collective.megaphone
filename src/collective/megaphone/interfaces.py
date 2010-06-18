from zope.interface import Interface

class IMegaphone(Interface):
    """A PloneFormGen form masquerading as a Megaphone action letter or petition.
    """

class IActionAdapterMultiplexer(Interface):
    """
    A Archetypes-based folder for grouping PloneFormGen action adapters that
    should be run several times based on some input sequence.
    """

# deprecated
IActionLetter = IMegaphone
