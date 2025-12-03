import os
import glob
import json
import pandas as pd
from rapidfuzz import fuzz
from src.modules.vision.service import OCRService

# Configuration
SYNTHETIC_DIR = "/app/uploads/synthetic"
RESULTS_DIR = "/app/uploads/benchmark_results"

class BenchmarkRunner:
    def __init__(self):
        self.ocr_service = OCRService()
        os.makedirs(RESULTS_DIR, exist_ok=True)

    def load_ground_truth(self, json_path: str) -> str:
        """
        Reads the Synthetic JSON and reconstructs the 'perfect' text string.
        """
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Concatenate all text parts in the order they appear
        # We join them with newlines or spaces to mimic natural reading
        full_text = []
        for item in data:
            if "text" in item:
                full_text.append(item["text"])
        
        return "\n".join(full_text)

    def run_full_benchmark(self):
        print(f"Starting benchmark on {SYNTHETIC_DIR}...")
        
        # 1. Find all synthetic images
        image_files = glob.glob(os.path.join(SYNTHETIC_DIR, "*.png"))
        if not image_files:
            return {"error": "No synthetic data found. Run /admin/generate-synthetic-data first."}

        results = []
        total_score = 0
        
        for img_path in image_files:
            base_name = os.path.basename(img_path)
            json_path = img_path.replace(".png", ".json")
            
            if not os.path.exists(json_path):
                print(f"Skipping {base_name}: No JSON Ground Truth found.")
                continue

            # A. Get Ground Truth
            truth_text = self.load_ground_truth(json_path)
            
            # B. Run OCR (Hypothesis)
            try:
                ocr_text = self.ocr_service.process_file(img_path)
            except Exception as e:
                print(f"OCR Error on {base_name}: {e}")
                ocr_text = ""

            # C. Compare (Levenshtein Ratio)
            # fuzz.ratio returns 0-100 similarity
            score = fuzz.ratio(truth_text.lower(), ocr_text.lower())
            total_score += score
            
            results.append({
                "filename": base_name,
                "score": round(score, 2),
                "truth_length": len(truth_text),
                "ocr_length": len(ocr_text),
                "truth_snippet": truth_text[:50].replace("\n", " "),
                "ocr_snippet": ocr_text[:50].replace("\n", " ")
            })

        # 3. Calculate Aggregates
        avg_score = total_score / len(results) if results else 0
        
        # 4. Save Report to CSV
        df = pd.DataFrame(results)
        report_path = os.path.join(RESULTS_DIR, "latest_benchmark.csv")
        df.to_csv(report_path, index=False)
        
        summary = {
            "total_documents": len(results),
            "average_similarity_score": round(avg_score, 2),
            "report_path": report_path,
            "details": results
        }
        
        print(f"Benchmark Complete. Average Score: {avg_score:.2f}%")
        return summary

# Allow running from command line
if __name__ == "__main__":
    runner = BenchmarkRunner()
    runner.run_full_benchmark()
    