import json
import datetime

def convert_to_fhir(data):
    """
    Converts internal JSON to a simplified FHIR Bundle.
    """
    bundle = {
        "resourceType": "Bundle",
        "type": "document",
        "timestamp": datetime.datetime.now().isoformat(),
        "entry": []
    }

    # 1. Patient Resource
    patient_entry = {
        "resourceType": "Patient",
        "name": [{"text": data.get("patient", "Inconnu")}]
    }
    bundle["entry"].append({"resource": patient_entry})

    # 2. Practitioner Resource
    doctor_entry = {
        "resourceType": "Practitioner",
        "name": [{"text": data.get("doctor", "Inconnu")}]
    }
    bundle["entry"].append({"resource": doctor_entry})

    # 3. MedicationRequests
    for med in data.get("medicines", []):
        med_entry = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "text": med.get("drug_name", "Unknown Drug")
            },
            "dosageInstruction": [{
                "text": med.get("raw_instruction", ""),
                "doseAndRate": [{
                    "type": {"text": med.get("dosage", "")}
                }]
            }]
        }
        bundle["entry"].append({"resource": med_entry})

    return json.dumps(bundle, indent=2)