from flask import Blueprint, render_template, session, redirect, url_for, send_from_directory, current_app, request, jsonify
from app.models.resource import Resource
from app.utils.decorators import login_required
from app.extensions import db
import os

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    return render_template('index.html')

@dashboard_bp.route('/dashboard')
@login_required
def index():
    user_id = session['user_id']
    resources = Resource.query.filter_by(user_id=user_id).order_by(Resource.created_at.desc()).all()
    # Filter by resource type for tabs
    pptx_files = [r for r in resources if r.resource_type == 'pptx']
    pdf_files = [r for r in resources if r.resource_type == 'pdf']
    quizzes = [r for r in resources if r.resource_type == 'quiz']
    flashcards = [r for r in resources if r.resource_type == 'flashcard']
    
    return render_template('dashboard.html', 
                         resources=resources,
                         pptx_files=pptx_files,
                         pdf_files=pdf_files,
                         quizzes=quizzes,
                         flashcards=flashcards)

@dashboard_bp.route('/download/<int:resource_id>')
@login_required
def download(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    if resource.user_id != session['user_id']:
        return "Unauthorized", 403
    if resource.filename:
        return redirect(resource.filename)
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/keep-alive', methods=['GET'])
def keep_alive():
    """Endpoint for cron jobs (e.g. cron-job.org) to ping every 5-10 minutes
    to keep the server awake."""
    return jsonify({"status": "alive"}), 200

@dashboard_bp.route('/toggle_favorite/<int:resource_id>', methods=['POST'])
@login_required
def toggle_favorite(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    if resource.user_id != session['user_id']:
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    resource.is_favorite = not resource.is_favorite
    db.session.commit()
    return jsonify({"success": True, "is_favorite": resource.is_favorite})
