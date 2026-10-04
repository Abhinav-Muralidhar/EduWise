import requests
import json
import re
from flask import current_app

def _call_gemini(prompt, is_json=False):
    api_key = current_app.config['GEMINI_API_KEY']
    if not api_key:
        current_app.logger.warning("Gemini API key is not configured.")
        return None

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent"
    body = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    if is_json:
        body["generationConfig"] = {"responseMimeType": "application/json"}
    
    try:
        response = requests.post(url, json=body, headers={
            'Content-Type': 'application/json',
            'x-goog-api-key': api_key
        }, timeout=180)
        response.raise_for_status()
        result = response.json()
        candidates = result.get('candidates') or []
        if not candidates:
            current_app.logger.warning("Gemini response contained no candidates.")
            return None

        content = candidates[0].get('content') or {}
        parts = content.get('parts') or []
        text_parts = [part.get('text', '') for part in parts if part.get('text')]
        if not text_parts:
            current_app.logger.warning("Gemini response contained no text parts.")
            return None

        full_text = "\n".join(text_parts).strip()
        
        # Manually extract JSON if the model wrapped it in markdown code blocks
        if is_json:
            full_text = re.sub(r'```(?:json)?\s*?([\s\S]*?)\s*?```', r'\1', full_text).strip()
            
        return full_text
    except Exception as e:
        current_app.logger.exception("Error calling Gemini API: %s", e)
        return None

def get_dynamic_theme(topic, customization):
    font_list_str = ", ".join(list(current_app.config['SUPPORTED_FONTS'].keys()))
    
    prompt = f"Suggest a visually aesthetic design theme for a document on the topic: '{topic}'.\n"
    prompt += "--- USER INSTRUCTIONS ---\n"
    
    if customization.get('context'):
        prompt += f"Context: {customization['context']}\n"
    
    if customization.get('theme_base') and customization['theme_base'] != 'ai_choice':
        prompt += f"Desired theme base: {customization['theme_base']}. "
        if customization['theme_base'] == 'dark':
            prompt += "Use a dark background and light text. "
        else:
            prompt += "Use a light background and dark text. "
    
    if customization.get('font_style') == 'serif':
        prompt += "You MUST choose 'Merriweather' for the fonts. "
    else:
        prompt += "You MUST choose fonts from this list: ['Roboto', 'Lato', 'Montserrat']. "
    
    if customization.get('bg_color') != '#FFFFFF':
        prompt += f"The user explicitly wants this background color: {customization['bg_color']}. "
    if customization.get('font_color') != '#333333':
        prompt += f"The user explicitly wants this text color: {customization['font_color']}. "
    if customization.get('accent_color') != '#007BFF':
        prompt += f"The user explicitly wants this accent color: {customization['accent_color']}. "
    
    prompt += "Use all these instructions to create a cohesive theme.\n"
    
    if customization.get('extra_instructions'):
        prompt += f"Other instructions: {customization['extra_instructions']}\n"
    
    prompt += "--- END INSTRUCTIONS ---\n"
    
    prompt += (
        f"Provide the theme strictly in this format (no markdown or extra text):\n"
        f"font-title: [One from {font_list_str}]; font-body: [One from {font_list_str}]; "
        f"font-color-title: #[Hex]; font-color-body: #[Hex]; "
        f"bg-color: #[Hex]; accent-color: #[Hex]; "
        f"layout-style: [centered|left]; background-type: [solid|gradient]"
    )
    
    text = _call_gemini(prompt)
    if not text:
        return {}
        
    theme_data = {}
    for item in text.split(";"):
        if ":" in item:
            key, val = item.split(":", 1)
            theme_data[key.strip()] = val.strip()
    
    # User overrides
    if customization.get('bg_color') != '#FFFFFF':
        theme_data['bg-color'] = customization['bg_color']
    if customization.get('font_color') != '#333333':
        theme_data['font-color-body'] = customization['font_color']
        theme_data['font-color-title'] = customization['accent_color']
    if customization.get('accent_color') != '#007BFF':
        theme_data['accent-color'] = customization['accent_color']
            
    return theme_data

