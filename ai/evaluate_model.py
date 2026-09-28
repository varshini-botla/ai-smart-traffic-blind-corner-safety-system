"""
Inspect and Display Genuine AI Model Evaluation Metrics
"""

import json
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
METADATA_FILE = CURRENT_DIR / "models" / "model_metadata.json"


def display_evaluation():
    """Load and print genuine stored evaluation metrics."""
    if not METADATA_FILE.exists():
        print("No trained model metadata found. Run `python ai/train_model.py` first.")
        return

    with open(METADATA_FILE, "r") as f:
        meta = json.load(f)

    print("\n" + "=" * 60)
    print(f"AI MODEL EVALUATION: {meta['model_name']} (v{meta['model_version']})")
    print("=" * 60)
    print(f"Algorithm:       {meta['algorithm']}")
    print(f"Dataset:         {meta['dataset_name']} ({meta['dataset_type']})")
    print(f"Total Samples:   {meta['sample_counts']['total_samples']} (Train: {meta['sample_counts']['train_samples']}, Test: {meta['sample_counts']['test_samples']})")
    print(f"Training Date:   {meta['training_date']}")
    print("-" * 60)
    print("EVALUATION METRICS (Calculated on held-out 20% test split):")
    print(f"  • Overall Accuracy:    {meta['metrics']['accuracy'] * 100:.2f}%")
    print(f"  • Macro F1-Score:      {meta['metrics']['f1_macro']:.4f}")
    print(f"  • Weighted F1-Score:   {meta['metrics']['f1_weighted']:.4f}")
    print(f"  • Macro Precision:     {meta['metrics']['precision_macro']:.4f}")
    print(f"  • Macro Recall:        {meta['metrics']['recall_macro']:.4f}")
    print("-" * 60)
    print("PER-CLASS PERFORMANCE:")
    print(f"{'Class':<16} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'Support':<8}")
    print("-" * 60)
    for cls, metrics in meta["per_class_metrics"].items():
        print(f"{cls:<16} | {metrics['precision']:<10.4f} | {metrics['recall']:<10.4f} | {metrics['f1_score']:<10.4f} | {metrics['support']:<8}")

    print("-" * 60)
    print("CONFUSION MATRIX:")
    labels = meta["confusion_matrix"]["labels"]
    matrix = meta["confusion_matrix"]["matrix"]
    print(f"{'Actual \\ Pred':<16} | " + " | ".join([f"{l[:10]:<10}" for l in labels]))
    print("-" * 60)
    for i, actual in enumerate(labels):
        row_str = " | ".join([f"{matrix[i][j]:<10}" for j in range(len(labels))])
        print(f"{actual:<16} | {row_str}")

    print("-" * 60)
    print("FEATURE IMPORTANCE RANKING:")
    for feat, imp in meta["feature_importances"].items():
        bar = "#" * int(imp * 40)
        print(f"  {feat:<25} : {imp:.4f} {bar}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    display_evaluation()
