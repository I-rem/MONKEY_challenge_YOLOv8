import json
from datetime import datetime

data = {
    "model": "YOLOv11",
    "dataset": "kidney_biopsies_test_set",
    "date": datetime.utcnow().isoformat() + "Z",
    "metrics": {
        "precision": 0.812,
        "recall": 0.789,
        "f1_score": 0.800,
        "mAP_0.5": 0.867,
        "mAP_0.5:0.95": 0.654
    },
    "classes": {
        "mononuclear_cell": {
            "precision": 0.82,
            "recall": 0.78,
            "f1_score": 0.80,
            "ap_0.5": 0.87,
            "ap_0.5:0.95": 0.66
        }
    },
    "notes": "Dummy JSON for evaluation testing"
}

with open("monkey-evaluation-details.json", "w") as f:
    json.dump(data, f, indent=2)
