# BIRDPJ — 北部九州野鳥 BirdNET 追加学習

北部九州（福岡・佐賀・長崎・大分・熊本）の野鳥音声データを Xeno-canto から収集し、BirdNET モデルに追加学習させるパイプライン。

## パイプライン構成

```
01_download_data.py    Xeno-canto API から録音データを取得
02_prepare_dataset.py  3 秒セグメントに分割・前処理
03_train_model.py      BirdNET Custom Classifier を追加学習
04_evaluate_model.py   精度評価・混同行列の出力
```

## 対象種（抜粋）

身近な鳥（スズメ・ヒヨドリ・メジロ）、水辺の鳥（カワセミ・アオサギ）、猛禽類（トビ・ノスリ）ほか北部九州で観察される約 40 種。`config.yaml` で追加・変更可能。

## セットアップ

```bash
# 依存パッケージのインストール（uv 推奨）
uv sync

# Xeno-canto API キーを設定
cp .env.example .env
# .env に XENOCANTO_API_KEY を記入
```

## 使い方

```bash
# 1. データダウンロード（全県）
uv run python scripts/01_download_data.py

# 特定の県のみ
uv run python scripts/01_download_data.py --pref fukuoka oita

# メタデータ確認のみ（ダウンロードなし）
uv run python scripts/01_download_data.py --metadata-only

# 2. データセット準備
uv run python scripts/02_prepare_dataset.py

# 3. 学習
uv run python scripts/03_train_model.py

# 4. 評価
uv run python scripts/04_evaluate_model.py
```

## 設定（config.yaml）

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `download.max_recordings_per_species` | 100 | 種あたり最大録音数 |
| `preprocessing.segment_length_sec` | 3 | セグメント長（BirdNET 固定） |
| `training.epochs` | 100 | 学習エポック数 |

## データ構成

```
data/
  raw/          Xeno-canto からダウンロードした生データ
  training/     前処理済みセグメント
models/         学習済みカスタム分類器
```
