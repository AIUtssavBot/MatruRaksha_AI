"""
Risk Assessment Agent - Enhanced with ML and Rule-based Logic
"""

from typing import Dict, Any, List
from datetime import datetime
import numpy as np


class RiskAgent:
    """
    Specialized agent for maternal risk assessment
    """
    
    def __init__(self):
        self.risk_factors = {
            "age": {"low": (20, 35), "medium": (18, 40), "high": (0, 18, 40, 100)},
            "bmi": {"low": (18.5, 25), "medium": (16, 30), "high": (0, 16, 30, 100)},
            "blood_pressure_systolic": {"low": (90, 140), "medium": (140, 160), "high": (160, 300)},
            "hemoglobin": {"low": (11, 100), "medium": (9, 11), "high": (0, 9)},
        }
        self.requests_processed = 0
    
    async def assess_risk(self, mother_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive risk assessment using multiple factors
        """
        self.requests_processed += 1
        
        print(f"[RISK AGENT] Assessing risk for mother: {mother_data.get('name', 'Unknown')}")
        
        risk_scores = []
        risk_factors_identified = []
        
        # 1. Age Risk
        age = mother_data.get("age", 25)
        age_risk = self._assess_age_risk(age)
        risk_scores.append(age_risk["score"])
        if age_risk["risk"] != "low":
            risk_factors_identified.append(age_risk)
        
        # 2. BMI Risk
        height = mother_data.get("height", 160)
        weight = mother_data.get("weight", 60)
        bmi = weight / ((height / 100) ** 2)
        bmi_risk = self._assess_bmi_risk(bmi)
        risk_scores.append(bmi_risk["score"])
        if bmi_risk["risk"] != "low":
            risk_factors_identified.append(bmi_risk)
        
        # 3. Blood Pressure Risk
        bp_systolic = mother_data.get("bp_systolic", 120)
        bp_diastolic = mother_data.get("bp_diastolic", 80)
        bp_risk = self._assess_bp_risk(bp_systolic, bp_diastolic)
        risk_scores.append(bp_risk["score"])
        if bp_risk["risk"] != "low":
            risk_factors_identified.append(bp_risk)
        
        # 4. Hemoglobin Risk
        hemoglobin = mother_data.get("hemoglobin", 12)
        hb_risk = self._assess_hemoglobin_risk(hemoglobin)
        risk_scores.append(hb_risk["score"])
        if hb_risk["risk"] != "low":
            risk_factors_identified.append(hb_risk)
        
        # 5. Medical History Risk
        history_risk = self._assess_medical_history(mother_data.get("medical_history", {}))
        risk_scores.append(history_risk["score"])
        if history_risk["risk"] != "low":
            risk_factors_identified.append(history_risk)
        
        # 6. Pregnancy-specific Risk
        pregnancy_week = mother_data.get("pregnancy_week", 20)
        pregnancy_risk = self._assess_pregnancy_risk(pregnancy_week, mother_data)
        risk_scores.append(pregnancy_risk["score"])
        if pregnancy_risk["risk"] != "low":
            risk_factors_identified.append(pregnancy_risk)
        
        # Calculate overall risk
        avg_score = np.mean(risk_scores)
        max_score = max(risk_scores)
        
        # Determine risk level
        if max_score >= 0.8 or avg_score >= 0.7:
            risk_level = "critical"
        elif max_score >= 0.6 or avg_score >= 0.5:
            risk_level = "high"
        elif max_score >= 0.4 or avg_score >= 0.3:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        result = {
            "mother_id": mother_data.get("id"),
            "risk_level": risk_level,
            "risk_score": round(avg_score, 2),
            "max_risk_score": round(max_score, 2),
            "risk_factors": risk_factors_identified,
            "recommendations": self._generate_recommendations(risk_level, risk_factors_identified),
            "next_checkup": self._calculate_next_checkup(risk_level),
            "assessed_at": datetime.now().isoformat(),
            "details": {
                "age_risk": age_risk,
                "bmi_risk": bmi_risk,
                "bp_risk": bp_risk,
                "hemoglobin_risk": hb_risk,
                "history_risk": history_risk,
                "pregnancy_risk": pregnancy_risk
            }
        }
        
        print(f"[RISK AGENT] Assessment complete. Risk Level: {risk_level}")
        return result
    
    def _assess_age_risk(self, age: int) -> Dict[str, Any]:
        if 20 <= age <= 35:
            return {"factor": "age", "value": age, "risk": "low", "score": 0.1}
        elif (18 <= age < 20) or (35 < age <= 40):
            return {"factor": "age", "value": age, "risk": "medium", "score": 0.4, 
                    "message": "Age slightly outside optimal range"}
        else:
            return {"factor": "age", "value": age, "risk": "high", "score": 0.8,
                    "message": "Age significantly increases pregnancy risks"}
    
    def _assess_bmi_risk(self, bmi: float) -> Dict[str, Any]:
        if 18.5 <= bmi <= 25:
            return {"factor": "bmi", "value": round(bmi, 1), "risk": "low", "score": 0.1}
        elif (16 <= bmi < 18.5) or (25 < bmi <= 30):
            return {"factor": "bmi", "value": round(bmi, 1), "risk": "medium", "score": 0.5,
                    "message": "BMI outside healthy range"}
        else:
            return {"factor": "bmi", "value": round(bmi, 1), "risk": "high", "score": 0.8,
                    "message": "BMI significantly outside healthy range"}
    
    def _assess_bp_risk(self, systolic: int, diastolic: int) -> Dict[str, Any]:
        if systolic < 140 and diastolic < 90:
            return {"factor": "blood_pressure", "value": f"{systolic}/{diastolic}", 
                    "risk": "low", "score": 0.1}
        elif 140 <= systolic < 160 or 90 <= diastolic < 100:
            return {"factor": "blood_pressure", "value": f"{systolic}/{diastolic}",
                    "risk": "high", "score": 0.7,
                    "message": "Elevated blood pressure - possible pre-eclampsia"}
        else:
            return {"factor": "blood_pressure", "value": f"{systolic}/{diastolic}",
                    "risk": "critical", "score": 0.9,
                    "message": "Severe hypertension - immediate medical attention needed"}
    
    def _assess_hemoglobin_risk(self, hemoglobin: float) -> Dict[str, Any]:
        if hemoglobin >= 11:
            return {"factor": "hemoglobin", "value": hemoglobin, "risk": "low", "score": 0.1}
        elif 9 <= hemoglobin < 11:
            return {"factor": "hemoglobin", "value": hemoglobin, "risk": "medium", "score": 0.5,
                    "message": "Mild anemia detected"}
        else:
            return {"factor": "hemoglobin", "value": hemoglobin, "risk": "high", "score": 0.8,
                    "message": "Severe anemia - iron supplementation required"}
    
    def _assess_medical_history(self, history: Dict) -> Dict[str, Any]:
        risk_conditions = [
            "diabetes", "hypertension", "heart_disease", "previous_complications",
            "gestational_diabetes", "preeclampsia_history"
        ]
        
        found_conditions = [cond for cond in risk_conditions if history.get(cond, False)]
        
        if not found_conditions:
            return {"factor": "medical_history", "risk": "low", "score": 0.1}
        elif len(found_conditions) == 1:
            return {"factor": "medical_history", "risk": "medium", "score": 0.5,
                    "conditions": found_conditions,
                    "message": f"Pre-existing condition: {found_conditions[0]}"}
        else:
            return {"factor": "medical_history", "risk": "high", "score": 0.8,
                    "conditions": found_conditions,
                    "message": f"Multiple risk conditions: {', '.join(found_conditions)}"}
    
    def _assess_pregnancy_risk(self, week: int, mother_data: Dict) -> Dict[str, Any]:
        issues = []
        score = 0.1
        
        if week < 12 and mother_data.get("first_trimester_complications"):
            issues.append("First trimester complications")
            score = 0.6
        elif week > 37 and not mother_data.get("hospital_plan"):
            issues.append("Near delivery without hospital plan")
            score = 0.4
        
        if mother_data.get("multiple_pregnancy"):
            issues.append("Multiple pregnancy (twins/triplets)")
            score = max(score, 0.6)
        
        if issues:
            return {"factor": "pregnancy_status", "week": week, "risk": "medium" if score < 0.7 else "high",
                    "score": score, "issues": issues}
        else:
            return {"factor": "pregnancy_status", "week": week, "risk": "low", "score": 0.1}
    
    def _generate_recommendations(self, risk_level: str, factors: List[Dict]) -> List[str]:
        recommendations = []
        
        if risk_level == "critical":
            recommendations.append("⚠️ URGENT: Schedule immediate medical consultation")
            recommendations.append("Consider hospitalization or close monitoring")
        elif risk_level == "high":
            recommendations.append("Schedule medical checkup within 24-48 hours")
            recommendations.append("Increase monitoring frequency")
        
        for factor in factors:
            if factor["factor"] == "blood_pressure" and factor["risk"] != "low":
                recommendations.append("Monitor blood pressure daily")
                recommendations.append("Reduce salt intake immediately")
            elif factor["factor"] == "hemoglobin" and factor["risk"] != "low":
                recommendations.append("Start iron and folic acid supplementation")
                recommendations.append("Increase iron-rich foods in diet")
            elif factor["factor"] == "bmi":
                if factor["value"] < 18.5:
                    recommendations.append("Increase caloric intake - consult nutritionist")
                elif factor["value"] > 25:
                    recommendations.append("Monitor weight gain - follow healthy diet plan")
        
        return recommendations
    
    def _calculate_next_checkup(self, risk_level: str) -> str:
        if risk_level == "critical":
            return "Immediate (within 24 hours)"
        elif risk_level == "high":
            return "Within 3-5 days"
        elif risk_level == "medium":
            return "Within 1-2 weeks"
        else:
            return "Within 4 weeks"
    
    async def handle_query(self, mother_id: str, query: str, context: Dict) -> Dict[str, Any]:
        """Handle queries related to risk assessment"""
        return {
            "agent": "risk_agent",
            "mother_id": mother_id,
            "response": "Based on your current assessment, I recommend following your care plan closely. "
                       "If you notice any unusual symptoms, contact your healthcare provider immediately.",
            "handled_at": datetime.now().isoformat()
        }
    
    async def get_current_status(self, mother_id: str) -> Dict[str, Any]:
        """Get current risk status for a mother"""
        return {
            "mother_id": mother_id,
            "last_assessment": "Recent",
            "status": "Monitoring"
        }
    
    def get_status(self) -> Dict[str, str]:
        return {
            "status": "active",
            "requests_processed": str(self.requests_processed)
        }