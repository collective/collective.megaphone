from zope.interface import Interface

class IActionLetter(Interface):
    """ A PloneFormGen form masquerading as an action letter.
    """

class IActionAdapterMultiplexer(Interface):
    """
    A Archetypes-based folder for grouping PloneFormGen action adapters that
    should be run several times based on some input sequence.
    """