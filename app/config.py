import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
# Note: basedir is now inside app/, so we need to go up one level for database and uploads
project_root = os.path.abspath(os.path.join(basedir, '..'))

load_dotenv(os.path.join(project_root, '.env'), override=True)

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(project_root, 'eduwise.db')}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(project_root, 'uploads')
    
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    CUSTOM_SEARCH_API_KEY = os.getenv("CUSTOM_SEARCH_API_KEY")
    CUSTOM_SEARCH_CX_ID = os.getenv("CUSTOM_SEARCH_CX_ID")
    
    # Fonts
    FONT_DIR = os.path.join(project_root, 'fonts')
    SUPPORTED_FONTS = {
        'Roboto': ('Roboto-Regular.ttf', 'Roboto-Bold.ttf', 'Roboto-Italic.ttf', 'Roboto-BoldItalic.ttf'),
        'Lato': ('Lato-Regular.ttf', 'Lato-Bold.ttf', 'Lato-Italic.ttf', 'Lato-BoldItalic.ttf'),
        'Montserrat': ('Montserrat-Regular.ttf', 'Montserrat-Bold.ttf', 'Montserrat-Italic.ttf', 'Montserrat-BoldItalic.ttf'),
        'Merriweather': ('Merriweather-Regular.ttf', 'Merriweather-Bold.ttf', 'Merriweather-Italic.ttf', 'Merriweather-BoldItalic.ttf')
    }
