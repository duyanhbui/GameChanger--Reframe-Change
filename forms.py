from flask_wtf import FlaskForm
from wtforms import RadioField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Length

class AssessmentForm(FlaskForm):
    """Form for the change management assessment"""
    
    question1 = RadioField(
        'When facing organizational change, what is your primary concern?',
        choices=[
            ('A', 'How will this impact our established processes and procedures?'),
            ('B', 'What opportunities does this create for innovation and growth?'),
            ('C', 'How will this affect team morale and relationships?'),
            ('D', 'What are the financial implications and ROI considerations?')
        ],
        validators=[DataRequired(message="Please select an answer for question 1")]
    )
    
    question2 = RadioField(
        'How do you prefer to make decisions during times of change?',
        choices=[
            ('A', 'Based on proven methods and historical data'),
            ('B', 'Using intuition and creative problem-solving'),
            ('C', 'Through collaborative discussions and consensus building'),
            ('D', 'By analyzing metrics and quantifiable outcomes')
        ],
        validators=[DataRequired(message="Please select an answer for question 2")]
    )
    
    question3 = RadioField(
        'What motivates you most when implementing new initiatives?',
        choices=[
            ('A', 'Maintaining stability and minimizing disruption'),
            ('B', 'Exploring new possibilities and breakthrough solutions'),
            ('C', 'Ensuring everyone feels heard and supported'),
            ('D', 'Achieving measurable results and competitive advantage')
        ],
        validators=[DataRequired(message="Please select an answer for question 3")]
    )
    
    additional_comments = TextAreaField(
        'Additional thoughts or concerns about change management (optional):',
        validators=[Optional(), Length(max=500)],
        render_kw={"placeholder": "Share any additional insights or specific challenges you face..."}
    )
    
    submit = SubmitField('Get My Assessment Results')
