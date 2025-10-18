# 🤰 MatruRakshaAI

> AI-Powered Maternal Health Monitoring & Care System for Underserved Communities

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

MatruRakshaAI is an intelligent maternal health monitoring system that leverages AI agents, Telegram integration, and continuous care protocols to provide 24/7 support for pregnant mothers in low-resource settings.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [AI Agents](#-ai-agents)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### 🤖 **AI-Powered Health Monitoring**
- **6 Specialized AI Agents** working in orchestration
- Real-time risk assessment and emergency detection
- Personalized care plans and nutrition guidance
- Medication management and reminders
- ASHA worker coordination

### 📱 **Telegram Bot Integration**
- 24/7 conversational health support
- Daily health check-ins and reminders
- Interactive symptom reporting
- Natural language query processing
- Emergency protocol activation

### 📊 **Continuous Care System**
- Daily health monitoring (40-week journey)
- Weekly automated assessments
- Milestone tracking (12, 20, 28, 36 weeks)
- Health timeline and trend analysis
- Risk progression tracking

### 👩‍⚕️ **Healthcare Worker Tools**
- ASHA visit scheduling and reporting
- Emergency alert system
- Risk-based visit frequency
- Comprehensive patient dashboard
- Analytics and reporting

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  MatruRakshaAI                       │
└─────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐     ┌────▼────┐     ┌────▼────┐
   │ Telegram│     │ Backend │     │   Web   │
   │   Bot   │◄────┤ FastAPI │────►│Dashboard│
   └─────────┘     └────┬────┘     └─────────┘
                        │
              ┌─────────┼─────────┐
              │         │         │
        ┌─────▼───┐ ┌──▼──┐ ┌───▼────┐
        │ Supabase│ │Agent│ │Schedule│
        │   DB    │ │ AI  │ │  Jobs  │
        └─────────┘ └─────┘ └────────┘
```

### **Agent Orchestration**

```
┌──────────────────────────────────────────┐
│         Agent Orchestrator               │
└────────────┬─────────────────────────────┘
             │
    ┌────────┼────────┬────────┬────────┐
    │        │        │        │        │
┌───▼──┐ ┌──▼──┐ ┌───▼──┐ ┌───▼──┐ ┌──▼──┐
│ Risk │ │Care │ │Nutr. │ │ Med. │ │ASHA │
│Agent │ │Agent│ │Agent │ │Agent │ │Agent│
└──────┘ └─────┘ └──────┘ └──────┘ └─────┘
    │        │        │        │        │
    └────────┴────────┴────────┴────────┘
                     │
            ┌────────▼────────┐
            │ Emergency Agent │
            └─────────────────┘
```

---

## 🛠️ Tech Stack

### **Backend**
- **Framework:** FastAPI (Python 3.11+)
- **Database:** Supabase (PostgreSQL)
- **AI/ML:** NumPy, scikit-learn
- **Task Scheduler:** Python Schedule
- **API:** REST with async support

### **Frontend**
- **Framework:** React 18
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **Charts:** Recharts
- **Icons:** Lucide React

### **Integration**
- **Messaging:** Telegram Bot API
- **Real-time:** WebSocket support
- **Authentication:** Supabase Auth
- **Storage:** Supabase Storage

### **AI Agents**
- Risk Assessment Agent
- Care Planning Agent
- Nutrition Agent
- Medication Agent
- Emergency Detection Agent
- ASHA Coordination Agent

---

## 🚀 Installation

### **Prerequisites**
- Python 3.11 or higher
- Node.js 18 or higher
- Supabase account
- Telegram Bot Token

### **1. Clone Repository**
```bash
git clone https://github.com/yourusername/maatru-raksha-ai.git
cd maatru-raksha-ai
```

### **2. Backend Setup**

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your credentials
```

**Backend `.env` configuration:**
```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

### **3. Database Setup**

Run migrations in Supabase SQL Editor:
```sql
-- See /infra/supabase/schema.sql for complete schema
```

### **4. Frontend Setup**

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local file
cp .env.example .env.local
# Edit with your configuration
```

**Frontend `.env.local` configuration:**
```env
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_API_URL=http://localhost:8000
```

### **5. Get Telegram Bot Token**

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow instructions
3. Copy the bot token
4. Add to `backend/.env`

---

## 💻 Usage

### **Start Backend Server**

```bash
cd backend
python main.py
```

Server runs at: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### **Start Frontend**

```bash
cd frontend
npm run dev
```

Dashboard runs at: `http://localhost:5173`

### **Start Scheduler (For Automated Tasks)**

```bash
cd backend
python scheduler.py

# Or test mode (immediate execution):
python scheduler.py test
```

### **Configure Telegram Bot**

1. Get your Chat ID:
   - Message your bot: `/start`
   - Copy the chat ID displayed

2. Register a mother with Telegram:
   ```bash
   curl -X POST http://localhost:8000/mothers/register \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test Mother",
       "phone": "9876543210",
       "age": 28,
       "gravida": 2,
       "parity": 1,
       "bmi": 22.5,
       "location": "Mumbai",
       "preferred_language": "en",
       "telegram_chat_id": "YOUR_CHAT_ID"
     }'
   ```

---

## 📡 API Documentation

### **Core Endpoints**

#### **Health Check**
```http
GET /health
```
Returns system health status and agent availability.

#### **Register Mother**
```http
POST /mothers/register
Content-Type: application/json

{
  "name": "string",
  "phone": "string",
  "age": integer,
  "gravida": integer,
  "parity": integer,
  "bmi": float,
  "location": "string",
  "telegram_chat_id": "string" (optional)
}
```

#### **Risk Assessment**
```http
POST /risk/assess
Content-Type: application/json

{
  "mother_id": "string",
  "systolic_bp": integer,
  "diastolic_bp": integer,
  "hemoglobin": float,
  "symptoms": ["string"]
}
```

#### **Daily Check-in**
```http
POST /mothers/{mother_id}/daily-checkin
Content-Type: application/json

{
  "date": "YYYY-MM-DD",
  "feeling_today": "good|okay|unwell",
  "symptoms": ["string"],
  "medications_taken": boolean
}
```

#### **AI Agent Query**
```http
POST /agents/query
Content-Type: application/json

{
  "mother_id": "string",
  "query": "string"
}
```

### **Agent Endpoints**

- `GET /agents/status` - Check all agent statuses
- `GET /mothers/{id}/daily-summary` - AI-generated daily summary
- `POST /mothers/{id}/weekly-assessment` - Trigger weekly assessment
- `POST /mothers/{id}/report-symptom` - Emergency symptom reporting

### **Full API Documentation**
Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

---

## 🤖 AI Agents

### **1. Risk Assessment Agent**
- Analyzes 6 risk factors (age, BMI, BP, hemoglobin, history, pregnancy status)
- Multi-factor risk scoring algorithm
- Personalized recommendations
- Next checkup scheduling

### **2. Emergency Detection Agent**
- Real-time emergency protocol activation
- 5+ emergency condition monitoring
- Immediate action instructions
- ASHA worker alerting

### **3. Care Planning Agent**
- Daily task generation
- Exercise plans (risk-adjusted)
- Checkup scheduling
- Warning sign monitoring

### **4. Nutrition Agent**
- Trimester-specific meal plans
- Anemia-aware nutrition
- Supplement recommendations
- Foods to avoid

### **5. Medication Agent**
- Smart medication scheduling
- Drug interaction awareness
- Reminder system
- Compliance tracking

### **6. ASHA Coordination Agent**
- Risk-based visit scheduling
- Emergency alerts
- Visit checklists
- Follow-up coordination

---

## 🎯 Key Features in Detail

### **Continuous Monitoring (40 Weeks)**

```
Week 1-40: Daily
├─ 8:00 AM: Daily reminder
├─ Mother check-in
├─ AI analysis
├─ Alerts if needed
└─ Weekly assessment

Milestones:
├─ Week 12: First trimester screening
├─ Week 20: Anatomy scan
├─ Week 28: Glucose test
├─ Week 36: Birth plan
└─ Week 40: Delivery prep
```

### **Telegram Bot Commands**

```
/start    - Get chat ID & welcome message
/checkin  - Daily health check-in
/status   - Current health status
/timeline - View health history
/report   - Report symptoms
/help     - Show all commands
```

**Natural Language Queries:**
- "What should I eat to increase hemoglobin?"
- "I have a severe headache"
- "When should I take my iron tablets?"

---

## 📊 Analytics Dashboard

- Total mothers registered
- Risk level distribution (High/Medium/Low)
- Total assessments performed
- Agent performance metrics
- Emergency response times
- ASHA visit statistics

---

## 🔧 Configuration

### **Scheduler Configuration**

Edit times in `backend/scheduler.py`:

```python
# Daily reminders at 8 AM
schedule.every().day.at("08:00").do(send_daily_reminders)

# Medication reminders
schedule.every().day.at("09:00").do(send_medication_reminders_morning)
schedule.every().day.at("18:00").do(send_medication_reminders_evening)

# Weekly assessment every Monday at 9 AM
schedule.every().monday.at("09:00").do(run_weekly_assessments)
```

### **Agent Configuration**

Agents can be configured in individual files:
- `backend/agents/risk_agent.py` - Risk thresholds
- `backend/agents/emergency_agent.py` - Emergency protocols
- `backend/agents/nutrition_agent.py` - Meal plans
- etc.

---

## 🐳 Deployment

### **Docker Deployment**

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

### **Production Considerations**

1. **Environment Variables**: Use production keys
2. **Database**: Use managed PostgreSQL
3. **Scheduler**: Run as systemd service or cron
4. **SSL/TLS**: Use HTTPS for production
5. **Monitoring**: Setup logging and alerts
6. **Backups**: Regular database backups

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# API tests
curl http://localhost:8000/health

# Agent tests
curl http://localhost:8000/agents/status

# Scheduler test
python scheduler.py test
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### **Development Guidelines**
- Follow PEP 8 for Python code
- Use ESLint for JavaScript/React
- Write meaningful commit messages
- Add tests for new features
- Update documentation

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Team

**MatruRakshaAI** - Developed for improving maternal healthcare in underserved communities.

---

## 📞 Support

For issues, questions, or contributions:
- **GitHub Issues**: [Create an issue](https://github.com/yourusername/maatru-raksha-ai/issues)
- **Email**: support@matruraksha.ai
- **Telegram**: [@MatruRakshaSupport](https://t.me/MatruRakshaSupport)

---

## 🙏 Acknowledgments

- **Anthropic Claude** - AI assistance and agent orchestration
- **Supabase** - Database and authentication
- **Telegram** - Messaging platform
- **FastAPI** - Modern Python web framework
- **React** - Frontend library
- **ASHA Workers** - Community health workers inspiration

---

## 📈 Roadmap

- [ ] Voice-based interaction (multilingual)
- [ ] WhatsApp integration
- [ ] IoT device integration (BP monitors, weight scales)
- [ ] Predictive analytics for complications
- [ ] Mobile app (iOS/Android)
- [ ] Multi-language support (Hindi, Tamil, Telugu, Bengali)
- [ ] Doctor portal
- [ ] SMS fallback for no internet
- [ ] Offline mode support

---

## 🌟 Star History

If you find this project useful, please consider giving it a ⭐ on GitHub!

---

<p align="center">
  Made with ❤️ for mothers everywhere
</p>

<p align="center">
  <sub>MatruRakshaAI - Because every mother deserves quality healthcare</sub>
</p>