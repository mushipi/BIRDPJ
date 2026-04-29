"""
03_train_model.py - BirdNETカスタム分類器の学習
"""
import argparse, os, subprocess, sys
from pathlib import Path
import yaml

def load_config():
    with open(Path(__file__).parent.parent / "config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def verify_training_data(d):
    if not d.exists():
        print(f"Error: {d} not found"); return False
    dirs = [x for x in d.iterdir() if x.is_dir()]
    print(f"Classes: {len(dirs)}")
    for x in sorted(dirs):
        n = len(list(x.glob("*.wav")))
        print(f"  {x.name}: {n} files")
    return bool(dirs)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input-dir", type=str, default=None)
    p.add_argument("--output-dir", type=str, default=None)
    p.add_argument("--epochs", type=int, default=None)
    p.add_argument("--batch-size", type=int, default=None)
    p.add_argument("--learning-rate", type=float, default=None)
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    cfg = load_config()
    t = cfg["training"]; pp = cfg["preprocessing"]
    inp = Path(a.input_dir or pp["output_dir"])
    out = Path(a.output_dir or t["output_dir"])
    ep = a.epochs or t["epochs"]
    bs = a.batch_size or t["batch_size"]
    lr = a.learning_rate or t["learning_rate"]
    print("BirdNET Train"); print("=" * 50)
    if not verify_training_data(inp): sys.exit(1)
    out.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "birdnet_analyzer.train",
           "--i", str(inp.resolve()), "--o", str(out.resolve()),
           "--epochs", str(ep), "--batch_size", str(bs),
           "--learning_rate", str(lr)]
    print(f"CMD: {' '.join(cmd)}")
    if a.dry_run: print("(dry run)"); return
    subprocess.run(cmd, check=True)
    print(f"Done! Model: {out}")

if __name__ == "__main__":
    main()
