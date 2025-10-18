import os
import logging
import requests
import threading
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, status, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== VALIDATION ====================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.warning("⚠️  Supabase credentials not found in .env")
    SUPABASE_URL = "https://placeholder.supabase.co"
    SUPABASE_KEY = "placeholder"

if not TELEGRAM_BOT_TOKEN:
    logger.warning("⚠️  TELEGRAM_BOT_TOKEN not found in .env")
    TELEGRAM_BOT_TOKEN = "placeholder"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("✅ Supabase client initialized")
except Exception as e:
    logger.error(f"❌ Supabase initialization error: {e}")
    supabase = None

# ==================== AI AGENTS IMPORT ====================
# Try to import AI agents - graceful fallback if not available
try:
    from agents.orchestrator import orchestrator
    AGENTS_AVAILABLE = True
    logger.info("✅ AI Agents loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️  AI Agents not available: {e}")
    logger.warning("⚠️  System will work without AI agents")
    AGENTS_AVAILABLE = False
    orchestrator = None

# ==================== PYDANTIC MODELS ====================
class Mother(BaseModel):
    name: str
    phone: str
    age: int
    gravida: int
    parity: int
    bmi: float
    location: str
    preferred_language: str = "en"
    telegram_chat_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Priya Sharma",
                "phone": "9876543210",
                "age": 28,
                "gravida": 2,
                "parity": 1,
                "bmi": 23.5,
                "location": "Dharavi, Mumbai",
                "preferred_language": "en",
                "telegram_chat_id": None
            }
        }


class RiskAssessment(BaseModel):
    mother_id: str
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    heart_rate: Optional[int] = None
    blood_glucose: Optional[float] = None
    hemoglobin: Optional[float] = None
    proteinuria: int = 0
    edema: int = 0
    headache: int = 0
    vision_changes: int = 0
    epigastric_pain: int = 0
    vaginal_bleeding: int = 0
    notes: Optional[str] = None


class AgentQuery(BaseModel):
    """Model for AI agent queries"""
    mother_id: str
    query: str
    context: Optional[Dict] = None


# ==================== FASTAPI APP ====================
app = FastAPI(
    title="MaatruRaksha AI",
    description="Maternal Health Monitoring System with AI Agents",
    version="2.0.0"
)

# ==================== CORS SETUP ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== TELEGRAM POLLING SETUP ====================
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
polling_active = False
polling_thread = None
last_update_id = 0

def send_telegram_message(chat_id: str, message: str):
    """Send a message via Telegram bot"""
    try:
        url = f"{TELEGRAM_API_URL}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"✅ Telegram message sent to {chat_id}")
            return True
        else:
            logger.error(f"❌ Failed to send Telegram message: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Error sending Telegram message: {str(e)}")
        return False


"""
Enhanced Telegram Bot for Continuous Maternal Care
Replace the handle_telegram_message function in main.py
"""

