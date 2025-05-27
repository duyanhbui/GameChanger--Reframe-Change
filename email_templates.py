"""
Email Templates for Change Management Communication
Personalized templates based on mental models and stakeholder preferences
"""

def get_mental_model_email_template(mental_model, stakeholder_name, project_name):
    """Get personalized email template based on mental model"""
    
    templates = {
        "The Architect": {
            "subject": f"Strategic Update: {project_name} Implementation Plan",
            "body": f"""Dear {stakeholder_name},

I hope this message finds you well. As someone who values strategic planning and evidence-based approaches, I wanted to share some key developments in our {project_name} initiative.

📊 **Project Progress & Metrics:**
- Current milestone completion rate
- Evidence-based success indicators
- Strategic alignment with organizational goals

🎯 **What This Means for You:**
Given your preference for systematic approaches, you'll appreciate that we've developed comprehensive implementation blueprints and risk mitigation strategies. Your analytical perspective is crucial for refining our strategic direction.

📈 **Next Steps & Timeline:**
- Detailed implementation phases
- Key decision points requiring your input
- Resource allocation and planning sessions

We value your strategic insights and would welcome your thoughts on optimizing our approach.

Best regards,
Change Management Team"""
        },
        
        "The Driver": {
            "subject": f"Action Required: {project_name} Execution Updates",
            "body": f"""Hi {stakeholder_name},

Quick update on {project_name} - cutting straight to what matters for results-focused leaders like yourself.

⚡ **Key Actions & Deliverables:**
- Current execution status and performance metrics
- Critical path items requiring your attention
- Resource needs and bottleneck resolution

🎯 **Impact & Results:**
Your focus on driving outcomes aligns perfectly with our current phase. We need your expertise in streamlining processes and ensuring accountability across teams.

📋 **Action Items:**
- Review attached execution plan
- Provide feedback on resource allocation
- Join our next accountability checkpoint

Let's drive this initiative to successful completion.

Best,
Change Management Team"""
        },
        
        "The Facilitator": {
            "subject": f"Team Collaboration: {project_name} Community Update",
            "body": f"""Dear {stakeholder_name},

I hope you're doing well! Your collaborative spirit and people-first approach make you such a valuable part of our {project_name} journey.

🤝 **Building Together:**
Your talent for bringing people together is exactly what we need as we navigate this change. The team dynamics and stakeholder engagement you foster are essential to our success.

💬 **How You Can Help:**
- Facilitate discussions in your area
- Help bridge different perspectives
- Support team members who may need encouragement

🌟 **Community Impact:**
We're seeing great results when teams work together, and your leadership in creating inclusive environments is making a real difference.

Looking forward to continuing this journey together!

Warm regards,
Change Management Team"""
        },
        
        "The Creator": {
            "subject": f"Innovation Opportunity: {project_name} Creative Possibilities",
            "body": f"""Hi {stakeholder_name},

Exciting developments in {project_name}! Your innovative mindset and creative problem-solving skills are exactly what we need right now.

🚀 **Innovation Opportunities:**
This change initiative opens up incredible possibilities for breakthrough solutions and creative approaches. Your ability to see beyond conventional thinking is invaluable.

💡 **Creative Challenges:**
- Reimagining current processes
- Developing innovative solutions
- Exploring new possibilities for growth

🌟 **Your Vision Matters:**
We'd love to hear your ideas on how we can turn this change into a catalyst for innovation and transformation.

Ready to create something amazing together?

Best,
Change Management Team"""
        },
        
        "The Guru": {
            "subject": f"Evidence & Insights: {project_name} Research Update",
            "body": f"""Dear {stakeholder_name},

Given your expertise and evidence-based approach, I wanted to share some comprehensive insights about our {project_name} initiative.

📚 **Research & Evidence:**
Your preference for thorough analysis and wisdom-based decisions aligns perfectly with our current research phase. We've compiled extensive data and case studies that support our approach.

🔍 **Key Insights:**
- Industry best practices and benchmarking data
- Risk analysis and mitigation strategies
- Evidence from similar successful implementations

📖 **Your Expertise Needed:**
Your deep knowledge and analytical skills would be invaluable in reviewing our research findings and providing guidance on complex decisions.

We value your wisdom and would appreciate your insights.

Best regards,
Change Management Team"""
        },
        
        "The Implementer": {
            "subject": f"Implementation Details: {project_name} Execution Plan",
            "body": f"""Dear {stakeholder_name},

I know you value clear processes and systematic execution, so I wanted to provide you with detailed information about our {project_name} implementation.

⚙️ **Process & Procedures:**
Your attention to detail and systematic approach are crucial for successful implementation. We've developed comprehensive procedures and checklists to ensure nothing falls through the cracks.

📋 **Implementation Steps:**
- Detailed task breakdowns and timelines
- Quality checkpoints and validation processes
- Standard operating procedures and guidelines

🎯 **Your Role:**
Your expertise in turning plans into reality is essential. We need your skills in process optimization and systematic execution.

Thank you for your meticulous approach to implementation!

Best regards,
Change Management Team"""
        }
    }
    
    # Default template for unknown mental models
    default_template = {
        "subject": f"Important Update: {project_name}",
        "body": f"""Dear {stakeholder_name},

Thank you for your participation in our {project_name} initiative. Your perspective and engagement are valuable to our success.

We wanted to keep you informed about recent developments and next steps in our change journey.

Your continued involvement and feedback help us tailor our approach to meet everyone's needs effectively.

Best regards,
Change Management Team"""
    }
    
    return templates.get(mental_model, default_template)


