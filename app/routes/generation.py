from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, send_file, session, jsonify
from werkzeug.utils import secure_filename
from app.utils.decorators import login_required
from app.utils.text import extract_text
from app.utils.resource_helper import save_resource_to_db
from app.services import gemini, pptx_builder, pdf_builder
from app.services.retrieval import get_relevant_chunks
from app.extensions import limiter

generation_bp = Blueprint('generation', __name__)
ALLOWED_UPLOAD_EXTENSIONS = {'.pdf', '.docx', '.txt'}


def _is_fetch_request():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _generation_error(message, status_code=503):
    if _is_fetch_request():
        return jsonify({"success": False, "message": message}), status_code
    flash(message, "danger")
    return redirect(url_for('dashboard.index'))


def _validate_non_empty_text(value, field_name):
    cleaned = (value or '').strip()
    if not cleaned:
        flash(f"{field_name} is required.", "danger")
        return None
    return cleaned


def _validate_upload(uploaded_file):
    if not uploaded_file or uploaded_file.filename == '':
        return None

    filename = secure_filename(uploaded_file.filename)
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    ext = f'.{ext}' if ext else ''

    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        flash("Unsupported file type. Please upload a PDF, DOCX, or TXT file.", "danger")
        return False

    return filename


def _get_rag_context_and_sources(user_id, query_text, knowledge_source_id=None):
    if not user_id or not knowledge_source_id:
        return None, []
    
    try:
        source_id = int(knowledge_source_id) if str(knowledge_source_id).isdigit() else None
    except Exception:
        source_id = None
        
    chunks = get_relevant_chunks(user_id=user_id, query=query_text, source_id=source_id, k=5)
    if not chunks:
        return None, []
        
    rag_context = "\n\n---\n\n".join(
        f"[Source Document: {c['source_title']} (Passage {c['chunk_index'] + 1})]\n{c['content']}"
        for c in chunks
    )
    source_titles = list({c['source_title'] for c in chunks})
    return rag_context, source_titles

@generation_bp.route('/generate', methods=['POST'])
@limiter.limit("10 per hour")
@login_required
def generate_pptx():
    try:
        raw_count = int(request.form.get('slide_count', 5))
        slide_count = max(3, min(raw_count, 10))
    except ValueError:
        slide_count = 5

    customization = {
        'resource_type': 'pptx',
        'topic': request.form.get('topic', 'Untitled'),
        'subtopics': request.form.get('subtopics', ''),
        'context': request.form.get('context', ''),
        'image_strategy': request.form.get('image_strategy', 'all_slides'),
        'intro_slide': request.form.get('intro_slide', 'false'),
        'thanks_slide': request.form.get('thanks_slide', 'false'),
        'theme_base': request.form.get('theme_base', 'ai_choice'),
        'font_style': request.form.get('font_style', 'ai_choice'),
        'bg_color': request.form.get('bg_color', '#FFFFFF'),
        'font_color': request.form.get('font_color', '#333333'),
        'accent_color': request.form.get('accent_color', '#007BFF'),
        'extra_instructions': request.form.get('extra_instructions', ''),
        'slide_count': str(slide_count),
        'visual_instructions': request.form.get('visual_instructions', '')
    }
    topic = _validate_non_empty_text(customization['topic'], "Topic")
    if topic is None:
        return redirect(url_for('dashboard.index'))
    customization['topic'] = topic

    try:
        user_id = session.get('user_id')
        ks_id = request.form.get('knowledge_source_id')
        rag_context, _ = _get_rag_context_and_sources(user_id, topic, ks_id)

        theme_data = gemini.get_dynamic_theme(topic, customization)
        if not theme_data:
            theme_data = {
                'font-title': 'Roboto', 'font-body': 'Roboto',
                'font-color-title': '#000000', 'font-color-body': '#333333',
                'bg-color': '#FFFFFF', 'accent-color': '#007BFF'
            }

        slides_data = gemini.generate_slide_content(topic, customization, theme_data, rag_context=rag_context)
        if not slides_data:
            return _generation_error("We couldn't generate slides right now. Please try again in a moment.")
        
        file_bytes = pptx_builder.create_pptx_file(slides_data, theme_data, customization)
        resource = save_resource_to_db(topic, 'pptx', file_bytes.getvalue())
        file_bytes.seek(0)
        
        filename = f"{secure_filename(topic)}.pptx"
        response = make_response(send_file(
            file_bytes, 
            as_attachment=True, 
            download_name=filename, 
            mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation'
        ))
        response.set_cookie('fileDownload', 'true', max_age=20, samesite='Lax')
        if resource:
            import urllib.parse, json
            resource_data = {
                'id': resource.id,
                'topic': resource.topic,
                'type': resource.resource_type,
                'date': resource.created_at.strftime('%b %d, %Y'),
                'message': "PPTX generated and saved to your dashboard!"
            }
            response.set_cookie('resourceUpdate', urllib.parse.quote(json.dumps(resource_data)), max_age=20, samesite='Lax')
            if _is_fetch_request():
                response.headers['X-Resource-Id'] = str(resource.id)
                response.headers['X-Resource-Topic'] = urllib.parse.quote(resource.topic)
                response.headers['X-Resource-Type'] = resource.resource_type
                response.headers['X-Resource-Date'] = urllib.parse.quote(resource.created_at.strftime('%b %d, %Y'))
                response.headers['X-Resource-Message'] = urllib.parse.quote(resource_data['message'])
        return response
    except Exception:
        generation_bp.logger.exception("PPTX generation failed for topic '%s'.", topic)
        return _generation_error("We couldn't generate slides right now. Please try again in a moment.")

