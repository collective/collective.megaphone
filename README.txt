Introduction
============

Megaphone makes it easy to build powerful online advocacy campaigns in Plone.

Features
--------

 * Letters to decision makers
 * Required and optional recipients
 * Save data locally
 * Save data to Salesforce.com (requires salesforcepfgadapter)
 * Email letters to targets
 * Customizable thank-you letter to sender

Limitations
-----------

No product is perfect. There are some important things Megaphone doesn't do
(yet), including:

 * Matching of users to targets based on postal address
 * Delivery to targets who don't have a publicly-accessible email address

Coming soon
-----------

Megaphone is still under development, and there are quite a few features we've
got in progress, but are not released yet. Highlights include:

 * Advocacy petitions with public display of results

You can view our full `development tracker`_.

.. _`development tracker`: http://www.pivotaltracker.com/projects/12032

How it works
============

Megaphone builds on top of several fantastic Plone products to do its work
without reinventing the wheel.

 * The heart of Megaphone is `PloneFormGen`_, which provides the core
   form-handling capabilities.
 * Because advocacy letter is a fairly complicated PloneFormGen with lots of
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

Megaphone has been tested with Plone 3.2 and 3.3, and should be installed using
buildout in order to include the needed dependencies.  Support for Plone 4
is on its way, but is waiting for releases of a few key dependencies.

Simply add collective.megaphone to the list of eggs for your instance.  If
using Plone <3.3, you must also load its zcml.

After running buildout and starting your Zope instance, install
collective.megaphone via the Add/Remove Products configlet or
portal_quickinstaller.

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


Credits
=======

Megaphone was developed by Groundwire (formerly ONE/Northwest) as part of the
Civic Engagement Platform funded by Meyer Memorial Trust and Surdna Foundation.

Conceptual work by Jon Stahl, Drew Bernard, et al.

Development by David Glick and Jon Baldivieso.
