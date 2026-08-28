#!/usr/bin/env python3
"""台本テキスト(.txt)からナレーション音声(.wav)を生成します（Gemini の音声合成 / TTS）。

使い方:
    python generate_narration.py script.txt
    python generate_narration.py script.txt --voice Puck --style "元気なトーンで、テンポよく"

出力される .wav（24kHz / 16bit / モノラル）は、そのまま Premiere Pro に読み込めます。

事前準備（詳細は scripts/gemini/README.md）:
    pip install -r requirements.txt
    export GEMINI_API_KEY="あなたのAPIキー"
"""
from __future__ import annotations

import argparse
import os
import sys
import wave
from pathlib import Path

DEFAULT_MODEL = "gemini-2.5-flash-tts"
DEFAULT_VOICE = "Kore"  # 他の声: Puck, Charon, Leda など（公式ドキュメント参照）

SAMPLE_RATE = 24_000  # Gemini TTS の出力仕様
SAMPLE_WIDTH = 2      # 16bit
CHANNELS = 1          # モノラル

CHUNK_CHARS = 3_000       # 1回のリクエストで読み上げる最大文字数
PAUSE_BETWEEN_CHUNKS = 0.4  # チャンク間に挟む無音（秒）


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


def split_script(text: str) -> list[str]:
    """段落（空行）区切りで、CHUNK_CHARS を超えないようにまとめる。"""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if current and len(current) + len(para) + 2 > CHUNK_CHARS:
            chunks.append(current)
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para
        # 1段落だけで上限を超える場合はそのまま1チャンクにする
        while len(current) > CHUNK_CHARS * 2:
            chunks.append(current[:CHUNK_CHARS])
            current = current[CHUNK_CHARS:]
    if current:
        chunks.append(current)
    return chunks


def synthesize(client, model: str, voice: str, style: str, text: str) -> bytes:
    """テキスト1チャンクを音声（PCMバイト列）に変換する。"""
    from google.genai import types

    if style:
        contents = f"次のナレーション原稿を、「{style}」という調子で読み上げてください。\n\n{text}"
    else:
        contents = text

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                )
            ),
        ),
    )
    try:
        return response.candidates[0].content.parts[0].inline_data.data
    except (AttributeError, IndexError, TypeError):
        sys.exit(
            "エラー: 音声データを取得できませんでした。\n"
            f"モデル名（{model}）が TTS 対応か、公式ドキュメントで確認してください:\n"
            "https://ai.google.dev/gemini-api/docs/speech-generation"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="台本からナレーション音声(.wav)を生成")
    parser.add_argument("script", help="台本テキストファイル（.txt）")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help=f"声の種類（既定: {DEFAULT_VOICE}）")
    parser.add_argument("--style", default="落ち着いた解説調で、聞き取りやすい速さ", help="読み方の指示（空文字で指示なし）")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"使用モデル（既定: {DEFAULT_MODEL}）")
    parser.add_argument("-o", "--output", help="出力先 .wav（既定: 入力名_narration.wav）")
    args = parser.parse_args()

    src = Path(args.script)
    if not src.exists():
        sys.exit(f"エラー: ファイルが見つかりません: {src}")

    text = src.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        sys.exit("エラー: 台本が空です。")

    chunks = split_script(text)
    client = get_client()

    print(f"音声生成中...（{len(chunks)} パート / 声: {args.voice} / モデル: {args.model}）")
    silence = b"\x00" * int(SAMPLE_RATE * PAUSE_BETWEEN_CHUNKS) * SAMPLE_WIDTH

    pcm_parts: list[bytes] = []
    for i, chunk in enumerate(chunks, 1):
        print(f"  パート {i}/{len(chunks)} を生成中...")
        pcm_parts.append(synthesize(client, args.model, args.voice, args.style, chunk))

    out = Path(args.output) if args.output else src.with_name(f"{src.stem}_narration.wav")
    with wave.open(str(out), "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        for i, pcm in enumerate(pcm_parts):
            if i > 0:
                wf.writeframes(silence)
            wf.writeframes(pcm)

    duration = sum(len(p) for p in pcm_parts) / (SAMPLE_RATE * SAMPLE_WIDTH)
    print(f"✅ 保存しました: {out}（約 {duration/60:.1f} 分）")
    print("   Premiere Pro の「読み込み」からタイムラインに配置してください。")
    print("   発音がおかしい単語は、台本側をひらがなに直して再生成すると改善します。")


if __name__ == "__main__":
    main()