@generation_bp.route('/generate_pdf', methods=['POST'])
@limiter.limit("10 per hour")
@login_required
def generate_pdf():
    try:
        raw_pages = int(request.form.get('page_count', 5))
        page_count = max(2, min(raw_pages, 15))
    except ValueError:
        page_count = 5

    customization = {
        'resource_type': 'pdf',
        'topic': request.form.get('topic', 'Untitled'),
        'subtopics': request.form.get('subtopics', ''),
        'context': request.form.get('context', ''),
        'image_strategy': request.form.get('image_strategy', 'all_slides'),
        'intro_slide': request.form.get('intro_slide', 'false'),
        'thanks_slide': request.form.get('thanks_slide', 'false'),
        'theme_base': request.form.get('theme_base', 'ai_choice'),
        'font_style': request.form.get('font_style', 'ai_choice'),
        'bg_color': '#FFFFFF',
        'font_color': request.form.get('font_color', '#333333'),
        'accent_color': request.form.get('accent_color', '#007BFF'),
        'extra_instructions': request.form.get('extra_instructions', ''),
        'page_count': str(page_count)
    }
    topic = _validate_non_empty_text(customization['topic'], "Topic")
    if topic is None:
        return redirect(url_for('dashboard.index'))
    customization['topic'] = topic

    try:
        user_id = session.get('user_id')
        ks_id = request.form.get('knowledge_source_id')
        rag_context, _ = _get_rag_context_and_sources(user_id, topic, ks_id)

        theme_data = gemini.get_dynamic_theme(topic, customization)
        if not theme_data:
            theme_data = {
                'font-title': 'Roboto', 'font-body': 'Roboto',
                'font-color-title': customization['accent_color'], 
                'font-color-body': customization['font_color'],
                'bg-color': '#FFFFFF', 'accent-color': customization['accent_color']
            }

        content = gemini.generate_detailed_content(topic, customization, theme_data, rag_context=rag_context)
        if not content:
            return _generation_error("We couldn't generate notes right now. Please try again in a moment.")
            
        file_bytes = pdf_builder.create_pdf_reportlab(topic, content, theme_data, customization)
        resource = save_resource_to_db(topic, 'pdf', file_bytes.getvalue())
        file_bytes.seek(0)
        
        filename = f"{secure_filename(topic)}.pdf"
        response = make_response(send_file(
            file_bytes, 
            as_attachment=True, 
            download_name=filename, 
            mimetype='application/pdf'
        ))
        response.set_cookie('fileDownload', 'true', max_age=20, samesite='Lax')
        if resource:
            import urllib.parse, json
            resource_data = {
                'id': resource.id,
                'topic': resource.topic,
                'type': resource.resource_type,
                'date': resource.created_at.strftime('%b %d, %Y'),
                'message': "PDF generated and saved to your dashboard!"
            }
            response.set_cookie('resourceUpdate', urllib.parse.quote(json.dumps(resource_data)), max_age=20, samesite='Lax')
            if _is_fetch_request():
                response.headers['X-Resource-Id'] = str(resource.id)
                response.headers['X-Resource-Topic'] = urllib.parse.quote(resource.topic)
                response.headers['X-Resource-Type'] = resource.resource_type
                response.headers['X-Resource-Date'] = urllib.parse.quote(resource.created_at.strftime('%b %d, %Y'))
                response.headers['X-Resource-Message'] = urllib.parse.quote(resource_data['message'])
        return response
    except Exception:
        generation_bp.logger.exception("PDF generation failed for topic '%s'.", topic)
        return _generation_error("We couldn't generate notes right now. Please try again in a moment.")

