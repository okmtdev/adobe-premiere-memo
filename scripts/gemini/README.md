# Gemini API スクリプト集

Gemini API キーで動く、動画制作の定型作業を自動化するスクリプトです。
どれも「ターミナルで1行実行するだけ」で使えるように作ってあります。

| スクリプト | 入力 | 出力 |
|---|---|---|
| `generate_youtube_metadata.py` | 文字起こし（.txt / .srt） | タイトル案・概要欄・タグ・チャプター（Markdown） |
| `translate_srt.py` | 字幕（.srt） | 翻訳済み字幕（.srt、タイムコード維持） |
| `generate_narration.py` | 台本（.txt） | ナレーション音声（.wav、24kHz） |
| `video_to_chapters.py` | 動画ファイル（.mp4 等） | チャプター案・ショート切り出し案（Markdown） |

---

## セットアップ（最初の1回だけ）

### 1. Python を用意する

Python **3.10 以上**が必要です。ターミナル（Mac: ターミナル.app / Windows: PowerShell）で確認：

```bash
python3 --version   # Windows は python --version
```

入っていなければ [python.org](https://www.python.org/downloads/) からインストール（Windows はインストーラーで「Add python.exe to PATH」に必ずチェック）。

### 2. ライブラリをインストールする

このフォルダー（`scripts/gemini/`）に移動して：

```bash
cd scripts/gemini
python3 -m venv .venv                 # 仮想環境を作る（初回のみ）
source .venv/bin/activate             # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> 💡 次回からは `source .venv/bin/activate`（Windows: `.venv\Scripts\activate`）だけで OK。

### 3. API キーを設定する

[Google AI Studio](https://aistudio.google.com) で発行した API キー（→ [05章](../../docs/05_gemini.md#api-キーの発行手順)）を環境変数に設定します。

**Mac / Linux：**
```bash
export GEMINI_API_KEY="ここにAPIキー"
```
（毎回打つのが面倒なら `~/.zshrc` などに同じ行を追記）

**Windows（PowerShell）：**
```powershell
$env:GEMINI_API_KEY = "ここにAPIキー"
```
（恒久設定は `setx GEMINI_API_KEY "ここにAPIキー"` を1回実行 → ターミナルを開き直す）

> ⚠️ API キーをスクリプト内に直接書いたり、Git にコミットしたりしないでください。

---

## 使い方

### 📝 generate_youtube_metadata.py — タイトル・概要欄・タグ・チャプター生成

Premiere Pro から書き出した文字起こし（→ [02章](../../docs/02_premiere-ai-features.md#1-自動文字起こしすべての土台)）を渡します。

```bash
python generate_youtube_metadata.py 文字起こし.txt
python generate_youtube_metadata.py captions.srt --channel "初心者向け料理チャンネル。視聴者は20代一人暮らし。トーンは親しみやすく"
```

- 結果は画面に表示され、`文字起こし_metadata.md` にも保存されます。
- `--channel` でチャンネルの前提を渡すと精度が上がります。

### 🌍 translate_srt.py — 字幕の翻訳

```bash
python translate_srt.py captions.srt                 # 英語へ（デフォルト）
python translate_srt.py captions.srt --lang 韓国語   # 他言語も指定可
```

- 番号とタイムコードはそのまま、テキストだけ翻訳した `captions_en.srt` などを出力します。
- できた .srt は YouTube Studio の「字幕」からアップロードできます。

### 🎙 generate_narration.py — ナレーション音声生成

```bash
python generate_narration.py script.txt
python generate_narration.py script.txt --voice Puck --style "元気なトーンで、テンポよく"
```

- `script_narration.wav`（24kHz / モノラル）を出力。Premiere Pro にそのまま読み込めます。
- 声の種類（`--voice`）は [公式ドキュメント](https://ai.google.dev/gemini-api/docs/speech-generation)に一覧があります（例：Kore, Puck, Charon, Leda）。
- 長い台本は自動で分割して1本の WAV につなぎます。

### 🎬 video_to_chapters.py — 動画からチャプター案・ショート切り出し案

```bash
python video_to_chapters.py 完成動画.mp4
```

- 動画を Gemini にアップロードして「視聴」させ、チャプター案とショート向きの箇所を提案させます。
- ⚠️ アップロードには時間がかかります（動画の長さ次第で数分）。ファイルは 2GB まで。
- アップロードされた動画は Google 側に一時保存されます（既定で約48時間後に自動削除。スクリプトは処理後に削除を試みます）。

---

## よくあるエラー

| エラー | 原因と対処 |
|---|---|
| `GEMINI_API_KEY が設定されていません` | 上の「3. API キーを設定する」を実施。ターミナルを開き直した場合は再設定が必要 |
| `429 RESOURCE_EXHAUSTED` | 無料枠のレート制限。数十秒〜数分待って再実行。頻発するなら従量課金を検討（→ [05章](../../docs/05_gemini.md#無料枠と有料の違い)） |
| `400 API key not valid` | キーの貼り間違い。AI Studio で再確認・再発行 |
| `ModuleNotFoundError: google` | 仮想環境が有効になっていない。`source .venv/bin/activate` してから実行 |
| モデル名のエラー | モデルの世代交代の可能性。`--model` で [現行モデル](https://ai.google.dev/gemini-api/docs/models) を指定 |

## 料金の目安

- テキスト系（メタデータ生成・翻訳・動画理解）：無料枠内で収まることが多く、有料でも1回あたり数円以下のオーダーです。
- 音声合成（TTS）：テキストより単価は高めですが、動画1本のナレーションで大きな額にはなりません。
- 心配な場合は [Google AI Studio の Usage](https://aistudio.google.com) や Google Cloud コンソールで使用量を確認できます。最新単価は [料金ページ](https://ai.google.dev/gemini-api/docs/pricing) を参照。
