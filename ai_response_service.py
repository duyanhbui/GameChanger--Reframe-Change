import os
import json
from datetime import datetime
from mental_models import get_mental_model_data

# Check if OpenAI is available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = bool(os.environ.get("OPENAI_API_KEY"))
    if OPENAI_AVAILABLE:
        openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
except ImportError:
    OPENAI_AVAILABLE = False
    openai_client = None


def generate_ai_response_suggestion(concern_text, stakeholder_mental_model, project_data, existing_faqs=None):
    """
    Generate AI-powered response suggestions based on:
    - Stakeholder concern
    - Their mental model (KB16 framework)
    - Project context (strategy, key messages, dates)
    - Existing FAQ content
    """
    
    if not OPENAI_AVAILABLE or not openai_client:
        return {
            "suggested_response": "",
            "tone_notes": "AI response suggestions require an OpenAI API key to be configured.",
            "key_points": [],
            "error": "OpenAI API key not configured"
        }
    
    try:
        # Get mental model details
        mental_model_data = get_mental_model_data(stakeholder_mental_model)
        
        # Build context for AI
        context = build_response_context(concern_text, mental_model_data, project_data, existing_faqs)
        
        # Generate response using OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert change management consultant. Generate personalized responses to stakeholder concerns based on their mental model, project context, and communication preferences. Respond with JSON in this format: {'suggested_response': 'response text', 'tone_notes': 'communication guidance', 'key_points': ['point1', 'point2']}"
                },
                {
                    "role": "user",
                    "content": context
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=1000
        )
        
        result = json.loads(response.choices[0].message.content)
        return {
            "suggested_response": result.get("suggested_response", ""),
            "tone_notes": result.get("tone_notes", ""),
            "key_points": result.get("key_points", []),
            "error": None
        }
        
    except Exception as e:
        return {
            "suggested_response": "",
            "tone_notes": f"Error generating AI suggestion: {str(e)}",
            "key_points": [],
            "error": str(e)
        }


def build_response_context(concern_text, mental_model_data, project_data, existing_faqs):
    """Build comprehensive context for AI response generation"""
    
    context = f"""
STAKEHOLDER CONCERN:
{concern_text}

STAKEHOLDER MENTAL MODEL: {mental_model_data['name']}
Description: {mental_model_data['description']}
Strengths: {', '.join(mental_model_data['strengths'])}
Challenges: {', '.join(mental_model_data['challenges'])}
Recommendations: {', '.join(mental_model_data['recommendations'])}

PROJECT CONTEXT:
Project Name: {project_data.get('name', 'N/A')}
Description: {project_data.get('description', 'N/A')}

CHANGE STRATEGY:
{project_data.get('change_strategy', 'No strategy document available')}

KEY MESSAGES:
{project_data.get('key_messages', 'No key messages defined')}

IMPORTANT DATES:
"""
    
    # Add project dates
    if project_data.get('project_start_date'):
        context += f"Project Start: {project_data['project_start_date'].strftime('%B %d, %Y')}\n"
    if project_data.get('communication_start_date'):
        context += f"Communication Start: {project_data['communication_start_date'].strftime('%B %d, %Y')}\n"
    if project_data.get('go_live_date'):
        context += f"Go Live Date: {project_data['go_live_date'].strftime('%B %d, %Y')}\n"
    if project_data.get('assessment_end_date'):
        context += f"Assessment End: {project_data['assessment_end_date'].strftime('%B %d, %Y')}\n"
    
    # Add existing FAQs if available
    if existing_faqs:
        context += f"\nEXISTING FAQ CONTENT:\n{existing_faqs}\n"
    
    context += """

INSTRUCTIONS:
1. Address the specific concern directly and personally
2. Use the stakeholder's mental model to tailor your communication approach
3. Reference relevant project information, strategy, and key messages
4. Include specific dates when relevant
5. Match the tone and style that resonates with this mental model
6. Keep the response professional but approachable
7. Provide actionable information where possible
8. Ensure the response addresses their underlying motivators and concerns

Generate a suggested response that the change manager can review and edit before sending.
"""
    
    return context


def get_existing_faqs(project_id):
    """Get existing FAQ content for context"""
    from main import ConcernAssignment
    
    # Get resolved concerns that could serve as FAQ content
    resolved_concerns = ConcernAssignment.query.filter_by(
        project_id=project_id,
        status='resolved'
    ).filter(
        ConcernAssignment.response_text.isnot(None)
    ).all()
    
    faq_content = []
    for concern in resolved_concerns:
        if concern.response_text and concern.response_text.strip():
            faq_content.append(f"Q: {concern.concern_text}\nA: {concern.response_text}")
    
    return "\n\n".join(faq_content) if faq_content else None


def update_faq_database(project_id, concern_text, response_text, mental_model):
    """Add resolved concern and response to FAQ database for future reference"""
    # This could be expanded to create a dedicated FAQ table
    # For now, we use the resolved concerns as FAQ content
    pass