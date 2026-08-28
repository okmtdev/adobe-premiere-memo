# adobe-premiere-memo

**AI を活用した動画編集・動画制作の操作マニュアル**（Adobe Premiere Pro × Claude × Gemini）

YouTube に投稿する動画を、AI の力を借りてできるだけ楽に作るための手順書です。
動画編集がまったく初めての方でも読めるように書いています。

## 前提環境

このマニュアルは以下を持っている前提で書かれています。

| 項目 | 状態 |
|---|---|
| Adobe Premiere Pro | サブスクリプション契約済み |
| Adobe Stock | サブスクリプション契約済み |
| Claude | claude.ai のアカウントあり（**API キーは発行不可**） |
| Gemini | Google アカウントあり（**API キーも発行可能**） |

## マニュアルの歩き方

**動画編集が初めての方**は、上から順に読むのがおすすめです。
「とにかく1本作りたい」という方は、`01` → `06`（実践レシピ）に飛んでも大丈夫です。

| # | ドキュメント | 内容 |
|---|---|---|
| 01 | [Premiere Pro 超入門](docs/01_premiere-basics.md) | 最低限の用語・画面の見方・はじめての1本の作り方 |
| 02 | [Premiere Pro の AI 機能](docs/02_premiere-ai-features.md) | 文字起こし・自動字幕・スピーチ強調・生成拡張などの使い方 |
| 03 | [Adobe Stock の使い方](docs/03_adobe-stock.md) | 素材の探し方・ライセンスの注意点 |
| 04 | [Claude の活用法](docs/04_claude.md) | API キーなしでも十分使える、企画・台本・文章まわりの相棒 |
| 05 | [Gemini の活用法](docs/05_gemini.md) | アプリ・AI Studio・API（動画理解 / 音声合成 / 動画生成） |
| 06 | [実践レシピ](docs/06_workflows.md) | 企画から投稿まで、動画が1本できるまでの具体的な流れ×3パターン |
| 07 | [プロンプト集](docs/07_prompts.md) | コピペで使える AI への頼み方テンプレート |
| 08 | [FAQ・用語集](docs/08_faq-glossary.md) | つまずきやすいポイントと用語の意味 |

## スクリプト（Gemini API 活用）

`scripts/gemini/` に、Gemini API キーで動く実用スクリプトを置いています。
セットアップ方法は [scripts/gemini/README.md](scripts/gemini/README.md) を見てください。

| スクリプト | できること |
|---|---|
| `generate_youtube_metadata.py` | 文字起こしから タイトル案・概要欄・タグ・チャプター を自動生成 |
| `translate_srt.py` | 字幕ファイル（.srt）をタイムコードを保ったまま翻訳 |
| `generate_narration.py` | 台本テキストからナレーション音声（.wav）を生成 |
| `video_to_chapters.py` | 動画ファイルを AI が視聴してチャプター案・ショート切り出し案を提案 |

## 注意事項

- 本マニュアルの情報は **2026年7月時点** のものです。Premiere Pro や各 AI サービスは更新が速いため、メニュー名や料金は変わることがあります。迷ったら各ドキュメント内の公式リンクを確認してください。
- 生成 AI の出力（文章・画像・音声・映像）を動画で使う際のルールは [docs/06_workflows.md の投稿前チェックリスト](docs/06_workflows.md#投稿前チェックリスト) と [docs/08 の FAQ](docs/08_faq-glossary.md) にまとめています。
