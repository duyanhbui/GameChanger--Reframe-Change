from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.utils import secure_filename
import os
import PyPDF2
from dateutil import parser
import uuid
from email_service import send_concern_assignment_email, send_response_notification_email
from ai_response_service import generate_ai_response_suggestion, get_existing_faqs
from departments import DEPARTMENTS

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "change-management-key")

# File upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    """Extract text content from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

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
    
    # Project association
    project_id = db.Column(db.Integer, db.ForeignKey('change_project.id'), nullable=False)
    
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
    
    # Relationship
    project = db.relationship('ChangeProject', backref='responses')
    
    def __repr__(self):
        return f'<StakeholderResponse {self.name}: {self.mental_model}>'

class ConcernAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Links
    stakeholder_response_id = db.Column(db.Integer, db.ForeignKey('stakeholder_response.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('change_project.id'), nullable=False)
    
    # Assignment details
    concern_text = db.Column(db.Text, nullable=False)
    assigned_by = db.Column(db.String(100))  # Change manager name
    
    # SME details
    sme_name = db.Column(db.String(100))
    sme_email = db.Column(db.String(120))
    
    # Status tracking
    status = db.Column(db.String(20), default='pending')  # pending, responded, resolved
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime)
    
    # Response
    response_text = db.Column(db.Text)
    response_method = db.Column(db.String(20))  # 'sme' or 'manager'
    
    # Email tracking
    email_sent = db.Column(db.Boolean, default=False)
    email_sent_at = db.Column(db.DateTime)
    
    # Relationships
    stakeholder_response = db.relationship('StakeholderResponse', backref='concern_assignments')
    project = db.relationship('ChangeProject', backref='concern_assignments')
    
class ChangeProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    description = db.Column(db.Text)
    
    # Strategy Components (text and file uploads)
    bcip = db.Column(db.Text)  # Business Case & Implementation Plan
    bcip_document_path = db.Column(db.String(500))  # Uploaded BCIP document
    bcip_document_name = db.Column(db.String(200))  # Original BCIP filename
    
    change_logic = db.Column(db.Text)  # Rationale and reasoning
    change_logic_document_path = db.Column(db.String(500))  # Uploaded Change Logic document
    change_logic_document_name = db.Column(db.String(200))  # Original Change Logic filename
    
    change_story = db.Column(db.Text)  # Compelling narrative
    change_story_document_path = db.Column(db.String(500))  # Uploaded Change Story document
    change_story_document_name = db.Column(db.String(200))  # Original Change Story filename
    
    change_strategy = db.Column(db.Text)  # Overall approach
    change_strategy_document_path = db.Column(db.String(500))  # Uploaded Change Strategy document
    change_strategy_document_name = db.Column(db.String(200))  # Original Change Strategy filename
    
    key_messages = db.Column(db.Text)  # Core communications
    key_messages_document_path = db.Column(db.String(500))  # Uploaded Key Messages document
    key_messages_document_name = db.Column(db.String(200))  # Original Key Messages filename
    
    # File uploads
    strategy_document_path = db.Column(db.String(500))  # Path to uploaded PDF
    strategy_document_name = db.Column(db.String(200))  # Original filename
    
    # Key dates
    project_start_date = db.Column(db.Date)
    go_live_date = db.Column(db.Date)
    communication_start_date = db.Column(db.Date)
    assessment_end_date = db.Column(db.Date)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)


class FAQEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    project_id = db.Column(db.Integer, db.ForeignKey('change_project.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    
    # Link to original concern assignment if applicable
    concern_assignment_id = db.Column(db.Integer, db.ForeignKey('concern_assignment.id'), nullable=True)
    
    # Categorization
    category = db.Column(db.String(100), default='General')
    tags = db.Column(db.String(500))  # comma-separated tags
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    project = db.relationship('ChangeProject', backref='faq_entries')
    concern_assignment = db.relationship('ConcernAssignment', backref='faq_entry')

def get_active_project_id():
    """Get the active project ID from URL params or session."""
    project_id = request.args.get('project_id', type=int)
    if project_id is not None:
        session['active_project_id'] = project_id
        return project_id
    return session.get('active_project_id')

def get_active_project():
    """Get the active project object from URL params or session."""
    project_id = get_active_project_id()
    if project_id:
        project = ChangeProject.query.get(project_id)
        if project:
            return project
        session.pop('active_project_id', None)
    return None

@app.route("/manager/clear-project")
def clear_active_project():
    """Clear the active project filter and return to all-projects view."""
    session.pop('active_project_id', None)
    return redirect(request.args.get('next', url_for('manager_dashboard')))

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
    # Get project from URL parameter or use default
    project_id = request.args.get('project_id', type=int)
    if project_id:
        project = ChangeProject.query.get_or_404(project_id)
    else:
        # Use most recent active project or create default
        project = ChangeProject.query.filter_by(is_active=True).first()
        if not project:
            project = ChangeProject(
                name="Default Change Project",
                description="Default project for change management assessments",
                change_strategy="Assessment collection for organizational change",
                key_messages="Your input helps us understand and support you during this change."
            )
            db.session.add(project)
            db.session.commit()
    
    return render_template("stakeholder_form.html", project=project, departments=DEPARTMENTS)

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
    project_id = request.form.get("project_id", type=int)
    
    # Assign mental model
    mental_model = assign_model(feeling, style, focus_areas)
    
    # Save to database
    response = StakeholderResponse()
    response.project_id = project_id
    response.name = name
    response.email = email
    response.department = department
    response.feeling = feeling
    response.style = style
    response.focus_areas = focus_areas
    response.concern = concern
    response.mental_model = mental_model
    response.frequency_preference = frequency
    
    try:
        db.session.add(response)
        db.session.commit()
        return render_template("stakeholder_result.html", 
                             model=mental_model, 
                             name=name,
                             response_id=response.id,
                             project_id=project_id)
    except Exception as e:
        db.session.rollback()
        flash("Error saving your response. Please try again.", "error")
        return redirect(url_for("index"))

@app.route("/manager")
def manager_dashboard():
    """Change manager dashboard"""
    projects = ChangeProject.query.filter_by(is_active=True).all()
    selected_project = get_active_project()
    
    if selected_project:
        responses = StakeholderResponse.query.filter_by(opted_out=False, project_id=selected_project.id).all()
    else:
        responses = StakeholderResponse.query.filter_by(opted_out=False).all()
    
    # Calculate statistics
    total_responses = len(responses)
    model_counts = {}
    focus_counts = {"proof": 0, "process": 0, "people": 0, "possibilities": 0}
    # Get concerns and check their assignment status
    all_concerns = [response for response in responses if response.concern and response.concern.strip()]
    
    # Only show concerns that have NO assignments yet OR have pending assignments
    concerns_needing_attention = []
    for concern in all_concerns:
        assignments = ConcernAssignment.query.filter_by(stakeholder_response_id=concern.id).all()
        if not assignments:
            # No assignment exists - definitely needs attention
            concerns_needing_attention.append(concern)
        elif any(assignment.status == 'pending' and not assignment.response_text for assignment in assignments):
            # Has pending assignments without responses - needs attention
            concerns_needing_attention.append(concern)
    
    # Sort by timestamp descending and format for display
    concerns = []
    for concern in sorted(concerns_needing_attention, key=lambda x: x.timestamp, reverse=True):
        concerns.append({
            'name': concern.name,
            'concern': concern.concern,
            'model': concern.mental_model,
            'id': concern.id,
            'department': concern.department,
            'timestamp': concern.timestamp,
            'project_name': concern.project.name
        })
    
    sentiment_analysis = {"eager": 0, "cautious": 0}
    department_breakdown = {}
    
    for response in responses:
        # Mental model distribution
        model = response.mental_model
        model_counts[model] = model_counts.get(model, 0) + 1
        
        # Focus area distribution  
        if response.focus_areas:
            for focus in response.focus_areas.split(','):
                if focus.strip() in focus_counts:
                    focus_counts[focus.strip()] += 1
        
        # Sentiment analysis
        if response.feeling:
            sentiment_analysis[response.feeling] += 1
        
        # Department breakdown
        dept = response.department or "Not specified"
        department_breakdown[dept] = department_breakdown.get(dept, 0) + 1
    
    # Generate strategic recommendations based on mental models, concerns, and project context
    recommendations = generate_strategic_recommendations(
        model_counts, focus_counts, sentiment_analysis, total_responses, 
        all_concerns, selected_project
    )
    
    return render_template("manager_dashboard.html",
                         responses=responses,
                         total_responses=total_responses,
                         model_counts=model_counts,
                         focus_counts=focus_counts,
                         concerns=concerns,
                         sentiment_analysis=sentiment_analysis,
                         department_breakdown=department_breakdown,
                         recommendations=recommendations,
                         projects=projects,
                         selected_project=selected_project)

def generate_strategic_recommendations(model_counts, focus_counts, sentiment_analysis, total_responses, concerns, project):
    """Generate intelligent strategic recommendations based on mental models, concerns, and project context"""
    import os
    recommendations = []
    
    if total_responses == 0:
        return ["Start gathering stakeholder feedback to generate strategic insights"]
    
    # Analyze concern patterns
    concern_themes = analyze_concern_themes(concerns)
    
    # Generate strategic insights
    recommendations.extend(generate_sentiment_insights(sentiment_analysis, total_responses))
    recommendations.extend(generate_mental_model_insights(model_counts, total_responses))
    recommendations.extend(generate_concern_insights(concern_themes))
    recommendations.extend(generate_focus_insights(focus_counts, total_responses))
    
    # Add project-specific insights if available
    if project and project.change_strategy:
        recommendations.append("📋 Align communications with your documented change strategy for consistency")
    
    return recommendations if recommendations else ["Continue monitoring stakeholder feedback for strategic insights"]


def analyze_concern_themes(concerns):
    """Analyze common themes in stakeholder concerns"""
    if not concerns:
        return {}
    
    themes = {
        'communication': 0,
        'timeline': 0,
        'resources': 0,
        'training': 0,
        'process': 0,
        'technology': 0,
        'role_impact': 0
    }
    
    for concern in concerns:
        concern_text = concern.concern.lower()
        if any(word in concern_text for word in ['when', 'timeline', 'date', 'schedule']):
            themes['timeline'] += 1
        if any(word in concern_text for word in ['how', 'training', 'learn', 'support']):
            themes['training'] += 1
        if any(word in concern_text for word in ['what', 'why', 'information', 'communication']):
            themes['communication'] += 1
        if any(word in concern_text for word in ['cost', 'budget', 'resource', 'money']):
            themes['resources'] += 1
        if any(word in concern_text for word in ['process', 'procedure', 'workflow']):
            themes['process'] += 1
        if any(word in concern_text for word in ['system', 'technology', 'software', 'tool']):
            themes['technology'] += 1
        if any(word in concern_text for word in ['job', 'role', 'responsibility', 'impact']):
            themes['role_impact'] += 1
    
    return {k: v for k, v in themes.items() if v > 0}


def generate_sentiment_insights(sentiment_analysis, total_responses):
    """Generate insights based on sentiment distribution"""
    insights = []
    cautious_percentage = (sentiment_analysis.get("cautious", 0) / total_responses) * 100
    
    if cautious_percentage > 70:
        insights.append("⚠️ High resistance detected (>70% cautious) - Implement intensive change support and address specific concerns immediately")
    elif cautious_percentage > 50:
        insights.append("🔍 Moderate resistance (>50% cautious) - Increase communication frequency and provide more detailed information")
    elif cautious_percentage < 20:
        insights.append("🚀 Strong change readiness (<20% cautious) - Accelerate implementation and leverage enthusiastic stakeholders as champions")
    else:
        insights.append("⚖️ Balanced sentiment - Maintain current communication approach while monitoring for shifts")
    
    return insights


def generate_mental_model_insights(model_counts, total_responses):
    """Generate insights based on mental model distribution"""
    insights = []
    
    if not model_counts:
        return insights
    
    # Find dominant mental models (>30% of responses)
    dominant_models = {k: v for k, v in model_counts.items() if (v / total_responses) > 0.3}
    
    if len(dominant_models) == 1:
        model_name = list(dominant_models.keys())[0]
        percentage = (list(dominant_models.values())[0] / total_responses) * 100
        insights.append(f"🎯 Dominant {model_name} mindset ({percentage:.0f}%) - Tailor all communications to this mental model's preferences")
    elif len(dominant_models) > 1:
        insights.append("🎭 Multiple dominant mental models - Create segmented communication strategies for different stakeholder groups")
    else:
        insights.append("🌈 Diverse mental model distribution - Use varied communication approaches and multiple channels")
    
    return insights


def generate_concern_insights(concern_themes):
    """Generate insights based on concern themes"""
    insights = []
    
    if not concern_themes:
        return insights
    
    top_theme = max(concern_themes, key=concern_themes.get)
    theme_count = concern_themes[top_theme]
    
    theme_actions = {
        'communication': "📢 Focus on clearer, more frequent communication and information sharing",
        'timeline': "⏰ Provide detailed project timelines and milestone updates",
        'training': "🎓 Develop comprehensive training programs and support resources",
        'resources': "💰 Address resource allocation concerns and budget transparency",
        'process': "⚙️ Document and communicate new processes clearly",
        'technology': "💻 Provide technology training and technical support",
        'role_impact': "👥 Clarify role changes and career impact communications"
    }
    
    if theme_count > 1:
        insights.append(f"{theme_actions.get(top_theme, f'Address {top_theme} concerns')} - This is the top concern area")
    
    return insights


def generate_focus_insights(focus_counts, total_responses):
    """Generate insights based on stakeholder focus areas"""
    insights = []
    
    if not focus_counts or total_responses == 0:
        return insights
    
    top_focus = max(focus_counts, key=focus_counts.get)
    focus_percentage = (focus_counts[top_focus] / total_responses) * 100
    
    if focus_percentage > 40:
        focus_strategies = {
            "people": "👥 People-first approach needed - Emphasize team impact, relationships, and collaborative benefits",
            "process": "⚙️ Process-focused strategy - Provide detailed procedures, documentation, and structured implementation",
            "proof": "📊 Evidence-based approach - Share data, metrics, case studies, and concrete proof points",
            "possibilities": "🌟 Innovation-focused strategy - Highlight future opportunities, creative potential, and breakthrough possibilities"
        }
        insights.append(focus_strategies.get(top_focus, f"Focus on {top_focus}-oriented communications"))
    
    return insights

@app.route("/opt-out/<int:response_id>")
def opt_out(response_id):
    """Allow stakeholders to opt out"""
    response = StakeholderResponse.query.get_or_404(response_id)
    response.opted_out = True
    db.session.commit()
    return render_template("opt_out_success.html")

@app.route("/manager/concern/<int:concern_id>/assign", methods=["POST"])
def assign_concern_to_sme(concern_id):
    """Assign a concern to an SME"""
    sme_name = request.json.get('sme_name')
    
    response = StakeholderResponse.query.get_or_404(concern_id)
    
    # Create concern assignment record
    assignment = ConcernAssignment()
    assignment.stakeholder_response_id = response.id
    assignment.project_id = response.project_id
    assignment.concern_text = response.concern
    assignment.assigned_by = "Change Manager"
    assignment.sme_name = sme_name
    assignment.status = "pending"
    
    db.session.add(assignment)
    db.session.commit()
    
    return jsonify({"status": "success", "message": "Concern assigned to SME"})

@app.route("/manager/concerns")
def concerns_management():
    """Concerns management dashboard"""
    project = get_active_project()
    
    if project:
        responses = StakeholderResponse.query.filter_by(project_id=project.id).filter(StakeholderResponse.concern.isnot(None)).all()
        assignments = ConcernAssignment.query.filter_by(project_id=project.id).filter(ConcernAssignment.status != 'archived').all()
    else:
        responses = StakeholderResponse.query.filter(StakeholderResponse.concern.isnot(None)).all()
        assignments = ConcernAssignment.query.filter(ConcernAssignment.status != 'archived').all()
    
    projects = ChangeProject.query.filter_by(is_active=True).all()
    
    return render_template("concerns_management.html", 
                         responses=responses, 
                         assignments=assignments,
                         projects=projects,
                         current_project=project)

@app.route("/manager/concerns/assign", methods=["POST"])
def assign_concern():
    """Assign a concern to an SME or respond directly as manager"""
    response_id = request.form.get('response_id')
    assignment_type = request.form.get('assignment_type')  # 'sme' or 'manager'
    
    response = StakeholderResponse.query.get_or_404(response_id)
    
    if assignment_type == 'sme':
        # Assign to SME
        sme_name = request.form.get('sme_name')
        sme_email = request.form.get('sme_email')
        assigned_by = request.form.get('assigned_by', 'Change Manager')
        
        assignment = ConcernAssignment()
        assignment.stakeholder_response_id = response.id
        assignment.project_id = response.project_id
        assignment.concern_text = response.concern
        assignment.assigned_by = assigned_by
        assignment.sme_name = sme_name
        assignment.sme_email = sme_email
        assignment.status = "pending"
        
        db.session.add(assignment)
        db.session.commit()
        
        # Send email notification to SME
        if sme_email:
            project = ChangeProject.query.get(response.project_id)
            email_sent = send_concern_assignment_email(
                sme_email=sme_email,
                sme_name=sme_name,
                concern_text=response.concern,
                project_name=project.name if project else "Change Project",
                assignment_id=assignment.id,
                stakeholder_name=response.name
            )
            
            if email_sent:
                assignment.email_sent = True
                assignment.email_sent_at = datetime.utcnow()
                db.session.commit()
                flash(f"Concern assigned to {sme_name} and email sent successfully!", "success")
            else:
                flash(f"Concern assigned to {sme_name}, but email notification failed.", "warning")
        else:
            flash(f"Concern assigned to {sme_name} (no email provided).", "success")
    
    elif assignment_type == 'manager':
        # Manager responds directly
        manager_response = request.form.get('manager_response')
        assigned_by = request.form.get('assigned_by', 'Change Manager')
        
        assignment = ConcernAssignment()
        assignment.stakeholder_response_id = response.id
        assignment.project_id = response.project_id
        assignment.concern_text = response.concern
        assignment.assigned_by = assigned_by
        assignment.response_text = manager_response
        assignment.response_method = "manager"
        assignment.status = "resolved"
        assignment.responded_at = datetime.utcnow()
        
        db.session.add(assignment)
        db.session.commit()
        
        flash("Response added successfully by change manager!", "success")
    
    return redirect(url_for('concerns_management', project_id=response.project_id))

@app.route("/sme/respond/<int:assignment_id>", methods=["GET", "POST"])
def sme_respond(assignment_id):
    """SME response interface"""
    assignment = ConcernAssignment.query.get_or_404(assignment_id)
    
    if request.method == "POST":
        response_text = request.form.get('response_text')
        
        if response_text:
            assignment.response_text = response_text
            assignment.response_method = "sme"
            assignment.status = "responded"
            assignment.responded_at = datetime.utcnow()
            
            db.session.commit()
            
            return render_template("sme_response_success.html", assignment=assignment)
        else:
            flash("Please provide a response to the concern.", "error")
    
    return render_template("sme_response_form.html", assignment=assignment)

@app.route("/manager/concerns/<int:assignment_id>/resolve", methods=["POST"])
def resolve_concern(assignment_id):
    """Mark a concern as resolved"""
    assignment = ConcernAssignment.query.get_or_404(assignment_id)
    assignment.status = "resolved"
    db.session.commit()
    
    return jsonify({"status": "success", "message": "Concern marked as resolved"})

@app.route("/manager/concerns/<int:assignment_id>/reopen", methods=["POST"])
def reopen_concern(assignment_id):
    """Reopen a resolved concern"""
    assignment = ConcernAssignment.query.get_or_404(assignment_id)
    assignment.status = "responded"  # Change back to responded status
    db.session.commit()
    
    return jsonify({"status": "success", "message": "Concern reopened for further discussion"})

@app.route("/manager/concerns/<int:assignment_id>/archive", methods=["POST"])
def archive_concern(assignment_id):
    """Archive a concern (soft delete)"""
    assignment = ConcernAssignment.query.get_or_404(assignment_id)
    assignment.status = "archived"
    db.session.commit()
    
    return jsonify({"status": "success", "message": "Concern archived"})

@app.route("/manager/concerns/<int:response_id>/delete", methods=["DELETE"])
def delete_unassigned_concern(response_id):
    """Delete an unassigned concern"""
    try:
        # Check if the concern has any assignments
        response = StakeholderResponse.query.get_or_404(response_id)
        assignments = ConcernAssignment.query.filter_by(stakeholder_response_id=response_id).all()
        
        if assignments:
            return jsonify({
                'status': 'error', 
                'message': 'Cannot delete a concern that has been assigned. Please archive it instead.'
            }), 400
        
        # Only delete the concern text, keep the stakeholder response
        response.concern = None
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Concern deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route("/manager/concerns/update-response", methods=["POST"])
def update_response():
    """Update an existing response"""
    assignment_id = request.form.get('assignment_id')
    updated_response = request.form.get('updated_response')
    
    if not assignment_id or not updated_response:
        flash("Missing required information", "error")
        return redirect(url_for('concerns_management'))
    
    assignment = ConcernAssignment.query.get_or_404(assignment_id)
    assignment.response_text = updated_response
    assignment.responded_at = datetime.utcnow()  # Update timestamp
    
    db.session.commit()
    flash("Response updated successfully!", "success")
    
    return redirect(url_for('concerns_management', project_id=assignment.project_id))

@app.route("/manager/concerns/answer-directly", methods=["POST"])
def answer_directly():
    """Change manager answers a pending assignment directly"""
    assignment_id = request.form.get('assignment_id')
    direct_response = request.form.get('direct_response')
    
    if not assignment_id or not direct_response:
        flash("Missing required information", "error")
        return redirect(url_for('concerns_management'))
    
    assignment = ConcernAssignment.query.get_or_404(assignment_id)
    
    # Update the assignment with manager's direct response
    assignment.response_text = direct_response
    assignment.response_method = "manager"
    assignment.status = "resolved"
    assignment.responded_at = datetime.utcnow()
    
    db.session.commit()
    flash("You have successfully answered the concern directly!", "success")
    
    return redirect(url_for('concerns_management', project_id=assignment.project_id))

@app.route('/api/ai-suggest-response-assignment', methods=['POST'])
def ai_suggest_response_assignment():
    """API endpoint for AI-powered response suggestions for assignments"""
    data = request.get_json()
    assignment_id = data.get('assignment_id')
    
    if not assignment_id:
        return jsonify({"error": "Assignment ID is required"}), 400
    
    # Get the assignment and related stakeholder response
    assignment = ConcernAssignment.query.get_or_404(assignment_id)
    stakeholder_response = assignment.stakeholder_response
    
    # Get project data for AI context
    project = assignment.project
    project_data = {
        'name': project.name,
        'description': project.description,
        'change_strategy': project.change_strategy,
        'key_messages': project.key_messages,
        'project_start_date': project.project_start_date,
        'communication_start_date': project.communication_start_date,
        'go_live_date': project.go_live_date,
        'assessment_end_date': project.assessment_end_date
    }
    
    # Get existing FAQs for context
    existing_faqs = get_existing_faqs(project.id)
    
    # Generate AI response suggestion
    ai_suggestion = generate_ai_response_suggestion(
        concern_text=assignment.concern_text,
        stakeholder_mental_model=stakeholder_response.mental_model,
        project_data=project_data,
        existing_faqs=existing_faqs
    )
    
    return jsonify(ai_suggestion)

@app.route('/manager/concerns/add-to-faq', methods=['POST'])
def add_to_faq():
    """Add a resolved concern and response to the FAQ database"""
    data = request.get_json()
    assignment_id = data.get('assignment_id')
    question = data.get('question')
    answer = data.get('answer')
    
    if not assignment_id or not question or not answer:
        return jsonify({"error": "Missing required information"}), 400
    
    # Get the assignment to ensure it exists and get project info
    assignment = ConcernAssignment.query.get_or_404(assignment_id)
    
    # Check if this assignment already has an FAQ entry
    existing_faq = FAQEntry.query.filter_by(concern_assignment_id=assignment_id).first()
    if existing_faq:
        return jsonify({"error": "This concern has already been added to the FAQ database"}), 400
    
    # Create new FAQ entry
    faq_entry = FAQEntry(
        project_id=assignment.project_id,
        question=question.strip(),
        answer=answer.strip(),
        concern_assignment_id=assignment_id,
        category="Stakeholder Concerns"
    )
    
    try:
        db.session.add(faq_entry)
        db.session.commit()
        return jsonify({"status": "success", "message": "Successfully added to FAQ database"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500

@app.route("/manager/export")
def export_data():
    """Export stakeholder data for analysis"""
    responses = StakeholderResponse.query.filter_by(opted_out=False).all()
    
    export_data = []
    for response in responses:
        export_data.append({
            'name': response.name,
            'email': response.email,
            'department': response.department,
            'mental_model': response.mental_model,
            'feeling': response.feeling,
            'style': response.style,
            'focus_areas': response.focus_areas,
            'concern': response.concern,
            'frequency_preference': response.frequency_preference,
            'timestamp': response.timestamp.isoformat()
        })
    
    return jsonify(export_data)

@app.route("/manager/projects")
def project_management():
    """Project management page"""
    projects = ChangeProject.query.all()
    
    # Calculate statistics
    total_responses = sum(len(project.responses) for project in projects)
    active_projects = sum(1 for project in projects if project.is_active)
    
    return render_template("project_management_simple.html", 
                         projects=projects,
                         total_responses=total_responses,
                         active_projects=active_projects)

@app.route("/manager/projects/create", methods=["GET", "POST"])
def create_project():
    """Create new change project"""
    if request.method == "POST":
        project = ChangeProject()
        project.name = request.form.get("name")
        project.description = request.form.get("description")
        
        # Strategy Components (from uploads or text input)
        project.bcip = request.form.get("bcip")
        project.change_logic = request.form.get("change_logic")
        project.change_story = request.form.get("change_story")
        project.change_strategy = request.form.get("change_strategy")
        project.key_messages = request.form.get("key_messages")
        project.is_active = True
        
        # Handle strategy component file uploads
        component_files = {
            'bcip_document': ('bcip_document_path', 'bcip_document_name'),
            'change_logic_document': ('change_logic_document_path', 'change_logic_document_name'),
            'change_story_document': ('change_story_document_path', 'change_story_document_name'),
            'change_strategy_document': ('change_strategy_document_path', 'change_strategy_document_name'),
            'key_messages_document': ('key_messages_document_path', 'key_messages_document_name')
        }
        
        for file_key, (path_attr, name_attr) in component_files.items():
            if file_key in request.files:
                file = request.files[file_key]
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Create unique filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    unique_filename = f"{timestamp}_{filename}"
                    file_path = os.path.join(app.config.get('UPLOAD_FOLDER', 'uploads'), unique_filename)
                    
                    # Ensure upload directory exists
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    file.save(file_path)
                    
                    # Store file information in project
                    setattr(project, path_attr, file_path)
                    setattr(project, name_attr, filename)
        
        # Handle key dates
        try:
            start_date = request.form.get("project_start_date")
            if start_date:
                project.project_start_date = parser.parse(start_date).date()
            
            go_live = request.form.get("go_live_date")
            if go_live:
                project.go_live_date = parser.parse(go_live).date()
            
            comm_start = request.form.get("communication_start_date")
            if comm_start:
                project.communication_start_date = parser.parse(comm_start).date()
            
            assess_end = request.form.get("assessment_end_date")
            if assess_end:
                project.assessment_end_date = parser.parse(assess_end).date()
        except ValueError:
            flash("Invalid date format. Please use valid dates.", "error")
            return render_template("create_project.html")
        
        # Handle file upload
        if 'strategy_document' in request.files:
            file = request.files['strategy_document']
            if file and file.filename and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
                filename = timestamp + filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                # Extract text content from PDF
                extracted_text = extract_text_from_pdf(file_path)
                if not project.change_strategy:
                    project.change_strategy = extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text
                
                project.strategy_document_path = file_path
                project.strategy_document_name = file.filename
        
        try:
            db.session.add(project)
            db.session.commit()
            flash(f"Project '{project.name}' created successfully!", "success")
            return redirect(url_for("project_management"))
        except Exception as e:
            db.session.rollback()
            flash("Error creating project. Please try again.", "error")
    
    return render_template("create_project.html")

@app.route("/manager/projects/<int:project_id>/edit", methods=["GET", "POST"])
def edit_project(project_id):
    """Edit an existing change project"""
    project = ChangeProject.query.get_or_404(project_id)

    if request.method == "POST":
        project.name = request.form.get("name")
        project.description = request.form.get("description")

        project.bcip = request.form.get("bcip")
        project.change_logic = request.form.get("change_logic")
        project.change_story = request.form.get("change_story")
        project.change_strategy = request.form.get("change_strategy")
        project.key_messages = request.form.get("key_messages")

        component_files = {
            'bcip_document': ('bcip_document_path', 'bcip_document_name', 'bcip'),
            'change_logic_document': ('change_logic_document_path', 'change_logic_document_name', 'change_logic'),
            'change_story_document': ('change_story_document_path', 'change_story_document_name', 'change_story'),
            'change_strategy_document': ('change_strategy_document_path', 'change_strategy_document_name', 'change_strategy'),
            'key_messages_document': ('key_messages_document_path', 'key_messages_document_name', 'key_messages')
        }

        files_to_delete = []

        removed_files = request.form.getlist("remove_files")
        for file_key, (path_attr, name_attr, text_attr) in component_files.items():
            if file_key in removed_files:
                old_path = getattr(project, path_attr)
                if old_path:
                    files_to_delete.append(old_path)
                setattr(project, path_attr, None)
                setattr(project, name_attr, None)

        for file_key, (path_attr, name_attr, text_attr) in component_files.items():
            if file_key in request.files:
                file = request.files[file_key]
                if file and file.filename and allowed_file(file.filename):
                    old_path = getattr(project, path_attr)
                    if old_path:
                        files_to_delete.append(old_path)
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    unique_filename = f"{timestamp}_{filename}"
                    file_path = os.path.join(app.config.get('UPLOAD_FOLDER', 'uploads'), unique_filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    file.save(file_path)
                    setattr(project, path_attr, file_path)
                    setattr(project, name_attr, filename)

        try:
            start_date = request.form.get("project_start_date")
            project.project_start_date = parser.parse(start_date).date() if start_date else None

            go_live = request.form.get("go_live_date")
            project.go_live_date = parser.parse(go_live).date() if go_live else None

            comm_start = request.form.get("communication_start_date")
            project.communication_start_date = parser.parse(comm_start).date() if comm_start else None

            assess_end = request.form.get("assessment_end_date")
            project.assessment_end_date = parser.parse(assess_end).date() if assess_end else None
        except ValueError:
            flash("Invalid date format. Please use valid dates.", "error")
            return render_template("edit_project.html", project=project)

        if 'strategy_document' in request.files:
            file = request.files['strategy_document']
            if file and file.filename and file.filename != '' and allowed_file(file.filename):
                old_path = project.strategy_document_path
                if old_path:
                    files_to_delete.append(old_path)
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
                filename = timestamp + filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                if file_path.endswith('.pdf'):
                    extracted_text = extract_text_from_pdf(file_path)
                    if not project.change_strategy:
                        project.change_strategy = extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text
                project.strategy_document_path = file_path
                project.strategy_document_name = file.filename

        if 'remove_strategy_document' in request.form:
            old_path = project.strategy_document_path
            if old_path:
                files_to_delete.append(old_path)
            project.strategy_document_path = None
            project.strategy_document_name = None

        try:
            db.session.commit()
            for f in files_to_delete:
                if os.path.exists(f):
                    os.remove(f)
            flash(f"Project '{project.name}' updated successfully!", "success")
            return redirect(url_for("project_management"))
        except Exception as e:
            db.session.rollback()
            flash("Error updating project. Please try again.", "error")

    return render_template("edit_project.html", project=project)

@app.route("/manager/projects/<int:project_id>/remove-file/<file_type>", methods=["POST"])
def remove_project_file(project_id, file_type):
    """Remove a specific file from a project"""
    project = ChangeProject.query.get_or_404(project_id)

    file_map = {
        'bcip_document': ('bcip_document_path', 'bcip_document_name'),
        'change_logic_document': ('change_logic_document_path', 'change_logic_document_name'),
        'change_story_document': ('change_story_document_path', 'change_story_document_name'),
        'change_strategy_document': ('change_strategy_document_path', 'change_strategy_document_name'),
        'key_messages_document': ('key_messages_document_path', 'key_messages_document_name'),
        'strategy_document': ('strategy_document_path', 'strategy_document_name'),
    }

    if file_type in file_map:
        path_attr, name_attr = file_map[file_type]
        old_path = getattr(project, path_attr)
        if old_path and os.path.exists(old_path):
            os.remove(old_path)
        setattr(project, path_attr, None)
        setattr(project, name_attr, None)
        db.session.commit()

    return jsonify({"success": True})

@app.route("/manager/projects/<int:project_id>/document")
def view_project_document(project_id):
    """View uploaded project document"""
    project = ChangeProject.query.get_or_404(project_id)
    if project.strategy_document_path and os.path.exists(project.strategy_document_path):
        return send_file(project.strategy_document_path, as_attachment=False)
    else:
        flash("Document not found", "error")
        return redirect(url_for("project_management"))

@app.route("/manager/projects/<int:project_id>/toggle", methods=["POST"])
def toggle_project_status(project_id):
    """Toggle project active status"""
    project = ChangeProject.query.get_or_404(project_id)
    project.is_active = not project.is_active
    db.session.commit()
    
    status = "activated" if project.is_active else "deactivated"
    return jsonify({"status": "success", "message": f"Project {status}"})

@app.route("/manager/generate-faq")
def generate_faq():
    """Generate FAQ based on common concerns"""
    active_project = get_active_project()
    
    if active_project:
        responses = StakeholderResponse.query.filter(
            StakeholderResponse.concern.isnot(None),
            StakeholderResponse.project_id == active_project.id
        ).all()
    else:
        responses = StakeholderResponse.query.filter(StakeholderResponse.concern.isnot(None)).all()
    
    concerns_by_category = {}
    for response in responses:
        if response.concern and response.concern.strip():
            # Simple categorization based on focus areas
            category = "General"
            if response.focus_areas:
                primary_focus = response.focus_areas.split(',')[0].strip()
                if primary_focus == "proof":
                    category = "Evidence & Data"
                elif primary_focus == "process":
                    category = "Implementation & Process"
                elif primary_focus == "people":
                    category = "People & Relationships"
                elif primary_focus == "possibilities":
                    category = "Vision & Future"
            
            if category not in concerns_by_category:
                concerns_by_category[category] = []
            concerns_by_category[category].append(response.concern)
    
    return render_template("faq_generator.html", concerns_by_category=concerns_by_category)

@app.route("/api/stats")
def get_stats():
    """API endpoint for dashboard statistics"""
    responses = StakeholderResponse.query.filter_by(opted_out=False).all()
    
    stats = {
        'total_responses': len(responses),
        'model_distribution': {},
        'focus_distribution': {"proof": 0, "process": 0, "people": 0, "possibilities": 0},
        'sentiment_distribution': {"eager": 0, "cautious": 0}
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
        
        # Sentiment
        if response.feeling:
            stats['sentiment_distribution'][response.feeling] += 1
    
    return jsonify(stats)

@app.route('/api/ai-suggest-response', methods=['POST'])
def ai_suggest_response():
    """API endpoint for AI-powered response suggestions"""
    data = request.get_json()
    response_id = data.get('response_id')
    
    if not response_id:
        return jsonify({"error": "Response ID is required"}), 400
    
    # Get the stakeholder response
    stakeholder_response = StakeholderResponse.query.get_or_404(response_id)
    
    # Get project data for AI context
    project = stakeholder_response.project
    project_data = {
        'name': project.name,
        'description': project.description,
        'change_strategy': project.change_strategy,
        'key_messages': project.key_messages,
        'project_start_date': project.project_start_date,
        'communication_start_date': project.communication_start_date,
        'go_live_date': project.go_live_date,
        'assessment_end_date': project.assessment_end_date
    }
    
    # Get existing FAQs for context
    existing_faqs = get_existing_faqs(project.id)
    
    # Generate AI response suggestion
    ai_suggestion = generate_ai_response_suggestion(
        concern_text=stakeholder_response.concern,
        stakeholder_mental_model=stakeholder_response.mental_model,
        project_data=project_data,
        existing_faqs=existing_faqs
    )
    
    return jsonify(ai_suggestion)

@app.route("/stakeholder/<int:response_id>")
def stakeholder_portal(response_id):
    """Stakeholder portal to view assessment history"""
    response = StakeholderResponse.query.get_or_404(response_id)
    
    # Get all responses from this stakeholder (by email)
    stakeholder_history = StakeholderResponse.query.filter_by(email=response.email).order_by(StakeholderResponse.timestamp.desc()).all()
    
    # Get any concern assignments for this stakeholder
    concern_assignments = ConcernAssignment.query.filter_by(stakeholder_response_id=response_id).all()
    
    return render_template("stakeholder_portal.html",
                         response=response,
                         history=stakeholder_history,
                         concern_assignments=concern_assignments)

@app.route("/manager/communications")
def communications_center():
    """Communication center for sending personalized messages"""
    project = get_active_project()
    
    if project:
        responses = StakeholderResponse.query.filter_by(project_id=project.id, opted_out=False).all()
    else:
        responses = StakeholderResponse.query.filter_by(opted_out=False).all()
    
    projects = ChangeProject.query.filter_by(is_active=True).all()
    
    return render_template("communications_center.html",
                         responses=responses,
                         projects=projects,
                         selected_project=project)

@app.route("/manager/send-email", methods=["POST"])
def send_personalized_email():
    """Send personalized email to stakeholders"""
    stakeholder_ids = request.form.getlist('stakeholder_ids')
    message_type = request.form.get('message_type')
    custom_message = request.form.get('custom_message', '')
    
    if not stakeholder_ids:
        flash("Please select at least one stakeholder", "error")
        return redirect(url_for('communications_center'))
    
    sent_count = 0
    for stakeholder_id in stakeholder_ids:
        response = StakeholderResponse.query.get(stakeholder_id)
        if response and response.email:
            sent_count += 1
    
    flash(f"Successfully prepared {sent_count} personalized emails for sending", "success")
    return redirect(url_for('communications_center'))

@app.route("/api/generate-strategy", methods=["POST"])
def generate_strategy():
    """API endpoint for AI-powered strategy generation from meeting transcriptions"""
    try:
        data = request.get_json()
        transcription = data.get('transcription', '')
        project_name = data.get('project_name', '')
        project_description = data.get('project_description', '')
        
        if not transcription:
            return jsonify({'error': 'Meeting transcription is required'}), 400
        
        # Import here to avoid circular import issues
        from strategy_generator import generate_change_strategy_from_transcription, validate_transcription
        
        # Validate transcription
        is_valid, validation_message = validate_transcription(transcription)
        if not is_valid:
            return jsonify({'error': validation_message}), 400
        
        # Generate strategy using ChatGPT
        result = generate_change_strategy_from_transcription(
            transcription, 
            project_name, 
            project_description
        )
        
        if result['success']:
            return jsonify(result['components'])
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': f'Strategy generation failed: {str(e)}'}), 500

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
