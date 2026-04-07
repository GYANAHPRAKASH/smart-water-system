# pyre-ignore-all-errors
"""
AquaFlow Mail Service — Brevo (formerly Sendinblue) HTTPS API
=============================================================
Uses Brevo's REST API over HTTPS (port 443) instead of SMTP.
This works on ALL cloud platforms including Render's free tier,
which blocks outbound SMTP port 587.

Required env var: BREVO_API_KEY (set in Render dashboard & .env)
Optional: MAIL_SENDER_EMAIL (defaults to vsgpvsjd2006@gmail.com)
"""
import threading
import requests
from flask import current_app


BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
DEFAULT_SENDER_EMAIL = "vsgpvsjd2006@gmail.com"
DEFAULT_SENDER_NAME  = "AquaFlow"


# ── HTML Email Base Template ──────────────────────────────────────

def _base_html(title, content):
    return f"""
    <div style="font-family:'Outfit',Arial,sans-serif;max-width:560px;margin:0 auto;background:#f0f7f9;padding:30px;">
      <div style="background:linear-gradient(135deg,#0077b6,#00b4d8);border-radius:16px 16px 0 0;padding:24px 32px;text-align:center;">
        <h1 style="color:#fff;margin:0;font-size:1.6rem;">💧 AquaFlow</h1>
        <p style="color:rgba(255,255,255,0.85);margin:4px 0 0;font-size:0.88rem;">Smart Water Management</p>
      </div>
      <div style="background:#fff;border-radius:0 0 16px 16px;padding:32px;box-shadow:0 4px 20px rgba(0,119,182,0.1);">
        <h2 style="color:#03045e;margin-top:0;">{title}</h2>
        {content}
        <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;">
        <p style="color:#718096;font-size:0.82rem;margin:0;">
          AquaFlow Smart Water System &mdash; Colony Management Platform<br>
          If you did not expect this email, please contact <a href="mailto:vsgpvsjd2006@gmail.com" style="color:#0077b6;">vsgpvsjd2006@gmail.com</a>
        </p>
      </div>
    </div>
    """


# ── Core Sender (Brevo HTTPS API) ─────────────────────────────────

