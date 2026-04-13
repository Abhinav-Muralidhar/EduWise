from flask import Blueprint, render_template, session, redirect, url_for, send_from_directory, current_app, request, jsonify
from app.models.resource import Resource
from app.utils.decorators import login_required
from app.extensions import db
import os
import requests as req
from flask import Response

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
    
    search_query = ''
    showing_favorites = False
    
    # Client-side JS handles filtering, fetch all entries
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
                         flashcards=flashcards,
                         search_query=search_query,
                         showing_favorites=showing_favorites)

@dashboard_bp.route('/download/<int:resource_id>')
@login_required
def download(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    if resource.user_id != session['user_id']:
        return "Unauthorized", 403
    
    if not resource.filename:
        return redirect(url_for('dashboard.index'))
    
    # Determine extension and mimetype
    ext = 'pptx' if resource.resource_type == 'pptx' else 'pdf'
    mimetype = (
        'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        if ext == 'pptx' else 'application/pdf'
    )
    
    # Clean filename from topic
    import re
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', resource.topic)[:50]
    download_name = f"{safe_name}.{ext}"
    
    # Proxy the file through our server
    try:
        response = req.get(resource.filename, timeout=30)
        return Response(
            response.content,
            mimetype=mimetype,
            headers={
                'Content-Disposition': f'attachment; filename="{download_name}"'
            }
        )
    except Exception as e:
        print(f"Download failed: {e}")
        return redirect(resource.filename)

@dashboard_bp.route('/keep-alive', methods=['GET'])
def keep_alive():
    """Endpoint for cron jobs (e.g. cron-job.org) to ping every 5-10 minutes
    to keep the server awake."""
    try:
        db.session.execute(db.text('SELECT 1'))
        db.session.commit()
    except Exception:
        db.session.rollback()
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
