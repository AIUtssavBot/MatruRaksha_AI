"""
MatruRaksha AI - Database Service
Handles all Supabase database operations
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class DatabaseService:
    """Service for database operations"""
    
    @staticmethod
    async def save_chat_history(
        mother_id: str,
        telegram_chat_id: str,
        user_message: str,
        agent_response: str,
        agent_type: str,
        response_time_ms: Optional[int] = None,
        intent_classification: Optional[str] = None,
        confidence_score: Optional[float] = None
    ) -> bool:
        """Save chat conversation to database"""
        try:
            data = {
                'mother_id': mother_id,
                'telegram_chat_id': telegram_chat_id,
                'user_message': user_message,
                'agent_response': agent_response,
                'agent_type': agent_type,
                'response_time_ms': response_time_ms,
                'intent_classification': intent_classification,
                'confidence_score': confidence_score,
                'message_timestamp': datetime.now().isoformat()
            }
            
            result = supabase.table('chat_histories').insert(data).execute()
            
            if result.data:
                logger.info(f"✅ Chat history saved for mother {mother_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Error saving chat history: {e}")
            return False
    
    @staticmethod
    def get_recent_chats(mother_id: str, limit: int = 10) -> List[Dict]:
        """Get recent chat history for a mother"""
        try:
            result = supabase.table('chat_histories').select('*').eq(
                'mother_id', mother_id
            ).order('message_timestamp', desc=True).limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"❌ Error fetching chat history: {e}")
            return []
    
    @staticmethod
    def get_upcoming_appointments(mother_id: str, days_ahead: int = 30) -> List[Dict]:
        """Get upcoming appointments for a mother"""
        try:
            future_date = (datetime.now() + timedelta(days=days_ahead)).isoformat()
            
            result = supabase.table('appointments').select('*').eq(
                'mother_id', mother_id
            ).gte('appointment_date', datetime.now().isoformat()).lte(
                'appointment_date', future_date
            ).eq('status', 'scheduled').order('appointment_date', desc=False).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"❌ Error fetching appointments: {e}")
            return []
    
    @staticmethod
    def get_next_appointment(mother_id: str) -> Optional[Dict]:
        """Get the next upcoming appointment"""
        appointments = DatabaseService.get_upcoming_appointments(mother_id, days_ahead=60)
        return appointments[0] if appointments else None
    
    @staticmethod
    def create_appointment(
        mother_id: str,
        telegram_chat_id: str,
        appointment_type: str,
        appointment_date: datetime,
        appointment_location: Optional[str] = None,
        doctor_name: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[Dict]:
        """Create a new appointment"""
        try:
            data = {
                'mother_id': mother_id,
                'telegram_chat_id': telegram_chat_id,
                'appointment_type': appointment_type,
                'appointment_date': appointment_date.isoformat(),
                'appointment_location': appointment_location,
                'doctor_name': doctor_name,
                'notes': notes,
                'status': 'scheduled'
            }
            
            result = supabase.table('appointments').insert(data).execute()
            
            if result.data:
                logger.info(f"✅ Appointment created for mother {mother_id}")
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"❌ Error creating appointment: {e}")
            return None
    
    @staticmethod
    def get_medical_reports(mother_id: str, limit: int = 5) -> List[Dict]:
        """Get recent medical reports"""
        try:
            result = supabase.table('medical_reports').select('*').eq(
                'mother_id', mother_id
            ).order('uploaded_at', desc=True).limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"❌ Error fetching medical reports: {e}")
            return []
    
    @staticmethod
    def get_mother_profile(mother_id: str) -> Optional[Dict]:
        """Get mother's complete profile"""
        try:
            result = supabase.table('mothers').select('*').eq('id', mother_id).execute()
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"❌ Error fetching mother profile: {e}")
            return None
    
    @staticmethod
    def save_health_metric(
        mother_id: str,
        weight_kg: Optional[float] = None,
        blood_pressure_systolic: Optional[int] = None,
        blood_pressure_diastolic: Optional[int] = None,
        hemoglobin: Optional[float] = None,
        blood_sugar: Optional[float] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Save health metrics"""
        try:
            data = {
                'mother_id': mother_id,
                'weight_kg': weight_kg,
                'blood_pressure_systolic': blood_pressure_systolic,
                'blood_pressure_diastolic': blood_pressure_diastolic,
                'hemoglobin': hemoglobin,
                'blood_sugar': blood_sugar,
                'measured_at': datetime.now().isoformat(),
                'notes': notes
            }
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            result = supabase.table('health_metrics').insert(data).execute()
            
            if result.data:
                logger.info(f"✅ Health metrics saved for mother {mother_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Error saving health metrics: {e}")
            return False
    
    @staticmethod
    def get_health_metrics(mother_id: str, limit: int = 10) -> List[Dict]:
        """Get recent health metrics"""
        try:
            result = supabase.table('health_metrics').select('*').eq(
                'mother_id', mother_id
            ).order('measured_at', desc=True).limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"❌ Error fetching health metrics: {e}")
            return []
    
    @staticmethod
    def calculate_pregnancy_week(due_date: str) -> Optional[int]:
        """Calculate pregnancy week from due date"""
        try:
            due_date_obj = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            conception_date = due_date_obj - timedelta(weeks=40)
            weeks_pregnant = (datetime.now() - conception_date).days // 7
            return max(0, min(weeks_pregnant, 42))  # Cap at 0-42 weeks
            
        except Exception as e:
            logger.error(f"❌ Error calculating pregnancy week: {e}")
            return None
    
    @staticmethod
    def get_anc_schedule_status(mother_id: str) -> Dict[str, Any]:
        """Check ANC schedule compliance"""
        try:
            mother = DatabaseService.get_mother_profile(mother_id)
            if not mother:
                return {}
            
            pregnancy_week = DatabaseService.calculate_pregnancy_week(mother.get('due_date', ''))
            appointments = DatabaseService.get_upcoming_appointments(mother_id, days_ahead=365)
            completed_visits = len([a for a in appointments if a['status'] == 'completed'])
            
            # Minimum 4 ANC visits recommended
            recommended_visits = 4
            if pregnancy_week:
                if pregnancy_week >= 36:
                    recommended_visits = 8  # Weekly after 36 weeks
                elif pregnancy_week >= 28:
                    recommended_visits = 6  # Bi-weekly 28-36 weeks
            
            return {
                'pregnancy_week': pregnancy_week,
                'completed_visits': completed_visits,
                'recommended_visits': recommended_visits,
                'compliance': 'good' if completed_visits >= recommended_visits else 'needs_attention',
                'next_visit_due': 'now' if completed_visits < recommended_visits else 'on_track'
            }
            
        except Exception as e:
            logger.error(f"❌ Error checking ANC schedule: {e}")
            return {}