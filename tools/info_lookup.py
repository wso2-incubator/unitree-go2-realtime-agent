import os
from difflib import get_close_matches

DOC_DIR = "./data"

def load_all_docs():
    docs = {}
    for fname in os.listdir(DOC_DIR):
        if fname.endswith(".md"):
            title = fname.replace(".md", "").replace("_", " ").title()
            with open(os.path.join(DOC_DIR, fname), "r", encoding="utf-8") as f:
                docs[title] = f.read()
    return docs

def normalize(text: str) -> str:
    # Lowercase and strip common generic prefixes (customize as needed)
    # Remove any event/brand-specific keywords here if desired
    return text.lower().strip()

def find_relevant_info(topic: str, docs: dict[str, str]) -> str:
    """
    Find relevant information for a topic from a dictionary of title->text.
    This function is fully generic and can be used for any event, product, or topic.
    """
    query_norm = normalize(topic)

    # Try direct substring match first
    for title, text in docs.items():
        title_norm = normalize(title)
        if query_norm in title_norm or query_norm in text.lower():
            return f"Here's what I found about {topic}:\n\n{text[:600]}..."

    # Fuzzy match on topic titles if no direct match
    all_titles = list(docs.keys())
    close = get_close_matches(topic, all_titles, n=1, cutoff=0.6)
    if close:
        title = close[0]
        text = docs[title]
        return f"Here's what I found about {topic}:\n\n{text[:600]}..."

    return f"Sorry, I couldn't find anything relevant to '{topic}'."
