from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.utils import secure_filename
import os
import PyPDF2
from dateutil import parser
import uuid
from email_service import send_concern_assignment_email, send_response_notification_email
from ai_response_service import generate_ai_response_suggestion, get_existing_faqs

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "change-management-key")

# File upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
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
    change_strategy = db.Column(db.Text)
    key_messages = db.Column(db.Text)
    
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
    
    return render_template("stakeholder_form.html", project=project)

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
                             response_id=response.id)
    except Exception as e:
        db.session.rollback()
        flash("Error saving your response. Please try again.", "error")
        return redirect(url_for("index"))

@app.route("/manager")
def manager_dashboard():
    """Change manager dashboard"""
    # Get all projects for dropdown
    projects = ChangeProject.query.filter_by(is_active=True).all()
    selected_project_id = request.args.get('project_id', type=int)
    
    # Filter responses by project if specified
    if selected_project_id:
        responses = StakeholderResponse.query.filter_by(opted_out=False, project_id=selected_project_id).all()
        selected_project = ChangeProject.query.get(selected_project_id)
    else:
        responses = StakeholderResponse.query.filter_by(opted_out=False).all()
        selected_project = None
    
    # Calculate statistics
    total_responses = len(responses)
    model_counts = {}
    focus_counts = {"proof": 0, "process": 0, "people": 0, "possibilities": 0}
    # Get concerns with their assignment statuses (limit to recent ones for dashboard)
    concerns = [response for response in responses if response.concern and response.concern.strip()]
    # Sort by timestamp descending to show most recent first
    concerns = sorted(concerns, key=lambda x: x.timestamp, reverse=True)
    
    # Debug: Print actual count and details
    print(f"DEBUG: Found {len(concerns)} concerns for dashboard")
    for i, concern in enumerate(concerns):
        print(f"DEBUG: Concern {i+1}: ID={concern.id}, Name={concern.name}, Text={concern.concern[:50]}...")
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
        
        # Collect concerns
        if response.concern and response.concern.strip():
            concerns.append({
                'name': response.name,
                'concern': response.concern,
                'model': response.mental_model,
                'id': response.id,
                'department': response.department,
                'timestamp': response.timestamp,
                'project_name': response.project.name
            })
    
    # Generate engagement recommendations
    recommendations = generate_engagement_recommendations(model_counts, focus_counts, sentiment_analysis, total_responses)
    
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

def generate_engagement_recommendations(model_counts, focus_counts, sentiment_analysis, total_responses):
    """Generate actionable recommendations based on stakeholder data"""
    recommendations = []
    
    if total_responses == 0:
        return ["Start gathering stakeholder feedback to generate insights"]
    
    # Sentiment-based recommendations
    cautious_percentage = (sentiment_analysis.get("cautious", 0) / total_responses) * 100
    if cautious_percentage > 60:
        recommendations.append("High caution levels detected - increase evidence sharing and address specific concerns")
    elif cautious_percentage < 20:
        recommendations.append("Strong enthusiasm detected - leverage eager stakeholders as change champions")
    
    # Focus area recommendations
    total_focus = sum(focus_counts.values())
    if total_focus > 0:
        proof_percentage = (focus_counts["proof"] / total_focus) * 100
        people_percentage = (focus_counts["people"] / total_focus) * 100
        
        if proof_percentage > 40:
            recommendations.append("Data-driven stakeholders dominate - prepare detailed business case and metrics")
        if people_percentage > 40:
            recommendations.append("People-focused team - emphasize impact on relationships and team dynamics")
        if focus_counts["process"] > focus_counts["possibilities"]:
            recommendations.append("Process-oriented team - provide clear implementation roadmaps and timelines")
    
    # Mental model specific recommendations
    if model_counts.get("The Sceptic", 0) > 0:
        recommendations.append("Address sceptical stakeholders with evidence and risk mitigation plans")
    if model_counts.get("The Facilitator", 0) + model_counts.get("The Humanitarian", 0) > total_responses * 0.3:
        recommendations.append("Leverage collaborative stakeholders to build consensus and support others")
    
    return recommendations

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
    project_id = request.args.get('project_id')
    
    if project_id:
        responses = StakeholderResponse.query.filter_by(project_id=project_id).filter(StakeholderResponse.concern.isnot(None)).all()
        project = ChangeProject.query.get_or_404(project_id)
        assignments = ConcernAssignment.query.filter_by(project_id=project_id).all()
    else:
        responses = StakeholderResponse.query.filter(StakeholderResponse.concern.isnot(None)).all()
        project = None
        assignments = ConcernAssignment.query.all()
    
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
        project.change_strategy = request.form.get("change_strategy")
        project.key_messages = request.form.get("key_messages")
        project.is_active = True
        
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
    project_id = request.args.get('project_id', type=int)
    
    if project_id:
        responses = StakeholderResponse.query.filter(
            StakeholderResponse.concern.isnot(None),
            StakeholderResponse.project_id == project_id
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

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
