"""
Agent Orchestrator for MatruRakshaAI
Coordinates all AI agents and manages their interactions
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
from enum import Enum

from .risk_agent import RiskAgent
from .care_agent import CareAgent
from .nutrition_agent import NutritionAgent
from .medication_agent import MedicationAgent
from .emergency_agent import EmergencyAgent
from .asha_agent import AshaAgent


class AgentPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AgentOrchestrator:
    """
    Main orchestrator that coordinates all specialized agents
    """
    
    def __init__(self):
        self.risk_agent = RiskAgent()
        self.care_agent = CareAgent()
        self.nutrition_agent = NutritionAgent()
        self.medication_agent = MedicationAgent()
        self.emergency_agent = EmergencyAgent()
        self.asha_agent = AshaAgent()
        
        self.agent_history = []
        
    async def process_mother_data(self, mother_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point: Process complete mother data through all agents
        """
        print(f"[ORCHESTRATOR] Starting agent processing for mother: {mother_data.get('name', 'Unknown')}")
        
        results = {
            "mother_id": mother_data.get("id"),
            "timestamp": datetime.now().isoformat(),
            "agents_executed": [],
            "overall_status": "processing"
        }
        
        try:
            # Step 1: Risk Assessment (CRITICAL - Always first)
            print("[ORCHESTRATOR] Step 1: Risk Assessment")
            risk_result = await self.risk_agent.assess_risk(mother_data)
            results["risk_assessment"] = risk_result
            results["agents_executed"].append("risk_agent")
            
            # Step 2: Check for Emergency (if high risk)
            if risk_result["risk_level"] in ["high", "critical"]:
                print("[ORCHESTRATOR] Step 2: Emergency Check (High Risk Detected)")
                emergency_result = await self.emergency_agent.evaluate_emergency(
                    mother_data, risk_result
                )
                results["emergency_assessment"] = emergency_result
                results["agents_executed"].append("emergency_agent")
                
                # If emergency, notify ASHA immediately
                if emergency_result.get("is_emergency"):
                    print("[ORCHESTRATOR] EMERGENCY DETECTED - Notifying ASHA")
                    asha_notification = await self.asha_agent.send_emergency_alert(
                        mother_data, emergency_result
                    )
                    results["asha_alert"] = asha_notification
                    results["agents_executed"].append("asha_agent")
            
            # Step 3: Care Recommendations
            print("[ORCHESTRATOR] Step 3: Generating Care Plan")
            care_result = await self.care_agent.generate_care_plan(
                mother_data, risk_result
            )
            results["care_plan"] = care_result
            results["agents_executed"].append("care_agent")
            
            # Step 4: Nutrition Assessment
            print("[ORCHESTRATOR] Step 4: Nutrition Analysis")
            nutrition_result = await self.nutrition_agent.assess_nutrition(
                mother_data, risk_result
            )
            results["nutrition_plan"] = nutrition_result
            results["agents_executed"].append("nutrition_agent")
            
            # Step 5: Medication Management
            print("[ORCHESTRATOR] Step 5: Medication Review")
            medication_result = await self.medication_agent.review_medications(
                mother_data, risk_result
            )
            results["medication_plan"] = medication_result
            results["agents_executed"].append("medication_agent")
            
            # Step 6: ASHA Follow-up Scheduling (for non-emergency cases)
            if not results.get("emergency_assessment", {}).get("is_emergency"):
                print("[ORCHESTRATOR] Step 6: Scheduling ASHA Follow-up")
                asha_schedule = await self.asha_agent.schedule_follow_up(
                    mother_data, risk_result, care_result
                )
                results["asha_schedule"] = asha_schedule
                if "asha_agent" not in results["agents_executed"]:
                    results["agents_executed"].append("asha_agent")
            
            results["overall_status"] = "completed"
            print(f"[ORCHESTRATOR] Processing complete. Agents used: {results['agents_executed']}")
            
        except Exception as e:
            print(f"[ORCHESTRATOR] Error during processing: {str(e)}")
            results["overall_status"] = "error"
            results["error"] = str(e)
        
        # Store in history
        self.agent_history.append(results)
        
        return results
    
    async def process_query(self, mother_id: str, query: str, context: Dict = None) -> Dict[str, Any]:
        """
        Process natural language queries from mothers/ASHA workers
        Routes to appropriate agent based on query intent
        """
        print(f"[ORCHESTRATOR] Processing query: {query}")
        
        # Simple intent detection (can be enhanced with NLP)
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["emergency", "urgent", "pain", "bleeding", "danger"]):
            print("[ORCHESTRATOR] Routing to Emergency Agent")
            return await self.emergency_agent.handle_query(mother_id, query, context)
        
        elif any(word in query_lower for word in ["food", "nutrition", "diet", "eat", "meal"]):
            print("[ORCHESTRATOR] Routing to Nutrition Agent")
            return await self.nutrition_agent.handle_query(mother_id, query, context)
        
        elif any(word in query_lower for word in ["medicine", "medication", "tablet", "dose"]):
            print("[ORCHESTRATOR] Routing to Medication Agent")
            return await self.medication_agent.handle_query(mother_id, query, context)
        
        elif any(word in query_lower for word in ["risk", "assess", "check"]):
            print("[ORCHESTRATOR] Routing to Risk Agent")
            return await self.risk_agent.handle_query(mother_id, query, context)
        
        else:
            print("[ORCHESTRATOR] Routing to Care Agent (General)")
            return await self.care_agent.handle_query(mother_id, query, context)
    
    async def get_daily_summary(self, mother_id: str) -> Dict[str, Any]:
        """
        Generate daily health summary for a mother
        """
        print(f"[ORCHESTRATOR] Generating daily summary for mother: {mother_id}")
        
        # Gather data from all agents
        tasks = [
            self.risk_agent.get_current_status(mother_id),
            self.care_agent.get_today_tasks(mother_id),
            self.nutrition_agent.get_today_meals(mother_id),
            self.medication_agent.get_today_medications(mother_id)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "mother_id": mother_id,
            "date": datetime.now().date().isoformat(),
            "risk_status": results[0] if not isinstance(results[0], Exception) else None,
            "care_tasks": results[1] if not isinstance(results[1], Exception) else None,
            "nutrition": results[2] if not isinstance(results[2], Exception) else None,
            "medications": results[3] if not isinstance(results[3], Exception) else None
        }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get status of all agents
        """
        return {
            "orchestrator_status": "active",
            "total_requests_processed": len(self.agent_history),
            "agents": {
                "risk_agent": self.risk_agent.get_status(),
                "care_agent": self.care_agent.get_status(),
                "nutrition_agent": self.nutrition_agent.get_status(),
                "medication_agent": self.medication_agent.get_status(),
                "emergency_agent": self.emergency_agent.get_status(),
                "asha_agent": self.asha_agent.get_status()
            }
        }


# Global instance
orchestrator = AgentOrchestrator()