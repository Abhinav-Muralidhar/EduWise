import os
from flask import Flask
from app.extensions import db
from app.config import Config
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    from app.extensions import db, csrf, limiter, scheduler, migrate
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)
    scheduler.init_app(app)
    scheduler.start()

    # Register fonts
    _register_fonts(app)

    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.generation import generation_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(generation_bp)

    # Register error handlers
    from flask import render_template
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    return app

def _register_fonts(app):
    font_dir = app.config['FONT_DIR']
    supported_fonts = app.config['SUPPORTED_FONTS']
    
    for font_name, (regular, bold, italic, bold_italic) in supported_fonts.items():
        try:
            pdfmetrics.registerFont(TTFont(font_name, os.path.join(font_dir, regular)))
            pdfmetrics.registerFont(TTFont(f"{font_name}-Bold", os.path.join(font_dir, bold)))
            pdfmetrics.registerFont(TTFont(f"{font_name}-Italic", os.path.join(font_dir, italic)))
            pdfmetrics.registerFont(TTFont(f"{font_name}-BoldItalic", os.path.join(font_dir, bold_italic)))
            
            addMapping(font_name, 0, 0, font_name)
            addMapping(font_name, 1, 0, f"{font_name}-Bold")
            addMapping(font_name, 0, 1, f"{font_name}-Italic")
            addMapping(font_name, 1, 1, f"{font_name}-BoldItalic")
            app.logger.debug("Registered font: %s", font_name)
        except Exception as e:
            app.logger.warning("Could not register font %s: %s", font_name, e)
