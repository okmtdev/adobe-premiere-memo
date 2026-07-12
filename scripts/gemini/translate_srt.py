#!/usr/bin/env python3
"""字幕ファイル(.srt)を、番号とタイムコードを保ったまま翻訳します。

使い方:
    python translate_srt.py captions.srt                # 英語へ（デフォルト）
    python translate_srt.py captions.srt --lang 韓国語

事前準備（詳細は scripts/gemini/README.md）:
    pip install -r requirements.txt
    export GEMINI_API_KEY="あなたのAPIキー"
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

DEFAULT_MODEL = "gemini-2.5-flash"
BLOCKS_PER_REQUEST = 80  # 1回のリクエストで翻訳する字幕エントリ数

LANG_SUFFIX = {
    "英語": "en",
    "韓国語": "ko",
    "中国語": "zh",
    "スペイン語": "es",
    "フランス語": "fr",
    "ドイツ語": "de",
    "ポルトガル語": "pt",
    "インドネシア語": "id",
}

PROMPT_TEMPLATE = """以下は SRT 形式の字幕ファイルの一部です。{lang}に翻訳してください。

厳守するルール:
- 各エントリの「番号」と「タイムコード行（00:00:00,000 --> 00:00:00,000）」は一切変更しない
- テキスト行だけを自然な{lang}の口語に翻訳する（直訳より、字幕として読み切れる自然さを優先）
- エントリの数・順序を変えない
- 出力は SRT 形式のテキストのみ。説明文やコードブロック記号（```）は付けない

--- SRT ここから ---
{srt}
--- SRT ここまで ---
"""


def get_client():
    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
        sys.exit(
            "エラー: 環境変数 GEMINI_API_KEY が設定されていません。\n"
            '  Mac/Linux : export GEMINI_API_KEY="あなたのAPIキー"\n'
            '  Windows   : $env:GEMINI_API_KEY = "あなたのAPIキー"\n'
            "APIキーの発行方法は docs/05_gemini.md を参照してください。"
        )
    from google import genai

    return genai.Client()


def strip_code_fence(text: str) -> str:
    """モデルが ``` で囲んで返してきた場合に外す。"""
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n", "", text)
    text = re.sub(r"\n```$", "", text)
    return text.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="SRT 字幕をタイムコードを保ったまま翻訳")
    parser.add_argument("srt", help="翻訳する .srt ファイル")
    parser.add_argument("--lang", default="英語", help="翻訳先の言語（既定: 英語）")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"使用モデル（既定: {DEFAULT_MODEL}）")
    parser.add_argument("-o", "--output", help="出力先（既定: 入力名_en.srt など）")
    args = parser.parse_args()

    src = Path(args.srt)
    if not src.exists():
        sys.exit(f"エラー: ファイルが見つかりません: {src}")

    raw = src.read_text(encoding="utf-8-sig", errors="replace")
    blocks = [b.strip() for b in re.split(r"\n\s*\n", raw.strip()) if b.strip()]
    if not blocks:
        sys.exit("エラー: SRT のエントリが見つかりません。")

    client = get_client()

    translated_chunks: list[str] = []
    total = (len(blocks) + BLOCKS_PER_REQUEST - 1) // BLOCKS_PER_REQUEST
    for i in range(0, len(blocks), BLOCKS_PER_REQUEST):
        chunk = "\n\n".join(blocks[i : i + BLOCKS_PER_REQUEST])
        part_no = i // BLOCKS_PER_REQUEST + 1
        print(f"翻訳中... ({part_no}/{total})")
        response = client.models.generate_content(
            model=args.model,
            contents=PROMPT_TEMPLATE.format(lang=args.lang, srt=chunk),
        )
        translated_chunks.append(strip_code_fence(response.text or ""))

    result = "\n\n".join(translated_chunks).strip() + "\n"

    suffix = LANG_SUFFIX.get(args.lang, "translated")
    out = Path(args.output) if args.output else src.with_name(f"{src.stem}_{suffix}.srt")
    out.write_text(result, encoding="utf-8")

    # 簡単な整合性チェック（エントリ数の一致）
    out_blocks = [b for b in re.split(r"\n\s*\n", result.strip()) if b.strip()]
    if len(out_blocks) != len(blocks):
        print(
            f"⚠️ エントリ数が一致しません（元: {len(blocks)} / 翻訳後: {len(out_blocks)}）。"
            "出力ファイルを目視確認してください。"
        )

    print(f"✅ 保存しました: {out}")
    print("   YouTube Studio →「字幕」からアップロードできます。")


if __name__ == "__main__":
    main()
