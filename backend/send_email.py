from fastapi_mail import FastMail, MessageSchema, MessageType
from mail import conf


async def send_verification_email(email: str, name: str, code: str):

    message = MessageSchema(
        subject="Your FleetFlow verification code",
        recipients=[email],
        body=f"""
        <h2>Hello {name},</h2>

        <p>Use this verification code to activate your FleetFlow account:</p>

        <h1 style="letter-spacing: 6px;">{code}</h1>
        <p>This code expires in 10 minutes. Do not share it with anyone.</p>

        <br>

        <p>Regards,<br><strong>FleetFlow Team</strong></p>
        """,
        subtype="html",
    )

    fm = FastMail(conf)

    await fm.send_message(message)