def _format_rag_block(rag_context):
    if not rag_context:
        return ""
    return (
        "\n--- REFERENCE MATERIAL (from user's uploaded documents) ---\n"
        f"{rag_context}\n"
        "--- END REFERENCE MATERIAL ---\n"
        "IMPORTANT: Base your response primarily on the reference material provided above. "
        "Ground your facts, terminology, questions, and explanations directly in this material.\n\n"
    )

def generate_slide_content(topic, customization, theme_data, rag_context=None):
    image_strategy = customization.get('image_strategy', 'all_slides')
    slide_count = customization.get('slide_count', '5')
    visual_instructions = customization.get('visual_instructions', '')
    
    rag_block = _format_rag_block(rag_context)
    prompt = f"{rag_block}Create a slide-wise presentation on the topic: '{topic}'.\n"
    prompt += "--- USER INSTRUCTIONS ---\n"
    
    if customization.get('context'):
        prompt += f"Context: {customization['context']}\n"
    if customization.get('subtopics'):
        prompt += f"Must cover subtopics: {customization['subtopics']}\n"
    if customization.get('extra_instructions'):
        prompt += f"Other instructions: {customization['extra_instructions']}\n"
    
    prompt += f"The design theme is: {theme_data.get('mood', 'professional')}\n"
    prompt += f"You MUST generate exactly {slide_count} content slides (excluding Intro/Thanks).\n"

    if visual_instructions:
        prompt += "--- IMPORTANT: VISUAL OVERRIDE ---\n"
        prompt += f"The user has provided a strict Visual Plan: '{visual_instructions}'\n"
        prompt += "1. If the plan mentions a specific slide (e.g., 'Slide 1', 'Slide 3'), you MUST use that specific image description for 'image_query'.\n"
        prompt += "2. For slides NOT mentioned in the plan, generate your own relevant 'image_query'.\n"
        prompt += "--------------------------------------\n"
    elif image_strategy == 'all_slides':
        prompt += "For each content slide, suggest a relevant image search query. \n"
    elif image_strategy == 'cover_only':
        prompt += "Suggest an image search query ONLY for the first main content slide. \n"
    else: 
        prompt += "Do NOT suggest any images. \n"
        
    prompt += "--- END INSTRUCTIONS ---\n"
    prompt += "You MUST return ONLY a JSON array of slide objects. Do not include any chat or preamble.\n"
    prompt += "Each object MUST have 'slide_type', 'title', 'points' (an array of strings), and 'image_query' ('none' if no image). \n"
    
    if customization.get('intro_slide') == 'true':
        prompt += "Start with a 'slide_type': 'intro' slide with just the title. \n"
    prompt += "Follow with the requested number of 'slide_type': 'content' slides. \n"
    if customization.get('thanks_slide') == 'true':
        prompt += "End with a 'slide_type': 'thanks' slide. \n"
    
    prompt += "Example Output Format: [{\"slide_type\": \"intro\", \"title\": \"Topic Name\", \"points\": [], \"image_query\": \"none\"}, ...]"
        
    text = _call_gemini(prompt, is_json=True)
    if not text:
        return []
        
    try:
        return json.loads(text)
    except Exception as e:
        current_app.logger.warning("Error parsing Gemini slide JSON: %s", e)
        return []