@generation_bp.route('/present', methods=['POST'])
@limiter.limit("20 per hour")
@login_required 
def present():
    topic = _validate_non_empty_text(request.form.get('topic'), "Topic")
    if topic is None:
        return redirect(url_for('dashboard.index'))
    
    user_id = session.get('user_id')
    ks_id = request.form.get('knowledge_source_id')
    rag_context, sources = _get_rag_context_and_sources(user_id, topic, ks_id)

    explanation = gemini.generate_explanation(topic, rag_context=rag_context)
    if not explanation:
        flash("We couldn't generate an explanation right now. Please try again in a moment.", "danger")
        return redirect(url_for('dashboard.index'))
    explanation = gemini.clean_generated_text(explanation)
    save_resource_to_db(topic, 'explanation', file_data=None)
    flash("Explanation generated successfully!", "success")
    return render_template('explain.html', explanation=explanation, topic=topic, sources=sources)

@generation_bp.route('/generate_quiz', methods=['POST'])
@limiter.limit("20 per hour")
@login_required 
def generate_quiz():
    topic_manual = request.form.get('topic_manual')
    uploaded_file = request.files.get('file')
    ks_id = request.form.get('knowledge_source_id')
    user_id = session.get('user_id')
    
    content_source = ""
    source_filename = "Knowledge Source"
    rag_context = None
    sources = []

    validated_filename = _validate_upload(uploaded_file)
    if validated_filename is False:
        return redirect(url_for('dashboard.index'))

    if validated_filename:
        content_source = extract_text(uploaded_file)
        source_filename = validated_filename
        if not content_source:
            flash("Could not extract text from the uploaded file.", "danger")
            return redirect(url_for('dashboard.index'))
    elif ks_id:
        query = topic_manual or "Key concepts and study definitions"
        rag_context, sources = _get_rag_context_and_sources(user_id, query, ks_id)
        if rag_context:
            content_source = rag_context
            source_filename = sources[0] if sources else "Knowledge Base"
        elif topic_manual and topic_manual.strip():
            content_source = f"The topic is: {topic_manual}."
            source_filename = topic_manual
        else:
            flash("Could not retrieve content from the selected knowledge source.", "warning")
            return redirect(url_for('dashboard.index'))
    elif topic_manual and topic_manual.strip():
        content_source = f"The topic is: {topic_manual}."
        source_filename = topic_manual
    else:
        flash("Please provide either a Topic, a File, or select a Knowledge Source.", "warning")
        return redirect(url_for('dashboard.index'))

    session.pop('questions', None)
    questions = gemini.generate_quiz_content(content_source, rag_context=rag_context)
    
    if not questions:
        flash("We couldn't generate a quiz right now. Please try again in a moment.", "warning")
        return redirect(url_for('dashboard.index'))
        
    # Add ID for form handling
    for i, q in enumerate(questions):
        q['id'] = i
        q['correct_index'] = q.get('correct_index', q.get('answer_index'))
        
    session['questions'] = questions
    quiz_topic = f"Quiz: {secure_filename(source_filename)}"
    save_resource_to_db(quiz_topic, 'quiz', file_data=None)
    
    flash("Quiz generated successfully!", "success")
    return render_template('quiz.html', questions=questions, topic=quiz_topic, sources=sources)

