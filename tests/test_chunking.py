from app.services.chunking import chunk_text

def test_chunk_text_empty():
    assert chunk_text("") == []
    assert chunk_text("   ") == []

def test_chunk_text_short():
    short_text = "Photosynthesis is the process by which plants convert sunlight into chemical energy."
    chunks = chunk_text(short_text, chunk_size=200, chunk_overlap=30)
    assert len(chunks) == 1
    assert "Photosynthesis" in chunks[0]

def test_chunk_text_long_paragraphs():
    p1 = "Paragraph 1: " + ("Neural networks are computational models. " * 15)
    p2 = "Paragraph 2: " + ("Gradient descent is an optimization algorithm. " * 15)
    p3 = "Paragraph 3: " + ("Backpropagation calculates gradients efficiently. " * 15)
    full_text = f"{p1}\n\n{p2}\n\n{p3}"
    
    chunks = chunk_text(full_text, chunk_size=300, chunk_overlap=50)
    assert len(chunks) > 1
    # Check that all text content is represented
    all_chunk_text = " ".join(chunks)
    assert "Neural networks" in all_chunk_text
    assert "Gradient descent" in all_chunk_text
    assert "Backpropagation" in all_chunk_text

def test_chunk_overlap_present():
    long_sentence = ("A quick brown fox jumps over the lazy dog repeatedly. " * 30)
    chunks = chunk_text(long_sentence, chunk_size=200, chunk_overlap=50)
    assert len(chunks) >= 2
    # Verify that there is overlapping content between chunk 0 and chunk 1
    chunk0_words = set(chunks[0].split()[-6:])
    chunk1_words = set(chunks[1].split()[:8])
    assert len(chunk0_words.intersection(chunk1_words)) > 0
