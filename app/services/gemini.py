import requests
import json
import re
from flask import current_app

def _call_gemini(prompt, is_json=False):
    api_key = current_app.config['GEMINI_API_KEY']
    if not api_key:
        current_app.logger.warning("Gemini API key is not configured.")
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite-preview:generateContent?key={api_key}"
    
    body = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    if is_json:
        body["generationConfig"] = {"responseMimeType": "application/json"}
    
    try:
        response = requests.post(url, json=body, headers={'Content-Type': 'application/json'}, timeout=30)
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

        return "\n".join(text_parts).strip()
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

def generate_slide_content(topic, customization, theme_data):
    image_strategy = customization.get('image_strategy', 'all_slides')
    slide_count = customization.get('slide_count', '5')
    visual_instructions = customization.get('visual_instructions', '')
    
    prompt = f"Create a slide-wise presentation on the topic: '{topic}'.\n"
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
    prompt += "You MUST return a JSON array of slide objects.\n"
    prompt += "Each object MUST have 'slide_type', 'title', 'points' (an array of strings), and 'image_query' ('none' if no image). \n"
    
    if customization.get('intro_slide') == 'true':
        prompt += "Start with a 'slide_type': 'intro' slide with just the title. \n"
    prompt += "Follow with the requested number of 'slide_type': 'content' slides. \n"
    if customization.get('thanks_slide') == 'true':
        prompt += "End with a 'slide_type': 'thanks' slide. \n"
        
    text = _call_gemini(prompt, is_json=True)
    if not text:
        return []
        
    try:
        return json.loads(text)
    except Exception as e:
        print(f"Error parsing Gemini slide JSON: {e}")
        return []

def generate_detailed_content(topic, customization, theme_data):
    image_strategy = customization.get('image_strategy', 'all_slides')
    
    prompt = f"Write a long, detailed, multi-page notes on the topic: '{topic}'.\n"
    prompt += "--- USER INSTRUCTIONS ---\n"
    
    if customization.get('context'):
        prompt += f"Context: {customization['context']}\n"
    if customization.get('subtopics'):
        prompt += f"Must cover subtopics as major sections: {customization['subtopics']}\n"
    if customization.get('extra_instructions'):
        prompt += f"Other instructions: {customization['extra_instructions']}\n"
        
    prompt += f"The design theme is: {theme_data.get('mood', 'professional')}\n"
    prompt += "Format the text using markdown: \n"
    prompt += " - Use '## Section Title' for main headings. \n"
    prompt += " - Use '### Sub-section Title' for sub-headings. \n"
    prompt += " - Use '* Bullet point' for lists. \n"
    prompt += " - Use '  * Nested bullet point' for nested lists (indent with 2 spaces). \n"
    prompt += " - Use '| Header 1 | Header 2 |' and '| --- | --- |' for tables. \n" 
    prompt += " - Use '**bold**' for inline bold text and '*italic*' for inline italic text. \n"
    prompt += " - Use '`inline code`' for code snippets. \n"
    prompt += " - Use '```python\ncode block\n```' for multi-line code blocks. \n"
    
    if image_strategy == 'all_slides' or image_strategy == 'cover_only':
        prompt += ("When a concept would benefit from a visual aid, insert a tag on its own line: "
                   "[IMAGE: descriptive search query for Google Images]\n")
        if image_strategy == 'cover_only':
             prompt += "Do this ONLY ONCE, near the beginning. \n"
    else: 
        prompt += "Do NOT include any [IMAGE: ...] tags. \n"
        
    prompt += "--- END INSTRUCTIONS ---\n"
    prompt += "Now, begin the report:"
    
    return _call_gemini(prompt)

def generate_quiz_content(topic_text, total_questions=10):
    prompt = f"Generate a comprehensive quiz based on this text: '{topic_text[:4000]}'.\n"
    prompt += f"The quiz should have exactly {total_questions} multiple-choice questions.\n"
    prompt += "Return ONLY a JSON array of objects. Each object must have: 'question', 'options' (array of 4 strings), and 'answer_index' (0-3).\n"
    prompt += "Do not include markdown backticks or any other text."

    text = _call_gemini(prompt, is_json=True)
    if not text:
        return []
    try:
        return json.loads(text)
    except:
        return []

def generate_flashcards(topic_text):
    prompt = f"Create 15 informative flashcards (Q&A style) from this text: '{topic_text[:4000]}'.\n"
    prompt += "Return ONLY a JSON array of objects with 'question' and 'answer' fields. No markdown."
    
    text = _call_gemini(prompt, is_json=True)
    if not text:
        return []
    try:
        return json.loads(text)
    except:
        return []

def generate_explanation(topic):
    prompt = (
        f"Explain the topic '{topic}' in a warm, natural, teacher-like voice.\n"
        "Write in plain English with short paragraphs and smooth transitions.\n"
        "Use simple analogies where they help.\n"
        "Do not use markdown, bullets, headings, tables, asterisks, hashtags, or code formatting.\n"
        "Avoid sounding robotic or textbook-heavy.\n"
        "Make it feel like a person is calmly explaining the idea out loud.\n"
        "Keep it to about 300-400 words."
    )
    return _call_gemini(prompt)

def generate_summary(text):
    prompt = (
        f"Summarize the following text in concise, natural plain English: '{text[:5000]}'\n"
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
