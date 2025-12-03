import re
from typing import List, Dict, Any

class ExtractionService:
    def __init__(self):
        # Regex patterns for French medical prescriptions
        # Captures lines starting with a number (e.g., "1. Doliprane...")
        self.line_pattern = re.compile(r'^\s*(\d+)[.)]\s*(.+)', re.MULTILINE)
        
        # Basic patterns to split Drug from Dosage (Simplistic for MVP)
        self.dosage_pattern = re.compile(r'(\d+\s*(?:mg|g|ml|cp|comprimé|gélule|sachet))', re.IGNORECASE)

    def extract_from_text(self, raw_text: str) -> Dict[str, Any]:
        """
        Parses raw OCR text and returns structured data.
        """
        structured_data = {
            "patient": self._extract_patient(raw_text),
            "doctor": self._extract_doctor(raw_text),
            "date": self._extract_date(raw_text),
            "medicines": []
        }

        # Parse the drugs (Line Items)
        matches = self.line_pattern.findall(raw_text)
        for _, content in matches:
            med_info = self._parse_drug_line(content)
            structured_data["medicines"].append(med_info)

        return structured_data

    def _parse_drug_line(self, text: str) -> Dict[str, str]:
        """
        Splits a line like 'Doliprane 1000mg 1 comprimé...' into components.
        """
        # 1. Extract Dosage if present
        dosage_match = self.dosage_pattern.search(text)
        dosage = dosage_match.group(1) if dosage_match else ""
        
        # 2. Assume Drug Name is everything before the dosage
        if dosage:
            drug_name = text.split(dosage)[0].strip()
            instructions = text.split(dosage)[-1].strip()
        else:
            drug_name = text.strip()
            instructions = ""

        # Cleanup artifacts
        drug_name = re.sub(r'[^\w\s]', '', drug_name).strip()

        return {
            "drug_name": drug_name,
            "dosage": dosage,
            "raw_instruction": instructions,
            # We can expand this later with mapping to ATC codes
            "standardized_code": None 
        }

    def _extract_patient(self, text: str) -> str:
        match = re.search(r'Patient\s*:\s*(.+)', text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _extract_doctor(self, text: str) -> str:
        match = re.search(r'Dr\.?\s*(.+)', text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _extract_date(self, text: str) -> str:
        # Matches dd/mm/yyyy
        match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
        return match.group(1) if match else None
    