import json
from validator import validate_scheme
from datetime import datetime

def clean_scheme(raw_scheme):

    # ---------- 1. Basic String Fields ----------
    raw_scheme.setdefault("scheme_name", "")
    raw_scheme.setdefault("ministry", "")
    raw_scheme.setdefault("description", "")
    raw_scheme.setdefault("official_website", "")

    # ---------- 2. Benefits ----------
    if isinstance(raw_scheme.get("benefits"), str):
        raw_scheme["benefits"] = [raw_scheme["benefits"]]

    raw_scheme.setdefault("benefits", [])

    # ---------- 3. Eligibility ----------
    if "eligibility" not in raw_scheme or not isinstance(raw_scheme["eligibility"], dict):
        raw_scheme["eligibility"] = {}

    eligibility = raw_scheme["eligibility"]

    eligibility.setdefault("age", "")
    eligibility.setdefault("income", "")
    eligibility.setdefault("occupation", "")
    eligibility.setdefault("category", "")
    eligibility.setdefault("land_required", "")
    eligibility.setdefault("other", [])

    # Make sure "other" is always a list
    if isinstance(eligibility.get("other"), str):
        eligibility["other"] = [eligibility["other"]]

    raw_scheme["eligibility"] = eligibility

    # ---------- 4. Lists ----------
    raw_scheme.setdefault("documents_required", [])
    raw_scheme.setdefault("application_process", [])

    # Convert to list if string
    if isinstance(raw_scheme["documents_required"], str):
        raw_scheme["documents_required"] = [raw_scheme["documents_required"]]

    if isinstance(raw_scheme["application_process"], str):
        raw_scheme["application_process"] = [raw_scheme["application_process"]]

    # ---------- 5. Metadata ----------
    raw_scheme.setdefault("source_url", "")
    raw_scheme.setdefault("extraction_confidence", "0.0")

    # Always update last_checked automatically
    raw_scheme["last_checked"] = datetime.today().strftime("%Y-%m-%d")

    return raw_scheme



def add_to_database(cleaned_scheme):

    with open("schemes_database.json", "r") as f:
        database = json.load(f)

    database.append(cleaned_scheme)

    with open("schemes_database.json", "w") as f:
        json.dump(database, f, indent=4)


if __name__ == "__main__":

    filename = input("Enter file name to clean: ")

    with open(filename, "r") as f:
        raw_scheme = json.load(f)



    cleaned = clean_scheme(raw_scheme)

    if validate_scheme(cleaned):
        add_to_database(cleaned)
        print("Scheme added to database ✅")
    else:
        print("Invalid scheme ❌")
