# email_sender.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
import os
import logging
import re

logger = logging.getLogger(__name__)

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")  # From .env file
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # App password or SMTP password

def send_email(recipient, subject, attachment_path, delete_after_send=False):
    try:
        # Validate email credentials
        if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
            raise ValueError("Email credentials not found in environment variables")
        
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, recipient):
            raise ValueError(f"Invalid recipient email format: {recipient}")
        
        # Validate attachment exists
        if not os.path.exists(attachment_path):
            raise FileNotFoundError(f"Attachment file not found: {attachment_path}")
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = recipient
        msg['Subject'] = subject

        body = "Hi,\n\nPlease find your AI-generated resume attached.\n\nRegards,\nAI Resume Generator"
        msg.attach(MIMEText(body, 'plain'))

        # Attach the resume
        with open(attachment_path, "rb") as file:
            part = MIMEApplication(file.read(), Name=os.path.basename(attachment_path))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
            msg.attach(part)

        # Connect and send
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            
        logger.info(f"Email sent successfully to {recipient}")
        
        # Delete the file after successful email sending if requested
        if delete_after_send:
            try:
                os.remove(attachment_path)
                logger.info(f"Resume file deleted successfully: {attachment_path}")
            except OSError as e:
                logger.warning(f"Failed to delete resume file {attachment_path}: {str(e)}")
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication failed: {str(e)}")
        logger.error("Gmail Authentication Error - Please ensure you are using:")
        logger.error("1. A valid Gmail address in EMAIL_ADDRESS")
        logger.error("2. An App Password (not regular password) in EMAIL_PASSWORD")
        logger.error("3. 2-Factor Authentication enabled on your Gmail account")
        logger.error("Visit: https://support.google.com/accounts/answer/185833 for App Password setup")
        raise ValueError("Gmail authentication failed. Please check your App Password configuration.")
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise