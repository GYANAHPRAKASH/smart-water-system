# pyre-ignore-all-errors
from flask import render_template_string
from flask_mail import Message
from . import mail

# ── Email Templates ───────────────────────────────────────────────

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

# ── Senders ───────────────────────────────────────────────────────

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
      <a href="mailto:cityadmin@aquaflow.com" style="color:#0077b6;">cityadmin@aquaflow.com</a> or <strong>+91 98765 43210</strong>.
    </p>
    """
    msg = Message(subject="AquaFlow — Account Pending Approval",
                  recipients=[user_email],
                  html=_base_html("Account Created ✅", content))
    _send(msg)

def send_account_approved(user_email, username):
    """Sent when admin approves a user."""
    if not user_email:
        return
    content = f"""
    <p>Hi <strong>{username}</strong>,</p>
    <p>Great news! Your AquaFlow account has been <strong style="color:#198754;">approved</strong>.</p>
    <p>You can now log in and access your colony's water schedule, report issues, and earn credits.</p>
    <div style="text-align:center;margin:24px 0;">
      <a href="https://aquaflow-jylh.onrender.com/login"
         style="background:linear-gradient(135deg,#0077b6,#00b4d8);color:#fff;text-decoration:none;
                padding:12px 32px;border-radius:50px;font-weight:700;font-size:1rem;">
        Login to AquaFlow →
      </a>
    </div>
    """
    msg = Message(subject="AquaFlow — Account Approved 🎉",
                  recipients=[user_email],
                  html=_base_html("Your Account is Live!", content))
    _send(msg)

def send_account_rejected(user_email, username):
    """Sent when admin rejects a user."""
    if not user_email:
        return
    content = f"""
    <p>Hi <strong>{username}</strong>,</p>
    <p>Unfortunately your AquaFlow account request has been <strong style="color:#dc3545;">rejected</strong>.</p>
    <p>This may be due to incorrect colony information or an administrative decision. Please contact the City Admin for details.</p>
    <p>📧 <a href="mailto:cityadmin@aquaflow.com" style="color:#0077b6;">cityadmin@aquaflow.com</a>
       &nbsp;|&nbsp; 📞 <strong>+91 98765 43210</strong></p>
    """
    msg = Message(subject="AquaFlow — Account Update",
                  recipients=[user_email],
                  html=_base_html("Account Status Update", content))
    _send(msg)

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
      <a href="https://aquaflow-jylh.onrender.com/user/dashboard"
         style="background:linear-gradient(135deg,#0077b6,#00b4d8);color:#fff;text-decoration:none;
                padding:12px 32px;border-radius:50px;font-weight:700;">
        View My Dashboard →
      </a>
    </div>
    """
    msg = Message(subject="AquaFlow — Complaint Resolved 🎉",
                  recipients=[user_email],
                  html=_base_html("Issue Resolved!", content))
    _send(msg)

def send_schedule_alert(emails, colony, action, date_time_str, notes=''):
    """Sent to all users in a colony when a new schedule is created."""
    if not emails:
        return
    color = "#198754" if action == "Supply" else "#dc3545"
    icon  = "💧" if action == "Supply" else "🚫"
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
      <a href="https://aquaflow-jylh.onrender.com/user/dashboard"
         style="background:linear-gradient(135deg,#0077b6,#00b4d8);color:#fff;text-decoration:none;
                padding:12px 32px;border-radius:50px;font-weight:700;">
        View Schedule →
      </a>
    </div>
    """
    msg = Message(
        subject=f"AquaFlow — {action} Scheduled for {colony} {icon}",
        recipients=emails,
        html=_base_html(f"Water {action} Alert — {colony}", content)
    )
    _send(msg)

# ── Internal helper ───────────────────────────────────────────────

def _send(msg):
    """Send mail silently — never crash the app if email fails."""
    try:
        mail.send(msg)
    except Exception as e:
        print(f"[AquaFlow Mail] Failed to send email: {e}")