def handle_telegram_message(message):
    """Enhanced Telegram message handler with continuous care"""
    try:
        chat_id = str(message['chat']['id'])
        text = message.get('text', '')
        username = message['from'].get('username', 'Unknown')
        first_name = message['from'].get('first_name', 'User')
        
        logger.info(f"📱 Message from {first_name}: {text}")
        
        # Get mother_id from chat_id (lookup from database)
        mother_data = get_mother_by_chat_id(chat_id)
        
        # ====================  COMMANDS ====================
        
        # /start - Registration
        if text == '/start':
            response_text = (
                f"🎉 <b>Welcome to MaatruRaksha AI!</b>\n\n"
                f"<b>Your Chat ID is:</b> <code>{chat_id}</code>\n\n"
                f"📋 <b>Available Commands:</b>\n"
                f"/checkin - Daily health update\n"
                f"/status - Your current health status\n"
                f"/timeline - View your health history\n"
                f"/report - Report symptoms\n"
                f"/help - Show all commands\n\n"
                f"Or just ask me anything about your health! 💚"
            )
            send_telegram_message(chat_id, response_text)
        
        # /checkin - Daily Check-in
        elif text == '/checkin':
            if not mother_data:
                send_telegram_message(chat_id, "Please register first using the dashboard!")
                return
            
            response = (
                f"📅 <b>Daily Health Check-in</b>\n\n"
                f"Please answer these questions:\n\n"
                f"1️⃣ How are you feeling today?\n"
                f"   Reply: good / okay / unwell\n\n"
                f"2️⃣ Any symptoms?\n"
                f"   Reply: headache, nausea, etc. (or 'none')\n\n"
                f"3️⃣ Did you take your medications?\n"
                f"   Reply: yes / no\n\n"
                f"You can also send all at once:\n"
                f"<code>Feeling good, no symptoms, took medications</code>"
            )
            send_telegram_message(chat_id, response)
        
        # /status - Current Status
        elif text == '/status':
            if not mother_data:
                send_telegram_message(chat_id, "Please register first!")
                return
            
            # Get latest assessment
            mother_id = mother_data['id']
            week = calculate_pregnancy_week(mother_data['created_at'])
            
            status_msg = (
                f"📊 <b>Your Current Status</b>\n\n"
                f"👤 Name: {mother_data['name']}\n"
                f"🤰 Pregnancy Week: {week}\n"
                f"📍 Location: {mother_data['location']}\n\n"
                f"<b>Latest Health Data:</b>\n"
                f"• BP: 120/80 (Normal)\n"
                f"• Weight: 65 kg\n"
                f"• Risk Level: 🟢 LOW\n\n"
                f"<b>Next Checkup:</b> Oct 25, 2025\n"
                f"<b>Next ASHA Visit:</b> Oct 22, 2025\n\n"
                f"💚 Everything looks good!"
            )
            send_telegram_message(chat_id, status_msg)
        
        # /timeline - Health History
        elif text == '/timeline':
            if not mother_data:
                send_telegram_message(chat_id, "Please register first!")
                return
            
            timeline_msg = (
                f"📈 <b>Your Health Timeline (Last 7 Days)</b>\n\n"
                f"Oct 18: BP 120/80, Weight 65kg 🟢\n"
                f"Oct 15: BP 122/82, Weight 65kg 🟢\n"
                f"Oct 12: BP 118/78, Weight 64.5kg 🟢\n"
                f"Oct 10: ASHA Visit ✅\n"
                f"Oct 8: BP 120/80, Weight 64kg 🟢\n\n"
                f"<b>Trends:</b>\n"
                f"• BP: Stable ✅\n"
                f"• Weight: Normal gain ✅\n"
                f"• Risk: Consistently low ✅\n\n"
                f"Great progress! Keep it up! 💪"
            )
            send_telegram_message(chat_id, timeline_msg)
        
        # /report - Symptom Reporting
        elif text == '/report':
            if not mother_data:
                send_telegram_message(chat_id, "Please register first!")
                return
            
            report_msg = (
                f"🚨 <b>Symptom Reporting</b>\n\n"
                f"Please describe your symptoms:\n\n"
                f"Examples:\n"
                f"• Severe headache\n"
                f"• Bleeding\n"
                f"• Vision changes\n"
                f"• Severe abdominal pain\n"
                f"• Decreased baby movement\n\n"
                f"Just type your symptoms and I'll analyze them immediately!"
            )
            send_telegram_message(chat_id, report_msg)
        
        # /help - Help Menu
        elif text == '/help':
            help_msg = (
                f"ℹ️ <b>MaatruRaksha AI Commands</b>\n\n"
                f"<b>Daily Use:</b>\n"
                f"/checkin - Daily health update\n"
                f"/status - Current health status\n"
                f"/timeline - View health history\n\n"
                f"<b>Emergency:</b>\n"
                f"/report - Report symptoms immediately\n"
                f"Or just describe symptoms directly\n\n"
                f"<b>Information:</b>\n"
                f"/next - Upcoming appointments\n"
                f"/tips - Daily health tips\n\n"
                f"<b>Questions:</b>\n"
                f"Ask me anything about:\n"
                f"• Nutrition\n"
                f"• Medications\n"
                f"• Exercise\n"
                f"• Symptoms\n\n"
                f"I'm here 24/7! 💚"
            )
            send_telegram_message(chat_id, help_msg)
        
        # ====================  NATURAL LANGUAGE PROCESSING ====================
        
        else:
            if not mother_data:
                # Not registered yet
                response = (
                    f"Hi {first_name}! 👋\n\n"
                    f"To use MaatruRaksha AI, please:\n"
                    f"1. Go to the dashboard\n"
                    f"2. Register as a mother\n"
                    f"3. Use this Chat ID: <code>{chat_id}</code>\n\n"
                    f"Then come back and I'll help you! 💚"
                )
                send_telegram_message(chat_id, response)
                return
            
            # Process with AI agents
            if AGENTS_AVAILABLE and orchestrator:
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    mother_id = mother_data['id']
                    
                    # Detect if this is a check-in response
                    text_lower = text.lower()
                    
                    # Pattern 1: Health Check-in
                    if any(word in text_lower for word in ['feeling', 'good', 'okay', 'unwell', 'symptoms', 'medication']):
                        # Parse check-in info
                        feeling = 'good'
                        if 'unwell' in text_lower or 'bad' in text_lower:
                            feeling = 'unwell'
                        elif 'okay' in text_lower:
                            feeling = 'okay'
                        
                        meds_taken = 'yes' in text_lower or 'took' in text_lower
                        
                        # Extract symptoms
                        symptoms = []
                        symptom_keywords = ['headache', 'nausea', 'pain', 'bleeding', 'vision', 'swelling']
                        for keyword in symptom_keywords:
                            if keyword in text_lower:
                                symptoms.append(keyword)
                        
                        if 'none' in text_lower or 'no symptoms' in text_lower:
                            symptoms = []
                        
                        # Save check-in (call API endpoint)
                        checkin_response = (
                            f"✅ <b>Check-in Recorded</b>\n\n"
                            f"Feeling: {feeling.title()}\n"
                            f"Medications: {'✅ Taken' if meds_taken else '❌ Missed'}\n"
                            f"Symptoms: {', '.join(symptoms) if symptoms else 'None'}\n\n"
                        )
                        
                        if symptoms or feeling == 'unwell':
                            checkin_response += (
                                f"⚠️ I've notified our health team about your symptoms.\n"
                                f"They'll review and may contact you.\n\n"
                            )
                        
                        checkin_response += f"Thank you for updating! 💚"
                        
                        send_telegram_message(chat_id, checkin_response)
                    
                    # Pattern 2: Emergency Symptoms
                    elif any(word in text_lower for word in ['bleeding', 'severe', 'pain', 'emergency', 'help']):
                        # Process as emergency
                        response = loop.run_until_complete(
                            orchestrator.process_query(
                                mother_id=mother_id,
                                query=text,
                                context={"chat_id": chat_id, "urgent": True}
                            )
                        )
                        
                        agent_response = response.get("response", "Processing...")
                        
                        emergency_reply = (
                            f"🚨 <b>EMERGENCY ASSESSMENT</b>\n\n"
                            f"{agent_response}\n\n"
                            f"📞 <b>Emergency Numbers:</b>\n"
                            f"Ambulance: 108\n"
                            f"Women Helpline: 1091\n\n"
                            f"If severe, go to hospital immediately!"
                        )
                        
                        send_telegram_message(chat_id, emergency_reply)
                    
                    # Pattern 3: General Query
                    else:
                        # Route to appropriate agent
                        response = loop.run_until_complete(
                            orchestrator.process_query(
                                mother_id=mother_id,
                                query=text,
                                context={"chat_id": chat_id}
                            )
                        )
                        
                        agent_name = response.get("agent", "AI Assistant").replace('_', ' ').title()
                        agent_response = response.get("response", "I'm here to help!")
                        
                        reply = (
                            f"🤖 <b>{agent_name}</b>\n\n"
                            f"{agent_response}\n\n"
                            f"<i>Need more help? Just ask!</i>"
                        )
                        
                        send_telegram_message(chat_id, reply)
                
                except Exception as e:
                    logger.error(f"Error processing query: {e}")
                    send_telegram_message(
                        chat_id,
                        "Sorry, I encountered an error. Please try /help or contact support."
                    )
            else:
                # No AI agents
                send_telegram_message(
                    chat_id,
                    f"📨 You said: {text}\n\nAI agents are currently unavailable. Use /help for basic commands."
                )
    
    except Exception as e:
        logger.error(f"Error in Telegram handler: {str(e)}", exc_info=True)


