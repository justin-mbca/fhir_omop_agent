import requests
import json

# HAPI FHIR public test server base URL
FHIR_BASE = "https://hapi.fhir.org/baseR4"

# Resource types to fetch (add more as needed)
RESOURCE_TYPES = ["Patient", "Condition", "Encounter"]

# Number of resources to fetch per type
N = 10

def fetch_fhir_resources(resource_type, n=N):
    """Fetch n resources of a given type from the HAPI FHIR server."""
    url = f"{FHIR_BASE}/{resource_type}?_count={n}"
    resp = requests.get(url)
    resp.raise_for_status()
    bundle = resp.json()
    resources = [entry["resource"] for entry in bundle.get("entry", [])]
    return resources

def save_resources_to_file(resource_type, resources):
    filename = f"sample_{resource_type.lower()}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(resources, f, indent=2)
    print(f"Saved {len(resources)} {resource_type} resources to {filename}")

if __name__ == "__main__":
    for resource_type in RESOURCE_TYPES:
        resources = fetch_fhir_resources(resource_type, n=N)
        save_resources_to_file(resource_type, resources)