def _send_via_brevo(to_email, to_name, subject, html_content):
    """
    Send one email through Brevo's transactional API (HTTPS POST).
    Works on Render free tier — no SMTP port restrictions.
    """
    app = current_app._get_current_object()
    api_key = app.config.get('BREVO_API_KEY')

    if not api_key:
        print(f"[AquaFlow Mail] BREVO_API_KEY not set — skipping email to {to_email}")
        return

    sender_email = app.config.get('MAIL_SENDER_EMAIL', DEFAULT_SENDER_EMAIL)

    payload = {
        "sender": {"name": DEFAULT_SENDER_NAME, "email": sender_email},
        "to": [{"email": to_email, "name": to_name or to_email}],
        "subject": subject,
        "htmlContent": html_content
    }
    headers = {
        "accept":       "application/json",
        "content-type": "application/json",
        "api-key":      api_key
    }

    try:
        resp = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=10)
        if resp.status_code in (200, 201):
            print(f"[AquaFlow Mail] ✅ Email sent to {to_email} — {subject}")
        else:
            print(f"[AquaFlow Mail] ❌ Brevo error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"[AquaFlow Mail] ❌ Failed to send email to {to_email}: {e}")


def _send_async(to_email, to_name, subject, html_content):
    """Run email send in a background thread — never blocks the HTTP response."""
    app = current_app._get_current_object()
    def worker():
        with app.app_context():
            _send_via_brevo(to_email, to_name, subject, html_content)
    t = threading.Thread(target=worker, daemon=False)
    t.start()


# ── Public Email Senders ──────────────────────────────────────────

def send_registration_pending(user_email, username):
    """Sent immediately after a user registers — tells them to wait for admin approval."""
    if not user_email:
        return
    content = f"""
    <p>Hi <strong>{username}</strong>,</p>
    <p>Your AquaFlow account has been created and is <strong>pending admin approval</strong>.</p>
    <p>You'll receive another email once the admin reviews your request. This usually takes less than 24 hours.</p>
    <div style="background:#caf0f8;border-radius:10px;padding:14px 18px;margin:18px 0;">
      <p style="margin:0;color:#03045e;"><strong>Username:</strong> {username}</p>
    </div>
    <p>If you have questions, contact the City Admin at
      <a href="mailto:vsgpvsjd2006@gmail.com" style="color:#0077b6;">vsgpvsjd2006@gmail.com</a>
      or <strong>+91 98765 43210</strong>.
    </p>
    """
    _send_async(user_email, username,
                "AquaFlow — Account Pending Approval ⏳",
                _base_html("Account Created ✅", content))


def send_account_approved(user_email, username):
    """Sent when admin approves a user."""
    if not user_email:
        return
    content = f"""
    <p>Hi <strong>{username}</strong>,</p>
    <p>Great news! Your AquaFlow account has been <strong style="color:#198754;">approved</strong>.</p>
    <p>You can now log in and access your colony's water schedule, report issues, and earn credits.</p>
    <div style="text-align:center;margin:24px 0;">
      <a href="https://smart-water-system-h73w.onrender.com/login"
         style="background:linear-gradient(135deg,#0077b6,#00b4d8);color:#fff;text-decoration:none;
                padding:12px 32px;border-radius:50px;font-weight:700;font-size:1rem;">
        Login to AquaFlow →
      </a>
    </div>
    """
    _send_async(user_email, username,
                "AquaFlow — Account Approved 🎉",
                _base_html("Your Account is Live!", content))


def send_account_rejected(user_email, username):
    """Sent when admin rejects a user."""
    if not user_email:
        return
    content = f"""
    <p>Hi <strong>{username}</strong>,</p>
    <p>Unfortunately your AquaFlow account request has been <strong style="color:#dc3545;">rejected</strong>.</p>
    <p>This may be due to incorrect colony information or an administrative decision. Please contact the City Admin for details.</p>
    <p>📧 <a href="mailto:vsgpvsjd2006@gmail.com" style="color:#0077b6;">vsgpvsjd2006@gmail.com</a>
       &nbsp;|&nbsp; 📞 <strong>+91 98765 43210</strong></p>
    """
    _send_async(user_email, username,
                "AquaFlow — Account Update",
                _base_html("Account Status Update", content))


def send_account_deleted(user_email, username):
    """Sent when admin permanently deletes a user account."""
    if not user_email:
        return
    content = f"""
    <p>Hi <strong>{username}</strong>,</p>
    <p>Your AquaFlow account has been <strong style="color:#dc3545;">permanently removed</strong> by the city administrator.</p>
    <p>If you believe this was a mistake, please contact the City Admin immediately:</p>
    <div style="background:#fff3cd;border-radius:10px;padding:14px 18px;margin:18px 0;border-left:4px solid #ffc107;">
      <p style="margin:0;color:#664d03;">
        📧 <a href="mailto:vsgpvsjd2006@gmail.com" style="color:#0077b6;">vsgpvsjd2006@gmail.com</a><br>
        📞 <strong>+91 98765 43210</strong>
      </p>
    </div>
    <p style="color:#6c757d;font-size:0.9rem;">If you wish to rejoin AquaFlow, you may register again and await admin approval.</p>
    """
    _send_async(user_email, username,
                "AquaFlow — Account Removed 🚫",
                _base_html("Account Removed", content))


def send_complaint_resolved(user_email, username, credits_awarded=10):
    """Sent when admin resolves a complaint and awards credits."""
    if not user_email:
        return
    content = f"""
    <p>Hi <strong>{username}</strong>,</p>
    <p>Your water issue complaint has been <strong style="color:#198754;">resolved</strong> by the admin team.</p>
    <div style="background:#d1e7dd;border-radius:10px;padding:14px 18px;margin:18px 0;text-align:center;">
      <p style="margin:0;color:#0f5132;font-size:1.1rem;">
        🪙 <strong>+{credits_awarded} Credits</strong> have been added to your account!
      </p>
    </div>
    <p>Top contributors earn a <strong>50% discount on their water bill</strong>. Keep reporting issues to help your community!</p>
    <div style="text-align:center;margin:20px 0;">
      <a href="https://smart-water-system-h73w.onrender.com/user/dashboard"
         style="background:linear-gradient(135deg,#0077b6,#00b4d8);color:#fff;text-decoration:none;
                padding:12px 32px;border-radius:50px;font-weight:700;">
        View My Dashboard →
      </a>
    </div>
    """
    _send_async(user_email, username,
                "AquaFlow — Complaint Resolved 🎉",
                _base_html("Issue Resolved!", content))


def send_schedule_alert(emails, colony, action, date_time_str, notes=''):
    """Sent to all users in a colony when a new schedule is created."""
    if not emails:
        return
    color  = "#198754" if action == "Supply" else "#dc3545"
    icon   = "💧" if action == "Supply" else "🚫"
    note_block = f'<p style="color:#4a5568;"><strong>Notes:</strong> {notes}</p>' if notes else ''
    content = f"""
    <p>Dear <strong>{colony}</strong> Resident,</p>
    <p>A new water schedule has been set for your colony:</p>
    <div style="background:#f0f7f9;border-left:5px solid {color};border-radius:8px;padding:16px 20px;margin:18px 0;">
      <p style="margin:0;font-size:1.1rem;color:#03045e;">
        {icon} <strong>{action}</strong> scheduled on <strong>{date_time_str}</strong>
      </p>
      {note_block}
    </div>
    <p>Log in to your dashboard to view the full schedule.</p>
    <div style="text-align:center;margin:20px 0;">
      <a href="https://smart-water-system-h73w.onrender.com/user/dashboard"
         style="background:linear-gradient(135deg,#0077b6,#00b4d8);color:#fff;text-decoration:none;
                padding:12px 32px;border-radius:50px;font-weight:700;">
        View Schedule →
      </a>
    </div>
    """
    html = _base_html(f"Water {action} Alert — {colony}", content)
    subject = f"AquaFlow — {action} Scheduled for {colony} {icon}"
    # Send to each recipient separately (Brevo free tier works best this way)
    app = current_app._get_current_object()
    for email in emails:
        def _send_one(e=email):
            with app.app_context():
                _send_via_brevo(e, colony + " Resident", subject, html)
        t = threading.Thread(target=_send_one, daemon=False)
        t.start()
