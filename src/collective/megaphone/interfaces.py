from zope.interface import Interface

class IMegaphone(Interface):
    """A PloneFormGen form masquerading as a Megaphone action letter or petition.
    """

# deprecated
IActionLetter = IMegaphone
