"""
Emergency Agent - Emergency Detection and Protocol
"""

from typing import Dict, Any, List
from datetime import datetime


class EmergencyAgent:
    """
    Detects emergencies and triggers immediate response
    """
    
    def __init__(self):
        self.requests_processed = 0
        self.emergency_protocols = self._load_emergency_protocols()
    
    def _load_emergency_protocols(self) -> Dict:
        return {
            "severe_bleeding": {
                "severity": "critical",
                "action": "Call ambulance immediately (108)",
                "instructions": [
                    "Lie down with legs elevated",
                    "Do not insert anything into vagina",
                    "Keep track of blood loss",
                    "Stay calm"
                ]
            },
            "severe_headache_vision": {
                "severity": "critical",
                "action": "Emergency hospital visit",
                "condition": "Possible pre-eclampsia",
                "instructions": [
                    "Check blood pressure immediately",
                    "Go to hospital emergency",
                    "Monitor for seizures"
                ]
            },
            "decreased_fetal_movement": {
                "severity": "high",
                "action": "Contact doctor immediately",
                "instructions": [
                    "Drink cold water and lie on left side",
                    "Count movements for 2 hours",
                    "If less than 10 movements, go to hospital"
                ]
            },
            "water_breaking": {
                "severity": "high",
                "action": "Go to hospital",
                "instructions": [
                    "Note the time",
                    "Check fluid color (clear is normal)",
                    "Do not insert anything",
                    "Proceed to hospital"
                ]
            },
            "severe_abdominal_pain": {
                "severity": "critical",
                "action": "Emergency hospital visit",
                "instructions": [
                    "Lie down in comfortable position",
                    "Do not take any medication",
                    "Call ambulance if severe"
                ]
            }
        }
    
    async def evaluate_emergency(self, mother_data: Dict, risk_result: Dict) -> Dict[str, Any]:
        """Evaluate if situation is an emergency"""
        self.requests_processed += 1
        
        print(f"[EMERGENCY AGENT] Evaluating emergency status...")
        
        is_emergency = False
        emergency_type = None
        severity = "normal"
        actions = []
        
        # Check symptoms
        symptoms = mother_data.get("symptoms", [])
        for symptom in symptoms:
            symptom_lower = symptom.lower()
            for emergency_key, protocol in self.emergency_protocols.items():
                if emergency_key.replace("_", " ") in symptom_lower:
                    is_emergency = True
                    emergency_type = emergency_key
                    severity = protocol["severity"]
                    actions = protocol["instructions"]
                    break
        
        # Check vital signs
        bp_systolic = mother_data.get("bp_systolic", 120)
        if bp_systolic >= 160:
            is_emergency = True
            emergency_type = "severe_hypertension"
            severity = "critical"
            actions = [
                "Check blood pressure again in 15 minutes",
                "If still high, go to emergency immediately",
                "Lie down on left side",
                "Do not take any medication without doctor approval"
            ]
        
        hemoglobin = mother_data.get("hemoglobin", 12)
        if hemoglobin < 7:
            is_emergency = True
            emergency_type = "severe_anemia"
            severity = "critical"
            actions = [
                "Immediate medical attention required",
                "Blood transfusion may be needed",
                "Do not travel alone"
            ]
        
        # Check risk level
        risk_level = risk_result.get("risk_level", "low")
        if risk_level == "critical" and not is_emergency:
            is_emergency = True
            emergency_type = "critical_risk_factors"
            severity = "high"
            actions = [
                "Schedule immediate doctor consultation",
                "Do not delay medical care",
                "Monitor symptoms closely"
            ]
        
        result = {
            "is_emergency": is_emergency,
            "emergency_type": emergency_type,
            "severity": severity,
            "immediate_actions": actions,
            "emergency_contacts": {
                "ambulance": "108",
                "emergency_helpline": "102",
                "women_helpline": "1091"
            },
            "assessed_at": datetime.now().isoformat()
        }
        
        if is_emergency:
            print(f"[EMERGENCY AGENT] ⚠️ EMERGENCY DETECTED: {emergency_type} (Severity: {severity})")
        else:
            print(f"[EMERGENCY AGENT] No emergency detected")
        
        return result
    
    async def handle_query(self, mother_id: str, query: str, context: Dict) -> Dict[str, Any]:
        """Handle emergency-related queries"""
        
        query_lower = query.lower()
        
        # Detect emergency keywords
        for emergency_key, protocol in self.emergency_protocols.items():
            if any(word in query_lower for word in emergency_key.split("_")):
                return {
                    "agent": "emergency_agent",
                    "is_emergency": True,
                    "emergency_type": emergency_key,
                    "response": f"⚠️ EMERGENCY PROTOCOL ACTIVATED\n\n"
                               f"Action: {protocol['action']}\n\n"
                               f"Immediate Steps:\n" + 
                               "\n".join([f"• {step}" for step in protocol['instructions']]),
                    "severity": protocol["severity"]
                }
        
        return {
            "agent": "emergency_agent",
            "is_emergency": False,
            "response": "If you're experiencing an emergency, please call 108 immediately. "
                       "Otherwise, describe your symptoms in detail."
        }
    
    def get_status(self) -> Dict:
        return {
            "status": "active",
            "requests_processed": str(self.requests_processed),
            "protocols_loaded": str(len(self.emergency_protocols))
        }