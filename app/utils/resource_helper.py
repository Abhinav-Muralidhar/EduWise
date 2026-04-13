import os
import uuid
import io
import cloudinary
import cloudinary.uploader
import re
from flask import session, current_app
from app.models.resource import Resource
from app.extensions import db

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

import re

def save_resource_to_db(topic, resource_type, file_data=None):
    try:
        user_id = session.get('user_id')
        if not user_id:
            return None
            
        file_url = None
        if file_data:
            # Clean topic for use as filename
            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', topic)[:50]
            public_id = f"{safe_name}_{uuid.uuid4().hex[:8]}"
            
            result = cloudinary.uploader.upload(
                io.BytesIO(file_data),
                resource_type="raw",
                folder="eduwise",
                public_id=public_id
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
        return resource
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Error saving resource to DB: %s", e)
        return None
