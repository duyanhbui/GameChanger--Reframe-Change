"""
Notification Service for Change Management Platform
Real-time updates for new concerns and responses
"""

from datetime import datetime, timedelta
from flask import flash
from email_templates import get_mental_model_email_template, get_concern_response_template
import os

class NotificationService:
    def __init__(self, db):
        self.db = db
    
    def create_notification(self, user_type, message, priority="normal", related_id=None):
        """Create a new notification"""
        # In a real implementation, this would store in a notifications table
        notification = {
            'id': datetime.utcnow().timestamp(),
            'user_type': user_type,  # 'manager', 'sme', 'stakeholder'
            'message': message,
            'priority': priority,  # 'low', 'normal', 'high', 'urgent'
            'created_at': datetime.utcnow(),
            'read': False,
            'related_id': related_id
        }
        return notification
    
    def notify_new_concern(self, concern_response):
        """Notify managers about new concerns"""
        message = f"New concern from {concern_response.name}: {concern_response.concern[:50]}..."
        return self.create_notification('manager', message, 'normal', concern_response.id)
    
    def notify_concern_assigned(self, assignment):
        """Notify SME about concern assignment"""
        message = f"You've been assigned a new concern to address from {assignment.stakeholder_response.name}"
        return self.create_notification('sme', message, 'high', assignment.id)
    
    def notify_response_received(self, assignment):
        """Notify manager about SME response"""
        message = f"SME {assignment.sme_name} has responded to a concern"
        return self.create_notification('manager', message, 'normal', assignment.id)
    
    def get_dashboard_notifications(self, user_type='manager'):
        """Get recent notifications for dashboard"""
        # In a real implementation, this would query the notifications table
        # For now, we'll generate based on recent activity
        notifications = []
        
        from main import StakeholderResponse, ConcernAssignment
        
        # Recent unassigned concerns
        recent_concerns = StakeholderResponse.query.filter(
            StakeholderResponse.concern.isnot(None),
            StakeholderResponse.timestamp > datetime.utcnow() - timedelta(days=7)
        ).all()
        
        for concern in recent_concerns:
            assignments = ConcernAssignment.query.filter_by(stakeholder_response_id=concern.id).all()
            if not assignments:
                notifications.append({
                    'type': 'concern',
                    'message': f"New concern from {concern.name}: {concern.concern[:50]}...",
                    'timestamp': concern.timestamp,
                    'priority': 'normal',
                    'id': concern.id
                })
        
        # Recent pending assignments
        pending_assignments = ConcernAssignment.query.filter(
            ConcernAssignment.status == 'pending',
            ConcernAssignment.assigned_at > datetime.utcnow() - timedelta(days=3)
        ).all()
        
        for assignment in pending_assignments:
            notifications.append({
                'type': 'assignment',
                'message': f"Pending response from {assignment.sme_name}",
                'timestamp': assignment.assigned_at,
                'priority': 'high',
                'id': assignment.id
            })
        
        # Sort by timestamp, most recent first
        notifications.sort(key=lambda x: x['timestamp'], reverse=True)
        return notifications[:5]  # Return top 5 notifications


def generate_personalized_email(stakeholder_response, email_type="update"):
    """Generate personalized email based on mental model"""
    from email_templates import get_mental_model_email_template
    
    template = get_mental_model_email_template(
        stakeholder_response.mental_model,
        stakeholder_response.name,
        stakeholder_response.project.name
    )
    
    return template


def send_mental_model_communication(stakeholder_response, custom_message=None):
    """Send personalized communication based on mental model"""
    template = generate_personalized_email(stakeholder_response)
    
    if custom_message:
        # Integrate custom message with template
        template['body'] = template['body'].replace(
            '[Response content will be customized based on the specific concern and mental model preferences]',
            custom_message
        )
    
    # In a real implementation, this would integrate with your email service
    return {
        'to': stakeholder_response.email,
        'subject': template['subject'],
        'body': template['body'],
        'mental_model': stakeholder_response.mental_model
    }


def get_communication_insights(responses):
    """Analyze communication patterns and suggest improvements"""
    insights = []
    
    if not responses:
        return insights
    
    # Analyze mental model distribution for communication strategy
    model_counts = {}
    for response in responses:
        model = response.mental_model
        model_counts[model] = model_counts.get(model, 0) + 1
    
    total_responses = len(responses)
    
    # Generate communication insights
    for model, count in model_counts.items():
        percentage = (count / total_responses) * 100
        if percentage > 30:  # Significant representation
            if model == "The Architect":
                insights.append("📊 Use data-driven communications with strategic frameworks")
            elif model == "The Driver":
                insights.append("⚡ Focus on results and action-oriented messaging")
            elif model == "The Facilitator":
                insights.append("🤝 Emphasize collaboration and team-building approaches")
            elif model == "The Creator":
                insights.append("💡 Highlight innovation opportunities and creative solutions")
            elif model == "The Guru":
                insights.append("📚 Provide detailed research and evidence-based content")
            elif model == "The Implementer":
                insights.append("⚙️ Include step-by-step processes and clear procedures")
    
    return insights