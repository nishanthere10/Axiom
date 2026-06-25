import re

def extract_high_signal_chunks(text: str, query: str, max_chars: int = 2500) -> str:
    """
    Cleans raw web text and extracts the chunks most relevant to the query.
    1. Removes massive whitespaces.
    2. Splits into paragraphs.
    3. Scores paragraphs based on query term overlap.
    4. Returns the top paragraphs up to max_chars.
    """
    if not text:
        return ""
        
    # Clean whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    paragraphs = text.split('\n\n')
    
    # Filter out obvious boilerplate (very short lines usually nav/footer)
    # Require at least some decent length or technical symbols to be considered a real paragraph
    valid_paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 60 or "{" in p or "}" in p or "=" in p]
    
    if not valid_paragraphs:
        return text[:max_chars]
        
    # Simple scoring: term frequency of query words
    query_terms = set(re.findall(r'\w+', query.lower()))
    # Filter out common stop words from query terms
    stop_words = {"what", "is", "the", "a", "an", "for", "and", "or", "to", "in", "of", "with", "vs", "versus"}
    query_terms = query_terms - stop_words
    
    scored_paragraphs = []
    for i, p in enumerate(valid_paragraphs):
        p_lower = p.lower()
        # Count occurrences of query terms
        score = sum(p_lower.count(term) for term in query_terms)
        
        # Add a slight positional bias to favor the top of the article (intro)
        position_bonus = max(0, (20 - i) * 0.1)
        
        # Add a bias for code snippets or technical density
        tech_bonus = 0
        if "```" in p or "function" in p or "import " in p or "class " in p:
            tech_bonus = 1.0
            
        final_score = score + position_bonus + tech_bonus
        scored_paragraphs.append((final_score, i, p))
        
    # Sort by score (desc), but keep original order when reconstructing
    scored_paragraphs.sort(key=lambda x: x[0], reverse=True)
    
    selected = []
    current_length = 0
    
    # Take highest scored paragraphs until max_chars
    for score, idx, p in scored_paragraphs:
        # Ignore low-signal paragraphs entirely if we already have good content
        if score < 0.5 and current_length > 500:
            continue
            
        if current_length + len(p) > max_chars and current_length > 0:
            # We can partially slice the last paragraph if we really need to fit it
            remaining = max_chars - current_length
            if remaining > 100:
                selected.append((idx, p[:remaining] + "..."))
                current_length += remaining
            continue
            
        selected.append((idx, p))
        current_length += len(p)
        if current_length >= max_chars:
            break
            
    # Sort back by original index to maintain readability/context flow
    selected.sort(key=lambda x: x[0])
    
    result = "\n\n...\n\n".join([p for idx, p in selected])
    return result
