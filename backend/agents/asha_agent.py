"""
ASHA Agent - ASHA Worker Coordination
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta


class AshaAgent:
    """
    Coordinates with ASHA workers for follow-ups and community care
    """
    
    def __init__(self):
        self.requests_processed = 0
        self.asha_workers = {}  # Would be loaded from database
    
    async def send_emergency_alert(self, mother_data: Dict, emergency_result: Dict) -> Dict[str, Any]:
        """Send emergency alert to ASHA worker"""
        self.requests_processed += 1
        
        print(f"[ASHA AGENT] 🚨 Sending emergency alert to ASHA worker...")
        
        alert = {
            "alert_type": "emergency",
            "mother_id": mother_data.get("id"),
            "mother_name": mother_data.get("name"),
            "emergency_type": emergency_result.get("emergency_type"),
            "severity": emergency_result.get("severity"),
            "location": mother_data.get("address") or mother_data.get("location"),
            "phone": mother_data.get("phone"),
            "sent_at": datetime.now().isoformat(),
            "asha_worker": self._get_assigned_asha(mother_data.get("location")),
            "status": "sent"
        }
        
        print(f"[ASHA AGENT] Emergency alert sent successfully")
        
        return alert
    
    async def schedule_follow_up(self, mother_data: Dict, risk_result: Dict, care_result: Dict) -> Dict[str, Any]:
        """Schedule follow-up visit with ASHA worker"""
        self.requests_processed += 1
        
        print(f"[ASHA AGENT] Scheduling follow-up visit...")
        
        risk_level = risk_result.get("risk_level", "low")
        
        # Determine follow-up frequency based on risk
        if risk_level == "critical":
            days_until_visit = 1
            visit_type = "Emergency home visit"
        elif risk_level == "high":
            days_until_visit = 3
            visit_type = "Urgent home visit"
        elif risk_level == "medium":
            days_until_visit = 7
            visit_type = "Regular checkup"
        else:
            days_until_visit = 14
            visit_type = "Routine visit"
        
        visit_date = datetime.now() + timedelta(days=days_until_visit)
        
        schedule = {
            "mother_id": mother_data.get("id"),
            "mother_name": mother_data.get("name"),
            "visit_type": visit_type,
            "scheduled_date": visit_date.strftime("%Y-%m-%d"),
            "scheduled_time": "10:00 AM",
            "asha_worker": self._get_assigned_asha(mother_data.get("location")),
            "visit_purpose": self._generate_visit_purpose(risk_result, care_result),
            "location": mother_data.get("location"),
            "status": "scheduled",
            "reminders": {
                "mother": f"ASHA visit scheduled for {visit_date.strftime('%B %d, %Y')}",
                "asha": f"Home visit for {mother_data.get('name')} on {visit_date.strftime('%B %d, %Y')}"
            }
        }
        
        print(f"[ASHA AGENT] Follow-up scheduled for {visit_date.strftime('%Y-%m-%d')}")
        
        return schedule
    
    def _get_assigned_asha(self, location: str) -> Dict:
        """Get ASHA worker assigned to area"""
        # This would query database in real implementation
        return {
            "name": "Asha Devi",
            "phone": "+91-9876543210",
            "area": "Sector 5",
            "experience": "8 years"
        }
    
    def _generate_visit_purpose(self, risk_result: Dict, care_result: Dict) -> List[str]:
        """Generate checklist for ASHA visit"""
        purposes = [
            "Check vital signs (BP, weight)",
            "Review medication compliance",
            "Assess nutrition status"
        ]
        
        risk_factors = risk_result.get("risk_factors", [])
        for factor in risk_factors:
            if factor.get("factor") == "blood_pressure":
                purposes.append("Monitor blood pressure closely")
            elif factor.get("factor") == "hemoglobin":
                purposes.append("Check for anemia symptoms")
            elif factor.get("factor") == "bmi":
                purposes.append("Nutritional counseling")
        
        purposes.append("Answer any questions or concerns")
        
        return purposes
    
    async def report_visit(self, visit_data: Dict) -> Dict[str, Any]:
        """Report completed ASHA visit"""
        print(f"[ASHA AGENT] Recording ASHA visit report...")
        
        return {
            "visit_id": f"V{int(datetime.now().timestamp())}",
            "recorded_at": datetime.now().isoformat(),
            "status": "completed",
            "report": visit_data
        }
    
    async def get_asha_dashboard(self, asha_id: str) -> Dict[str, Any]:
        """Get dashboard for ASHA worker"""
        return {
            "asha_id": asha_id,
            "today_visits": 3,
            "pending_visits": 5,
            "high_risk_mothers": 2,
            "upcoming_deliveries": 4,
            "emergency_alerts": 0
        }
    
    def get_status(self) -> Dict:
        return {
            "status": "active",
            "requests_processed": str(self.requests_processed)
        }