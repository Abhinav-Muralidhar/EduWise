import re

def chunk_text(text: str, chunk_size: int = 1400, chunk_overlap: int = 200) -> list[str]:
    """
    Split text into overlapping chunks suitable for embedding and retrieval.
    Respects paragraph breaks, sentences, and word boundaries.
    
    :param text: Raw text to split
    :param chunk_size: Target maximum characters per chunk (~350-400 words)
    :param chunk_overlap: Overlap characters between consecutive chunks (~15%)
    :return: List of chunk text strings
    """
    if not text or not text.strip():
        return []
    
    # Normalize line breaks
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # If text is smaller than chunk size, return directly
    if len(text) <= chunk_size:
        return [text.strip()]
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        
        # If we haven't reached the end of the text, try to find a natural break point
        if end < text_len:
            # Look backwards for paragraph break
            p_break = text.rfind('\n\n', start + chunk_size // 2, end)
            if p_break != -1:
                end = p_break + 2
            else:
                # Look backwards for newline
                n_break = text.rfind('\n', start + chunk_size // 2, end)
                if n_break != -1:
                    end = n_break + 1
                else:
                    # Look backwards for sentence ending (. ? !)
                    match = re.search(r'[.!?]\s+', text[start + chunk_size // 2:end])
                    if match:
                        end = start + chunk_size // 2 + match.end()
                    else:
                        # Look for space
                        s_break = text.rfind(' ', start + chunk_size // 2, end)
                        if s_break != -1:
                            end = s_break + 1
        
        chunk = text[start:end].strip()
        if chunk and len(chunk) > 20:
            chunks.append(chunk)
        
        if end >= text_len:
            break
            
        # Move forward by (chunk_size - chunk_overlap)
        next_start = end - chunk_overlap
        if next_start <= start:
            next_start = end
        start = next_start
        
    return chunks
