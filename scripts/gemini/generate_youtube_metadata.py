#!/usr/bin/env python3
"""文字起こし(.txt / .srt)から YouTube 用のタイトル・概要欄・タグ・チャプター案を生成します。

使い方:
    python generate_youtube_metadata.py 文字起こし.txt
    python generate_youtube_metadata.py captions.srt --channel "初心者向け料理チャンネル。トーンは親しみやすく"

事前準備（詳細は scripts/gemini/README.md）:
    pip install -r requirements.txt
    export GEMINI_API_KEY="あなたのAPIキー"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

DEFAULT_MODEL = "gemini-2.5-flash"

PROMPT_TEMPLATE = """あなたは日本の YouTube チャンネル運営を支援する敏腕編集者です。
以下の動画の文字起こしを読み、視聴者に届きやすいメタデータを作成してください。

チャンネルの前提: {channel}

必ず次のキーを持つ JSON オブジェクトだけを出力してください:
{{
  "summary": "動画内容の要約（2〜3文）",
  "title_candidates": ["タイトル案を5つ。各60文字以内。煽りすぎず、検索されそうな言葉を含める"],
  "description": "概要欄の本文。最初の2行で内容が分かるように。全体400字程度。末尾に関連ハッシュタグを3つ",
  "tags": ["検索用タグを15個"],
  "chapters": [{{"time": "00:00", "title": "チャプター名（15文字以内）"}}],
  "notes": "制作者への補足やアドバイスがあれば（なければ空文字）"
}}

チャプターは、文字起こしにタイムコードが含まれる場合のみ、それを根拠に5〜8個作成してください
（必ず 00:00 から始めること）。タイムコードが無い場合は chapters を空配列にしてください。

--- 文字起こしここから ---
{transcript}
--- 文字起こしここまで ---
"""


def get_client():
    """環境変数の API キーで Gemini クライアントを作る。"""
    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
        sys.exit(
            "エラー: 環境変数 GEMINI_API_KEY が設定されていません。\n"
            '  Mac/Linux : export GEMINI_API_KEY="あなたのAPIキー"\n'
            '  Windows   : $env:GEMINI_API_KEY = "あなたのAPIキー"\n'
            "APIキーの発行方法は docs/05_gemini.md を参照してください。"
        )
    from google import genai

    return genai.Client()


def format_markdown(data: dict, source_name: str) -> str:
    lines = [f"# YouTube メタデータ案（{source_name}）", ""]
    if data.get("summary"):
        lines += ["## 内容の要約", "", data["summary"], ""]
    lines += ["## タイトル案", ""]
    for i, title in enumerate(data.get("title_candidates", []), 1):
        lines.append(f"{i}. {title}")
    lines += ["", "## 概要欄（コピペ用）", "", "```", data.get("description", ""), "```", ""]
    tags = data.get("tags", [])
    lines += ["## タグ（コピペ用）", "", "```", ",".join(tags), "```", ""]
    chapters = data.get("chapters", [])
    if chapters:
        lines += ["## チャプター（概要欄に貼り付け）", "", "```"]
        for ch in chapters:
            lines.append(f"{ch.get('time', '')} {ch.get('title', '')}")
        lines += ["```", ""]
    if data.get("notes"):
        lines += ["## AI からの補足", "", data["notes"], ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="文字起こしから YouTube メタデータを生成")
    parser.add_argument("transcript", help="文字起こしファイル（.txt または .srt）")
    parser.add_argument("--channel", default="（特に指定なし）", help="チャンネルの前提（ジャンル・視聴者・トーンなど）")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"使用モデル（既定: {DEFAULT_MODEL}）")
    parser.add_argument("-o", "--output", help="出力先 Markdown（既定: 入力名_metadata.md）")
    args = parser.parse_args()

    src = Path(args.transcript)
    if not src.exists():
        sys.exit(f"エラー: ファイルが見つかりません: {src}")

    transcript = src.read_text(encoding="utf-8", errors="replace").strip()
    if not transcript:
        sys.exit("エラー: ファイルが空です。")
    if len(transcript) > 400_000:
        print("⚠️ 文字起こしが非常に長いため、先頭 40 万文字のみ使用します。")
        transcript = transcript[:400_000]

    client = get_client()
    from google.genai import types

    print(f"Gemini（{args.model}）で生成中...")
    response = client.models.generate_content(
        model=args.model,
        contents=PROMPT_TEMPLATE.format(channel=args.channel, transcript=transcript),
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )

    try:
        data = json.loads(response.text)
    except (json.JSONDecodeError, TypeError):
        print("⚠️ JSON の解析に失敗しました。生の応答をそのまま表示します:\n")
        print(response.text)
        sys.exit(1)

    markdown = format_markdown(data, src.name)
    out = Path(args.output) if args.output else src.with_name(f"{src.stem}_metadata.md")
    out.write_text(markdown, encoding="utf-8")

    print("\n" + markdown)
    print(f"\n✅ 保存しました: {out}")


if __name__ == "__main__":
    main()