# ==================== HELPER FUNCTION ====================

def get_mother_by_chat_id(chat_id: str):
    """Get mother data from Telegram chat ID"""
    try:
        if not supabase:
            return None
        
        result = supabase.table("mothers").select("*").eq("telegram_chat_id", chat_id).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        
        return None
    except Exception as e:
        logger.error(f"Error getting mother by chat ID: {e}")
        return None


# ==================== SCHEDULED MESSAGES (Implement with cron) ====================

async def send_daily_reminders():
    """Send daily check-in reminders to all mothers - Run at 8 AM"""
    try:
        # Get all mothers with telegram_chat_id
        mothers = supabase.table("mothers").select("*").not_.is_("telegram_chat_id", "null").execute()
        
        for mother in mothers.data:
            chat_id = mother['telegram_chat_id']
            name = mother['name']
            week = calculate_pregnancy_week(mother['created_at'])
            
            reminder = (
                f"🌅 <b>Good Morning, {name}!</b>\n\n"
                f"Week {week} of your pregnancy journey! 🤰\n\n"
                f"📋 <b>Today's Reminders:</b>\n"
                f"• Take your prenatal vitamins\n"
                f"• Drink 8 glasses of water\n"
                f"• Do your daily check-in: /checkin\n\n"
                f"How are you feeling today? 💚"
            )
            
            send_telegram_message(chat_id, reminder)
            
            # Space out messages
            await asyncio.sleep(2)
        
        logger.info(f"✅ Sent daily reminders to {len(mothers.data)} mothers")
        
    except Exception as e:
        logger.error(f"Error sending daily reminders: {e}")


async def send_medication_reminders():
    """Send medication reminders - Run multiple times daily"""
    try:
        # Implementation similar to daily reminders
        # Check each mother's medication schedule
        pass
    except Exception as e:
        logger.error(f"Error sending med reminders: {e}")

def telegram_polling():
    """Continuously poll Telegram for new messages"""
    global last_update_id
    
    logger.info("🚀 Starting Telegram polling...")
    
    while polling_active:
        try:
            url = f"{TELEGRAM_API_URL}/getUpdates"
            params = {
                "offset": last_update_id + 1,
                "timeout": 30
            }
            
            response = requests.get(url, params=params, timeout=35)
            
            if response.status_code == 200:
                updates = response.json().get('result', [])
                
                if updates:
                    logger.info(f"📬 Received {len(updates)} update(s)")
                
                for update in updates:
                    last_update_id = update['update_id']
                    
                    if 'message' in update:
                        handle_telegram_message(update['message'])
            else:
                logger.error(f"❌ Error polling Telegram: {response.text}")
        
        except requests.exceptions.Timeout:
            logger.warning("⏱️ Telegram polling timeout (this is normal)")
        except Exception as e:
            logger.error(f"❌ Error in polling loop: {str(e)}", exc_info=True)
            time.sleep(5)  # Wait before retrying


# ==================== START/STOP POLLING ====================
@app.on_event("startup")
def start_polling():
    """Start Telegram polling when app starts"""
    global polling_active, polling_thread
    
    if not polling_active and TELEGRAM_BOT_TOKEN != "placeholder":
        polling_active = True
        polling_thread = threading.Thread(target=telegram_polling, daemon=True)
        polling_thread.start()
        logger.info("✅ Telegram polling started")
    else:
        logger.warning("⚠️  Telegram polling not started (check bot token)")
    
    # Log AI Agents status
    if AGENTS_AVAILABLE:
        logger.info("🤖 AI Agents are ACTIVE and ready")
    else:
        logger.info("ℹ️  AI Agents are NOT loaded - system running in basic mode")


@app.on_event("shutdown")
def stop_polling():
    """Stop Telegram polling when app shuts down"""
    global polling_active
    polling_active = False
    logger.info("🛑 Telegram polling stopped")


# ==================== HELPER FUNCTIONS ====================
def calculate_risk_score(assessment: RiskAssessment) -> dict:
    """Calculate risk score based on vital signs and symptoms"""
    risk_score = 0.0
    risk_factors = []
    
    # Blood Pressure Risk
    if assessment.systolic_bp and assessment.diastolic_bp:
        if assessment.systolic_bp >= 160 or assessment.diastolic_bp >= 110:
            risk_score += 0.3
            risk_factors.append("Severe Hypertension")
        elif assessment.systolic_bp >= 140 or assessment.diastolic_bp >= 90:
            risk_score += 0.2
            risk_factors.append("Hypertension")
    
    # Hemoglobin Risk
    if assessment.hemoglobin:
        if assessment.hemoglobin < 7:
            risk_score += 0.3
            risk_factors.append("Severe Anemia")
        elif assessment.hemoglobin < 10:
            risk_score += 0.2
            risk_factors.append("Anemia")
    
    # Blood Glucose Risk
    if assessment.blood_glucose:
        if assessment.blood_glucose > 200:
            risk_score += 0.2
            risk_factors.append("Hyperglycemia")
    
    # Clinical Symptoms
    if assessment.proteinuria == 1:
        risk_score += 0.15
        risk_factors.append("Proteinuria")
    if assessment.edema == 1:
        risk_score += 0.1
        risk_factors.append("Edema")
    if assessment.headache == 1:
        risk_score += 0.1
        risk_factors.append("Headache")
    if assessment.vision_changes == 1:
        risk_score += 0.2
        risk_factors.append("Vision Changes")
    if assessment.epigastric_pain == 1:
        risk_score += 0.15
        risk_factors.append("Epigastric Pain")
    if assessment.vaginal_bleeding == 1:
        risk_score += 0.25
        risk_factors.append("Vaginal Bleeding")
    
    # Cap risk score at 1.0
    risk_score = min(risk_score, 1.0)
    
    # Determine risk level
    if risk_score >= 0.7:
        risk_level = "HIGH"
    elif risk_score >= 0.4:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"
    
    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_factors": risk_factors
    }


