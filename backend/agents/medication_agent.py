"""
Medication Agent - Medication Management
"""

from typing import Dict, Any, List
from datetime import datetime


class MedicationAgent:
    """
    Manages medication schedules and reminders
    """
    
    def __init__(self):
        self.requests_processed = 0
    
    async def review_medications(self, mother_data: Dict, risk_result: Dict) -> Dict[str, Any]:
        """Review and recommend medications"""
        self.requests_processed += 1
        
        print(f"[MEDICATION AGENT] Reviewing medications...")
        
        hemoglobin = mother_data.get("hemoglobin", 12)
        risk_factors = risk_result.get("risk_factors", [])
        
        medications = {
            "regular_medications": self._get_regular_medications(),
            "conditional_medications": self._get_conditional_medications(hemoglobin, risk_factors),
            "schedule": self._create_medication_schedule(),
            "important_notes": self._get_medication_notes()
        }
        
        print(f"[MEDICATION AGENT] Medication review complete")
        
        return medications
    
    def _get_regular_medications(self) -> List[Dict]:
        return [
            {
                "name": "Folic Acid",
                "dosage": "5 mg",
                "frequency": "Once daily",
                "time": "Morning after breakfast",
                "duration": "Throughout pregnancy"
            },
            {
                "name": "Calcium",
                "dosage": "500 mg",
                "frequency": "Twice daily",
                "time": "After meals",
                "duration": "Throughout pregnancy"
            }
        ]
    
    def _get_conditional_medications(self, hemoglobin: float, risk_factors: List) -> List[Dict]:
        conditional = []
        
        if hemoglobin < 11:
            conditional.append({
                "name": "Iron (Ferrous Sulfate)",
                "dosage": "100-200 mg",
                "frequency": "Once daily",
                "time": "Morning with orange juice",
                "note": "May cause constipation - increase fiber intake"
            })
        
        for factor in risk_factors:
            if factor.get("factor") == "blood_pressure" and factor.get("risk") != "low":
                conditional.append({
                    "name": "Consult doctor for BP medication",
                    "note": "Do not self-medicate for blood pressure"
                })
        
        return conditional
    
    def _create_medication_schedule(self) -> Dict:
        return {
            "morning": ["Folic Acid", "Iron (if prescribed)"],
            "afternoon": ["Calcium"],
            "evening": ["Calcium"]
        }
    
    def _get_medication_notes(self) -> List[str]:
        return [
            "Take medications at the same time daily",
            "Do not skip doses",
            "Take iron separately from calcium (2 hours apart)",
            "Report any side effects to doctor",
            "Keep all medications out of reach of children"
        ]
    
    async def handle_query(self, mother_id: str, query: str, context: Dict) -> Dict:
        return {
            "agent": "medication_agent",
            "response": "Remember to take your medications as prescribed. "
                       "Iron should be taken with vitamin C for better absorption."
        }
    
    async def get_today_medications(self, mother_id: str) -> Dict:
        return {"taken": 2, "total": 3, "next_dose": "Calcium at 6:00 PM"}
    
    def get_status(self) -> Dict:
        return {"status": "active", "requests_processed": str(self.requests_processed)}