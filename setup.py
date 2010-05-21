from setuptools import setup, find_packages

version = '1.3'

setup(name='collective.megaphone',
      version=version,
      description="Run an online advocacy campaign from your Plone site.",
      long_description=open("README.txt").read() + "\n" +
                       open("CHANGES.txt").read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Development Status :: 5 - Production/Stable",
        ],
      keywords='plone advocacy action letter',
      author='Groundwire',
      author_email='davidglick@groundwire.org',
      url='http://svn.plone.org/svn/collective/collective.megaphone/trunk',
      license='GPL',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'z3c.form>=1.9.0',
          'Plone',
          'plone.z3cform>=0.5.3',
          'plone.app.z3cform>=0.4.9',
          'Products.PloneFormGen>=1.5.0',
          'collective.jqueryui',
          'collective.z3cform.wizard>=1.1',
          'plone.app.jquerytools>=1.0b4',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """
      )
