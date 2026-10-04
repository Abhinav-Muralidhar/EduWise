import io
from app.utils.text import extract_text

class DummyFileStorage:
    def __init__(self, filename, content_bytes):
        self.filename = filename
        self.stream = io.BytesIO(content_bytes)

    def seek(self, offset):
        self.stream.seek(offset)

    def read(self):
        return self.stream.read()

def test_extract_text_txt():
    content = b"This is a test document about thermodynamics and heat transfer."
    f = DummyFileStorage("physics_notes.txt", content)
    text = extract_text(f)
    assert "thermodynamics" in text
    assert "heat transfer" in text

def test_extract_text_empty():
    f = DummyFileStorage("empty.txt", b"")
    text = extract_text(f)
    assert text == ""

def test_extract_text_unsupported():
    f = DummyFileStorage("image.png", b"\x89PNG\r\n\x1a\n")
    text = extract_text(f)
    assert text == ""
