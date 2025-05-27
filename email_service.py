import os
import sys
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from flask import url_for

def send_concern_assignment_email(sme_email, sme_name, concern_text, project_name, assignment_id, stakeholder_name=None):
    """Send email to SME about concern assignment"""
    sendgrid_key = os.environ.get('SENDGRID_API_KEY')
    
    if not sendgrid_key:
        print("SendGrid API key not configured - email not sent")
        return False
    
    sg = SendGridAPIClient(sendgrid_key)
    
    # Create response URL (we'll build this route)
    response_url = f"{os.environ.get('REPLIT_DOMAINS', 'localhost:5000')}/sme/respond/{assignment_id}"
    
    subject = f"Change Management Concern Assignment - {project_name}"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c5aa0;">Change Management Concern Assignment</h2>
            
            <p>Hello {sme_name},</p>
            
            <p>You have been assigned to address a stakeholder concern for the <strong>{project_name}</strong> change management project.</p>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #2c5aa0; margin: 20px 0;">
                <h4 style="margin-top: 0;">Stakeholder Concern:</h4>
                <p style="font-style: italic; margin-bottom: 0;">"{concern_text}"</p>
                {f'<p style="margin-top: 10px; font-size: 0.9em; color: #666;">- {stakeholder_name}</p>' if stakeholder_name else ''}
            </div>
            
            <p>Please provide your expert response to address this concern. Your input will help us better support our stakeholders through this change.</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="http://{response_url}" 
                   style="background-color: #2c5aa0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                   Respond to Concern
                </a>
            </div>
            
            <p style="font-size: 0.9em; color: #666;">
                If you have any questions about this assignment, please contact the change management team.
            </p>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="font-size: 0.8em; color: #888;">
                This is an automated message from the Change Management Assessment Platform.
            </p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Change Management Concern Assignment - {project_name}
    
    Hello {sme_name},
    
    You have been assigned to address a stakeholder concern for the {project_name} change management project.
    
    Stakeholder Concern:
    "{concern_text}"
    {f'- {stakeholder_name}' if stakeholder_name else ''}
    
    Please respond by visiting: http://{response_url}
    
    Thank you for your expertise in supporting our stakeholders through this change.
    """
    
    message = Mail(
        from_email=Email("noreply@changemanagement.com", "Change Management Team"),
        to_emails=To(sme_email),
        subject=subject
    )
    
    message.content = [
        Content("text/plain", text_content),
        Content("text/html", html_content)
    ]
    
    try:
        response = sg.send(message)
        print(f"Email sent successfully to {sme_email} - Status: {response.status_code}")
        return True
    except Exception as e:
        print(f"SendGrid error: {e}")
        return False

def send_response_notification_email(manager_email, sme_name, concern_text, response_text, project_name):
    """Send notification to change manager when SME responds"""
    sendgrid_key = os.environ.get('SENDGRID_API_KEY')
    
    if not sendgrid_key:
        print("SendGrid API key not configured - email not sent")
        return False
    
    sg = SendGridAPIClient(sendgrid_key)
    
    subject = f"SME Response Received - {project_name}"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #28a745;">SME Response Received</h2>
            
            <p>A Subject Matter Expert has responded to an assigned concern for <strong>{project_name}</strong>.</p>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #6c757d; margin: 20px 0;">
                <h4 style="margin-top: 0;">Original Concern:</h4>
                <p style="font-style: italic; margin-bottom: 0;">"{concern_text}"</p>
            </div>
            
            <div style="background-color: #e8f5e8; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0;">
                <h4 style="margin-top: 0;">SME Response by {sme_name}:</h4>
                <p style="margin-bottom: 0;">"{response_text}"</p>
            </div>
            
            <p>You can now review this response and take any necessary follow-up actions in your dashboard.</p>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="font-size: 0.8em; color: #888;">
                This is an automated message from the Change Management Assessment Platform.
            </p>
        </div>
    </body>
    </html>
    """
    
    message = Mail(
        from_email=Email("noreply@changemanagement.com", "Change Management Team"),
        to_emails=To(manager_email),
        subject=subject
    )
    
    message.content = Content("text/html", html_content)
    
    try:
        response = sg.send(message)
        print(f"Notification email sent to manager - Status: {response.status_code}")
        return True
    except Exception as e:
        print(f"SendGrid error: {e}")
        return False