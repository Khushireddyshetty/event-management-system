"""
Email service for sending confirmation emails using Flask-Mail.
Credentials are read from environment variables — never hardcoded.
"""

import os
from flask_mail import Mail, Message

mail = Mail()


def init_mail(app):
    """Configure and bind Flask-Mail to the Flask app."""
    app.config["MAIL_SERVER"]   = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"]     = int(os.environ.get("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"]  = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "")
    app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "")
    app.config["MAIL_DEFAULT_SENDER"] = os.environ.get(
        "MAIL_DEFAULT_SENDER",
        os.environ.get("MAIL_USERNAME", "noreply@eventplatform.com"),
    )
    mail.init_app(app)


def send_confirmation_email(attendee: dict):
    """
    Send a registration confirmation email to the attendee.

    attendee dict must contain:
        full_name, email, event_name, registration_id, unique_pin, registration_date
    """
    username = os.environ.get("MAIL_USERNAME", "")
    if not username:
        print("[Email] MAIL_USERNAME not set — skipping confirmation email.")
        return False

    recipient   = attendee.get("email", "")
    name        = attendee.get("full_name", "Attendee")
    event       = attendee.get("event_name") or "the event"
    reg_id      = attendee.get("registration_id", "N/A")
    pin         = attendee.get("unique_pin", "N/A")
    reg_date    = attendee.get("registration_date", "N/A")

    subject = "Registration Confirmed"

    body = f"""Hello {name},

Your registration has been successfully completed.

Event Name      : {event}
Registration ID : {reg_id}
Unique PIN      : {pin}
Date & Time     : {reg_date}

Please use this PIN during event check-in.

Thank you for registering. We look forward to seeing you!

— Event Management Team
"""

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: Arial, sans-serif; background: #f4f4f7; margin: 0; padding: 0; }}
    .container {{ max-width: 560px; margin: 40px auto; background: #fff; border-radius: 12px;
                  box-shadow: 0 2px 12px rgba(0,0,0,.08); overflow: hidden; }}
    .header {{ background: #7c3aed; padding: 32px 40px; color: #fff; }}
    .header h1 {{ margin: 0; font-size: 22px; }}
    .body {{ padding: 32px 40px; color: #333; line-height: 1.7; }}
    .card {{ background: #f5f3ff; border: 1px solid #ede9fe; border-radius: 8px;
             padding: 20px 24px; margin: 20px 0; }}
    .card table {{ width: 100%; border-collapse: collapse; }}
    .card td {{ padding: 6px 0; font-size: 14px; }}
    .card td:first-child {{ color: #6b7280; width: 160px; }}
    .card td:last-child {{ font-weight: 600; color: #1f2937; }}
    .pin {{ font-size: 28px; font-weight: 700; color: #7c3aed; letter-spacing: 6px; }}
    .footer {{ padding: 16px 40px; background: #f9fafb; color: #9ca3af;
               font-size: 12px; text-align: center; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>&#10003; Registration Confirmed</h1>
      <p style="margin:4px 0 0;opacity:.85;font-size:14px;">
        You're all set for <strong>{event}</strong>
      </p>
    </div>
    <div class="body">
      <p>Hello <strong>{name}</strong>,</p>
      <p>Your registration has been successfully completed. Here are your details:</p>

      <div class="card">
        <table>
          <tr>
            <td>Registration ID</td>
            <td>{reg_id}</td>
          </tr>
          <tr>
            <td>Event</td>
            <td>{event}</td>
          </tr>
          <tr>
            <td>Date &amp; Time</td>
            <td>{reg_date}</td>
          </tr>
          <tr>
            <td>Your PIN</td>
            <td class="pin">{pin}</td>
          </tr>
        </table>
      </div>

      <p>
        <strong>Please save this PIN.</strong> You will need it at the event check-in desk.
      </p>
      <p>Thank you for registering. We look forward to seeing you!</p>
    </div>
    <div class="footer">Event Management Platform &bull; This is an automated message.</div>
  </div>
</body>
</html>
"""

    try:
        msg = Message(subject=subject, recipients=[recipient], body=body, html=html)
        mail.send(msg)
        print(f"[Email] Confirmation sent to {recipient}")
        return True
    except Exception as exc:
        print(f"[Email] Failed to send to {recipient}: {exc}")
        return False
