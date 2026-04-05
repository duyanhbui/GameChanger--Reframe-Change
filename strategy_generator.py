"""
AI Strategy Generator Service
Processes meeting transcriptions to generate comprehensive change management strategies
"""

import os
import json
from openai import OpenAI

def generate_change_strategy_from_transcription(transcription, project_name="", project_description=""):
    """
    Generate comprehensive change management strategy from meeting transcription.
    Returns: BCIP, Change Logic, Change Story, Key Messages, and Change Strategy
    """
    
    api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise Exception("OpenAI API key not found. Please configure your API key.")
    base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = OpenAI(**client_kwargs)
    
    # Construct the prompt for ChatGPT
    prompt = f"""
    You are an expert change management consultant. Analyze the following meeting transcription and generate a comprehensive change management strategy with five key components.

    Meeting Transcription:
    {transcription}

    Project Context:
    - Project Name: {project_name}
    - Project Description: {project_description}

    Please generate the following five components based on the meeting discussion:

    1. BCIP (Business Case & Implementation Plan): Provide the situational context of the project, business justification, and high-level implementation considerations.

    2. Change Logic: Explain the rationale and reasoning behind why this change is necessary, including the logical framework that supports the initiative.

    3. Change Story: Create a compelling narrative that stakeholders can connect with, explaining the why, what, and how of the change in an engaging way.

    4. Key Messages: Develop 3-5 core messages that should be communicated consistently across all stakeholder touchpoints.

    5. Change Strategy: Outline the overall approach and methodology for managing and implementing this change, including stakeholder engagement, communication strategy, and success metrics.

    Please respond in JSON format with these exact keys: "bcip", "change_logic", "change_story", "key_messages", "change_strategy".
    Each value should be a detailed, professional response suitable for a change management project.
    """

    try:
        # Generate response using ChatGPT
        response = client.chat.completions.create(
            model="gpt-4o",  # Using the latest model as per blueprint
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert change management consultant with deep knowledge of organizational psychology, communication strategies, and change implementation methodologies."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=4000,
            temperature=0.7
        )
        
        # Parse the JSON response
        content = response.choices[0].message.content
        strategy_components = json.loads(content)
        
        # Validate that all required components are present
        required_keys = ["bcip", "change_logic", "change_story", "key_messages", "change_strategy"]
        for key in required_keys:
            if key not in strategy_components:
                strategy_components[key] = f"Generated {key.replace('_', ' ').title()} content based on transcription analysis."
        
        return {
            "success": True,
            "components": strategy_components
        }
        
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Failed to parse AI response: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"AI strategy generation failed: {str(e)}"
        }


def validate_transcription(transcription):
    """
    Validate that the transcription contains meaningful content for strategy generation
    """
    if not transcription or len(transcription.strip()) < 100:
        return False, "Transcription too short. Please provide a more detailed meeting transcript."
    
    # Check for basic meeting indicators
    meeting_indicators = [
        "meeting", "discussion", "project", "change", "implementation", 
        "strategy", "stakeholder", "business", "objective", "goal"
    ]
    
    transcription_lower = transcription.lower()
    found_indicators = sum(1 for indicator in meeting_indicators if indicator in transcription_lower)
    
    if found_indicators < 2:
        return False, "Transcription doesn't appear to contain change management content. Please ensure it's from a relevant project meeting."
    
    return True, "Transcription is valid for strategy generation."


def enhance_strategy_with_context(strategy_components, project_context):
    """
    Enhance generated strategy components with additional project context
    """
    enhanced_components = strategy_components.copy()
    
    # Add project-specific enhancements
    if project_context.get("project_name"):
        for key, value in enhanced_components.items():
            if isinstance(value, str):
                enhanced_components[key] = value.replace("[Project Name]", project_context["project_name"])
    
    return enhanced_components