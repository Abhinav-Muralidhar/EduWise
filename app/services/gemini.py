import requests
import json
from flask import current_app

def _call_gemini(prompt, is_json=False):
    api_key = current_app.config['GEMINI_API_KEY']
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={api_key}"
    
    body = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    if is_json:
        body["generationConfig"] = {"responseMimeType": "application/json"}
    
    try:
        response = requests.post(url, json=body, headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
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
    
    text = _call_gemini(prompt)
    return text if text else "Error generating content. Please try again."

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
    prompt = f"Explain the topic '{topic}' in a clear, friendly, 'teacher-like' manner. Use simple analogies. Limit to 300-400 words."
    return _call_gemini(prompt)

def generate_summary(text):
    prompt = f"Summarize the following text in a concise, structured manner with bullet points: '{text[:5000]}'"
    return _call_gemini(prompt)
