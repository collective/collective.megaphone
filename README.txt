Introduction
============

Megaphone makes it easy to build powerful online advocacy campaigns in Plone.

Letters to decision makers
--------------------------
 * Collect arbitrary fields
 * Required and optional recipients
 * Save data locally
 * Save data to Salesforce.com (requires salesforcepfgadapter)
 * E-mail template-based letters to targets
 * Customizable thank-you letter to sender

Petitions
---------
 * Collect arbitrary fields
 * Save data locally
 * Save data to Salesforce.com (requires salesforcepfgadapter)
 * List signatures within your Plone site
 * Customizable thank-you letter to sender

Limitations
===========

No product is perfect. There are some important things Megaphone doesn't do
(yet), including:

 * Matching of users to targets based on postal address
 * Delivery to targets who don't have a publicly-accessible email address


How it works
============

Megaphone builds on top of several fantastic Plone products to do its work
without reinventing the wheel.

 * The heart of Megaphone is `PloneFormGen`_, which provides the core
   form-handling capabilities.
 * Because Megaphone actions are a fairly complicated PloneFormGens with lots of
   defaults, we've built `collective.z3cform.wizard`_ which lets us make a very
   user-friendly wizard for building out the advocacy letter. The wizard
   can be run and then re-run to let a user change the settings. More advanced
   users can directly edit the PloneFormGen fields and objects to create more
   complex setups.
 * Salesforce integration is via the `Salesforce PFG Adapter`_ and the
   underlying `Salesforce Base Connector`_.

.. _`PloneFormGen`: http://plone.org/products/ploneformgen
.. _`collective.z3cform.wizard`: http://plone.org/products/collective.z3cform.wizard
.. _`Salesforce PFG Adapter`: http://plone.org/products/salesforcepfgadapter
.. _`Salesforce Base Connector`: http://plone.org/products/salesforcebaseconnector

Installation
============

Megaphone has been tested with Plone 3.3 and Plone 4.

Adding to buildout
------------------

Megaphone has several dependencies. These should get pulled in automatically
if you add the collective.megaphone egg to your buildout.  _However_, you need
to make sure that you get versions of the dependencies that are compatible with
your version of Plone. To do so, you may extend the following known good sets
of version pins:

For Plone 4::

  [buildout]
  extends = http://good-py.appspot.com/release/collective.megaphone/2.0b1?plone=4.0rc1
  
  [instance]
  ...
  eggs =
      ...
      collective.megaphone

For Plone 3::
  
  [buildout]
  extends = http://good-py.appspot.com/release/collective.megaphone/2.0b1?zope=2.10.x
  
  [instance]
  ...
  eggs =
      ...
      collective.megaphone

Of course, you may need to adjust the specified Plone version, or create a
derivative set of version pins if the ones in this set conflict with those
recommended for some other add-on.

Activating the add-on
---------------------

After running buildout and starting your Zope instance, install
collective.megaphone via the Add/Remove Products configlet in Plone Site Setup.

Now you should be able to add an 'Action Letter' via the add item menu.

Make sure that you configure your Plone site's e-mail settings before trying
to send a letter.

Salesforce export
-----------------

In order to create a letter that saves contact information to Salesforce, you
must install the Products.salesforcepfgadapter and
Products.salesforcebaseconnector eggs.

CAPTCHA support
---------------

In order to include CAPTCHA fields, you must also install the
collective.captcha or collective.recaptcha egg, and load its ZCML.

If using collective.recaptcha, you must also configure your recaptcha keys via
the /@@recaptcha-settings view.

Upgrading
=========

If you have a previous version of Megaphone already installed, update your
buildout as described above. (Make sure you have a backup first!)

Then start your Zope instance, go to the Add/Remove Products configlet in Plone
Site Setup, and find the button to upgrade Megaphone.

Megaphone will also automatically update its dependencies plone.app.jquerytools
and plone.app.z3cform to compatible versions.

Bug tracker
===========

Please report issues at http://plone.org/products/megaphone/issues

Credits
=======

Megaphone was developed by Groundwire (formerly ONE/Northwest) as part of the
Civic Engagement Platform funded by Meyer Memorial Trust and Surdna Foundation.

Conceptual work by Jon Stahl, Drew Bernard, et al.

Development by David Glick and Jon Baldivieso.
