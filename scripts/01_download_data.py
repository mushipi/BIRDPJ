"""
01_download_data.py
北部九州の野鳥音声データをXeno-cantoからダウンロード

使い方:
    # 全対象県をダウンロード
    uv run python scripts/01_download_data.py

    # 特定の県のみ（福岡・大分）
    uv run python scripts/01_download_data.py --pref fukuoka oita

    # メタデータのみ確認（ダウンロードなし）
    uv run python scripts/01_download_data.py --metadata-only

    # 特定の種のみ
    uv run python scripts/01_download_data.py --species "Japanese Bush Warbler" "Brown-eared Bulbul"
"""

import argparse
import os
import sys
import time
from pathlib import Path

import yaml
from dotenv import load_dotenv

# プロジェクトルートから.envを読み込み
load_dotenv(Path(__file__).parent.parent / ".env")

from xcapi.query import QueryBuilder
from xcapi.client import XenoCantoClient
from xcapi.downloader import Downloader


def load_config() -> dict:
    """config.yamlを読み込む"""
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_prefecture_bbox(config: dict, pref_key: str) -> dict:
    """県のバウンディングボックスを取得"""
    return config["prefectures"][pref_key]


def download_species_for_bbox(
    client: XenoCantoClient,
    species_name: str,
    bbox: dict,
    quality: str,
    output_dir: str,
    metadata_only: bool = False,
    max_recordings: int = 100,
) -> int:
    """
    指定したバウンディングボックス内で特定の種の音声をダウンロード
    
    Returns:
        ダウンロードした録音数
    """
    query = (
        QueryBuilder()
        .group("birds")
        .english_name(species_name)
        .bounding_box(
            bbox["lat_min"], bbox["lon_min"],
            bbox["lat_max"], bbox["lon_max"]
        )
        .quality(quality)
        .build()
    )

    print(f"  クエリ: {query}")

    try:
        recordings = client.search(query)
    except Exception as e:
        print(f"  ⚠ 検索エラー: {e}")
        return 0

    if not recordings:
        print(f"  → 録音なし")
        return 0

    # 最大数で制限
    if len(recordings) > max_recordings:
        recordings = recordings[:max_recordings]

    print(f"  → {len(recordings)} 件の録音が見つかりました")

    # 種名でサブフォルダ作成
    species_dir = species_name.replace(" ", "_")
    species_output = os.path.join(output_dir, species_dir)

    downloader = Downloader(output_dir=species_output)

    if metadata_only:
        downloader.save_metadata_only(recordings)
        print(f"  → メタデータを保存しました")
    else:
        downloader.download_recordings(recordings)
        print(f"  → ダウンロード完了")

    return len(recordings)


def download_species_country_wide(
    client: XenoCantoClient,
    species_name: str,
    country: str,
    quality: str,
    output_dir: str,
    metadata_only: bool = False,
    max_recordings: int = 100,
) -> int:
    """
    国全体で特定の種の音声をダウンロード（bboxがヒットしない場合のフォールバック）
    """
    query = (
        QueryBuilder()
        .group("birds")
        .english_name(species_name)
        .country(country)
        .quality(quality)
        .build()
    )

    print(f"  クエリ (全国): {query}")

    try:
        recordings = client.search(query)
    except Exception as e:
        print(f"  ⚠ 検索エラー: {e}")
        return 0

    if not recordings:
        print(f"  → 録音なし")
        return 0

    if len(recordings) > max_recordings:
        recordings = recordings[:max_recordings]

    print(f"  → {len(recordings)} 件の録音が見つかりました")

    species_dir = species_name.replace(" ", "_")
    species_output = os.path.join(output_dir, species_dir)

    downloader = Downloader(output_dir=species_output)

    if metadata_only:
        downloader.save_metadata_only(recordings)
        print(f"  → メタデータを保存しました")
    else:
        downloader.download_recordings(recordings)
        print(f"  → ダウンロード完了")

    return len(recordings)


def download_species_worldwide(
    client: XenoCantoClient,
    species_name: str,
    quality: str,
    output_dir: str,
    metadata_only: bool = False,
    max_recordings: int = 100,
) -> int:
    """
    世界中で特定の種の音声をダウンロード（最終フォールバック）
    """
    query = (
        QueryBuilder()
        .group("birds")
        .english_name(species_name)
        .quality(quality)
        .build()
    )

    print(f"  クエリ (世界): {query}")

    try:
        recordings = client.search(query)
    except Exception as e:
        print(f"  ⚠ 検索エラー: {e}")
        return 0

    if not recordings:
        print(f"  → 録音なし")
        return 0

    if len(recordings) > max_recordings:
        recordings = recordings[:max_recordings]

    print(f"  → {len(recordings)} 件の録音が見つかりました")

    species_dir = species_name.replace(" ", "_")
    species_output = os.path.join(output_dir, species_dir)

    downloader = Downloader(output_dir=species_output)

    if metadata_only:
        downloader.save_metadata_only(recordings)
        print(f"  → メタデータを保存しました")
    else:
        downloader.download_recordings(recordings)
        print(f"  → ダウンロード完了")

    return len(recordings)


