from flask import render_template, request, redirect, url_for, flash
from app import app, db
from forms import AssessmentForm
from mental_models import calculate_mental_model, get_mental_model_data, MENTAL_MODELS
from datetime import datetime

@app.route('/')
def index():
    """Home page with introduction to the assessment"""
    return render_template('index.html')

@app.route('/assessment', methods=['GET', 'POST'])
def assessment():
    """Assessment questionnaire page"""
    from models import AssessmentResponse
    
    form = AssessmentForm()
    
    if form.validate_on_submit():
        # Calculate mental model based on responses
        mental_model_id = calculate_mental_model(
            form.question1.data,
            form.question2.data, 
            form.question3.data
        )
        
        # Store response in database
        response = AssessmentResponse(
            question1_response=form.question1.data,
            question2_response=form.question2.data,
            question3_response=form.question3.data,
            additional_comments=form.additional_comments.data,
            mental_model_id=mental_model_id,
            ip_address=request.remote_addr
        )
        
        try:
            db.session.add(response)
            db.session.commit()
            
            # Redirect to results page
            return redirect(url_for('result', model_id=mental_model_id, response_id=response.id))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error saving assessment response: {e}")
            flash('There was an error processing your assessment. Please try again.', 'error')
    
    return render_template('assessment.html', form=form)

@app.route('/result/<model_id>')
@app.route('/result/<model_id>/<int:response_id>')
def result(model_id, response_id=None):
    """Display assessment results"""
    from models import AssessmentResponse
    
    mental_model_data = get_mental_model_data(model_id)
    
    response = None
    if response_id:
        response = AssessmentResponse.query.get_or_404(response_id)
    
    return render_template('result.html', 
                         mental_model=mental_model_data,
                         model_id=model_id,
                         response=response)

@app.route('/admin')
def admin():
    """Admin dashboard to view all responses"""
    from models import AssessmentResponse
    
    responses = AssessmentResponse.query.order_by(AssessmentResponse.timestamp.desc()).all()
    
    # Calculate statistics
    total_responses = len(responses)
    model_counts = {}
    
    for response in responses:
        model_id = response.mental_model_id
        if model_id in model_counts:
            model_counts[model_id] += 1
        else:
            model_counts[model_id] = 1
    
    # Sort by count
    sorted_models = sorted(model_counts.items(), key=lambda x: x[1], reverse=True)
    
    return render_template('admin.html', 
                         responses=responses,
                         total_responses=total_responses,
                         model_counts=sorted_models,
                         mental_models=MENTAL_MODELS)

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('base.html', 
                         content="<div class='container mt-5'><div class='alert alert-warning'><h4>Page Not Found</h4><p>The page you're looking for doesn't exist.</p><a href='/' class='btn btn-primary'>Return Home</a></div></div>"), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return render_template('base.html',
                         content="<div class='container mt-5'><div class='alert alert-danger'><h4>Internal Error</h4><p>An unexpected error occurred. Please try again later.</p><a href='/' class='btn btn-primary'>Return Home</a></div></div>"), 500
