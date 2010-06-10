import doctest, unittest
from Testing import ZopeTestCase as ztc
from collective.megaphone.tests.base import HAS_SALESFORCE, MegaphoneTestCase

def test_suite():
    tests = []
    if HAS_SALESFORCE:
        tests.append(
            ztc.FunctionalDocFileSuite(
                'letter.txt', package='collective.megaphone.tests',
                test_class=MegaphoneTestCase,
                optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS),
        )
    else:
        tests.append(
            ztc.FunctionalDocFileSuite(
                'letter_no_salesforce.txt', package='collective.megaphone.tests',
                test_class=MegaphoneTestCase,
                optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS),
        )
    return unittest.TestSuite(tests)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
