# AquaFlow – Render Deployment Guide

## Prerequisites

Before deploying, make sure you have:
- Your code pushed to a **GitHub repository**
- A free account at [render.com](https://render.com)
- A **MongoDB Atlas** cluster with a connection string (`mongodb+srv://...`)
- *(Optional)* A Gmail App Password for registration emails

---

## Step 1 – Push Your Code to GitHub

In your project folder, run:

```bash
git add .
git commit -m "Remove Google OAuth, deploy-ready"
git push origin main
```

---

## Step 2 – Create a New Web Service on Render

1. Go to [dashboard.render.com](https://dashboard.render.com) → **New** → **Web Service**
2. Connect your GitHub account and select the **smart-water-system** repository
3. Fill in the settings:

| Setting | Value |
|---|---|
| **Name** | `smart-water-system` (or anything you like) |
| **Region** | Singapore (closest to India) |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn -w 1 --timeout 120 --preload run:app` |
| **Instance Type** | Free |

> [!IMPORTANT]
> The **Start Command** above must match exactly. Render will use this instead of your `Procfile` if you paste it here — but having `Procfile` in the repo also works automatically.

---

## Step 3 – Set Environment Variables

In the Render dashboard → your service → **Environment** tab, add these variables:

| Key | Value |
|---|---|
| `SECRET_KEY` | A long random string (e.g. run `python -c "import secrets; print(secrets.token_hex(32))"` locally) |
| `MONGO_URI` | Your full Atlas URI: `mongodb+srv://user:pass@cluster.mongodb.net/smart_water_db?retryWrites=true&w=majority&appName=Cluster0` |
| `MAIL_USERNAME` | Your Gmail address (e.g. `vsgpvsjd2006@gmail.com`) |
| `MAIL_PASSWORD` | Your **Gmail App Password** (16 chars, not your real password) |

> [!TIP]
> **How to get a Gmail App Password:**  
> myaccount.google.com → Security → 2-Step Verification → App Passwords → Create one for "Mail"

> [!WARNING]
> Do NOT set `GOOGLE_CLIENT_ID` or `GOOGLE_CLIENT_SECRET` — those are removed and no longer needed.

---

## Step 4 – Allow MongoDB Atlas Access from Render

1. Go to [cloud.mongodb.com](https://cloud.mongodb.com) → your cluster → **Network Access**
2. Click **Add IP Address** → select **Allow access from anywhere** (`0.0.0.0/0`)
3. Click **Confirm**

> [!IMPORTANT]
> Without this, Render cannot connect to your database and all logins/registrations will fail silently.

---

## Step 5 – Deploy

1. Click **Create Web Service** on Render
2. Watch the build logs — it should say `Build successful`
3. On first boot, `run.py` auto-creates the admin account if it doesn't exist yet (you'll see `Admin user created.` in the logs)

---

## Step 6 – Test It

| Test | Expected Result |
|---|---|
| Visit `https://<your-app>.onrender.com` | Landing page loads |
| Go to `/register`, fill all fields, submit | "Account created! You can login after admin approval." |
| Go to `/login`, enter `Prakash` / `admin123` | Redirected to Admin Dashboard |
| Approve the pending user from Admin Dashboard | User can now log in from their own device |

> [!NOTE]
> On the **free tier**, Render spins down after 15 minutes of inactivity. The first request after sleep takes ~30 seconds to wake up — this is normal and not a crash.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Application error` on login/register | Check Render logs → likely MongoDB IP not whitelisted (Step 4) |
| `Admin user not found` | Check Render logs for `Admin user created` — if missing, the MONGO_URI is wrong |
| Registration email not received | Check spam folder; verify `MAIL_PASSWORD` is an App Password not your real Gmail password |
| `gunicorn: command not found` | Ensure `gunicorn` is in `requirements.txt` ✅ (it is) |
