import re

PHONE_RE = re.compile(r'(\+?\d[\d \-\.]{6,17}\d)')
EMAIL_RE = re.compile(r'[\w\.\+-]+@[\w-]+\.[\w\.-]+')

ADDRESS_KEYWORDS = [
    'rue', 'avenue', 'av.', 'quartier', 'bp', 'street', 'st.', 'road', 'rd',
    'blvd', 'boulevard', 'residence', 'résidence', 'immeuble', 'porte',
    'apt', 'appartement', 'lane', 'ave',
]


def _normalize_phone(raw):
    cleaned = re.sub(r'[ \-\.]', '', raw)
    return cleaned


def parse_smart_paste(text):
    """Best-effort extraction of name/phone/email/address/notes from a raw
    pasted message (e.g. a driver or client text). Pure regex/line heuristics
    — no NLP/LLM involved, so it will misfire on unusual formats, multiple
    people in one message, or addresses without a recognizable street-type
    keyword. Always present the result for human review before saving."""
    fields = {'name': '', 'phone': '', 'email': '', 'address': '', 'notes': ''}
    confidence = {}

    remaining = text

    phone_match = PHONE_RE.search(remaining)
    if phone_match:
        fields['phone'] = _normalize_phone(phone_match.group(1))
        confidence['phone'] = 'high'
        remaining = remaining[:phone_match.start()] + remaining[phone_match.end():]

    email_match = EMAIL_RE.search(remaining)
    if email_match:
        fields['email'] = email_match.group(0)
        confidence['email'] = 'high'
        remaining = remaining[:email_match.start()] + remaining[email_match.end():]

    lines = [ln.strip() for ln in remaining.splitlines() if ln.strip()]

    name_idx = None
    for i, line in enumerate(lines):
        if not re.search(r'\d', line) and 1 <= len(line.split()) <= 5:
            fields['name'] = line
            confidence['name'] = 'low'
            name_idx = i
            break
    if name_idx is not None:
        lines.pop(name_idx)

    address_idx = None
    for i, line in enumerate(lines):
        low = line.lower()
        if any(kw in low for kw in ADDRESS_KEYWORDS):
            fields['address'] = line
            confidence['address'] = 'high'
            address_idx = i
            break
    if address_idx is None and lines:
        longest = max(lines, key=len)
        fields['address'] = longest
        confidence['address'] = 'low'
        address_idx = lines.index(longest)
    if address_idx is not None:
        lines.pop(address_idx)

    if lines:
        fields['notes'] = '\n'.join(lines)

    return {'ok': True, 'fields': fields, 'confidence': confidence}
