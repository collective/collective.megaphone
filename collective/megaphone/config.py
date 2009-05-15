from Products.PloneFormGen.config import MA_ADD_CONTENT_PERMISSION

PROJECTNAME = 'collective.megaphone'
ANNOTATION_KEY = 'collective.megaphone'

ADD_PERMISSIONS = {
    'LetterRecipientMailerAdapter': MA_ADD_CONTENT_PERMISSION,
}

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
"""Dear ${recip_honorific} ${recip_first} ${recip_last},

${sender_body}

Sincerely,
${sender_first} ${sender_last}
${sender_street}
${sender_city}, ${sender_state} ${sender_zip}
${sender_email}
"""

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
"""Dear ${sender_first} ${sender_last},

Thanks for sending a letter to ${recip_honorific} ${recip_first} ${recip_last}.
"""


# this is the id of the Mailer Adapter used for thanking letter-writers
THANK_YOU_EMAIL_ID = "thank-you-email"
RECIPIENT_MAILER_ID = 'recipient-mailer'
