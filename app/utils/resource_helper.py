import os
import uuid
from flask import session, current_app
from app.models.resource import Resource
from app.extensions import db

def save_resource_to_db(topic, resource_type, file_data=None):
    try:
        user_id = session.get('user_id')
        if not user_id:
            return False
            
        filename = None
        if file_data:
            ext = 'pptx' if resource_type == 'pptx' else 'pdf'
            filename = f"{uuid.uuid4()}.{ext}"
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            with open(file_path, 'wb') as f:
                f.write(file_data)
                
        resource = Resource(
            user_id=user_id,
            resource_type=resource_type,
            topic=topic,
            filename=filename
        )
        db.session.add(resource)
        db.session.commit()
        print(f"Saved resource: {topic} ({resource_type}) for user {user_id}")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error saving resource to DB: {e}")
        return False
