"""
MatruRaksha AI - Complete Telegram Bot with All Fixes
File: backend/telegram_bot.py

FIXES IMPLEMENTED:
✅ 1. Agent routing - messages routed to specialized agents via orchestrator
✅ 2. File storage - using Telegram URLs directly (no 404 errors)
✅ 3. Markdown fixes - no parsing errors
✅ 4. Mother switching - full support for multiple profiles
"""

import os
import logging
import requests
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Import orchestrator
try:
    from agents.orchestrator import get_orchestrator
    ORCHESTRATOR_AVAILABLE = True
    logger.info("✅ Orchestrator loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Orchestrator not available: {e}")
    ORCHESTRATOR_AVAILABLE = False

# Conversation states for registration
(AWAITING_NAME, AWAITING_AGE, AWAITING_PHONE, AWAITING_DUE_DATE, 
 AWAITING_LOCATION, AWAITING_GRAVIDA, AWAITING_PARITY, AWAITING_BMI, 
 AWAITING_LANGUAGE, CONFIRM_REGISTRATION) = range(10)


class MatruRakshaBot:
    """Enhanced Telegram Bot with agent routing and mother switching"""
    
    def __init__(self):
        self.registration_data = {}  # telegram_id -> temp registration data
        self.orchestrator = get_orchestrator() if ORCHESTRATOR_AVAILABLE else None
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        telegram_id = update.effective_user.id
        first_name = update.effective_user.first_name or "User"
        
        # Check existing registrations
        try:
            result = supabase.table('mothers').select('*').eq('telegram_chat_id', str(telegram_id)).execute()
            registered_mothers = result.data if result.data else []
        except Exception as e:
            logger.error(f"Database error: {e}")
            registered_mothers = []
        
        if registered_mothers:
            # Get currently selected mother
            selected_mother_id = context.user_data.get('selected_mother_id')
            if not selected_mother_id or not any(m['id'] == selected_mother_id for m in registered_mothers):
                # Default to first mother
                selected_mother_id = registered_mothers[0]['id']
                context.user_data['selected_mother_id'] = selected_mother_id
            
            selected_mother = next(m for m in registered_mothers if m['id'] == selected_mother_id)
            
            # Build keyboard
            keyboard = [
                [InlineKeyboardButton("📤 Upload Medical Report", callback_data="upload")],
                [InlineKeyboardButton("💬 Ask Health Question", callback_data="ask")],
                [InlineKeyboardButton("📊 View Health Summary", callback_data="summary")],
            ]
            
            # Add mother switching if multiple profiles
            if len(registered_mothers) > 1:
                keyboard.append([
                    InlineKeyboardButton(
                        f"🔄 Switch Profile ({len(registered_mothers)} profiles)", 
                        callback_data="switch_mother"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("➕ Register Another Mother", callback_data="register_new")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Build mothers list with indicator for selected
            mothers_list = "\n".join([
                f"{'✅' if m['id'] == selected_mother_id else '•'} {m['name']} (Age: {m['age']})" 
                for m in registered_mothers
            ])
            
            await update.message.reply_text(
                f"🤰 Welcome back, {first_name}!\n\n"
                f"Registered Profiles:\n{mothers_list}\n\n"
                f"Current Profile: {selected_mother['name']}\n\n"
                f"How can I help you today?",
                reply_markup=reply_markup
            )
        else:
            # New user
            keyboard = [[InlineKeyboardButton("📋 Register as Mother", callback_data="register")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"🎉 Welcome to MatruRaksha AI, {first_name}!\n\n"
                f"I'm your personal maternal health assistant.\n\n"
                f"Your Telegram Chat ID: {telegram_id}\n\n"
                f"To get started, please register your profile:",
                reply_markup=reply_markup
            )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        telegram_id = update.effective_user.id
        
        if query.data in ["register", "register_new"]:
            # Start registration process
            self.registration_data[telegram_id] = {}
            await query.message.reply_text(
                "📝 Let's register your profile!\n\n"
                "Please enter your full name:"
            )
            return AWAITING_NAME
            
        elif query.data == "upload":
            await query.message.reply_text(
                "📤 Upload Medical Report\n\n"
                "Please send me your medical report.\n\n"
                "Supported formats:\n"
                "• PDF documents\n"
                "• Images (JPG, PNG)\n"
                "• Word documents (.docx)"
            )
            
        elif query.data == "ask":
            await query.message.reply_text(
                "💬 Ask Health Question\n\n"
                "Type your health-related question, and I'll provide personalized insights."
            )
            
        elif query.data == "summary":
            await self.send_health_summary(query.message, telegram_id, context)
        
        elif query.data == "switch_mother":
            await self.show_mother_selection(query.message, telegram_id, context)
        
        elif query.data.startswith("select_mother_"):
            # Handle mother selection
            mother_id = query.data.replace("select_mother_", "")
            context.user_data['selected_mother_id'] = mother_id
            
            # Get mother info
            try:
                result = supabase.table('mothers').select('*').eq('id', mother_id).execute()
                if result.data:
                    mother = result.data[0]
                    
                    # Build main menu
                    keyboard = [
                        [InlineKeyboardButton("📤 Upload Medical Report", callback_data="upload")],
                        [InlineKeyboardButton("💬 Ask Health Question", callback_data="ask")],
                        [InlineKeyboardButton("📊 View Health Summary", callback_data="summary")],
                    ]
                    
                    # Get all mothers for switch option
                    all_mothers_result = supabase.table('mothers').select('*').eq('telegram_chat_id', str(telegram_id)).execute()
                    if all_mothers_result.data and len(all_mothers_result.data) > 1:
                        keyboard.append([
                            InlineKeyboardButton(
                                f"🔄 Switch Profile ({len(all_mothers_result.data)} profiles)", 
                                callback_data="switch_mother"
                            )
                        ])
                    
                    keyboard.append([InlineKeyboardButton("➕ Register Another Mother", callback_data="register_new")])
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.message.reply_text(
                        f"✅ Switched to profile: {mother['name']}\n\n"
                        f"All actions will now use this profile.\n\n"
                        f"How can I help you today?",
                        reply_markup=reply_markup
                    )
            except Exception as e:
                logger.error(f"Error switching mother: {e}")
                await query.message.reply_text("❌ Error switching profile. Please try again.")
        
        return ConversationHandler.END
    
    async def show_mother_selection(self, message, telegram_id, context: ContextTypes.DEFAULT_TYPE):
        """Show mother selection menu"""
        try:
            result = supabase.table('mothers').select('*').eq('telegram_chat_id', str(telegram_id)).execute()
            if not result.data:
                await message.reply_text("❌ No profiles found.")
                return
            
            mothers = result.data
            selected_mother_id = context.user_data.get('selected_mother_id')
            
            keyboard = []
            for mother in mothers:
                is_selected = "✅ " if mother['id'] == selected_mother_id else ""
                keyboard.append([
                    InlineKeyboardButton(
                        f"{is_selected}{mother['name']} (Age: {mother['age']})",
                        callback_data=f"select_mother_{mother['id']}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await message.reply_text(
                "🔄 Select Mother Profile\n\n"
                "Choose which profile to use:\n"
                "(✅ indicates current profile)",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error showing mother selection: {e}")
            await message.reply_text("❌ Error loading profiles. Please try again.")
    
    # Registration handlers (same as before)
    async def receive_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive name and ask for age"""
        telegram_id = update.effective_user.id
        name = update.message.text.strip()
        
        if not name or len(name) < 2:
            await update.message.reply_text("❌ Please enter a valid name (at least 2 characters):")
            return AWAITING_NAME
        
        self.registration_data[telegram_id]['name'] = name
        await update.message.reply_text(f"✅ Name: {name}\n\nPlease enter your age (in years):")
        return AWAITING_AGE
    
    async def receive_age(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive age and ask for phone"""
        telegram_id = update.effective_user.id
        
        try:
            age = int(update.message.text.strip())
            if age < 15 or age > 55:
                await update.message.reply_text("❌ Please enter a valid age between 15 and 55:")
                return AWAITING_AGE
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number for age:")
            return AWAITING_AGE
        
        self.registration_data[telegram_id]['age'] = age
        await update.message.reply_text(f"✅ Age: {age} years\n\nPlease enter your phone number (10 digits):")
        return AWAITING_PHONE
    
    async def receive_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive phone and ask for due date"""
        telegram_id = update.effective_user.id
        phone = update.message.text.strip().replace("+", "").replace("-", "").replace(" ", "")
        
        if not phone.isdigit() or len(phone) < 10:
            await update.message.reply_text("❌ Please enter a valid 10-digit phone number:")
            return AWAITING_PHONE
        
        self.registration_data[telegram_id]['phone'] = phone
        await update.message.reply_text(
            f"✅ Phone: {phone}\n\n"
            f"Please enter your expected due date (format: DD-MM-YYYY):"
        )
        return AWAITING_DUE_DATE
    
    async def receive_due_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive due date and ask for location"""
        telegram_id = update.effective_user.id
        due_date_text = update.message.text.strip()
        
        try:
            due_date = datetime.strptime(due_date_text, "%d-%m-%Y").date()
            if due_date < datetime.now().date():
                await update.message.reply_text("❌ Due date must be in the future. Please try again (DD-MM-YYYY):")
                return AWAITING_DUE_DATE
        except ValueError:
            await update.message.reply_text("❌ Invalid date format. Please use DD-MM-YYYY (e.g., 15-08-2025):")
            return AWAITING_DUE_DATE
        
        self.registration_data[telegram_id]['due_date'] = str(due_date)
        await update.message.reply_text(f"✅ Due Date: {due_date_text}\n\nPlease enter your location (City, State):")
        return AWAITING_LOCATION
    
    async def receive_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive location and ask for gravida"""
        telegram_id = update.effective_user.id
        location = update.message.text.strip()
        
        if len(location) < 3:
            await update.message.reply_text("❌ Please enter a valid location:")
            return AWAITING_LOCATION
        
        self.registration_data[telegram_id]['location'] = location
        await update.message.reply_text(
            f"✅ Location: {location}\n\n"
            f"How many times have you been pregnant (including this pregnancy)?\n"
            f"Enter Gravida number:"
        )
        return AWAITING_GRAVIDA
    
    async def receive_gravida(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive gravida and ask for parity"""
        telegram_id = update.effective_user.id
        
        try:
            gravida = int(update.message.text.strip())
            if gravida < 1 or gravida > 10:
                await update.message.reply_text("❌ Please enter a valid number (1-10):")
                return AWAITING_GRAVIDA
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number:")
            return AWAITING_GRAVIDA
        
        self.registration_data[telegram_id]['gravida'] = gravida
        await update.message.reply_text(
            f"✅ Gravida: {gravida}\n\n"
            f"How many live births have you had?\n"
            f"Enter Parity number:"
        )
        return AWAITING_PARITY
    
    async def receive_parity(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive parity and ask for BMI"""
        telegram_id = update.effective_user.id
        
        try:
            parity = int(update.message.text.strip())
            gravida = self.registration_data[telegram_id]['gravida']
            if parity < 0 or parity >= gravida:
                await update.message.reply_text(f"❌ Parity must be less than Gravida ({gravida}). Please try again:")
                return AWAITING_PARITY
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number:")
            return AWAITING_PARITY
        
        self.registration_data[telegram_id]['parity'] = parity
        await update.message.reply_text(
            f"✅ Parity: {parity}\n\n"
            f"Please enter your BMI (Body Mass Index):\n"
            f"(If you don't know, calculate: weight(kg) / height(m)²)"
        )
        return AWAITING_BMI
    
    async def receive_bmi(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive BMI and ask for language preference"""
        telegram_id = update.effective_user.id
        
        try:
            bmi = float(update.message.text.strip())
            if bmi < 10 or bmi > 50:
                await update.message.reply_text("❌ Please enter a valid BMI (typically 15-40):")
                return AWAITING_BMI
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number for BMI:")
            return AWAITING_BMI
        
        self.registration_data[telegram_id]['bmi'] = bmi
        
        keyboard = [
            [InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")],
            [InlineKeyboardButton("हिंदी 🇮🇳", callback_data="lang_hi")],
            [InlineKeyboardButton("मराठी", callback_data="lang_mr")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ BMI: {bmi}\n\n"
            f"Please select your preferred language:",
            reply_markup=reply_markup
        )
        return AWAITING_LANGUAGE
    
    async def receive_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive language preference and show confirmation"""
        query = update.callback_query
        await query.answer()
        
        telegram_id = update.effective_user.id
        language_code = query.data.split('_')[1]
        language_map = {"en": "English", "hi": "Hindi", "mr": "Marathi"}
        
        self.registration_data[telegram_id]['preferred_language'] = language_code
        
        # Show confirmation
        data = self.registration_data[telegram_id]
        confirmation_text = (
            "📋 Registration Summary\n\n"
            f"👤 Name: {data['name']}\n"
            f"📅 Age: {data['age']} years\n"
            f"📱 Phone: {data['phone']}\n"
            f"🗓️ Due Date: {data['due_date']}\n"
            f"📍 Location: {data['location']}\n"
            f"🤰 Gravida: {data['gravida']}\n"
            f"👶 Parity: {data['parity']}\n"
            f"⚖️ BMI: {data['bmi']}\n"
            f"🌐 Language: {language_map[language_code]}\n\n"
            f"Is this information correct?"
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ Confirm & Register", callback_data="confirm_yes")],
            [InlineKeyboardButton("❌ Cancel", callback_data="confirm_no")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(confirmation_text, reply_markup=reply_markup)
        return CONFIRM_REGISTRATION
    
    async def confirm_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm and save registration"""
        query = update.callback_query
        await query.answer()
        
        telegram_id = update.effective_user.id
        
        if query.data == "confirm_no":
            if telegram_id in self.registration_data:
                del self.registration_data[telegram_id]
            
            await query.message.reply_text("❌ Registration cancelled.\n\nUse /start to begin again.")
            return ConversationHandler.END
        
        # Save to database
        try:
            data = self.registration_data[telegram_id]
            data['telegram_chat_id'] = str(telegram_id)
            data['created_at'] = datetime.now().isoformat()
            
            result = supabase.table('mothers').insert(data).execute()
            
            if result.data:
                new_mother_id = result.data[0]['id']
                # Set as selected mother
                context.user_data['selected_mother_id'] = new_mother_id
                
                del self.registration_data[telegram_id]
                
                keyboard = [
                    [InlineKeyboardButton("📤 Upload Medical Report", callback_data="upload")],
                    [InlineKeyboardButton("💬 Ask Health Question", callback_data="ask")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.message.reply_text(
                    f"✅ Registration Successful!\n\n"
                    f"Welcome to MatruRaksha AI, {data['name']}! 🤰\n\n"
                    f"You can now:\n"
                    f"• Upload medical reports\n"
                    f"• Ask health questions\n"
                    f"• Get personalized insights\n\n"
                    f"What would you like to do?",
                    reply_markup=reply_markup
                )
            else:
                raise Exception("Failed to insert into database")
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            await query.message.reply_text(
                "❌ Registration failed. Please try again later.\n\n"
                "Error: Database connection issue."
            )
        
        return ConversationHandler.END
    
    async def cancel_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel registration"""
        telegram_id = update.effective_user.id
        if telegram_id in self.registration_data:
            del self.registration_data[telegram_id]
        
        await update.message.reply_text("❌ Registration cancelled.\n\nUse /start to begin again.")
        return ConversationHandler.END
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads - FIXED: Using Telegram URLs directly"""
        telegram_id = update.effective_user.id
        
        # Check if user is registered
        try:
            result = supabase.table('mothers').select('*').eq('telegram_chat_id', str(telegram_id)).execute()
            if not result.data:
                await update.message.reply_text("❌ Please register first using /start")
                return
            
            # Get selected mother
            selected_mother_id = context.user_data.get('selected_mother_id')
            if selected_mother_id:
                mother_data = next((m for m in result.data if m['id'] == selected_mother_id), result.data[0])
            else:
                mother_data = result.data[0]
                context.user_data['selected_mother_id'] = mother_data['id']
                
        except Exception as e:
            logger.error(f"Database error: {e}")
            await update.message.reply_text("❌ Database error. Please try again.")
            return
        
        # Get file info
        file = None
        file_type = None
        file_id = None
        file_name = None
        
        if update.message.document:
            file = await update.message.document.get_file()
            file_type = update.message.document.mime_type
            file_name = update.message.document.file_name
            file_id = update.message.document.file_id
        elif update.message.photo:
            file = await update.message.photo[-1].get_file()
            file_type = "image/jpeg"
            file_name = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            file_id = update.message.photo[-1].file_id
        
        if not file:
            await update.message.reply_text("❌ Unsupported file type")
            return
        
        await update.message.reply_text("📥 Processing your document...")
        
        # ✅ FIX: Use Telegram's file URL directly (no download/upload needed!)
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file.file_path}"
        storage_path = f"telegram/{telegram_id}/{file_id}"
        
        logger.info(f"✅ Using Telegram file URL: {file_url}")
        
        try:
            # Save to medical_reports table directly
            report_data = {
                'mother_id': str(mother_data['id']),
                'telegram_chat_id': str(telegram_id),
                'file_name': file_name,
                'file_type': file_type,
                'file_url': file_url,  # Telegram URL - accessible!
                'file_path': storage_path,
                'uploaded_at': datetime.now().isoformat(),
                'analysis_status': 'pending'
            }
            
            db_result = supabase.table('medical_reports').insert(report_data).execute()
            
            if db_result.data:
                report_id = db_result.data[0]['id']
                
                await update.message.reply_text("🤖 Analyzing with AI... (1-2 minutes)")
                
                # Trigger analysis via backend API
                try:
                    def call_analysis_api():
                        return requests.post(
                            f"{BACKEND_API_URL}/analyze-report",
                            json={
                                "report_id": str(report_id),
                                "mother_id": str(mother_data['id']),
                                "file_url": file_url,
                                "file_type": file_type
                            },
                            timeout=180
                        )
                    
                    loop = asyncio.get_event_loop()
                    response = await asyncio.wait_for(
                        loop.run_in_executor(None, call_analysis_api),
                        timeout=180.0
                    )
                    
                    if response.status_code == 200:
                        analysis_result = response.json()
                        
                        risk_level = analysis_result.get('risk_level', 'unknown').upper()
                        concerns = analysis_result.get('concerns', [])
                        recommendations = analysis_result.get('recommendations', [])
                        
                        message = "✅ Analysis Complete!\n\n"
                        message += f"📊 Risk Level: {risk_level}\n\n"
                        
                        if concerns:
                            message += "⚠️ Concerns Found:\n"
                            for concern in concerns[:3]:
                                message += f"• {concern}\n"
                            message += "\n"
                        
                        if recommendations:
                            message += "💡 Recommendations:\n"
                            for rec in recommendations[:3]:
                                message += f"• {rec}\n"
                            message += "\n"
                        
                        message += "📄 Report saved successfully!"
                        
                        await update.message.reply_text(message)
                    else:
                        await update.message.reply_text(
                            f"✅ Document Saved!\n\n"
                            f"📄 File: {file_name}\n"
                            f"⏳ Analysis in progress...\n\n"
                            f"You'll be notified when complete!"
                        )
                        
                except asyncio.TimeoutError:
                    await update.message.reply_text(
                        f"✅ Document Saved!\n\n"
                        f"📄 File: {file_name}\n"
                        f"🔄 AI analysis running in background...\n\n"
                        f"Results will be ready soon!"
                    )
                except Exception as api_error:
                    logger.error(f"API error: {api_error}")
                    await update.message.reply_text(
                        f"✅ Document Saved!\n\n"
                        f"📄 File: {file_name}\n"
                        f"⚠️ Analysis will be processed shortly."
                    )
            else:
                raise Exception("Failed to save to database")
                
        except Exception as e:
            logger.error(f"File processing error: {e}")
            await update.message.reply_text(
                f"❌ Upload Failed\n\n"
                f"Error: {str(e)[:100]}\n\n"
                f"Please try again."
            )
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages - FIXED: Routes to specialized agents + saves chat history"""
        telegram_id = update.effective_user.id
        user_message = update.message.text
        start_time = datetime.now()
        
        # Check if user is registered
        try:
            result = supabase.table('mothers').select('*').eq('telegram_chat_id', str(telegram_id)).execute()
            if not result.data:
                await update.message.reply_text("❌ Please register first using /start to ask health questions.")
                return
            
            # Get selected mother
            selected_mother_id = context.user_data.get('selected_mother_id')
            if selected_mother_id:
                mother_data = next((m for m in result.data if m['id'] == selected_mother_id), result.data[0])
            else:
                mother_data = result.data[0]
                context.user_data['selected_mother_id'] = mother_data['id']
                
        except Exception as e:
            logger.error(f"Database error: {e}")
            await update.message.reply_text("❌ Error checking registration. Please try again.")
            return
        
        # Show typing indicator (with try-except to avoid timeout)
        try:
            await asyncio.wait_for(
                update.message.chat.send_action(action="typing"),
                timeout=5.0
            )
        except:
            pass  # Continue even if typing indicator fails
        
        try:
            # Get recent reports for context
            reports_result = supabase.table('medical_reports').select('*').eq(
                'mother_id', str(mother_data['id'])
            ).order('uploaded_at', desc=True).limit(3).execute()
            
            recent_reports = reports_result.data if reports_result.data else []
            
            # ✅ Route to specialized agents via orchestrator (INCREASED TIMEOUT)
            if self.orchestrator:
                logger.info(f"📤 Routing message via orchestrator")
                response = await asyncio.wait_for(
                    self.orchestrator.route_message(
                        message=user_message,
                        mother_context=mother_data,
                        reports_context=recent_reports
                    ),
                    timeout=60.0  # 60 seconds timeout (increased from 30)
                )
                agent_type = "orchestrator"
            else:
                # Fallback if orchestrator not available
                logger.warning("⚠️ Orchestrator not available, using fallback")
                response = await asyncio.wait_for(
                    self._fallback_gemini_response(user_message, mother_data, recent_reports),
                    timeout=60.0
                )
                agent_type = "fallback"
            
            # Calculate response time
            response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Clean response (remove markdown special chars)
            response = response.replace('*', '').replace('_', '').replace('`', '')
            
            # ✅ SAVE CHAT HISTORY TO DATABASE
            try:
                from services.database_service import DatabaseService
                await DatabaseService.save_chat_history(
                    mother_id=str(mother_data['id']),
                    telegram_chat_id=str(telegram_id),
                    user_message=user_message,
                    agent_response=response,
                    agent_type=agent_type,
                    response_time_ms=response_time_ms
                )
            except Exception as save_error:
                logger.error(f"Failed to save chat history: {save_error}")
            
            # Send response
            response_message = (
                f"🤖 MatruRaksha AI Assistant\n\n"
                f"{response}\n\n"
                f"Note: This is AI-generated advice. For medical concerns, consult your healthcare provider."
            )
            
            await update.message.reply_text(response_message)
            
        except asyncio.TimeoutError:
            await update.message.reply_text("⏱️ Response took too long. Please try asking again.")
        except Exception as e:
            logger.error(f"Error handling query: {e}")
            await update.message.reply_text("❌ Sorry, I couldn't process your question. Please try again.")
    
    async def _fallback_gemini_response(self, message: str, mother_data: Dict, reports: List):
        """Fallback response if orchestrator not available"""
        try:
            import google.generativeai as genai
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            context_info = f"""
Mother Profile:
- Name: {mother_data.get('name')}
- Age: {mother_data.get('age')}
- Gravida: {mother_data.get('gravida')}
- Parity: {mother_data.get('parity')}
- BMI: {mother_data.get('bmi')}

Recent Reports: {len(reports)}
"""
            
            prompt = f"""
You are a maternal health assistant for {mother_data.get('name')}.

{context_info}

User Question: {message}

Provide a helpful, empathetic response in 2-3 paragraphs.
If urgent, advise consulting healthcare provider immediately.

Response:
"""
            
            response = model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Fallback error: {e}")
            return "I apologize, but I'm having difficulty processing your request. Please try again."
    
    async def send_health_summary(self, message, telegram_id, context: ContextTypes.DEFAULT_TYPE):
        """Send health summary for selected mother"""
        try:
            result = supabase.table('mothers').select('*').eq('telegram_chat_id', str(telegram_id)).execute()
            if not result.data:
                await message.reply_text("❌ No registration found.")
                return
            
            # Get selected mother
            selected_mother_id = context.user_data.get('selected_mother_id')
            if selected_mother_id:
                mother = next((m for m in result.data if m['id'] == selected_mother_id), result.data[0])
            else:
                mother = result.data[0]
            
            # Get reports for this mother
            reports_result = supabase.table('medical_reports').select('*').eq(
                'mother_id', str(mother['id'])
            ).order('uploaded_at', desc=True).limit(5).execute()
            reports = reports_result.data if reports_result.data else []
            
            # ✅ FIX: Build summary without markdown
            summary_text = f"📊 Health Summary for {mother['name']}\n\n"
            summary_text += f"👤 Age: {mother['age']} years\n"
            summary_text += f"🤰 Gravida: {mother['gravida']} | Parity: {mother['parity']}\n"
            summary_text += f"⚖️ BMI: {mother['bmi']}\n"
            summary_text += f"📍 Location: {mother['location']}\n\n"
            
            if reports:
                summary_text += f"📄 Recent Reports: {len(reports)}\n"
                for i, report in enumerate(reports[:3], 1):
                    uploaded_date = report['uploaded_at'][:10]
                    summary_text += f"{i}. {report['file_name']} ({uploaded_date})\n"
            else:
                summary_text += "📄 No reports uploaded yet.\n"
            
            summary_text += "\n💡 Upload medical reports to get personalized insights!"
            
            await message.reply_text(summary_text)
            
        except Exception as e:
            logger.error(f"Summary error: {e}")
            await message.reply_text("❌ Failed to fetch summary. Please try again.")


def main():
    """Main function to run the bot"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN not set in environment!")
        return
    
    bot = MatruRakshaBot()
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Registration conversation handler
    registration_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(bot.button_callback, pattern="^(register|register_new)$")
        ],
        states={
            AWAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_name)],
            AWAITING_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_age)],
            AWAITING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_phone)],
            AWAITING_DUE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_due_date)],
            AWAITING_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_location)],
            AWAITING_GRAVIDA: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_gravida)],
            AWAITING_PARITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_parity)],
            AWAITING_BMI: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_bmi)],
            AWAITING_LANGUAGE: [CallbackQueryHandler(bot.receive_language, pattern="^lang_")],
            CONFIRM_REGISTRATION: [CallbackQueryHandler(bot.confirm_registration, pattern="^confirm_")]
        },
        fallbacks=[CommandHandler('cancel', bot.cancel_registration)],
        name="registration",
        persistent=False
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(registration_handler)
    application.add_handler(CallbackQueryHandler(bot.button_callback))
    application.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, bot.handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_text_message))
    
    logger.info("✅ MatruRaksha AI Telegram Bot Started!")
    logger.info("🚀 All fixes applied:")
    logger.info("   ✅ Agent routing via orchestrator")
    logger.info("   ✅ File storage using Telegram URLs")
    logger.info("   ✅ Markdown parsing fixed")
    logger.info("   ✅ Mother switching enabled")
    logger.info("🤖 Bot is running... Press Ctrl+C to stop")
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()