"""Outbound email for password reset using FastAPI-Mail."""
import os

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS") == "True",
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS") == "True",
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


async def send_reset_email(recipient_email: str, token: str) -> None:
    """Send an HTML email with a link to the frontend reset-password page.

    Args:
        recipient_email: Address to deliver the message to.
        token: Opaque reset JWT appended to the reset URL query string.

    Note:
        The reset link host is currently fixed to ``localhost:5173`` in the template.
    """
    reset_link = f"http://localhost:5173/reset-password?token={token}"
    html_content = f"""
    <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>You requested a password reset. Click the link below to set a new password:</p>
            <p><a href="{reset_link}">Reset My Password</a></p>
            <p>If you did not request this, please ignore this email.</p>
        </body>
    </html>
    """
    message = MessageSchema(
        subject="Reset Your Password",
        recipients=[recipient_email],
        body=html_content,
        subtype=MessageType.html,
    )
    fm = FastMail(conf)
    await fm.send_message(message)