def get_concern_response_template(mental_model, stakeholder_name, concern_text):
    """Get personalized template for responding to specific concerns"""
    
    response_styles = {
        "The Architect": "Here's a strategic analysis of your concern with supporting evidence and systematic approach...",
        "The Driver": "Let me address your concern directly with actionable solutions and clear outcomes...",
        "The Facilitator": "Thank you for raising this important concern. Let's work together to find a solution that works for everyone...",
        "The Creator": "Your concern opens up interesting possibilities. Let's explore innovative solutions together...",
        "The Guru": "Your concern is well-founded. Based on research and best practices, here's a comprehensive response...",
        "The Implementer": "Thank you for this detailed concern. Here's a step-by-step response with clear processes..."
    }
    
    style = response_styles.get(mental_model, "Thank you for your concern. Here's our response...")
    
    return {
        "subject": f"Response to Your Question About {concern_text[:50]}...",
        "body": f"""Dear {stakeholder_name},

{style}

[Response content will be customized based on the specific concern and mental model preferences]

If you have any follow-up questions, please don't hesitate to reach out.

Best regards,
Change Management Team"""
    }


def get_project_announcement_template(project_name, project_description, audience_mental_models):
    """Get template for project announcements tailored to audience"""
    
    if "The Architect" in audience_mental_models:
        focus = "strategic planning and evidence-based implementation"
    elif "The Driver" in audience_mental_models:
        focus = "results-driven execution and clear accountability"
    elif "The Facilitator" in audience_mental_models:
        focus = "collaborative approach and team engagement"
    elif "The Creator" in audience_mental_models:
        focus = "innovative opportunities and creative solutions"
    else:
        focus = "systematic implementation and continuous improvement"
    
    return {
        "subject": f"Introducing {project_name}: Your Role in Our Success",
        "body": f"""Dear Team,

We're excited to announce the launch of {project_name}, a strategic initiative designed with {focus} at its core.

**Project Overview:**
{project_description}

**Why Your Perspective Matters:**
Your unique approach to change and problem-solving is essential to our success. We've designed this initiative to leverage the diverse strengths of our team.

**Next Steps:**
- Complete the stakeholder assessment to help us tailor our approach
- Join upcoming information sessions
- Share your questions and concerns

Together, we'll make this transformation successful.

Best regards,
Change Management Team"""
    }