@generation_bp.route('/submit_quiz', methods=['POST'])
@login_required 
def submit_quiz():
    questions = session.get('questions', [])
    if not questions:
        flash("Quiz session expired or not found.", "warning")
        return redirect(url_for('dashboard.index'))
    
    score = 0
    user_answers = {}
    
    for q in questions:
        user_answer_str = request.form.get(f'question_{q["id"]}')
        user_answer_idx = -1
        
        if user_answer_str is not None:
            try:
                user_answer_idx = int(user_answer_str)
                user_answers[q['id']] = user_answer_idx
                correct_idx = q.get('correct_index', q.get('answer_index'))
                if user_answer_idx == correct_idx:
                    score += 1
            except ValueError:
                user_answers[q['id']] = -1
        else:
            user_answers[q['id']] = -1
            
    return render_template('result.html', questions=questions, user_answers=user_answers, score=score)

@generation_bp.route('/generate_flashcards', methods=['POST'])
@limiter.limit("20 per hour")
@login_required 
def generate_flashcards():
    topic_or_text = _validate_non_empty_text(
        request.form.get('topic_or_text', request.form.get('topic', '')),
        "Topic or text"
    )
    if topic_or_text is None:
        return redirect(url_for('dashboard.index'))
        
    user_id = session.get('user_id')
    ks_id = request.form.get('knowledge_source_id')
    rag_context, sources = _get_rag_context_and_sources(user_id, topic_or_text, ks_id)

    flashcards_data = gemini.generate_flashcards(topic_or_text, rag_context=rag_context)
    
    if not flashcards_data:
        flash("We couldn't generate flashcards right now. Please try again in a moment.", "danger")
        return redirect(url_for('dashboard.index'))
        
    topic = f"Flashcards on: {topic_or_text[:50]}..."
    save_resource_to_db(topic, 'flashcard', file_data=None)
    flash("Flashcards generated successfully!", "success")
    return render_template('flashcards.html', flashcards=flashcards_data, sources=sources)

@generation_bp.route('/summarize_text', methods=['POST'])
@limiter.limit("20 per hour")
@login_required 
def summarize_text():
    text_to_summarize = _validate_non_empty_text(request.form.get('text', ''), "Text")
    if text_to_summarize is None:
        return redirect(url_for('dashboard.index'))
        
    user_id = session.get('user_id')
    ks_id = request.form.get('knowledge_source_id')
    rag_context, sources = _get_rag_context_and_sources(user_id, text_to_summarize, ks_id)

    summary = gemini.generate_summary(text_to_summarize, rag_context=rag_context)
    
    if not summary:
        flash("We couldn't generate a summary right now. Please try again in a moment.", "danger")
        return redirect(url_for('dashboard.index'))
    summary = gemini.clean_generated_text(summary)
        
    topic = f"Summary of: {text_to_summarize[:50]}..."
    save_resource_to_db(topic, 'summary', file_data=None)
    flash("Summary generated successfully!", "success")
    return render_template('summary.html', summary_text=summary, sources=sources)
