# 第3回 解答

## 演習

モデルはすべて `gemini-3.5-flash-lite`。ローカルの Mac で実行した。

- 第1回（素のLLM）とエージェントの回答の違い：
  - 「lecNN-start タグとは？」に対して、`app.ask` は NN を「Neural Network」と解釈し、「NN を学ぶ回のスターターコード」と答えた。講座名も「おそらく AIエンジニア育成プログラム2026」と推測していた（出力 359 トークン）。
  - `app.agent` は `search_glossary` を1回呼び、用語集の定義どおり「各回の演習開始時点のコードに付けた Git タグ（例: lec03-start）」と答えた。最後に「関係する回: 第1回」と付けていた。
- `--trace` で見えたツール呼び出し（ツール名と引数）：
  - 「LoRAとQLoRAの違いは？」では `search_glossary({'query': 'LoRA'})` と `search_glossary({'query': 'QLoRA'})` の2回。docstring の「query には用語を1つだけ入れる」どおり、2語に分けて呼んでいた。
- 1つの質問での LLM 呼び出し回数（`requests`）：
  - lecNN-start は `requests=2`、`tool_calls=1`。LoRA/QLoRA は `requests=2`、`tool_calls=2`。
  - 2回の検索は1回目の応答でまとめて出されるので、ツールを2回呼んでも LLM 呼び出しは増えなかった。
- 追加したツールと、docstring に書いた説明：
  - `make_quiz(lecture: int)`。指定した回の用語を用語集からランダムに1つ選び、`{"lecture", "question": "「用語」の意味は？", "answer": 定義}` を返す。用語がない回を指定したときは、用語がある回の一覧を返す。
  - docstring：「『第2回の確認問題を出して』『復習クイズがほしい』のように、学習者が理解を確かめる問題を求めたときに使う。返した answer は、学習者が答えるまで見せないこと」
  - 「第2回の内容から確認問題を1問出して」で `make_quiz({'lecture': 2})` が呼ばれた（`requests=2`）。答えは伏せ、問題だけを出した。
  - テストを2本追加した（第2回の用語から選ばれること、用語がない回の扱い）。

## 宿題

- 取り組んだレベル：発展 (a)（基礎・実装も実施）
- やったこと：
  - **発展 (a)**：`adk_agent/glossary_agent/agent.py` で、`INSTRUCTIONS` と `search_glossary`・`get_lecture_summary`・`make_quiz` をそのまま ADK（google-adk 2.14.0）の `Agent` に渡した。`adk run` で演習と同じ3問を投げ、ツール呼び出しはセッションの記録（session.db の events）から読んだ。`adk web` でも同じ質問を投げた。
  - **基礎**：一度に1か所だけ変え、各条件で同じ質問を3回ずつ実行した。リポジトリのファイルは変えず、差し替えたエージェントを別スクリプトで組んだ。
  - **実装**：`save_learning_log(topic, content)` を作り、`requires_approval=True` で登録した。エージェントの `output_type` を `[str, DeferredToolRequests]` にし、CLI で `[y/N]` を聞いて `DeferredToolResults` を渡し、続きを実行するようにした。ファイル名は日時から作った（topic を使うと `../` で保存先の外に書けるため）。TestModel を使ったテストを3本（承認待ちで止まる、承認後に保存される、拒否で保存されない）と、ツール単体のテストを1本追加した。
