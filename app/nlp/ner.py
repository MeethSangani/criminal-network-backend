import re
from typing import List, Dict, Any

def extract_entities_from_text(text: str, report_id: str = "REP-UNKNOWN") -> List[Dict[str, Any]]:
    entities = []

    # 1. Extract Phones (e.g. 10 digit numbers)
    phone_pattern = r'\b[6-9]\d{9}\b'
    for match in re.finditer(phone_pattern, text):
        entities.append({
            "text": match.group(0),
            "type": "PHONE",
            "start": match.start(),
            "end": match.end(),
            "report_id": report_id
        })

    # 2. Extract Person Names (Capitalized double words like "Rahul Sharma", "Ajay Kumar")
    person_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
    # Exclude common non-name words
    stopwords = {"Cyber Shield", "Operation Cyber", "State Bank", "Andheri West", "Bandra Kurla"}
    for match in re.finditer(person_pattern, text):
        val = match.group(0)
        if val not in stopwords:
            entities.append({
                "text": val,
                "type": "PERSON",
                "start": match.start(),
                "end": match.end(),
                "report_id": report_id
            })

    # 3. Extract Locations (Keywords like "Andheri", "Bandra", "Delhi", "Mumbai", "Kolkata")
    locations = ["Andheri", "Bandra", "Delhi", "Mumbai", "Kolkata", "Connaught Place"]
    for loc in locations:
        for match in re.finditer(r'\b' + re.escape(loc) + r'\b', text, re.IGNORECASE):
            entities.append({
                "text": match.group(0),
                "type": "LOCATION",
                "start": match.start(),
                "end": match.end(),
                "report_id": report_id
            })

    # Deduplicate extracted entities by text & type
    seen = set()
    unique_entities = []
    for item in entities:
        key = (item["text"], item["type"])
        if key not in seen:
            seen.add(key)
            unique_entities.append(item)

    return unique_entities
