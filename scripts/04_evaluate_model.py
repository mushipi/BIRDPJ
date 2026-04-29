"""
04_evaluate_model.py - 学習済カスタム分類器の評価
"""
import argparse, sys
from pathlib import Path
import subprocess
import yaml

def load_config():
    with open(Path(__file__).parent.parent / "config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--test-dir", type=str, required=True, help="テストデータディレクトリ")
    p.add_argument("--model-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default="./results")
    a = p.parse_args()
    cfg = load_config()
    model_dir = Path(a.model_dir or cfg["training"]["output_dir"])
    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    # Find custom classifier
    classifiers = list(model_dir.glob("*.tflite"))
    if not classifiers:
        print(f"No classifier found in {model_dir}")
        sys.exit(1)
    classifier = classifiers[0]
    print(f"Classifier: {classifier}")
    # Run BirdNET analysis with custom classifier
    cmd = [sys.executable, "-m", "birdnet_analyzer.analyze",
           "--i", str(Path(a.test_dir).resolve()),
           "--o", str(out.resolve()),
           "--classifier", str(classifier.resolve())]
    print(f"CMD: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print(f"Results: {out}")

if __name__ == "__main__":
    main()
