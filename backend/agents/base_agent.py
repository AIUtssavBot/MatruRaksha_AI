"""
MatruRaksha AI - Base Agent Class
All specialized agents inherit from this base class
"""

import os
import logging
from typing import Dict, Any, List
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Import Gemini
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
    else:
        GEMINI_AVAILABLE = False
except:
    GEMINI_AVAILABLE = False


class BaseAgent(ABC):
    """Base class for all specialized agents"""
    
    def __init__(self, agent_name: str, agent_role: str):
        self.agent_name = agent_name
        self.agent_role = agent_role
        self.model = None
        
        if GEMINI_AVAILABLE:
            try:
                self.model = genai.GenerativeModel('gemini-2.5-flash')
                logger.info(f"✅ {agent_name} initialized with Gemini")
            except Exception as e:
                logger.error(f"❌ {agent_name} failed to initialize: {e}")
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent"""
        pass
    
    def build_context(
        self,
        mother_context: Dict[str, Any],
        reports_context: List[Dict[str, Any]]
    ) -> str:
        """Build context string from mother and reports data"""
        context = f"""
Mother Profile:
- Name: {mother_context.get('name')}
- Age: {mother_context.get('age')} years
- Gravida: {mother_context.get('gravida')}
- Parity: {mother_context.get('parity')}
- BMI: {mother_context.get('bmi')}
- Location: {mother_context.get('location')}
- Due Date: {mother_context.get('due_date')}
"""
        
        if reports_context:
            context += f"\nRecent Medical Reports: {len(reports_context)}\n"
            for i, report in enumerate(reports_context[:2], 1):
                analysis = report.get('analysis_result', {})
                if analysis:
                    risk = analysis.get('risk_level', 'unknown')
                    concerns = analysis.get('concerns', [])
                    context += f"\nReport {i} ({report.get('uploaded_at', '')[:10]}):\n"
                    context += f"- Risk Level: {risk}\n"
                    if concerns:
                        context += f"- Key Concerns: {', '.join(concerns[:3])}\n"
        
        return context
    
    async def process_query(
        self,
        query: str,
        mother_context: Dict[str, Any],
        reports_context: List[Dict[str, Any]]
    ) -> str:
        """Process a query and return response"""
        if not self.model:
            return (
                f"⚠️ {self.agent_name} is currently unavailable. "
                "Please try again later or contact support."
            )
        
        try:
            # Build full prompt
            system_prompt = self.get_system_prompt()
            context_info = self.build_context(mother_context, reports_context)
            
            full_prompt = f"""
{system_prompt}

{context_info}

User Question: {query}

Instructions:
- Provide a helpful, empathetic response
- Keep response concise (2-4 paragraphs)
- If urgent or concerning, strongly advise consulting healthcare provider
- Be specific and actionable
- Use simple, clear language

Response:
"""
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            
            # Clean response
            cleaned_response = response.text.strip()
            
            logger.info(f"✅ {self.agent_name} processed query successfully")
            return cleaned_response
            
        except Exception as e:
            logger.error(f"❌ {self.agent_name} error: {e}")
            return (
                f"I apologize, but I encountered an issue processing your request. "
                f"Please try rephrasing your question or contact your healthcare provider if urgent."
            )