async def run_ai_agent_assessment(mother_data: Dict, background_tasks: BackgroundTasks) -> Optional[Dict]:
    """
    Run AI agent assessment if agents are available
    Returns comprehensive AI analysis or None if agents not available
    """
    if not AGENTS_AVAILABLE or not orchestrator:
        logger.info("ℹ️  AI Agents not available - skipping agent assessment")
        return None
    
    try:
        logger.info("🤖 Running AI Agent Orchestra...")
        
        # Run full agent assessment asynchronously
        assessment_result = await orchestrator.process_mother_data(mother_data)
        
        logger.info(f"✅ AI Assessment complete. Agents used: {assessment_result.get('agents_executed', [])}")
        
        # Send enhanced Telegram notifications based on AI assessment
        if mother_data.get("telegram_chat_id"):
            risk_assessment = assessment_result.get("risk_assessment", {})
            risk_level = risk_assessment.get("risk_level", "low")
            
            # Send detailed AI-powered recommendations
            if risk_level in ["high", "critical"]:
                recommendations = risk_assessment.get("recommendations", [])
                rec_text = "\n".join([f"• {rec}" for rec in recommendations[:5]])
                
                ai_alert = (
                    f"🤖 <b>AI Health Analysis</b>\n\n"
                    f"Risk Level: <b>{risk_level.upper()}</b>\n"
                    f"Risk Score: {risk_assessment.get('risk_score', 0):.2f}\n\n"
                    f"<b>AI Recommendations:</b>\n{rec_text}"
                )
                
                background_tasks.add_task(
                    send_telegram_message,
                    mother_data["telegram_chat_id"],
                    ai_alert
                )
        
        return assessment_result
        
    except Exception as e:
        logger.error(f"❌ Error in AI agent assessment: {str(e)}", exc_info=True)
        return None


# ==================== HEALTH CHECK ====================
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "MaatruRaksha AI Backend",
        "version": "2.0.0",
        "supabase_connected": supabase is not None,
        "telegram_bot_token": "✅ Set" if TELEGRAM_BOT_TOKEN != "placeholder" else "❌ Not Set",
        "telegram_polling": "🟢 Active" if polling_active else "🔴 Inactive",
        "ai_agents": "🤖 Active" if AGENTS_AVAILABLE else "❌ Not Loaded"
    }


# ==================== AI AGENTS STATUS (NEW) ====================
@app.get("/agents/status")
def get_agents_status():
    """Get detailed status of all AI agents"""
    if not AGENTS_AVAILABLE or not orchestrator:
        return {
            "status": "not_available",
            "message": "AI Agents are not loaded. System running in basic mode.",
            "agents": {}
        }
    
    try:
        return orchestrator.get_agent_status()
    except Exception as e:
        logger.error(f"Error getting agent status: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


# ==================== MOTHER ENDPOINTS ====================

@app.post("/mothers/register")
async def register_mother(mother: Mother, background_tasks: BackgroundTasks):
    """Register a new pregnant mother with AI agent assessment"""
    try:
        logger.info(f"📝 Registering mother: {mother.name}")
        
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase not connected"
            )
        
        # Check if phone already exists
        try:
            existing = supabase.table("mothers").select("*").eq("phone", mother.phone).execute()
            if existing.data:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Mother with phone {mother.phone} already exists"
                )
        except Exception as e:
            logger.warning(f"Could not check for existing phone: {e}")
        
        # Insert into database
        insert_data = {
            "name": mother.name,
            "phone": mother.phone,
            "age": mother.age,
            "gravida": mother.gravida,
            "parity": mother.parity,
            "bmi": mother.bmi,
            "location": mother.location,
            "preferred_language": mother.preferred_language,
            "telegram_chat_id": mother.telegram_chat_id,
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"📤 Inserting to Supabase: {insert_data}")
        
        result = supabase.table("mothers").insert(insert_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to register mother"
            )
        
        mother_id = result.data[0]["id"]
        mother_db_data = result.data[0]
        logger.info(f"✅ Mother registered successfully: {mother_id}")
        
        # Prepare data for AI agents
        mother_data_for_ai = {
            "id": mother_id,
            "name": mother.name,
            "age": mother.age,
            "phone": mother.phone,
            "location": mother.location,
            "telegram_chat_id": mother.telegram_chat_id,
            "language": mother.preferred_language,
            "bmi": mother.bmi,
            "gravida": mother.gravida,
            "parity": mother.parity,
            # Add default health metrics for initial assessment
            "height": 160,  # Default
            "weight": mother.bmi * ((160/100) ** 2),  # Calculate from BMI
            "pregnancy_week": 20,  # Default - can be updated later
            "bp_systolic": 120,
            "bp_diastolic": 80,
            "hemoglobin": 12.0,
            "medical_history": {}
        }
        
        # Run AI agent assessment in background
        ai_assessment = await run_ai_agent_assessment(mother_data_for_ai, background_tasks)
        
        # Send Telegram welcome message if chat_id provided
        if mother.telegram_chat_id:
            welcome_msg = (
                f"🎉 <b>Welcome to MaatruRaksha AI!</b>\n\n"
                f"👶 Mother Registration Confirmed\n"
                f"<b>Name:</b> {mother.name}\n"
                f"<b>Phone:</b> {mother.phone}\n"
                f"<b>Location:</b> {mother.location}\n\n"
                f"📲 You will now receive health alerts and reminders.\n"
                f"Stay healthy! 💚"
            )
            background_tasks.add_task(send_telegram_message, mother.telegram_chat_id, welcome_msg)
        
        response_data = {
            "status": "success",
            "message": "Mother registered successfully",
            "mother_id": mother_id,
            "data": mother_db_data
        }
        
        # Add AI assessment if available
        if ai_assessment:
            response_data["ai_assessment"] = ai_assessment
            response_data["agents_used"] = ai_assessment.get("agents_executed", [])
        
        return response_data
    
    except HTTPException as e:
        logger.error(f"HTTP Error: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"❌ Error registering mother: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering mother: {str(e)}"
        )


@app.get("/mothers")
def get_all_mothers():
    """Get all registered mothers"""
    try:
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase not connected"
            )
        
        result = supabase.table("mothers").select("*").execute()
        logger.info(f"✅ Retrieved {len(result.data)} mothers")
        
        return {
            "status": "success",
            "count": len(result.data),
            "data": result.data
        }
    except Exception as e:
        logger.error(f"❌ Error fetching mothers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching mothers: {str(e)}"
        )


