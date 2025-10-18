"""
Nutrition Agent - Personalized Nutrition Planning
"""

from typing import Dict, Any, List
from datetime import datetime


class NutritionAgent:
    """
    Provides nutrition guidance and meal planning
    """
    
    def __init__(self):
        self.requests_processed = 0
    
    async def assess_nutrition(self, mother_data: Dict, risk_result: Dict) -> Dict[str, Any]:
        """Generate nutrition assessment and meal plan"""
        self.requests_processed += 1
        
        print(f"[NUTRITION AGENT] Creating nutrition plan...")
        
        pregnancy_week = mother_data.get("pregnancy_week", 20)
        hemoglobin = mother_data.get("hemoglobin", 12)
        bmi = mother_data.get("bmi", mother_data.get("weight", 60) / ((mother_data.get("height", 160) / 100) ** 2))
        
        nutrition_plan = {
            "daily_requirements": self._calculate_requirements(pregnancy_week, bmi),
            "meal_plan": self._generate_meal_plan(hemoglobin, bmi),
            "supplements": self._recommend_supplements(hemoglobin, risk_result),
            "foods_to_avoid": self._get_foods_to_avoid(),
            "hydration": {"water": "3-4 liters daily", "other": "Coconut water, fresh juice"}
        }
        
        print(f"[NUTRITION AGENT] Nutrition plan created")
        
        return nutrition_plan
    
    def _calculate_requirements(self, week: int, bmi: float) -> Dict:
        base_calories = 2000
        if week > 13:
            base_calories += 300  # Second trimester
        if week > 26:
            base_calories += 500  # Third trimester
        
        return {
            "calories": f"{base_calories} kcal/day",
            "protein": "75-100g/day",
            "iron": "27mg/day",
            "calcium": "1000mg/day",
            "folic_acid": "600mcg/day"
        }
    
    def _generate_meal_plan(self, hemoglobin: float, bmi: float) -> Dict:
        meal_plan = {
            "breakfast": [
                "Oats porridge with nuts",
                "Whole wheat paratha with vegetables",
                "Idli/Dosa with sambar"
            ],
            "mid_morning": ["Fresh fruit", "Nuts (almonds, walnuts)"],
            "lunch": [
                "Rice/Roti with dal",
                "Green leafy vegetables",
                "Salad",
                "Curd/Buttermilk"
            ],
            "evening_snack": ["Sprouted legumes", "Fruit smoothie"],
            "dinner": [
                "Light roti with vegetable curry",
                "Soup",
                "Milk"
            ]
        }
        
        if hemoglobin < 11:
            meal_plan["iron_rich_additions"] = [
                "Spinach", "Beetroot", "Pomegranate",
                "Dates", "Jaggery"
            ]
        
        return meal_plan
    
    def _recommend_supplements(self, hemoglobin: float, risk_result: Dict) -> List[Dict]:
        supplements = [
            {"name": "Folic Acid", "dosage": "400-800 mcg daily", "required": True},
            {"name": "Calcium", "dosage": "1000 mg daily", "required": True}
        ]
        
        if hemoglobin < 11:
            supplements.append({
                "name": "Iron", 
                "dosage": "100 mg daily",
                "required": True,
                "note": "Take with vitamin C for better absorption"
            })
        
        return supplements
    
    def _get_foods_to_avoid(self) -> List[str]:
        return [
            "Raw/undercooked meat",
            "Unpasteurized dairy",
            "Raw eggs",
            "High-mercury fish",
            "Excessive caffeine",
            "Alcohol",
            "Papaya (unripe)",
            "Pineapple (excessive)"
        ]
    
    async def handle_query(self, mother_id: str, query: str, context: Dict) -> Dict:
        return {
            "agent": "nutrition_agent",
            "response": "Focus on iron-rich foods, green leafy vegetables, and adequate protein. "
                       "Make sure to take your supplements daily."
        }
    
    async def get_today_meals(self, mother_id: str) -> Dict:
        return {"meals_logged": 2, "target": 5, "calories": 1200}
    
    def get_status(self) -> Dict:
        return {"status": "active", "requests_processed": str(self.requests_processed)}