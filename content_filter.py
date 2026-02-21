def extract_scheme_content(raw_markdown):

    # Words that indicate start of actual scheme content
    start_keywords = [
        "Scheme",
        "Overview",
        "About",
        "Benefits",
        "Eligibility",
        "Application",
        "Pradhan Mantri",
        "PM-KISAN",
        "PMAY",
        "NREGA"
    ]

    # Words that indicate footer / junk section
    end_keywords = [
        "Privacy Policy",
        "Terms and Conditions",
        "Copyright",
        "Contact Us",
        "Follow Us",
        "All rights reserved",
        "Site is designed",
        "Last Updated"
    ]

    content = raw_markdown

    # Find start position
    start_positions = []

    for word in start_keywords:
        pos = content.find(word)
        if pos != -1:
            start_positions.append(pos)

    if start_positions:
        content = content[min(start_positions):]

    # Remove footer
    for word in end_keywords:
        pos = content.find(word)
        if pos != -1:
            content = content[:pos]

    # Limit size for AI
    content = content[:20000]

    return content
