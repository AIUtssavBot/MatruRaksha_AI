"""
Care Agent - Personalized Care Planning
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta


class CareAgent:
    """
    Generates personalized care plans based on risk assessment
    """
    
    def __init__(self):
        self.requests_processed = 0
    
    async def generate_care_plan(self, mother_data: Dict, risk_result: Dict) -> Dict[str, Any]:
        """Generate comprehensive care plan"""
        self.requests_processed += 1
        
        print(f"[CARE AGENT] Generating care plan...")
        
        pregnancy_week = mother_data.get("pregnancy_week", 20)
        risk_level = risk_result.get("risk_level", "low")
        
        care_plan = {
            "daily_tasks": self._generate_daily_tasks(pregnancy_week, risk_level),
            "weekly_checkups": self._generate_checkup_schedule(risk_level),
            "exercise_plan": self._generate_exercise_plan(pregnancy_week, risk_level),
            "rest_guidelines": self._generate_rest_guidelines(pregnancy_week),
            "warning_signs": self._get_warning_signs(pregnancy_week),
            "emergency_contacts": self._get_emergency_contacts()
        }
        
        print(f"[CARE AGENT] Care plan generated with {len(care_plan['daily_tasks'])} daily tasks")
        
        return care_plan
    
    def _generate_daily_tasks(self, week: int, risk_level: str) -> List[Dict]:
        tasks = [
            {"task": "Take prenatal vitamins", "time": "09:00 AM", "priority": "high"},
            {"task": "Drink 8 glasses of water", "time": "Throughout day", "priority": "high"},
            {"task": "Monitor baby movements", "time": "Multiple times", "priority": "medium"}
        ]
        
        if risk_level in ["high", "critical"]:
            tasks.extend([
                {"task": "Check blood pressure", "time": "Morning & Evening", "priority": "high"},
                {"task": "Rest for 2 hours", "time": "Afternoon", "priority": "high"}
            ])
        
        return tasks
    
    def _generate_checkup_schedule(self, risk_level: str) -> Dict:
        if risk_level == "critical":
            return {"frequency": "Every 2-3 days", "type": "Doctor visit"}
        elif risk_level == "high":
            return {"frequency": "Weekly", "type": "Doctor visit"}
        elif risk_level == "medium":
            return {"frequency": "Bi-weekly", "type": "ASHA checkup"}
        else:
            return {"frequency": "Monthly", "type": "ASHA checkup"}
    
    def _generate_exercise_plan(self, week: int, risk_level: str) -> Dict:
        if risk_level in ["high", "critical"]:
            return {
                "type": "Light activities only",
                "duration": "10-15 minutes",
                "activities": ["Gentle walking", "Breathing exercises"]
            }
        else:
            return {
                "type": "Moderate exercise",
                "duration": "30 minutes daily",
                "activities": ["Walking", "Prenatal yoga", "Swimming"]
            }
    
    def _generate_rest_guidelines(self, week: int) -> Dict:
        return {
            "sleep": "8-9 hours at night",
            "naps": "1-2 hours during day",
            "position": "Left side sleeping recommended",
            "breaks": "Take breaks every 2 hours"
        }
    
    def _get_warning_signs(self, week: int) -> List[str]:
        return [
            "Severe headache or vision changes",
            "Severe abdominal pain",
            "Vaginal bleeding",
            "Decreased baby movements",
            "Severe swelling in face or hands",
            "Fever above 100.4°F"
        ]
    
    def _get_emergency_contacts(self) -> Dict:
        return {
            "ambulance": "108",
            "doctor": "Contact your OB/GYN",
            "asha_worker": "Contact local ASHA",
            "hospital": "Nearest maternity hospital"
        }
    
    async def handle_query(self, mother_id: str, query: str, context: Dict) -> Dict[str, Any]:
        return {
            "agent": "care_agent",
            "response": "I recommend following your personalized care plan. "
                       "Make sure to attend all scheduled checkups and take your vitamins daily."
        }
    
    async def get_today_tasks(self, mother_id: str) -> List[Dict]:
        return [
            {"task": "Morning vitamins", "completed": False},
            {"task": "Check blood pressure", "completed": False}
        ]
    
    def get_status(self) -> Dict:
        return {"status": "active", "requests_processed": str(self.requests_processed)}