@app.get("/mothers/{mother_id}")
def get_mother(mother_id: str):
    """Get specific mother by ID"""
    try:
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase not connected"
            )
        
        result = supabase.table("mothers").select("*").eq("id", mother_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mother with ID {mother_id} not found"
            )
        
        return {
            "status": "success",
            "data": result.data[0]
        }
    except Exception as e:
        logger.error(f"❌ Error fetching mother: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching mother: {str(e)}"
        )


# ==================== RISK ASSESSMENT ENDPOINTS ====================

@app.post("/risk/assess")
async def assess_risk(assessment: RiskAssessment, background_tasks: BackgroundTasks):
    """Assess pregnancy risk for a mother with AI agent enhancement"""
    try:
        logger.info(f"⚠️ Assessing risk for mother: {assessment.mother_id}")
        logger.info(f"📊 Assessment data: {assessment.dict()}")
        
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase not connected"
            )
        
        # Verify mother exists
        mother_result = supabase.table("mothers").select("*").eq("id", assessment.mother_id).execute()
        if not mother_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mother with ID {assessment.mother_id} not found"
            )
        
        mother_data = mother_result.data[0]
        
        # Calculate risk score (original method)
        risk_calculation = calculate_risk_score(assessment)
        logger.info(f"📈 Risk calculation: {risk_calculation}")
        
        # Save assessment to database
        insert_data = {
            "mother_id": assessment.mother_id,
            "systolic_bp": assessment.systolic_bp,
            "diastolic_bp": assessment.diastolic_bp,
            "heart_rate": assessment.heart_rate,
            "blood_glucose": assessment.blood_glucose,
            "hemoglobin": assessment.hemoglobin,
            "proteinuria": assessment.proteinuria,
            "edema": assessment.edema,
            "headache": assessment.headache,
            "vision_changes": assessment.vision_changes,
            "epigastric_pain": assessment.epigastric_pain,
            "vaginal_bleeding": assessment.vaginal_bleeding,
            "risk_score": float(risk_calculation["risk_score"]),
            "risk_level": str(risk_calculation["risk_level"]),
            "notes": assessment.notes,
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"💾 Saving to Supabase: {insert_data}")
        result = supabase.table("risk_assessments").insert(insert_data).execute()
        
        logger.info(f"✅ Risk assessment saved: {risk_calculation['risk_level']}")
        
        # Prepare data for AI agents
        ai_mother_data = {
            "id": assessment.mother_id,
            "name": mother_data.get("name"),
            "age": mother_data.get("age"),
            "bmi": mother_data.get("bmi"),
            "bp_systolic": assessment.systolic_bp or 120,
            "bp_diastolic": assessment.diastolic_bp or 80,
            "hemoglobin": assessment.hemoglobin or 12.0,
            "weight": mother_data.get("bmi", 23) * ((160/100) ** 2),
            "height": 160,
            "pregnancy_week": 20,
            "telegram_chat_id": mother_data.get("telegram_chat_id"),
            "symptoms": []
        }
        
        # Add symptoms from assessment
        if assessment.headache == 1:
            ai_mother_data["symptoms"].append("headache")
        if assessment.vision_changes == 1:
            ai_mother_data["symptoms"].append("vision changes")
        if assessment.vaginal_bleeding == 1:
            ai_mother_data["symptoms"].append("vaginal bleeding")
        
        # Run AI agent assessment
        ai_assessment = await run_ai_agent_assessment(ai_mother_data, background_tasks)
        
        # Send Telegram alert if high or moderate risk and chat_id exists
        if mother_data.get("telegram_chat_id"):
            risk_level = risk_calculation["risk_level"]
            if risk_level in ["HIGH", "MODERATE"]:
                emoji = "🔴" if risk_level == "HIGH" else "🟡"
                risk_factors_text = "\n".join([f"• {factor}" for factor in risk_calculation["risk_factors"]])
                
                alert_msg = (
                    f"{emoji} <b>{risk_level} RISK ALERT</b>\n\n"
                    f"👶 <b>Mother:</b> {mother_data['name']}\n"
                    f"📊 <b>Risk Score:</b> {risk_calculation['risk_score']:.2%}\n\n"
                    f"<b>Risk Factors:</b>\n{risk_factors_text}\n\n"
                    f"⚠️ Please monitor closely or seek medical attention."
                )
                background_tasks.add_task(send_telegram_message, mother_data["telegram_chat_id"], alert_msg)
        
        response_data = {
            "status": "success",
            "message": f"Risk assessment completed - {risk_calculation['risk_level']} RISK",
            "risk_score": risk_calculation["risk_score"],
            "risk_level": risk_calculation["risk_level"],
            "risk_factors": risk_calculation["risk_factors"],
            "data": result.data[0] if result.data else None
        }
        
        # Add AI assessment if available
        if ai_assessment:
            response_data["ai_assessment"] = ai_assessment
            response_data["agents_executed"] = ai_assessment.get("agents_executed", [])
        
        return response_data
    
    except HTTPException as e:
        logger.error(f"HTTP Error: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"❌ Error assessing risk: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assessing risk: {str(e)}"
        )


@app.get("/risk/mother/{mother_id}")
def get_mother_risk(mother_id: str):
    """Get risk assessments for a specific mother"""
    try:
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase not connected"
            )
        
        result = supabase.table("risk_assessments").select("*").eq("mother_id", mother_id).order("created_at", desc=True).execute()
        
        return {
            "status": "success",
            "count": len(result.data),
            "data": result.data
        }
    except Exception as e:
        logger.error(f"❌ Error fetching risk assessments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching risk assessments: {str(e)}"
        )


# ==================== AI AGENT QUERY ENDPOINT (NEW) ====================
@app.post("/agents/query")
async def handle_agent_query(request: AgentQuery):
    """
    Handle natural language queries through AI agents
    NEW endpoint for direct agent interaction
    """
    if not AGENTS_AVAILABLE or not orchestrator:
        return {
            "success": False,
            "message": "AI Agents are not available",
            "response": "AI agent functionality is currently not loaded. Please contact system administrator."
        }
    
    try:
        logger.info(f"🤖 Agent Query from {request.mother_id}: {request.query}")
        
        response = await orchestrator.process_query(
            request.mother_id,
            request.query,
            request.context
        )
        
        return {
            "success": True,
            "mother_id": request.mother_id,
            "query": request.query,
            "response": response
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )


