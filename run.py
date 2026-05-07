import os

from app import create_app, db, models

app = create_app()

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "true").lower() in ("true", "1", "yes")
    app.run(debug=debug)