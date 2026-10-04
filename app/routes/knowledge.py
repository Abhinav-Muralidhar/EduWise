from flask import Blueprint, request, jsonify, redirect, url_for, flash, session, current_app
from app.extensions import db
from app.models.knowledge_source import KnowledgeSource
from app.utils.decorators import login_required
from app.services.ingestion import ingest_knowledge_source

knowledge_bp = Blueprint('knowledge', __name__, url_prefix='/knowledge')

@knowledge_bp.route('/', methods=['GET'])
@login_required
def list_sources():
    """List all knowledge sources for current user."""
    user_id = session.get('user_id')
    sources = KnowledgeSource.query.filter_by(user_id=user_id).order_by(KnowledgeSource.created_at.desc()).all()
    return jsonify({
        'sources': [s.to_dict() for s in sources]
    })


@knowledge_bp.route('/upload', methods=['POST'])
@login_required
def upload_source():
    """Upload and ingest a document into user's knowledge base."""
    user_id = session.get('user_id')
    
    if 'file' not in request.files:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'No file uploaded.'}), 400
        flash('No file selected.', 'error')
        return redirect(url_for('dashboard.index'))
        
    file = request.files['file']
    if not file or file.filename == '':
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'No file selected.'}), 400
        flash('No file selected.', 'error')
        return redirect(url_for('dashboard.index'))
        
    title = request.form.get('title', '').strip()
    
    try:
        source = ingest_knowledge_source(user_id, file, title)
        msg = f"Successfully indexed '{source.title}' ({source.chunk_count} chunks ready for RAG)."
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': msg, 'source': source.to_dict()})
        flash(msg, 'success')
    except Exception as e:
        current_app.logger.exception("Knowledge ingestion failed: %s", e)
        err_msg = str(e) or "Failed to process and index document."
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': err_msg}), 500
        flash(err_msg, 'error')
        
    return redirect(url_for('dashboard.index'))


@knowledge_bp.route('/delete/<int:source_id>', methods=['POST'])
@login_required
def delete_source(source_id):
    """Delete a knowledge source and all its chunks."""
    user_id = session.get('user_id')
    source = KnowledgeSource.query.filter_by(id=source_id, user_id=user_id).first_or_404()
    
    try:
        title = source.title
        db.session.delete(source)
        db.session.commit()
        msg = f"Deleted knowledge source '{title}'."
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': msg})
        flash(msg, 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Failed to delete knowledge source: %s", e)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Failed to delete knowledge source.'}), 500
        flash('Failed to delete knowledge source.', 'error')
        
    return redirect(url_for('dashboard.index'))
