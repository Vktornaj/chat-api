import smtplib
import ssl
from email.message import EmailMessage
from email.headerregistry import Address
from email.utils import make_msgid
import os


port = 465
email_sender = os.environ.get("EMAIL_SENDER")
email_password = os.environ.get("GOOGLE_APP_PASSWORD")
email_receiver = 'victor2211812@gmail.com'


def send_email(msg: EmailMessage):
    context = ssl.create_default_context()

    # Send the message via local SMTP server.
    with smtplib.SMTP_SSL('smtp.gmail.com', port, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, msg.as_string())


def send_confirmation_email(to: Address, code: str):
    # Create the base text message.
    msg = EmailMessage()
    msg['Subject'] = "Welcome to ChatApi!"
    msg['From'] = Address("ChatApi", "vktornaj", email_sender)
    msg['To'] = to

    msg.set_content(f"""\
Hi {to.display_name}.

Thank you for registering on ChatApi
to confirm that this email belongs to you.
This is the confirmation code.
{code}
If you do not recognize this action ignore it...\n

Please do not answer this email.
--Vktornaj
    """)

    # Add the html version.  This converts the message into a multipart/alternative
    # container, with the original text message as the first part and the new html
    # message as the second part.
    asparagus_cid = make_msgid()
    msg.add_alternative(f"""\
<html>
    <head></head>
    <body>
    <p>Hi {to.display_name}.</p>
    <p>
        Thank you for signing up for ChatApi.
        <p>
            Confirmation code: <b>{code}</b>
        </p>
        If you do not recognize this action ignore it...
        <br>
        <span style="color:grey">
        Please do not answer this email.
        </span>
    </p>
    <img src="cid:{asparagus_cid}" />
    </body>
</html>
    """.format(asparagus_cid=asparagus_cid[1:-1]), subtype='html')
    # note that we needed to peel the <> off the msgid for use in the html.

    send_email(msg)
