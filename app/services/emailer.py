"""Contact-form email delivery via Resend."""

import requests

from app.config import Config


def _send_contact_email_resend(sender_name: str, sender_email: str, subject: str, message: str):
    """Send email via Resend"""
    if not Config.RESEND_API_KEY:
        return False, 'Resend API key is not configured.'
    
    from_email = "MyPersonal Bible App <noreply@resend.dev>"
    to_email = Config.MAIL_TO
    
    email_body = f"""
    <h2>New Contact Form Submission</h2>
    <p><strong>Name:</strong> {sender_name or '(not provided)'}</p>
    <p><strong>Email:</strong> {sender_email or '(not provided)'}</p>
    <p><strong>Category:</strong> {subject or '(not specified)'}</p>
    <p><strong>Message:</strong></p>
    <p style="white-space: pre-wrap;">{message}</p>
    <hr>
    <p><small>Sent from MyPersonal Bible App Contact Form</small></p>
    """
    
    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": f"[MyPersonalBibleApp] {subject or 'New contact message'}",
        "html": email_body,
    }
    
    if sender_email:
        payload["reply_to"] = sender_email
    
    headers = {
        "Authorization": f"Bearer {Config.RESEND_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(Config.RESEND_API_URL, json=payload, headers=headers, timeout=15)
        
        if response.status_code in (200, 201, 202):
            return True, 'Your message was sent successfully. Thank you!'
        else:
            print(f"Resend error: {response.status_code}")
            return False, 'Failed to send email. Please try again later.'
            
    except Exception as e:
        print(f"Email send error: {e}")
        return False, 'Failed to send email. Please try again later.'
