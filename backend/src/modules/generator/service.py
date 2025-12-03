import os
import json
import random
import numpy as np
from typing import List
from dataclasses import dataclass
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# --- CONFIGURATION ---
FONT_PATH_NORMAL = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_PATH_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

ROUTE_MAP_FR = {
    "PO": "orale", "ORAL": "orale", "IV": "intraveineuse", "IM": "intramusculaire",
    "TOPICAL": "cutanée", "INHALATION": "inhalée", "SC": "sous-cutanée"
}

@dataclass
class LineItem:
    drug_name: str
    strength: str
    posology: str # Flattened for simplicity
    form: str

@dataclass
class OrdoDoc:
    patient_name: str
    prescriber_name: str
    date_str: str
    lines: List[LineItem]

class PrescriptionGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def load_font(self, font_type="normal", size=20):
        path = FONT_PATH_BOLD if font_type == "bold" else FONT_PATH_NORMAL
        try:
            return ImageFont.truetype(path, size=size)
        except IOError:
            return ImageFont.load_default()

    def apply_scan_effects(self, img: Image.Image) -> Image.Image:
        """Simulates a scanned document: Blur, Noise, Rotation, Grayscale."""
        # 1. Slight Rotation (-2 to +2 degrees)
        angle = random.uniform(-1.5, 1.5)
        img = img.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor="white")

        # 2. Gaussian Blur (Simulate bad focus)
        if random.random() > 0.5:
            img = img.filter(ImageFilter.GaussianBlur(radius=0.5))

        # 3. Add Salt & Pepper Noise
        # Convert to numpy array
        np_img = np.array(img)
        noise = np.random.randint(0, 255, np_img.shape, dtype='uint8')
        # Blend original image with noise (very subtle)
        noise_level = 0.05  # 5% noise opacity
        np_img = (np_img * (1 - noise_level) + noise * noise_level).astype('uint8')
        
        return Image.fromarray(np_img)

    def generate_batch(self, count: int, csv_path: str = None):
        catalog = self._load_catalog(csv_path)
        generated_files = []

        for i in range(count):
            doc = self._generate_doc_data(catalog)
            img, boxes = self._render_image(doc)
            
            # --- APPLY NOISE HERE ---
            img = self.apply_scan_effects(img)
            # ------------------------

            base_name = f"synth_{random.randint(10000, 99999)}"
            img_filename = f"{base_name}.png"
            json_filename = f"{base_name}.json"
            
            img.save(os.path.join(self.output_dir, img_filename))
            with open(os.path.join(self.output_dir, json_filename), "w") as f:
                json.dump(boxes, f, indent=2)
            
            generated_files.append(img_filename)
            
        return generated_files

    def _load_catalog(self, csv_path):
        """Loads MIMIC CSV or falls back to basic list."""
        if csv_path and os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path).fillna("")
                return df.to_dict(orient="records")
            except Exception as e:
                print(f"Error reading CSV: {e}")
        
        # Fallback Mock Data
        return [
            {"drug": "AMOXICILLINE", "prod_strength": "500mg", "route": "ORAL", "form_rx": "gélule"},
            {"drug": "DOLIPRANE", "prod_strength": "1000mg", "route": "ORAL", "form_rx": "comprimé"},
            {"drug": "VOLTARENE", "prod_strength": "1%", "route": "TOPICAL", "form_rx": "gel"},
        ]

    def _generate_doc_data(self, catalog):
        selection = random.sample(catalog, k=min(random.randint(1, 3), len(catalog)))
        lines = []
        for item in selection:
            # Map MIMIC columns to French
            route_fr = ROUTE_MAP_FR.get(item.get("route", "").upper(), "orale")
            form_fr = item.get("form_rx", "comprimé")
            
            pos_str = f"1 {form_fr}, 3 fois par jour ({route_fr})"
            
            lines.append(LineItem(
                drug_name=item.get("drug", "MEDICAMENT"), 
                strength=item.get("prod_strength", ""), 
                posology=pos_str,
                form=form_fr
            ))
            
        return OrdoDoc(
            patient_name=f"Patient {random.randint(100, 999)}", 
            prescriber_name="Dr. House", 
            date_str="12/12/2024", 
            lines=lines
        )

    def _render_image(self, doc: OrdoDoc):
        w, h = 800, 1000
        img = Image.new("RGB", (w, h), (250, 250, 250))
        draw = ImageDraw.Draw(img)
        font_reg = self.load_font("normal", 20)
        font_bold = self.load_font("bold", 24)
        
        # Draw Header
        draw.text((300, 50), "ORDONNANCE", fill="black", font=font_bold)
        draw.text((50, 120), f"Dr. {doc.prescriber_name}", fill="black", font=font_reg)
        draw.text((50, 150), f"Patient: {doc.patient_name}", fill="black", font=font_reg)
        draw.line((50, 190, 750, 190), fill="black")
        
        y = 220
        boxes = []
        
        for i, line in enumerate(doc.lines, 1):
            # Drug Name Line
            txt_drug = f"{i}. {line.drug_name} {line.strength}"
            draw.text((50, y), txt_drug, fill="black", font=font_bold)
            bbox = draw.textbbox((50, y), txt_drug, font=font_bold)
            boxes.append({"label": "DRUG", "text": line.drug_name, "box": bbox})
            y += 30
            
            # Posology Line
            draw.text((70, y), line.posology, fill="#333", font=font_reg)
            bbox_pos = draw.textbbox((70, y), line.posology, font=font_reg)
            boxes.append({"label": "INSTRUCTION", "text": line.posology, "box": bbox_pos})
            y += 50
            
        return img, boxes