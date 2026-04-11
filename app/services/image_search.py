import requests
import tempfile
import os
from flask import current_app

def get_image_urls_for_topic_google(query):
    """
    Searches Google Custom Search and returns a list of image URLs.
    """
    api_key = current_app.config['CUSTOM_SEARCH_API_KEY']
    cx_id = current_app.config['CUSTOM_SEARCH_CX_ID']
    
    if not api_key or not cx_id:
        print("Google Custom Search API Key or CX ID not set. Skipping image search.")
        return []
    
    excluded_sites = ["researchgate.net", "mdpi.com", "ieee.org", "sciencedirect.com"]
    excluded_sites_query = " ".join([f"-site:{site}" for site in excluded_sites])
    search_query = f"{query} {excluded_sites_query}"
    
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': api_key,
            'cx': cx_id,
            'q': search_query,
            'searchType': 'image',
            'num': 3,
            'safe': 'high',
            'imgSize': 'large',
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        image_urls = []
        if data.get('items') and len(data['items']) > 0:
            for item in data['items']:
                image_url = item['link']
                if image_url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    image_urls.append(image_url)
            
            return image_urls
                
    except Exception as e:
        print(f"Error fetching image from Google Custom Search: {e}")
    return []

def download_image_to_tempfile(image_url):
    """
    Downloads an image from a URL and saves it to a temporary file.
    """
    if not image_url:
        return None
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(image_url, headers=headers, timeout=10, stream=True)
        response.raise_for_status()
        
        content_type = response.headers.get('content-type')
        if not content_type or not content_type.startswith('image/'):
            print(f"Skipping download, non-image content type: {content_type} from {image_url}")
            return None

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        for chunk in response.iter_content(1024):
            temp_file.write(chunk)
        temp_file.close()
        return temp_file.name
    except Exception as e:
        print(f"Error downloading image from {image_url}: {e}")
    return None