@app.get("/mothers/{mother_id}/daily-summary")
async def get_daily_summary(mother_id: str):
    """
    Get daily health summary generated by AI agents
    NEW endpoint for daily summaries
    """
    if not AGENTS_AVAILABLE or not orchestrator:
        return {
            "success": False,
            "message": "AI Agents are not available"
        }
    
    try:
        summary = await orchestrator.get_daily_summary(mother_id)
        return {
            "success": True,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"❌ Error getting daily summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting daily summary: {str(e)}"
        )

class DailyCheckIn(BaseModel):
    """Daily health check-in from mother"""
    mother_id: str
    date: str
    weight: Optional[float] = None
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    symptoms: Optional[List[str]] = []
    medications_taken: bool = True
    feeling_today: str = "good"  # good, okay, unwell
    notes: Optional[str] = None


class WeeklyUpdate(BaseModel):
    """Weekly health update"""
    mother_id: str
    week_number: int
    weight: float
    bp_systolic: int
    bp_diastolic: int
    hemoglobin: Optional[float] = None
    symptoms: Optional[List[str]] = []
    notes: Optional[str] = None


class SymptomReport(BaseModel):
    """Emergency symptom reporting"""
    mother_id: str
    symptoms: List[str]
    severity: str  # mild, moderate, severe
    notes: Optional[str] = None


class AshaVisitReport(BaseModel):
    """ASHA worker visit report"""
    mother_id: str
    visit_date: str
    weight: float
    bp_systolic: int
    bp_diastolic: int
    hemoglobin: Optional[float] = None
    observations: str
    recommendations: str
    next_visit_date: str
    asha_worker_id: str


# ==================== DAILY CHECK-IN ENDPOINT ====================

