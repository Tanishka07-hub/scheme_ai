import json

required_fields = [
    "scheme_name",
    "description",
    "benefits",
    "eligibility",
    "documents_required",
    "application_process",
    "official_website"
]

def validate_scheme(scheme):

    for field in required_fields:
        if field not in scheme:
            print("Missing field:", field)
            return False

    return True


# Test validator
if __name__ == "__main__":

    with open("test_scheme.json", "r") as f:
        scheme = json.load(f)

    if validate_scheme(scheme):
        print("Scheme is valid ")
    else:
        print("Scheme is invalid ")
