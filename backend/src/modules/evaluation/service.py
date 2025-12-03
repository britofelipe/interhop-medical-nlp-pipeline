from typing import List, Dict
from rapidfuzz import fuzz

class MetricsService:
    def calculate_metrics(self, ai_data: Dict, human_data: Dict):
        """
        Compares AI prediction vs Human validation.
        """
        ai_meds = ai_data.get("medicines", [])
        human_meds = human_data.get("medicines", [])

        # 1. Entity Matching (Simple Name Match)
        tp = 0 # True Positives (AI found it, Human kept it)
        fp = 0 # False Positives (AI found it, Human deleted it)
        fn = 0 # False Negatives (AI missed it, Human added it)

        # Normalize names for comparison
        ai_names = [m.get("drug_name", "").lower().strip() for m in ai_meds]
        human_names = [m.get("drug_name", "").lower().strip() for m in human_meds]

        # Calculate TP and FP
        for name in ai_names:
            if name in human_names:
                tp += 1
            else:
                fp += 1
        
        # Calculate FN (Items in human list not in AI list)
        for name in human_names:
            if name not in ai_names:
                fn += 1

        # 2. Precision / Recall / F1
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        # 3. Text Similarity (Levenshtein on the full JSON string representation)
        # This serves as a proxy for "Word Error Rate" on the structured data
        similarity = fuzz.ratio(str(ai_meds), str(human_meds))

        return {
            "precision": round(precision, 2),
            "recall": round(recall, 2),
            "f1_score": round(f1, 2),
            "similarity_score": round(similarity, 2),
            "details": {
                "ai_count": len(ai_meds),
                "human_count": len(human_meds),
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn
            }
        }

    def aggregate_stats(self, prescriptions: List):
        """Averages metrics across multiple documents."""
        total_prec = 0
        total_rec = 0
        total_f1 = 0
        count = 0

        for p in prescriptions:
            if not p.is_validated or not p.ai_structured_json:
                continue
            
            stats = self.calculate_metrics(p.ai_structured_json, p.structured_json)
            total_prec += stats["precision"]
            total_rec += stats["recall"]
            total_f1 += stats["f1_score"]
            count += 1

        if count == 0:
            return {"count": 0, "message": "No validated documents found."}

        return {
            "count": count,
            "avg_precision": round(total_prec / count, 2),
            "avg_recall": round(total_rec / count, 2),
            "avg_f1": round(total_f1 / count, 2)
        }
    