def main():
    parser = argparse.ArgumentParser(
        description="北部九州の野鳥音声データをXeno-cantoからダウンロード"
    )
    parser.add_argument(
        "--pref",
        nargs="*",
        default=None,
        help="対象の県 (例: fukuoka saga oita nagasaki kumamoto)。"
             "省略時はconfig.yamlのtarget_prefecturesを使用",
    )
    parser.add_argument(
        "--all-japan",
        action="store_true",
        help="県フィルタを使わず日本全国で検索",
    )
    parser.add_argument(
        "--species",
        nargs="*",
        default=None,
        help="対象の種（英名）。省略時はconfig.yamlの全種",
    )
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="メタデータのみ取得（音声ファイルはダウンロードしない）",
    )
    parser.add_argument(
        "--max-per-species",
        type=int,
        default=None,
        help="種あたりの最大録音数。省略時はconfig.yamlの設定値",
    )
    args = parser.parse_args()

    # 設定読み込み
    config = load_config()
    download_cfg = config["download"]
    output_dir = download_cfg["output_dir"]
    quality = download_cfg["quality"]
    max_recordings = args.max_per_species or download_cfg.get("max_recordings_per_species", 100)

    # APIキー確認
    api_key = os.environ.get("XENO_CANTO_API_KEY")
    if not api_key:
        print("❌ XENO_CANTO_API_KEY が設定されていません。.envファイルを確認してください。")
        sys.exit(1)

    print(f"🔑 APIキー: {api_key[:8]}...{api_key[-4:]}")

    # XenoCantoクライアント初期化
    client = XenoCantoClient(api_key=api_key)

    # 対象種リスト
    if args.species:
        species_list = [{"en": s} for s in args.species]
    else:
        species_list = config["target_species"]

    # 対象県リスト
    if args.all_japan:
        prefectures = None
        print("\n📍 検索範囲: 日本全国")
    else:
        pref_keys = args.pref or config.get("target_prefectures", [])
        prefectures = []
        for pk in pref_keys:
            if pk not in config["prefectures"]:
                print(f"⚠ 不明な県キー: {pk} (使用可能: {list(config['prefectures'].keys())})")
                continue
            prefectures.append((pk, config["prefectures"][pk]))
        print(f"\n📍 対象県: {', '.join(p[1]['name'] for p in prefectures)}")

    print(f"🐦 対象種数: {len(species_list)}")
    print(f"📊 品質フィルタ: {quality}")
    print(f"📁 出力先: {output_dir}")
    print(f"{'📋 メタデータのみ' if args.metadata_only else '⬇ ダウンロードモード'}")
    print("=" * 60)

    # メイン処理
    os.makedirs(output_dir, exist_ok=True)
    total_downloads = 0
    results = []

    for i, species_info in enumerate(species_list, 1):
        species_name = species_info["en"]
        print(f"\n[{i}/{len(species_list)}] 🐦 {species_name}")

        species_count = 0

        if prefectures:
            # 県ごとにダウンロード
            for pref_key, pref_info in prefectures:
                print(f"  📍 {pref_info['name']}:")
                count = download_species_for_bbox(
                    client=client,
                    species_name=species_name,
                    bbox=pref_info,
                    quality=quality,
                    output_dir=output_dir,
                    metadata_only=args.metadata_only,
                    max_recordings=max_recordings,
                )
                species_count += count
                # API rate limit対策
                time.sleep(1)

            # フォールバック: 県で見つからない場合は全国で検索
            if species_count == 0:
                print(f"  ⚠ 県別で見つかりませんでした。日本全国で検索します...")
                count = download_species_country_wide(
                    client=client,
                    species_name=species_name,
                    country="Japan",
                    quality=quality,
                    output_dir=output_dir,
                    metadata_only=args.metadata_only,
                    max_recordings=max_recordings,
                )
                species_count += count
                time.sleep(1)

            # 第2フォールバック: 日本で見つからない場合は世界中で検索
            if species_count == 0:
                print(f"  ⚠ 日本国内で見つかりませんでした。世界中で検索します...")
                count = download_species_worldwide(
                    client=client,
                    species_name=species_name,
                    quality=quality,
                    output_dir=output_dir,
                    metadata_only=args.metadata_only,
                    max_recordings=max_recordings,
                )
                species_count += count
                time.sleep(1)
        elif args.all_japan:
            # 日本全国で検索
            count = download_species_country_wide(
                client=client,
                species_name=species_name,
                country="Japan",
                quality=quality,
                output_dir=output_dir,
                metadata_only=args.metadata_only,
                max_recordings=max_recordings,
            )
            species_count += count
            time.sleep(1)
        else:
            # 北部九州全体のbboxで検索
            bbox = config["northern_kyushu_bbox"]
            count = download_species_for_bbox(
                client=client,
                species_name=species_name,
                bbox=bbox,
                quality=quality,
                output_dir=output_dir,
                metadata_only=args.metadata_only,
                max_recordings=max_recordings,
            )
            species_count += count
            time.sleep(1)

        total_downloads += species_count
        results.append({"species": species_name, "count": species_count})

    # サマリー表示
    print("\n" + "=" * 60)
    print("📊 ダウンロードサマリー")
    print("=" * 60)
    for r in results:
        status = "✅" if r["count"] > 0 else "⚠"
        print(f"  {status} {r['species']}: {r['count']} 件")
    print(f"\n  合計: {total_downloads} 件")
    print(f"  録音なし: {sum(1 for r in results if r['count'] == 0)} 種")


if __name__ == "__main__":
    main()
