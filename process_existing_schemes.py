import json
from cleaner import clean_scheme, add_to_database
from validator import validate_scheme

INPUT_FILE = "gov_schemes_data.json"   # <-- change if your file name is different

def process_schemes():

    print("Loading extracted schemes...")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # If file contains a single object, convert to list
    if isinstance(data, dict):
        data = [data]

    print(f"🔍 Found {len(data)} schemes\n")

    for scheme in data:

        print(f"Processing: {scheme.get('scheme_name', 'Unknown')}")

        # 1️⃣ Clean
        cleaned = clean_scheme(scheme)

        # 2️⃣ Validate
        if validate_scheme(cleaned):
            add_to_database(cleaned)
            print("Stored in database\n")
        else:
            print("Failed validation\n")

    print("Processing Complete")


if __name__ == "__main__":
    process_schemes()