def generate_detailed_content(topic, customization, theme_data, rag_context=None):
    image_strategy = customization.get('image_strategy', 'all_slides')
    page_count = customization.get('page_count', '5')
    
    rag_block = _format_rag_block(rag_context)
    prompt = f"{rag_block}Write a comprehensive set of study notes on the topic: '{topic}'.\n"
    prompt += "--- USER INSTRUCTIONS ---\n"
    
    if customization.get('context'):
        prompt += f"Context: {customization['context']}\n"
    if customization.get('subtopics'):
        prompt += f"Major sections to cover: {customization['subtopics']}\n"
    if customization.get('extra_instructions'):
        prompt += f"Other instructions: {customization['extra_instructions']}\n"
        
    prompt += f"Target Length: The user expects approximately {page_count} pages of content. "
    prompt += "Use sufficient depth and examples to reach this volume.\n"

    prompt += "--- FORMATTING RULES (STRICT) ---\n"
    prompt += "1. Use exactly these markdown structures only:\n"
    prompt += "   - '## Title' for main headings\n"
    prompt += "   - '### Title' for sub-headings\n"
    prompt += "   - '* ' for bullet points\n"
    prompt += "   - '**bold**' and '*italic*' for emphasis\n"
    prompt += "   - '```' blocks for code\n"
    prompt += "2. DO NOT use '#' (single hash) for headings. Use '##' instead.\n"
    prompt += "3. DO NOT use '####' or more hashes. Stick to ## and ###.\n"
    prompt += "4. DO NOT use horizontal rules (---).\n"
    prompt += "5. DO NOT leave trailing hashes at the end of lines.\n"
    prompt += "6. Write in a clean, professional, and educational tone.\n"
    
    if image_strategy == 'all_slides' or image_strategy == 'cover_only':
        prompt += ("7. Insert visual aid tags on their own lines like this: "
                   "[IMAGE: descriptive search query]\n")
        if image_strategy == 'cover_only':
             prompt += "Do this ONLY ONCE at the very beginning.\n"
    else: 
        prompt += "7. DO NOT include any image tags.\n"
        
    prompt += "--- END INSTRUCTIONS ---\n"
    prompt += "Begin the notes now:"
    
    return _call_gemini(prompt)

def generate_quiz_content(topic_text, total_questions=10, rag_context=None):
    rag_block = _format_rag_block(rag_context)
    prompt = f"{rag_block}Generate a comprehensive quiz based on this content: '{topic_text[:4000]}'.\n"
    prompt += f"The quiz should have exactly {total_questions} multiple-choice questions.\n"
    prompt += "Return ONLY a JSON array of objects. Each object must have: 'question', 'options' (array of 4 strings), and 'answer_index' (0-3).\n"
    prompt += "Do not include markdown backticks or any other text."

    text = _call_gemini(prompt, is_json=True)
    if not text:
        return []
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return []

def generate_flashcards(topic_text, rag_context=None):
    rag_block = _format_rag_block(rag_context)
    prompt = f"{rag_block}Create 15 informative flashcards (Q&A style) from this content: '{topic_text[:4000]}'.\n"
    prompt += "Return ONLY a JSON array of objects with 'question' and 'answer' fields. No markdown."
    
    text = _call_gemini(prompt, is_json=True)
    if not text:
        return []
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return []

def generate_explanation(topic, rag_context=None):
    rag_block = _format_rag_block(rag_context)
    prompt = (
        f"{rag_block}Explain the topic '{topic}' in a warm, natural, teacher-like voice.\n"
        "Write in plain English with short paragraphs and smooth transitions.\n"
        "Use simple analogies where they help.\n"
        "Do not use markdown, bullets, headings, tables, asterisks, hashtags, or code formatting.\n"
        "Avoid sounding robotic or textbook-heavy.\n"
        "Make it feel like a person is calmly explaining the idea out loud.\n"
        "Keep it to about 300-400 words."
    )
    return _call_gemini(prompt)

def generate_summary(text, rag_context=None):
    rag_block = _format_rag_block(rag_context)
    prompt = (
        f"{rag_block}Summarize the following text in concise, natural plain English: '{text[:5000]}'\n"
        "Do not use markdown, bullets, headings, tables, asterisks, hashtags, or code formatting.\n"
        "Write short readable paragraphs only.\n"
        "Avoid special formatting symbols."
    )
    return _call_gemini(prompt)


def clean_generated_text(text):
    cleaned = str(text or '')
    cleaned = re.sub(r'```[\s\S]*?```', ' ', cleaned)
    cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)
    cleaned = re.sub(r'^\s*#{1,6}\s*', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'^\s*[-*+]\s+', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'^\s*\d+\.\s+', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)
    cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)
    cleaned = re.sub(r'_([^_]+)_', r'\1', cleaned)
    cleaned = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', cleaned)
    cleaned = cleaned.replace('|', ' ')
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = re.sub(r'[ \t]{2,}', ' ', cleaned)
    return cleaned.strip()
