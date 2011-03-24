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
  extends = http://good-py.appspot.com/release/collective.megaphone/2.1?plone=4.0.4
  
  [instance]
  ...
  eggs =
      ...
      collective.megaphone

For Plone 3::
  
  [buildout]
  extends = http://good-py.appspot.com/release/collective.megaphone/2.1?zope=2.10.x
  
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

Now you should be able to add a 'Megaphone Action' via the add item menu.
The wizard will walk you through the rest of the steps.

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

Legislator lookup
-----------------

An optional add-on, `collective.megaphonecicerolookup`_, makes it possible to
determine the Megaphone recipient by automatically looking up a legislator's
e-mail address based on the sender's mailing address, using Azavea's commercial
`Cicero API`_.

.. _`collective.megaphonecicerolookup`: http://plone.org/products/collective.megaphonecicerolookup
.. _`Cicero API`: http://www.azavea.com/Products/Cicero/API.aspx

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

Customizing Megaphone
=====================

There are a number of ways that developers can extend Megaphone's functionality.

PloneFormGen-based customizations
---------------------------------

Since Megaphone is an extension built on top of PloneFormGen, standard
techniques for extending PloneFormGen can be used. In particular, custom fields
and action adapters (actions executed when the form is submitted) can be
implemented.

Recipient sources
-----------------

Megaphone includes one built-in recipient source, which lets a manager enter
a name and e-mail address of a recipient. Additional recipient sources can be
implemented to determine the recipient in other ways.

To create a custom recipient source, you must register two components:

* A named utility implementing ``collective.megaphone.interfaces.IRecipientSource``
* A multi-adapter of ``collective.megaphone.interfaces.IMegaphone`` and
  ``zope.publisher.interfaces.browser.IBrowserRequest`` to
  ``collective.megaphone.interfaces.IRecipientSource``, with the same name as the
  utility.

For an example of a custom recipient source, see `collective.megaphonecicerolookup`_,
which looks up the user's legislator based on the address entered.

Variable providers
------------------

Megaphone allows the manager to configure various templates that can make use of
variable substitution. By default, variables are provided based on the recipient
information and on the form data entered by a user taking action. It's possible
to provide additional variables as well.

To add a new variable provider, register a named adapter of
``collective.megaphone.interfaces.IMegaphone`` and
``zope.publisher.interfaces.browser.IBrowserRequest`` to ``collective.megaphone.interfaces.IVariableProvider``. The name of the adapter
registration is the variable name, and the adapter should return the variable
value when called.


Credits
=======

Megaphone was originally developed by Groundwire (formerly ONE/Northwest) as
part of the Civic Engagement Platform funded by Meyer Memorial Trust and
Surdna Foundation.

Conceptual work by Jon Stahl, Drew Bernard, et al.

Development by David Glick and Jon Baldivieso.

Thanks also to:

* Kees Hink
