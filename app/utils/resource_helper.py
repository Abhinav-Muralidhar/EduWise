import os
import uuid
import io
import cloudinary
import cloudinary.uploader
from flask import session, current_app
from app.models.resource import Resource
from app.extensions import db

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def save_resource_to_db(topic, resource_type, file_data=None):
    try:
        user_id = session.get('user_id')
        if not user_id:
            return False
            
        file_url = None
        if file_data:
            result = cloudinary.uploader.upload(
                io.BytesIO(file_data),
                resource_type="raw",
                folder="eduwise",
                public_id=f"{uuid.uuid4()}"
            )
            file_url = result['secure_url']
                
        resource = Resource(
            user_id=user_id,
            resource_type=resource_type,
            topic=topic,
            filename=file_url
        )
        db.session.add(resource)
        db.session.commit()
        print(f"Saved resource: {topic} ({resource_type}) for user {user_id}")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error saving resource to DB: {e}")
        return False