- 結果：

  **発展 (a)**：ツールの呼ばれ方は Pydantic AI 版と同じだった。

  | 質問 | Pydantic AI（`--trace`） | ADK（`adk run`） |
  |---|---|---|
  | lecNN-start タグとは？ | `search_glossary('lecNN-start タグ')` | 同じ |
  | LoRAとQLoRAの違いは？ | `search_glossary('LoRA')`、`('QLoRA')` | 同じ |
  | 第2回の確認問題を1問 | `make_quiz(lecture=2)` | 同じ（答えは伏せた） |
  | LLM 呼び出し | 各2回 | 3問で6回（各2回） |

  - 書き方の違い：Pydantic AI は `Agent(instructions=...)` を作ってから `agent.tool_plain(関数)` で1つずつ登録し、モデルは実行時に渡す。ADK は `Agent(model=, name=, instruction=, tools=[関数, ...])` にまとめて書き、`root_agent` という名前の変数を `adk run` / `adk web` が探して読み込む。
  - 戻り値の扱い：ADK は文字列の戻り値を `{'result': ...}` に包んでモデルに渡していた。
  - 会話の扱い：`adk run` は1つのセッションで履歴を引き継ぐ。1回目の入力トークンは質問ごとに 520 → 737 → 1479 と増えた。Pydantic AI の CLI は毎回新しい会話になる。
  - ADK は何も指定しなくても、リポジトリ直下の `.env` を自動で読み込んだ。会話は `adk_agent/glossary_agent/.adk/session.db` に保存された（提出には含めていない）。`adk web` では `--session_service_uri=memory://` を付けてメモリに置いた。
  - `adk web` の見え方：エージェントから3つのツールへのグラフが描かれ、実際に呼ばれた `search_glossary` だけが強調された。呼ばれなかった2つはグレーのまま。1つの質問は「Event 3 of 4」のようにイベント単位で前後に送れ、チャット欄にもツール呼び出しが `search_glossary("QLoRA")` のように出た。

  **基礎**（各3回。数字はツールの呼ばれ方が同じだった回数）

  | 変えたところ | 質問 | ツール呼び出し |
  |---|---|---|
  | なし | LoRAとQLoRAの違いは？ | 3/3 で `'LoRA'` と `'QLoRA'` の2回 |
  | docstring「1つだけ入れる（例: "LoRA"）」→「まとめて入れる（例: "LoRA QLoRA"）」 | 同上 | 3/3 で `'LoRA QLoRA'` の1回 |
  | なし | lecNN-start タグ／LoRAとは？ | 6/6 で検索した |
  | INSTRUCTIONS の「必ず search_glossary で用語集を確認する」を削除 | 同上 | 6/6 で検索した |
  | docstring の「用語や講座固有の言葉について答える前に使うこと」を削除 | 同上 | 6/6 で検索した |
  | 上の2つを両方削除 | 同上 | 6/6 で検索した |
  | INSTRUCTIONS の上の行を「一般的なAIの用語は、ツールを使わず自分の知識で答えてよい」に置き換え | 同上 | 6/6 で検索した |

  - 「まとめて」にしても回答の中身は変わらなかった。検索関数が空白を除いた部分一致で LoRA と QLoRA の両方を返したため。

  **実装**（「LoRAとQLoRAの違いを調べて、学習の記録として保存して」）

  | | 結果 |
  |---|---|
  | 最初の docstring（最後に「保存の前に利用者の確認がある。」と書いた） | 2回とも `save_learning_log` を呼ばず、回答の最後に「保存しますか？」と文章で聞き返して終わった |
  | 上の一文を削除して `y` | `[承認待ち] save_learning_log({'topic': 'LoRAとQLoRAの違い', 'content': ...})` で止まり、承認後に `learning_log/` に保存された。`requests=3`、`tool_calls=3` |
  | 上の一文を削除して `n` | 保存されず、モデルは「保存がキャンセルされたため」と断ってから説明だけを返した。`requests=3`、`tool_calls=2`（拒否した呼び出しは数えられない） |

  - 既存の `test_base_tools_are_registered_and_called` が失敗した。TestModel に全ツールを呼ばせ、「呼び出し数 = 戻り値数」を確かめるテストだが、承認待ちの呼び出しには戻り値がない。承認待ちの数を足して比べるよう最小限だけ直した。テストは全17本が通る。

- 気づき・疑問：
  - docstring の一言は、ツールを「どう呼ぶか」（回数・引数）を確実に変えた。一方、「呼ぶかどうか」は指示を消しても、逆の指示を足しても変わらなかった。ツール名と説明が「用語集を検索する」で質問が用語そのものなら、指示がなくても使うようだ。指示の効き方は、ツールの説明に書くか INSTRUCTIONS に書くかよりも、「何を決めさせる指示か」で違うと感じた。
  - 実装で、仕組みが行う確認（`requires_approval`）を docstring に書いたところ、モデルが自分で確認しようとしてツールを呼ばなくなった。docstring はモデルへの指示として読まれるので、モデルにしてほしくないことは書かないほうがよい。
  - ADK と Pydantic AI では、同じ指示と関数なら呼ばれ方は同じだった。違いはフレームワークが担う部分（会話の保持、戻り値の包み方、`.env` の読み込み、可視化）にあった。`--trace` は呼び出しの引数と戻り値を一覧するのに向き、`adk web` は「候補のツールのうちどれが使われたか」を図で見るのに向いている。
  - 疑問：ADK で承認付きのツール（`save_learning_log`）を作る場合、Pydantic AI の `DeferredToolRequests` のように「一度止めて続きから再開する」流れはどう書くのか。
