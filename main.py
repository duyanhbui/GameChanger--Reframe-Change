from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "change-management-key")

# Database setup
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///change_assessment.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db = SQLAlchemy(app)

# Models
class StakeholderResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Basic info
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    department = db.Column(db.String(100))
    
    # Assessment responses
    feeling = db.Column(db.String(20))  # eager/cautious
    style = db.Column(db.String(20))    # rockstar/roadie
    focus_areas = db.Column(db.String(100))  # comma-separated: proof,process,people,possibilities
    concern = db.Column(db.Text)       # open text question
    
    # Results
    mental_model = db.Column(db.String(50))
    
    # Engagement tracking
    opted_out = db.Column(db.Boolean, default=False)
    frequency_preference = db.Column(db.String(20), default="fortnightly")
    
    def __repr__(self):
        return f'<StakeholderResponse {self.name}: {self.mental_model}>'

class SMEResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    stakeholder_id = db.Column(db.Integer, db.ForeignKey('stakeholder_response.id'))
    sme_name = db.Column(db.String(100))
    concern_addressed = db.Column(db.Text)
    response_text = db.Column(db.Text)
    
class ChangeProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    description = db.Column(db.Text)
    change_strategy = db.Column(db.Text)
    key_messages = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

# KB16 Model Logic
def assign_model(feeling, style, focus_areas):
    """Assign KB16 model based on responses"""
    # Handle multiple focus areas - use first one for model assignment
    primary_focus = focus_areas.split(',')[0] if focus_areas else 'proof'
    
    # Map focus areas to model keys
    focus_map = {
        'proof': 'proof',
        'process': 'process', 
        'people': 'people',
        'possibilities': 'possibilities'
    }
    
    focus_key = focus_map.get(primary_focus, 'proof')
    model_key = f"{feeling}_{style}_{focus_key}"
    
    model_map = {
        "eager_rockstar_proof": "The Architect",
        "eager_rockstar_process": "The Driver", 
        "eager_rockstar_people": "The Facilitator",
        "eager_rockstar_possibilities": "The Creator",
        "eager_roadie_proof": "The Guru",
        "eager_roadie_process": "The Implementer",
        "eager_roadie_people": "The Humanitarian", 
        "eager_roadie_possibilities": "The Explorer",
        "cautious_rockstar_proof": "The Sceptic",
        "cautious_rockstar_process": "The Perfectionist",
        "cautious_rockstar_people": "The Preservationist",
        "cautious_rockstar_possibilities": "The Fearful Optimist",
        "cautious_roadie_proof": "The Forecaster",
        "cautious_roadie_process": "The Bureaucrat",
        "cautious_roadie_people": "The Shepherd",
        "cautious_roadie_possibilities": "The Lost Soul"
    }
    
    return model_map.get(model_key, "Unknown")

# Routes
@app.route("/")
def index():
    """Stakeholder assessment form"""
    return render_template("stakeholder_form.html")

@app.route("/submit", methods=["POST"])
def submit_assessment():
    """Process stakeholder assessment"""
    # Get form data
    name = request.form.get("name")
    email = request.form.get("email") 
    department = request.form.get("department")
    feeling = request.form.get("feeling")
    style = request.form.get("style")
    focus_areas = ",".join(request.form.getlist("focus"))
    concern = request.form.get("concern", "")
    frequency = request.form.get("frequency", "fortnightly")
    
    # Assign mental model
    mental_model = assign_model(feeling, style, focus_areas)
    
    # Save to database
    response = StakeholderResponse(
        name=name,
        email=email,
        department=department,
        feeling=feeling,
        style=style,
        focus_areas=focus_areas,
        concern=concern,
        mental_model=mental_model,
        frequency_preference=frequency
    )
    
    try:
        db.session.add(response)
        db.session.commit()
        return render_template("stakeholder_result.html", 
                             model=mental_model, 
                             name=name,
                             response_id=response.id)
    except Exception as e:
        db.session.rollback()
        flash("Error saving your response. Please try again.", "error")
        return redirect(url_for("index"))

@app.route("/manager")
def manager_dashboard():
    """Change manager dashboard"""
    responses = StakeholderResponse.query.filter_by(opted_out=False).all()
    
    # Calculate statistics
    total_responses = len(responses)
    model_counts = {}
    focus_counts = {"proof": 0, "process": 0, "people": 0, "possibilities": 0}
    concerns = []
    
    for response in responses:
        # Mental model distribution
        model = response.mental_model
        model_counts[model] = model_counts.get(model, 0) + 1
        
        # Focus area distribution  
        if response.focus_areas:
            for focus in response.focus_areas.split(','):
                if focus.strip() in focus_counts:
                    focus_counts[focus.strip()] += 1
        
        # Collect concerns
        if response.concern and response.concern.strip():
            concerns.append({
                'name': response.name,
                'concern': response.concern,
                'model': response.mental_model,
                'id': response.id
            })
    
    return render_template("manager_dashboard.html",
                         responses=responses,
                         total_responses=total_responses,
                         model_counts=model_counts,
                         focus_counts=focus_counts,
                         concerns=concerns)

@app.route("/opt-out/<int:response_id>")
def opt_out(response_id):
    """Allow stakeholders to opt out"""
    response = StakeholderResponse.query.get_or_404(response_id)
    response.opted_out = True
    db.session.commit()
    return render_template("opt_out_success.html")

@app.route("/api/stats")
def get_stats():
    """API endpoint for dashboard statistics"""
    responses = StakeholderResponse.query.filter_by(opted_out=False).all()
    
    stats = {
        'total_responses': len(responses),
        'model_distribution': {},
        'focus_distribution': {"proof": 0, "process": 0, "people": 0, "possibilities": 0}
    }
    
    for response in responses:
        # Mental models
        model = response.mental_model
        stats['model_distribution'][model] = stats['model_distribution'].get(model, 0) + 1
        
        # Focus areas
        if response.focus_areas:
            for focus in response.focus_areas.split(','):
                if focus.strip() in stats['focus_distribution']:
                    stats['focus_distribution'][focus.strip()] += 1
    
    return jsonify(stats)

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
