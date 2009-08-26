from setuptools import setup, find_packages
import os

version = '1.0rc1'

setup(name='collective.megaphone',
      version=version,
      description="Run an online advocacy campaign from your Plone site.",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Development Status :: 4 - Beta",
        ],
      keywords='plone advocacy action letter',
      author='ONE/Northwest',
      author_email='davidglick@onenw.org',
      url='http://svn.plone.org/svn/collective/collective.megaphone/trunk',
      license='GPL',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'z3c.form>=1.9.0,<2.0.0dev',
          'plone.z3cform>=0.5.3',
          'plone.app.z3cform',
          'Products.PloneFormGen>=1.5.0',
          'collective.jqueryui',
          'collective.z3cform.wizard>=1.0b2',
          'Products.pipbox>=0.2dev',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """
      )
