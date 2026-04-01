# 💧 AquaFlow — Smart Water Management System

A full-stack AI-powered water management platform for urban colonies. It gives residents a portal to view water schedules, report issues, and earn credits — while giving city admins an intelligent dashboard with real ML-driven demand forecasting, anomaly detection, and colony health monitoring.

🌐 **Live Demo:** [aquaflow-jylh.onrender.com](https://aquaflow-jylh.onrender.com)

---

## 🚀 Features

### Resident Portal
- 🔐 Secure Registration + Admin Approval flow
- 📅 Colony-specific Water Schedule Calendar (FullCalendar.js)
- 🤖 AI Demand Forecast — 7-day water demand prediction chart  
- 📋 Complaint Submission with **real-time AI priority detection** (High / Medium / Low)
- 🏆 Gamification — Earn Credits for resolved complaints, Top-2 Leaderboard with 50% bill discount

### Admin Dashboard
- 📊 Live AI Demand Prediction chart (ML model trained on 365 days)
- 🚨 Anomaly Detection (Z-score statistical analysis)
- 🗺️ Colony Status Overview (Supply / Shutdown / Normal)
- ✅ User Approval / Rejection with email notification
- 🗓️ Water Schedule Management (calendar + modal, Supply / Shutdown)
- 📝 Complaint Management — view all complaints with resident details, resolve with one click (+10 Credits)
- 📧 Automated email alerts to entire colony for new schedules

---

## 🤖 AI / ML Components

| Component | Method | Details |
|-----------|--------|---------|
| **Water Demand Predictor** | `RandomForestRegressor` (scikit-learn) | Trained on 365 days of weather-aligned usage data. 6 features: max_temp, precipitation, day_of_week, month, is_summer, is_monsoon. R² = 0.785. 150 trees with confidence intervals. |
| **Complaint Priority Classifier** | NLP keyword matching | Scans complaint description for urgency signals → High / Medium / Low. Runs real-time while user types. |
| **Anomaly Detector** | Z-score (σ > 2.0) | Flags statistically abnormal usage days with contextual reasons (summer peak, monsoon, etc.) |

**External APIs:**
- [Open-Meteo Historical](https://archive-api.open-meteo.com/) — Real Chennai weather data to train the ML model (no API key required)
- [Open-Meteo Forecast](https://api.open-meteo.com/) — 7-day weather forecast for predictions (no API key required)

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python, Flask, Flask-Login, Flask-PyMongo, Flask-Mail |
| **ML** | scikit-learn (RandomForestRegressor), NumPy |
| **Database** | MongoDB Atlas |
| **Frontend** | Jinja2, Bootstrap 5, FullCalendar 6, Chart.js |
| **Deployment** | Render (gunicorn) |
| **Email** | Gmail SMTP via Flask-Mail |

---

## 📁 Project Structure

```
smart-water-system/
├── run.py                  # App entry point — seeds admin account
├── config.py               # Configuration (MongoDB URI, Mail SMTP)
├── requirements.txt        # Python dependencies
├── Procfile                # Render deployment command
├── app/
│   ├── __init__.py         # App factory (registers blueprints)
│   ├── models.py           # User model (Flask-Login)
│   ├── routes_auth.py      # /register /login /logout
│   ├── routes_user.py      # /user/dashboard /submit_complaint
│   ├── routes_admin.py     # /admin/* (dashboard, approve, resolve, schedule)
│   ├── routes_api.py       # /api/predict_demand /api/analyze_complaint
│   ├── ai_module.py        # ML core: RandomForest + NLP + Anomaly Detection
│   ├── weather_service.py  # Open-Meteo API wrappers
│   ├── mail_service.py     # HTML email notifications
│   └── templates/          # Jinja2 HTML templates
```

---

## ⚙️ Local Setup

### Prerequisites
- Python 3.11+
- MongoDB running locally (`mongodb://localhost:27017`) or MongoDB Atlas URI

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/GYANAHPRAKASH/smart-water-system.git
cd smart-water-system

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create a .env file (copy from .env.example)
copy .env.example .env
# Edit .env with your MongoDB URI and Mail credentials

# 4. Seed historical data (runs ML training data generation)
python populate_data.py

# 5. Run the development server
python run.py
```

Visit `http://127.0.0.1:5000`

**Default Admin Credentials:**  
- Username: `Prakash`  
- Password: `admin123`

---

## 🌐 Environment Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Flask session secret key |
| `MONGO_URI` | MongoDB connection string (Atlas or local) |
| `MAIL_USERNAME` | Gmail address for sending emails |
| `MAIL_PASSWORD` | Gmail App Password (not your regular password) |

---

## 🔐 Security

- Passwords hashed with **Werkzeug PBKDF2-SHA256**
- All protected routes use `@login_required` + role checks
- Unapproved users cannot log in (status gate at login)
- Email failures are caught silently — never crash the app
- API endpoints handle invalid input with clean JSON error responses

---

## 📊 Colony Water Thresholds

| Colony | Normal Daily | High Demand | Overusage (→ Shutdown) |
|--------|-------------|-------------|----------------------|
| Anna Nagar | ~650,000 L | > 700,000 L | > 800,000 L |
| Nungambakkam | ~550,000 L | > 600,000 L | > 800,000 L |
| T. Nagar | ~700,000 L | > 750,000 L | > 800,000 L |
| Alwarpet | ~500,000 L | > 560,000 L | > 800,000 L |
| Gopalapuram | ~480,000 L | > 540,000 L | > 800,000 L |

---

## 📦 Deployment (Render)

See [`render_deploy_guide.md`](render_deploy_guide.md) for step-by-step Render deployment instructions.

Key files:
- `Procfile`: `web: gunicorn run:app`
- `runtime.txt`: `python-3.11.6`

---

## 👨‍💻 Developer

**Gyanahprakash V S**  
Smart Water Management System — AI Phase 3 Project  
April 2026
