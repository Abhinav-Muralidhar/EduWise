import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app


def send_reset_email(to_email, reset_url):
    """Send a password reset email via Gmail SMTP."""
    sender = current_app.config.get('MAIL_USERNAME')
    password = current_app.config.get('MAIL_PASSWORD')

    if not sender or not password:
        current_app.logger.error("Mail credentials not configured in .env")
        return False

    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'EduWise — Reset Your Password'
    msg['From'] = f'EduWise <{sender}>'
    msg['To'] = to_email

    # Plain text fallback
    text_body = f"""Hi,

You requested a password reset for your EduWise account.
Click the link below to set a new password (valid for 1 hour):

{reset_url}

If you didn't request this, you can safely ignore this email.

— EduWise Team"""

    # HTML version
    html_body = f"""
    <div style="font-family: 'Inter', Arial, sans-serif; max-width: 520px; margin: 0 auto; padding: 32px;">
        <div style="text-align: center; margin-bottom: 32px;">
            <div style="display: inline-block; width: 40px; height: 40px; border-radius: 10px;
                        background: #EEF1FE; color: #4361EE; font-size: 18px; line-height: 40px;">
                🎓
            </div>
            <h2 style="color: #1B1F3B; margin: 12px 0 4px; font-size: 20px;">EduWise</h2>
        </div>

        <div style="background: #FFFFFF; border: 1px solid #E8E8EC; border-radius: 14px; padding: 32px;">
            <h3 style="color: #1B1F3B; margin: 0 0 8px; font-size: 18px;">Reset your password</h3>
            <p style="color: #4A4E6E; font-size: 14px; line-height: 1.6; margin: 0 0 24px;">
                We received a request to reset your password. Click the button below to choose a new one.
                This link expires in <strong>1 hour</strong>.
            </p>

            <a href="{reset_url}"
               style="display: inline-block; background: #4361EE; color: #FFFFFF; text-decoration: none;
                      padding: 12px 28px; border-radius: 8px; font-size: 14px; font-weight: 600;">
                Reset Password
            </a>

            <p style="color: #9CA3AF; font-size: 12px; margin: 24px 0 0; line-height: 1.5;">
                If you didn't request this, you can safely ignore this email. Your password won't change.
            </p>
        </div>

        <p style="text-align: center; color: #9CA3AF; font-size: 11px; margin-top: 24px;">
            &copy; EduWise &middot; Built with intention.
        </p>
    </div>
    """

    msg.attach(MIMEText(text_body, 'plain'))
    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        current_app.logger.info("Password reset email sent successfully.")
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send reset email: {e}")
        return False
