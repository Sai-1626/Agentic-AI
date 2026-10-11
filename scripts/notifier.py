"""
Email Notification Dispatcher.
Implements Module 7 (Nodes 33, 34, 35, 36) of the Agentic AI Video Creation System.
Formats and sends Success and Error emails via SMTP or logs safely when unconfigured.
"""

import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

from .config import Config

logger = logging.getLogger(__name__)

class EmailNotifier:
    """Dispatches publishing status emails to administrators or users."""

    @classmethod
    def send_email(cls, subject: str, body: str, recipient: Optional[str] = None) -> Dict[str, Any]:
        """Sends an email using configured SMTP credentials or simulates safely."""
        to_email = recipient or Config.NOTIFICATION_EMAIL_TO
        from_email = Config.NOTIFICATION_EMAIL_FROM or Config.SMTP_USERNAME

        is_placeholder = any(
            placeholder in (Config.SMTP_USERNAME or "").lower() or placeholder in (Config.SMTP_PASSWORD or "").lower()
            for placeholder in ["your_email", "your_app_password", "example.com"]
        )

        if not (Config.SMTP_USERNAME and Config.SMTP_PASSWORD and to_email) or is_placeholder:
            logger.info(f"[EmailNotifier Simulation]\nTo: {to_email or 'user@example.com'}\nSubject: {subject}\n\n{body}")
            return {
                "status": "success",
                "mode": "dry_run",
                "message": "Email logged to console (SMTP credentials not configured in .env)",
                "subject": subject
            }

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_email
            msg["To"] = to_email

            part_text = MIMEText(body, "plain")
            msg.attach(part_text)

            with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
                server.starttls()
                server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
                server.sendmail(from_email, [to_email], msg.as_string())

            logger.info(f"Email successfully sent to {to_email}")
            return {"status": "success", "mode": "smtp", "recipient": to_email}
        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {e}")
            return {"status": "error", "error": str(e)}

    @classmethod
    def send_success_notification(
        cls,
        video_title: str,
        youtube_url: str,
        instagram_url: str,
        recipient: Optional[str] = None
    ) -> Dict[str, Any]:
        """Implements Node 35: Success Email."""
        upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        body = f"""Hello,

Your social media video has been successfully uploaded and published.

Video Title:
{video_title}

Publishing Status:
YouTube: Successfully Uploaded
Instagram: Successfully Uploaded

YouTube Link:
{youtube_url}

Instagram Link:
{instagram_url}

Upload Date and Time:
{upload_time}

The video was automatically generated, optimized with SEO content, and published through the Agentic AI workflow.

Thank you.
"""
        subject = f"Success: Video Published - {video_title}"
        return cls.send_email(subject, body, recipient)

    @classmethod
    def send_error_notification(
        cls,
        video_title: str,
        youtube_status: str,
        instagram_status: str,
        error_message: str,
        recipient: Optional[str] = None
    ) -> Dict[str, Any]:
        """Implements Node 36: Error Email."""
        body = f"""Hello,

Your automated social media video workflow encountered a publishing problem.

Video Title:
{video_title}

YouTube Status:
{youtube_status}

Instagram Status:
{instagram_status}

Error:
{error_message}

Please check the n8n workflow for more information.

Thank you.
"""
        subject = f"Alert: Publishing Failed - {video_title}"
        return cls.send_email(subject, body, recipient)


if __name__ == "__main__":
    res = EmailNotifier.send_success_notification(
        video_title="Artificial Intelligence in Education",
        youtube_url="https://youtube.com/shorts/test123",
        instagram_url="https://instagram.com/reel/test123"
    )
    print("Notification result:", res)
