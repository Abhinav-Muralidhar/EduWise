import fitz  # PyMuPDF
import docx
from flask import current_app

def extract_text(file_storage):
    filename = file_storage.filename.lower()
    try:
        file_storage.seek(0)
        if filename.endswith(".pdf"):
            doc = fitz.open(stream=file_storage.read(), filetype="pdf")
            text = "".join([page.get_text() for page in doc])
            return text
        elif filename.endswith(".docx"):
            doc = docx.Document(file_storage)
            return "\n".join([p.text for p in doc.paragraphs])
        elif filename.endswith(".txt"):
            content = file_storage.read()
            for encoding in ('utf-8', 'utf-8-sig', 'latin-1', 'cp1252'):
                try:
                    return content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            return content.decode('utf-8', errors='ignore')
    except Exception as e:
        current_app.logger.exception("Error extracting text: %s", e)
    return ""
