import fitz  # PyMuPDF
import docx

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
            return file_storage.read().decode("utf-8")
    except Exception as e:
        print(f"Error extracting text: {e}")
    return ""
