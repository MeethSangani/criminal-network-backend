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

def extract_entities(text: str) -> Dict[str, List[str]]:
    """Extract structured entities (persons, vehicles, phones, locations) as lists of strings."""
    raw_list = extract_entities_from_text(text)
    result = {
        "persons": [],
        "vehicles": [],
        "phones": [],
        "locations": []
    }
    for item in raw_list:
        t = item["type"]
        if t == "PERSON":
            if item["text"] not in result["persons"]:
                result["persons"].append(item["text"])
        elif t == "PHONE":
            if item["text"] not in result["phones"]:
                result["phones"].append(item["text"])
        elif t == "LOCATION":
            if item["text"] not in result["locations"]:
                result["locations"].append(item["text"])
    
    # Regex pattern for vehicle license plates (e.g., MH01AB1234, MH12CX9999)
    veh_pattern = r'\b[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}\b'
    for match in re.finditer(veh_pattern, text):
        val = match.group(0)
        if val not in result["vehicles"]:
            result["vehicles"].append(val)

    return result

