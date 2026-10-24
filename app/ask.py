"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

ツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors, types

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str, temperature: float | None = None) -> str:
    client = genai.Client(api_key=get_api_key())
    # temperature を指定したときだけ config を渡す（省略時はモデルの既定値）
    config = types.GenerateContentConfig(temperature=temperature) if temperature is not None else None
    response = client.models.generate_content(model=MODEL, contents=question, config=config)

    # 入力（プロンプト）と出力（回答）のトークン数を表示する
    usage = response.usage_metadata
    if usage is not None:
        print(f"[tokens] 入力: {usage.prompt_token_count} / 出力: {usage.candidates_token_count}\n")

    return response.text


def chat_loop(temperature: float | None = None) -> None:
    """会話履歴を保ったまま、続けて質問できるモード（第1回 宿題：実装）。

    LLM自体は前の発言を覚えていない。chats.create() のセッションが履歴を保持し、
    send_message() のたびに履歴ごとモデルへ送り直すので、会話が続いて見える。
    """
    client = genai.Client(api_key=get_api_key())
    config = types.GenerateContentConfig(temperature=temperature) if temperature is not None else None
    chat = client.chats.create(model=MODEL, config=config)

    print("会話モード（空行か exit で終了）\n")
    while True:
        try:
            question = input("あなた> ").strip()
        except EOFError:
            break
        if question in ("", "exit"):
            break
        response = chat.send_message(question)
        print(f"\nAI> {response.text}")
        usage = response.usage_metadata
        if usage is not None:
            # 入力トークンは履歴の分だけ回を追うごとに増える
            print(f"[tokens] 入力: {usage.prompt_token_count} / 出力: {usage.candidates_token_count}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument("--temperature", type=float, default=None, help="生成のランダムさ（例: 0, 1.5）")
    parser.add_argument("--chat", action="store_true", help="会話履歴を保ったまま続けて質問する")
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    if args.temperature is not None:
        print(f"[temperature] {args.temperature}")
    try:
        if args.chat:
            chat_loop(args.temperature)
            return
        print(f"[質問] {args.question}\n")
        print(ask(args.question, args.temperature))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