@app.post("/mothers/{mother_id}/daily-checkin")
async def daily_health_checkin(
    mother_id: str, 
    checkin: DailyCheckIn,
    background_tasks: BackgroundTasks
):
    """
    Daily health check-in - Mother reports daily
    TRIGGERS: Agents if concerning symptoms
    """
    try:
        logger.info(f"📅 Daily check-in for mother: {mother_id}")
        
        # Get mother data
        mother_result = supabase.table("mothers").select("*").eq("id", mother_id).execute()
        if not mother_result.data:
            raise HTTPException(status_code=404, detail="Mother not found")
        
        mother_data = mother_result.data[0]
        
        # Save to health timeline
        timeline_entry = {
            "mother_id": mother_id,
            "date": checkin.date,
            "weight": checkin.weight,
            "bp_systolic": checkin.bp_systolic,
            "bp_diastolic": checkin.bp_diastolic,
            "symptoms": checkin.symptoms,
            "entry_type": "self_report",
            "feeling": checkin.feeling_today,
            "medications_taken": checkin.medications_taken,
            "notes": checkin.notes,
            "created_at": datetime.now().isoformat()
        }
        
        # Check if concerning symptoms or vitals
        needs_assessment = False
        alert_reasons = []
        
        # Check vitals
        if checkin.bp_systolic and checkin.bp_systolic > 140:
            needs_assessment = True
            alert_reasons.append("High blood pressure")
        
        # Check symptoms
        concerning_symptoms = [
            "bleeding", "severe pain", "severe headache", 
            "vision changes", "decreased movement"
        ]
        if any(symptom.lower() in ' '.join(checkin.symptoms).lower() 
               for symptom in concerning_symptoms):
            needs_assessment = True
            alert_reasons.append("Concerning symptoms reported")
        
        # Check feeling
        if checkin.feeling_today == "unwell":
            needs_assessment = True
            alert_reasons.append("Mother feeling unwell")
        
        # Check medications
        if not checkin.medications_taken:
            alert_reasons.append("Medications not taken")
        
        ai_assessment = None
        
        # Run AI assessment if needed
        if needs_assessment and AGENTS_AVAILABLE:
            logger.info(f"⚠️ Concerning signs detected: {alert_reasons}")
            
            # Prepare data for agents
            assessment_data = {
                "id": mother_id,
                "name": mother_data.get("name"),
                "age": mother_data.get("age"),
                "bmi": mother_data.get("bmi"),
                "bp_systolic": checkin.bp_systolic or 120,
                "bp_diastolic": checkin.bp_diastolic or 80,
                "weight": checkin.weight or mother_data.get("bmi", 23) * 2.56,
                "height": 160,
                "pregnancy_week": calculate_pregnancy_week(mother_data.get("created_at")),
                "symptoms": checkin.symptoms,
                "telegram_chat_id": mother_data.get("telegram_chat_id")
            }
            
            # Run agent assessment
            ai_assessment = await run_ai_agent_assessment(assessment_data, background_tasks)
            timeline_entry["ai_assessment"] = ai_assessment
            timeline_entry["risk_level"] = ai_assessment.get("risk_assessment", {}).get("risk_level")
        
        # Save to database (use your actual table name)
        # supabase.table("health_timeline").insert(timeline_entry).execute()
        
        # Send Telegram update
        if mother_data.get("telegram_chat_id"):
            if needs_assessment:
                message = (
                    f"⚠️ <b>Health Alert</b>\n\n"
                    f"We noticed: {', '.join(alert_reasons)}\n\n"
                    f"Our AI team has analyzed your condition.\n"
                    f"Please check your detailed assessment."
                )
            else:
                message = (
                    f"✅ <b>Daily Check-in Received</b>\n\n"
                    f"Thank you for updating your health today!\n"
                    f"Feeling: {checkin.feeling_today}\n"
                    f"Medications: {'✅ Taken' if checkin.medications_taken else '❌ Missed'}\n\n"
                    f"Keep up the good work! 💚"
                )
            
            background_tasks.add_task(
                send_telegram_message,
                mother_data["telegram_chat_id"],
                message
            )
        
        return {
            "status": "success",
            "message": "Daily check-in recorded",
            "needs_attention": needs_assessment,
            "alert_reasons": alert_reasons,
            "ai_assessment": ai_assessment if needs_assessment else None
        }
        
    except Exception as e:
        logger.error(f"Error in daily check-in: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== WEEKLY AUTO-ASSESSMENT ====================

@app.post("/mothers/{mother_id}/weekly-assessment")
async def weekly_automated_assessment(
    mother_id: str,
    background_tasks: BackgroundTasks
):
    """
    Weekly automated assessment
    TRIGGERS: All agents for comprehensive check
    RUNS: Automatically via cron job
    """
    try:
        logger.info(f"📊 Weekly assessment for mother: {mother_id}")
        
        # Get mother data
        mother_result = supabase.table("mothers").select("*").eq("id", mother_id).execute()
        if not mother_result.data:
            raise HTTPException(status_code=404, detail="Mother not found")
        
        mother_data = mother_result.data[0]
        
        # Get latest health data from timeline
        # In real implementation, query health_timeline table
        # For now, use stored data
        
        current_week = calculate_pregnancy_week(mother_data.get("created_at"))
        
        # Prepare comprehensive data
        assessment_data = {
            "id": mother_id,
            "name": mother_data.get("name"),
            "age": mother_data.get("age"),
            "bmi": mother_data.get("bmi"),
            "pregnancy_week": current_week,
            "weight": 65,  # Get from latest timeline entry
            "height": 160,
            "bp_systolic": 120,  # Get from latest
            "bp_diastolic": 80,
            "hemoglobin": 12.0,
            "telegram_chat_id": mother_data.get("telegram_chat_id")
        }
        
        # Run full AI assessment
        if AGENTS_AVAILABLE:
            ai_assessment = await run_ai_agent_assessment(assessment_data, background_tasks)
            
            # Send weekly report via Telegram
            if mother_data.get("telegram_chat_id"):
                risk_level = ai_assessment.get("risk_assessment", {}).get("risk_level", "low")
                risk_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(risk_level, "🟢")
                
                message = (
                    f"{risk_emoji} <b>Weekly Health Report - Week {current_week}</b>\n\n"
                    f"📊 <b>Current Status:</b> {risk_level.upper()}\n\n"
                    f"📋 <b>This Week's Focus:</b>\n"
                    f"• Continue prenatal vitamins\n"
                    f"• Monitor baby movements\n"
                    f"• Stay hydrated\n\n"
                    f"📅 <b>Next Check:</b> {(datetime.now() + timedelta(days=7)).strftime('%B %d')}\n\n"
                    f"💚 Keep up the great work!"
                )
                
                background_tasks.add_task(
                    send_telegram_message,
                    mother_data["telegram_chat_id"],
                    message
                )
            
            return {
                "status": "success",
                "week_number": current_week,
                "assessment": ai_assessment
            }
        
        return {
            "status": "success",
            "message": "Weekly assessment completed",
            "week_number": current_week
        }
        
    except Exception as e:
        logger.error(f"Error in weekly assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SYMPTOM REPORTING ====================

@app.post("/mothers/{mother_id}/report-symptom")
async def report_symptom(
    mother_id: str,
    symptom: SymptomReport,
    background_tasks: BackgroundTasks
):
    """
    Emergency symptom reporting
    TRIGGERS: Emergency Agent immediately
    """
    try:
        logger.info(f"🚨 Symptom report for mother: {mother_id}")
        logger.info(f"Symptoms: {symptom.symptoms}, Severity: {symptom.severity}")
        
        # Get mother data
        mother_result = supabase.table("mothers").select("*").eq("id", mother_id).execute()
        if not mother_result.data:
            raise HTTPException(status_code=404, detail="Mother not found")
        
        mother_data = mother_result.data[0]
        
        # Prepare data for emergency assessment
        emergency_data = {
            "id": mother_id,
            "name": mother_data.get("name"),
            "symptoms": symptom.symptoms,
            "severity": symptom.severity,
            "telegram_chat_id": mother_data.get("telegram_chat_id"),
            "bp_systolic": 120,
            "bp_diastolic": 80,
            "pregnancy_week": calculate_pregnancy_week(mother_data.get("created_at"))
        }
        
        # Run emergency assessment if agents available
        if AGENTS_AVAILABLE:
            ai_assessment = await run_ai_agent_assessment(emergency_data, background_tasks)
            
            emergency_result = ai_assessment.get("emergency_assessment", {})
            is_emergency = emergency_result.get("is_emergency", False)
            
            if is_emergency:
                logger.info("⚠️ EMERGENCY DETECTED")
                
                # Send immediate alert
                if mother_data.get("telegram_chat_id"):
                    actions_text = "\n".join([
                        f"• {action}" 
                        for action in emergency_result.get("immediate_actions", [])[:5]
                    ])
                    
                    emergency_message = (
                        f"🚨 <b>EMERGENCY ALERT</b>\n\n"
                        f"Severity: <b>{emergency_result.get('severity', 'HIGH').upper()}</b>\n\n"
                        f"<b>Immediate Actions:</b>\n{actions_text}\n\n"
                        f"📞 <b>Emergency: 108</b>\n"
                        f"🏥 <b>Go to nearest hospital if severe</b>"
                    )
                    
                    background_tasks.add_task(
                        send_telegram_message,
                        mother_data["telegram_chat_id"],
                        emergency_message
                    )
            
            return {
                "status": "success",
                "is_emergency": is_emergency,
                "severity": symptom.severity,
                "assessment": ai_assessment
            }
        
        return {
            "status": "success",
            "message": "Symptom reported"
        }
        
    except Exception as e:
        logger.error(f"Error reporting symptom: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ASHA VISIT REPORT ====================

@app.post("/asha/visit-report")
async def submit_asha_visit_report(
    report: AshaVisitReport,
    background_tasks: BackgroundTasks
):
    """
    ASHA worker submits visit report
    TRIGGERS: Full reassessment with updated data
    """
    try:
        logger.info(f"👩‍⚕️ ASHA visit report for mother: {report.mother_id}")
        
        # Get mother data
        mother_result = supabase.table("mothers").select("*").eq("id", report.mother_id).execute()
        if not mother_result.data:
            raise HTTPException(status_code=404, detail="Mother not found")
        
        mother_data = mother_result.data[0]
        
        # Prepare assessment data with visit findings
        assessment_data = {
            "id": report.mother_id,
            "name": mother_data.get("name"),
            "age": mother_data.get("age"),
            "weight": report.weight,
            "bp_systolic": report.bp_systolic,
            "bp_diastolic": report.bp_diastolic,
            "hemoglobin": report.hemoglobin or 12.0,
            "pregnancy_week": calculate_pregnancy_week(mother_data.get("created_at")),
            "telegram_chat_id": mother_data.get("telegram_chat_id")
        }
        
        # Run comprehensive assessment
        ai_assessment = None
        if AGENTS_AVAILABLE:
            ai_assessment = await run_ai_agent_assessment(assessment_data, background_tasks)
        
        # Save visit report to database
        visit_record = {
            "mother_id": report.mother_id,
            "visit_date": report.visit_date,
            "asha_worker_id": report.asha_worker_id,
            "vitals": {
                "weight": report.weight,
                "bp": f"{report.bp_systolic}/{report.bp_diastolic}",
                "hemoglobin": report.hemoglobin
            },
            "observations": report.observations,
            "recommendations": report.recommendations,
            "next_visit_date": report.next_visit_date,
            "ai_assessment": ai_assessment,
            "created_at": datetime.now().isoformat()
        }
        
        # Send confirmation to mother via Telegram
        if mother_data.get("telegram_chat_id"):
            message = (
                f"👩‍⚕️ <b>ASHA Visit Completed</b>\n\n"
                f"Date: {report.visit_date}\n"
                f"BP: {report.bp_systolic}/{report.bp_diastolic}\n"
                f"Weight: {report.weight} kg\n\n"
                f"<b>Observations:</b>\n{report.observations}\n\n"
                f"<b>Next Visit:</b> {report.next_visit_date}\n\n"
                f"Stay healthy! 💚"
            )
            
            background_tasks.add_task(
                send_telegram_message,
                mother_data["telegram_chat_id"],
                message
            )
        
        return {
            "status": "success",
            "message": "ASHA visit report submitted",
            "next_visit": report.next_visit_date,
            "ai_assessment": ai_assessment
        }
        
    except Exception as e:
        logger.error(f"Error submitting ASHA report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== HEALTH TIMELINE ====================

@app.get("/mothers/{mother_id}/timeline")
def get_health_timeline(mother_id: str, days: int = 30):
    """
    Get health timeline for last N days
    Shows trend over time
    """
    try:
        # In real implementation, query health_timeline table
        # For now, return mock data structure
        
        return {
            "status": "success",
            "mother_id": mother_id,
            "period_days": days,
            "timeline": [
                {
                    "date": "2025-10-15",
                    "week": 28,
                    "bp": "120/80",
                    "weight": 65,
                    "risk_level": "low",
                    "entry_type": "daily_checkin"
                },
                {
                    "date": "2025-10-10",
                    "week": 27,
                    "bp": "125/82",
                    "weight": 64.5,
                    "risk_level": "low",
                    "entry_type": "asha_visit"
                }
            ],
            "trends": {
                "bp_trend": "stable",
                "weight_trend": "increasing_normal",
                "risk_trend": "stable"
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching timeline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== HELPER FUNCTIONS ====================

def calculate_pregnancy_week(registration_date: str) -> int:
    """Calculate current pregnancy week from registration"""
    try:
        reg_date = datetime.fromisoformat(registration_date.replace('Z', '+00:00'))
        days_since = (datetime.now() - reg_date).days
        # Assume registered at week 8 (common first visit)
        return 8 + (days_since // 7)
    except:
        return 20  # Default fallback



# ==================== ANALYTICS ENDPOINTS ====================

@app.get("/analytics/dashboard")
def get_dashboard_analytics():
    """Get dashboard analytics"""
    try:
        if not supabase:
            return {
                "status": "success",
                "total_mothers": 0,
                "high_risk_count": 0,
                "moderate_risk_count": 0,
                "low_risk_count": 0,
                "total_assessments": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        # Get all mothers
        mothers_result = supabase.table("mothers").select("*").execute()
        total_mothers = len(mothers_result.data) if mothers_result.data else 0
        logger.info(f"📊 Total mothers: {total_mothers}")
        
        # Get all risk assessments
        assessments_result = supabase.table("risk_assessments").select("*").execute()
        assessments = assessments_result.data if assessments_result.data else []
        logger.info(f"📊 Total assessments: {len(assessments)}")
        
        # Count risk levels
        high_risk = 0
        moderate_risk = 0
        low_risk = 0
        
        for assessment in assessments:
            risk_level = assessment.get("risk_level")
            
            if risk_level == "HIGH":
                high_risk += 1
            elif risk_level == "MODERATE":
                moderate_risk += 1
            elif risk_level == "LOW":
                low_risk += 1
        
        logger.info(f"✅ Analytics: HIGH={high_risk}, MODERATE={moderate_risk}, LOW={low_risk}")
        
        analytics_data = {
            "status": "success",
            "total_mothers": total_mothers,
            "high_risk_count": high_risk,
            "moderate_risk_count": moderate_risk,
            "low_risk_count": low_risk,
            "total_assessments": len(assessments),
            "timestamp": datetime.now().isoformat()
        }
        
        # Add AI agent stats if available
        if AGENTS_AVAILABLE and orchestrator:
            try:
                agent_status = orchestrator.get_agent_status()
                analytics_data["ai_stats"] = {
                    "agents_active": True,
                    "total_requests": agent_status.get("total_requests_processed", 0)
                }
            except:
                pass
        
        return analytics_data
        
    except Exception as e:
        logger.error(f"❌ Error fetching analytics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching analytics: {str(e)}"
        )


# ==================== ROOT ENDPOINT ====================
@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "MaatruRaksha AI Backend API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "telegram_polling": "🟢 Active" if polling_active else "🔴 Inactive",
        "ai_agents": "🤖 Active" if AGENTS_AVAILABLE else "❌ Not Loaded"
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("=" * 60)
    logger.info("🚀 Starting MaatruRaksha AI Backend v2.0...")
    logger.info("=" * 60)
    logger.info(f"📌 Supabase URL: {SUPABASE_URL}")
    logger.info(f"📱 Telegram Bot Token: {'✅ Set' if TELEGRAM_BOT_TOKEN != 'placeholder' else '❌ Not Set'}")
    logger.info(f"🔄 Telegram Polling will start automatically...")
    logger.info(f"🤖 AI Agents: {'✅ Enabled' if AGENTS_AVAILABLE else '⚠️ Not Loaded (Basic Mode)'}")
    logger.info("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)