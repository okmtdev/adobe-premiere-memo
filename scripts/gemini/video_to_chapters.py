#!/usr/bin/env python3
"""動画ファイルを Gemini にアップロードして「視聴」させ、
チャプター案とショート切り出し案を提案させます。

使い方:
    python video_to_chapters.py 完成動画.mp4

注意:
    - アップロードと解析に数分かかることがあります（ファイルは 2GB まで）
    - アップロードした動画は Google 側に一時保存されます。
      このスクリプトは処理後に削除を試みます（既定でも約48時間で自動削除）

事前準備（詳細は scripts/gemini/README.md）:
    pip install -r requirements.txt
    export GEMINI_API_KEY="あなたのAPIキー"
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

DEFAULT_MODEL = "gemini-2.5-flash"

PROMPT = """あなたは日本の YouTube 編集者です。この動画を最初から最後まで確認し、
以下を Markdown で出力してください。

## 内容の要約
2〜3文で。

## チャプター案
- 「MM:SS チャプター名」の形式で5〜8個（必ず 00:00 から）
- チャプター名は15文字以内
- そのまま概要欄に貼れるよう、コードブロックにまとめる

## ショート切り出し案（3つ）
それぞれ:
- **切り出し範囲**: 開始タイムコード 〜 終了タイムコード（60秒以内）
- **選んだ理由**: フックの強さ・完結性の観点で
- **冒頭フックのテロップ案**: 15文字以内

## 改善メモ
テンポ・構成について気づいた点があれば2〜3個（なければ「特になし」）。
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


def state_name(file_obj) -> str:
    """SDK バージョン差異に耐える state 取得。"""
    state = getattr(file_obj, "state", None)
    return getattr(state, "name", None) or str(state or "")


def main() -> None:
    parser = argparse.ArgumentParser(description="動画からチャプター案・ショート切り出し案を生成")
    parser.add_argument("video", help="動画ファイル（.mp4 など、2GB まで）")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"使用モデル（既定: {DEFAULT_MODEL}）")
    parser.add_argument("-o", "--output", help="出力先 Markdown（既定: 入力名_chapters.md）")
    parser.add_argument("--keep", action="store_true", help="処理後もアップロードした動画を削除しない")
    args = parser.parse_args()

    src = Path(args.video)
    if not src.exists():
        sys.exit(f"エラー: ファイルが見つかりません: {src}")

    size_gb = src.stat().st_size / (1024**3)
    if size_gb > 2.0:
        sys.exit(f"エラー: ファイルが大きすぎます（{size_gb:.1f}GB / 上限 2GB）。"
                 "Premiere Pro で低解像度に書き出してから試してください。")

    client = get_client()

    print(f"アップロード中...（{size_gb*1024:.0f}MB。回線速度によっては数分かかります）")
    uploaded = client.files.upload(file=str(src))

    try:
        # Gemini 側の処理（動画の解析準備）が終わるまで待つ
        while state_name(uploaded) == "PROCESSING":
            print("  Gemini が動画を処理中...")
            time.sleep(10)
            uploaded = client.files.get(name=uploaded.name)

        if state_name(uploaded) == "FAILED":
            sys.exit("エラー: 動画の処理に失敗しました。形式（.mp4 推奨）やサイズを確認してください。")

        print(f"解析中...（{args.model}）")
        response = client.models.generate_content(
            model=args.model,
            contents=[uploaded, PROMPT],
        )
        result = (response.text or "").strip()
        if not result:
            sys.exit("エラー: 応答が空でした。時間をおいて再実行してください。")

        out = Path(args.output) if args.output else src.with_name(f"{src.stem}_chapters.md")
        out.write_text(f"# {src.name} の解析結果\n\n{result}\n", encoding="utf-8")

        print("\n" + result)
        print(f"\n✅ 保存しました: {out}")

    finally:
        if not args.keep:
            try:
                client.files.delete(name=uploaded.name)
                print("（アップロードした動画は削除しました）")
            except Exception:
                print("（アップロード動画の削除に失敗しましたが、約48時間で自動削除されます）")


if __name__ == "__main__":
    main()
