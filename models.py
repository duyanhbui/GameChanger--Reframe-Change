from app import db
from datetime import datetime

class AssessmentResponse(db.Model):
    """Model to store assessment responses and results"""
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Questions responses
    question1_response = db.Column(db.String(10), nullable=False)  # A, B, C, D
    question2_response = db.Column(db.String(10), nullable=False)  # A, B, C, D
    question3_response = db.Column(db.String(10), nullable=False)  # A, B, C, D
    additional_comments = db.Column(db.Text, nullable=True)
    
    # Results
    mental_model_id = db.Column(db.String(20), nullable=False)  # e.g., "innovator", "traditionalist"
    ip_address = db.Column(db.String(45), nullable=True)  # For basic analytics
    
    def __repr__(self):
        return f'<AssessmentResponse {self.id}: {self.mental_model_id}>'
