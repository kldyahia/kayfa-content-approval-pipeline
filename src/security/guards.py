def check_prompt_injection(content):
    suspicious_phrases = [
        "ignore all previous instructions",
        "ignore all style rules",
        "guaranteed to make you fly",
        "claim this phone is"
    ]

    content_lower = content.lower()
    for phrase in suspicious_phrases:
        if phrase in content_lower:
            return True

    return False


def sanitize_content(content):
    if check_prompt_injection(content):
        return "Security Alert: Prompt injection blocked."
    return content