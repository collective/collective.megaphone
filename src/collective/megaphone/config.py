from collective.megaphone.utils import MegaphoneMessageFactory as _
from Products.CMFCore.permissions import setDefaultRoles
from Products.PloneFormGen.config import MA_ADD_CONTENT_PERMISSION

PROJECTNAME = 'collective.megaphone'
ANNOTATION_KEY = 'collective.megaphone'

ADD_PERMISSIONS = {
    'LetterRecipientMailerAdapter': MA_ADD_CONTENT_PERMISSION,
}

VIEW_SIGNATURES_PERMISSION = 'Megaphone: View signatures'
setDefaultRoles(VIEW_SIGNATURES_PERMISSION, ('Anonymous',))

LETTER_MAILTEMPLATE_BODY = \
"""<html xmlns="http://www.w3.org/1999/xhtml">

  <head><title></title></head>

  <body>
    <p tal:content="here/getBody_pre | nothing" />
    <p tal:replace="structure here/aq_parent/@@letter-renderer/render_letter" />
    <p tal:content="here/getBody_post | nothing" />
    <pre tal:content="here/getBody_footer | nothing" />
  </body>
</html>
"""

DEFAULT_LETTER_TEMPLATE = \
_('megaphone_default_letter_template', default=u"""Dear ${recip_honorific} ${recip_first} ${recip_last},

${sender_body}

Sincerely,
${sender_first} ${sender_last}
${sender_street}
${sender_city}, ${sender_state} ${sender_zip}
${sender_email}
""")

THANKYOU_MAILTEMPLATE_BODY = \
"""<html xmlns="http://www.w3.org/1999/xhtml">

  <head><title></title></head>

  <body>
    <p tal:content="here/getBody_pre | nothing" />
    <p tal:replace="structure here/aq_parent/@@letter-renderer/render_thankyou" />
    <p tal:content="here/getBody_post | nothing" />
    <pre tal:content="here/getBody_footer | nothing" />
  </body>
</html>
"""

DEFAULT_THANKYOU_TEMPLATE = \
_('megaphone_default_thankyou_template', default=u"""Dear ${sender_first} ${sender_last},

Thanks for your participation.
""")

DEFAULT_SIGNER_PORTLET_TEMPLATE = \
u"${sender_public_name}, ${sender_city}, ${sender_state}"

DEFAULT_SIGNER_FULL_TEMPLATE = \
u"${sender_public_name} | ${sender_city}, ${sender_state} | ${sender_body}"

# this is the id of the Mailer Adapter used for thanking letter-writers
THANK_YOU_EMAIL_ID = "thank-you-email"

# this is the id of the Mailer Adapter used to send e-mail to letter recipients
RECIPIENT_MAILER_ID = 'recipient-mailer'

# this is the id of the Save Data Adapter
SAVEDATA_ID = 'saved-letters'
RENDERED_LETTER_ID = 'rendered-letter'

# ids for Salesforce adapters
SF_LEAD_ID = 'salesforce-lead'
SF_CAMPAIGNMEMBER_ID = 'salesforce-campaignmember'
# and we need a dummy field to pass the campaign id to the adapter
CAMPAIGN_ID_FIELD_ID = 'campaign-id'
# Salesforce requires a value for the 'Company' field, so we create a dummy
# field to map to it
ORG_FIELD_ID = 'organization'

# Field mappings for lead adapter (Plone, Salesforce, label)
SF_LEAD_FIELDMAPPING = (
    ('first', 'FirstName', u'First Name'),
    ('last', 'LastName', u'Last Name'),
    ('email', 'Email', u'E-mail Address'),
    ('street', 'Street', u'Street Address'),
    ('city', 'City', u'City'),
    ('state', 'State', u'State'),
    ('zip', 'PostalCode', u'Postal Code'),
    (ORG_FIELD_ID, 'Company', u'Organization'),
)

# Field mappings for contact adapter (Plone, Salesforce, label)
SF_CONTACT_FIELDMAPPING = (
    ('first', 'FirstName', u'First Name'),
    ('last', 'LastName', u'Last Name'),
    ('email', 'Email', u'E-mail Address'),
    ('street', 'OtherStreet', u'Street Address'),
    ('city', 'OtherCity', u'City'),
    ('state', 'OtherState', u'State'),
    ('zip', 'OtherPostalCode', u'Postal Code'),
)

STATES = """|--
AL|Alabama
AK|Alaska
AZ|Arizona
AR|Arkansas
CA|California
CO|Colorado
CT|Connecticut
DE|Delaware
FL|Florida
GA|Georgia
HI|Hawaii
ID|Idaho
IL|Illinois
IN|Indiana
IA|Iowa
KS|Kansas
KY|Kentucky
LA|Louisiana
ME|Maine
MD|Maryland
MA|Massachusetts
MI|Michigan
MN|Minnesota
MS|Mississippi
MO|Missouri
MT|Montana
NE|Nebraska
NV|Nevada
NH|New Hampshire
NJ|New Jersey
NM|New Mexico
NY|New York
NC|North Carolina
ND|North Dakota
OH|Ohio
OK|Oklahoma
OR|Oregon
PA|Pennsylvania
RI|Rhode Island
SC|South Carolina
SD|South Dakota
TN|Tennessee
TX|Texas
UT|Utah
VT|Vermont
VA|Virginia
WA|Washington
WV|West Virginia
WI|Wisconsin
WY|Wyoming
"""

# Minimum number of sent letters for portlet to show if sig_portlet_min_count
# is not set.
DEFAULT_SIG_PORTLET_MIN_COUNT = 0
