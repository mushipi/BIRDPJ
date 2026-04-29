"""
02_prepare_dataset.py
ダウンロード済みの音声データをBirdNET学習用に前処理

処理内容:
1. 音声ファイルを3秒セグメントに分割
2. 48kHz モノラルにリサンプリング
3. BirdNET学習用フォルダ構造に配置
4. Backgroundフォルダの作成（無音/低エネルギー区間を抽出）

使い方:
    uv run python scripts/02_prepare_dataset.py
    uv run python scripts/02_prepare_dataset.py --min-segments 20
"""

import argparse
import os
from pathlib import Path

import numpy as np
import yaml
import soundfile as sf
import librosa


def load_config() -> dict:
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def segment_audio(
    audio: np.ndarray,
    sr: int,
    segment_length_sec: float = 3.0,
    overlap_sec: float = 0.0,
) -> list[np.ndarray]:
    """音声を固定長セグメントに分割"""
    segment_length = int(segment_length_sec * sr)
    hop_length = int((segment_length_sec - overlap_sec) * sr)
    segments = []

    for start in range(0, len(audio) - segment_length + 1, hop_length):
        segment = audio[start : start + segment_length]
        segments.append(segment)

    return segments


def is_silent(audio: np.ndarray, threshold_db: float = -40.0) -> bool:
    """セグメントがほぼ無音かどうか判定"""
    rms = np.sqrt(np.mean(audio ** 2))
    if rms == 0:
        return True
    db = 20 * np.log10(rms)
    return db < threshold_db


def process_species_directory(
    input_dir: Path,
    output_dir: Path,
    background_dir: Path,
    target_sr: int = 48000,
    segment_length_sec: float = 3.0,
) -> tuple[int, int]:
    """
    1つの種のディレクトリを処理
    
    Returns:
        (種のセグメント数, 背景セグメント数)
    """
    species_segments = 0
    background_segments = 0

    # 音声ファイルを検索
    audio_extensions = {".mp3", ".wav", ".flac", ".ogg", ".m4a"}
    audio_files = []
    for ext in audio_extensions:
        audio_files.extend(input_dir.rglob(f"*{ext}"))

    if not audio_files:
        return 0, 0

    for audio_file in audio_files:
        try:
            # 音声読み込み（モノラル、ターゲットSRにリサンプリング）
            audio, sr = librosa.load(
                str(audio_file), sr=target_sr, mono=True
            )

            # 3秒セグメントに分割
            segments = segment_audio(audio, sr, segment_length_sec)

            for idx, segment in enumerate(segments):
                if is_silent(segment):
                    # 無音セグメントは背景ノイズとして保存
                    bg_filename = f"{audio_file.stem}_bg_{idx:04d}.wav"
                    bg_path = background_dir / bg_filename
                    sf.write(str(bg_path), segment, sr, subtype="PCM_16")
                    background_segments += 1
                else:
                    # 有音セグメントは種データとして保存
                    seg_filename = f"{audio_file.stem}_{idx:04d}.wav"
                    seg_path = output_dir / seg_filename
                    sf.write(str(seg_path), segment, sr, subtype="PCM_16")
                    species_segments += 1

        except Exception as e:
            print(f"    ⚠ 処理エラー: {audio_file.name} - {e}")
            continue

    return species_segments, background_segments


def main():
    parser = argparse.ArgumentParser(
        description="ダウンロード済みデータをBirdNET学習用に前処理"
    )
    parser.add_argument(
        "--min-segments",
        type=int,
        default=None,
        help="種あたり最低セグメント数（これ以下は除外）",
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=None,
        help="入力ディレクトリ（省略時はconfig.yamlのdownload.output_dir）",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="出力ディレクトリ（省略時はconfig.yamlのpreprocessing.output_dir）",
    )
    args = parser.parse_args()

    config = load_config()
    preproc_cfg = config["preprocessing"]

    input_dir = Path(args.input_dir or config["download"]["output_dir"])
    output_dir = Path(args.output_dir or preproc_cfg["output_dir"])
    target_sr = preproc_cfg["sample_rate"]
    segment_length = preproc_cfg["segment_length_sec"]
    min_segments = args.min_segments or preproc_cfg.get("min_segments_per_species", 10)

    print("🔧 BirdNET学習用データ前処理")
    print(f"  入力: {input_dir}")
    print(f"  出力: {output_dir}")
    print(f"  サンプルレート: {target_sr} Hz")
    print(f"  セグメント長: {segment_length} 秒")
    print(f"  最低セグメント数: {min_segments}")
    print("=" * 60)

    # Backgroundフォルダ作成
    background_dir = output_dir / "Background"
    background_dir.mkdir(parents=True, exist_ok=True)

    # 入力ディレクトリの種フォルダを列挙
    if not input_dir.exists():
        print(f"❌ 入力ディレクトリが存在しません: {input_dir}")
        return

    species_dirs = [d for d in input_dir.iterdir() if d.is_dir()]
    if not species_dirs:
        print("❌ 種フォルダが見つかりません")
        return

    print(f"\n📂 {len(species_dirs)} 種のフォルダを検出\n")

    results = []
    total_species_segments = 0
    total_bg_segments = 0

    for i, species_input in enumerate(sorted(species_dirs), 1):
        species_name = species_input.name
        print(f"[{i}/{len(species_dirs)}] 🐦 {species_name}")

        # 出力フォルダ作成
        species_output = output_dir / species_name
        species_output.mkdir(parents=True, exist_ok=True)

        # 処理実行
        sp_count, bg_count = process_species_directory(
            input_dir=species_input,
            output_dir=species_output,
            background_dir=background_dir,
            target_sr=target_sr,
            segment_length_sec=segment_length,
        )

        print(f"    → 種セグメント: {sp_count}, 背景: {bg_count}")

        # 最低セグメント数チェック
        if sp_count < min_segments:
            print(f"    ⚠ セグメント数不足 ({sp_count} < {min_segments}) - 除外対象")
            # 出力フォルダを削除
            import shutil
            if species_output.exists():
                shutil.rmtree(species_output)

        total_species_segments += sp_count
        total_bg_segments += bg_count
        results.append({
            "species": species_name,
            "segments": sp_count,
            "background": bg_count,
            "included": sp_count >= min_segments,
        })

    # サマリー
    included = [r for r in results if r["included"]]
    excluded = [r for r in results if not r["included"]]

    print("\n" + "=" * 60)
    print("📊 前処理サマリー")
    print("=" * 60)
    print(f"  有効な種: {len(included)} / {len(results)}")
    print(f"  種セグメント合計: {total_species_segments}")
    print(f"  背景セグメント合計: {total_bg_segments}")

    if excluded:
        print(f"\n  ⚠ 除外された種 ({len(excluded)}):")
        for r in excluded:
            print(f"    - {r['species']} ({r['segments']} セグメント)")

    print(f"\n  📁 学習用データ: {output_dir}")
    print(f"  📂 フォルダ構造:")

    training_dirs = [d for d in output_dir.iterdir() if d.is_dir()]
    for d in sorted(training_dirs)[:10]:
        file_count = len(list(d.glob("*.wav")))
        print(f"    {d.name}/ ({file_count} files)")
    if len(training_dirs) > 10:
        print(f"    ... 他 {len(training_dirs) - 10} フォルダ")


if __name__ == "__main__":
    main()
