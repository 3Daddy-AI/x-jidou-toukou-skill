---
name: x-jidou-toukou
description: X（旧Twitter）に「毎朝AIの最新ニュースを自動で投稿する仕組み」を一から組み立てるスキル。クラウドのClaudeが毎朝ニュースを調べて投稿案を作り、確認できる時間をはさんでから、GitHub Actions が X API で投稿する。画像（発表ページのスクショ、撮れない日は fal で作る図）を付けることもできる。費用は1日1本で月70円前後（画像付きは月70〜450円）。「Xに自動投稿したい」「ツイートを予約・自動化したい」「毎朝AIニュースを投稿したい」「X APIで投稿したい」「ニュース速報みたいな投稿を自動で」「自動投稿が止まった・403エラーが出る」「投稿の型や時間を変えたい」「投稿に画像やスクショを付けたい」「投稿されなかった」などと言われたら必ず使う。X 以外のSNS（Threads・Bluesky など）で同じ仕組みを作りたいときの下敷きにも使う。
---

# X 自動投稿システムづくり

毎朝、決まった時刻にクラウドの Claude が AI ニュースを調べて投稿案を作り、その数時間後に GitHub が X へ投稿する仕組みを組み立てる。
使う人はエンジニアではないことが多い。専門用語は一度かみ砕いて言い換え、画面で迷ったらスクリーンショットをもらって、その画面に合わせて案内する。
**本番の投稿と、GitHub への送信は、使う人の「OK」をもらってから行う。** 投稿は取り消しても見られている可能性があるため。

## このスキルの場所

この SKILL.md が入っているフォルダを、以下「<このスキルのフォルダ>」と書く。使う環境によって場所が違う（Claude Code なら `~/.claude/skills/x-jidou-toukou`、ブラウザ版やデスクトップアプリでは別の場所）。ひな形（`assets/repo/`）や `references/` は、このフォルダの中にある。

## どの Claude で使うか

組み立ての途中で、GitHub への送信（`gh` コマンド）や毎朝の予定づくり（`RemoteTrigger`）を Claude が代わりに行う。これができるのは **Claude Code**（デスクトップアプリの Code タブ、またはターミナル）だけ。

ブラウザ版・デスクトップアプリの Chat / Cowork で使われたときは、Claude が自分では動かせないので、次のように進める。最初に「Claude Code があるなら、そちらのほうが手作業が少ない」と一言伝える。
- ひな形（`<このスキルのフォルダ>/assets/repo/` の中身）を、`{{…}}` を埋めた状態で渡す。GitHub の画面で新しい保管場所（非公開）を作り、アップロードしてもらう。`.github/workflows/post.yml` は「Add file → Create new file」で、名前の欄に `.github/workflows/post.yml` と打って中身を貼ってもらう
- 合言葉4つは、保管場所の「Settings → Secrets and variables → Actions → New repository secret」から入れてもらう（名前は 3. の5と同じ）
- 接続確認・試運転は、保管場所の「Actions」→「X自動投稿」→「Run workflow」でモードを選んで動かしてもらう
- 毎朝の予定は https://claude.ai/code/routines から作ってもらう（中身は 5. と同じ）

## 仕組みの全体像

```
[毎朝 5:00] クラウドのClaude（routine）── news_routine.md の指示どおりニュースを調べる
                │  （画像付きなら）make_image.py で発表ページのスクショ → ダメなら fal で図 → images/日付.png
                │  投稿案を queue.md（投稿待ちリスト）の一番上に入れて GitHub に送る
[5:00〜7:00] 本人がスマホの GitHub アプリで queue.md を見る。ダメなら消す（見なくても投稿される）
[毎朝 7:00] GitHub Actions ── post_next.py が一番上の1本を（画像があれば付けて）X API で投稿し、posted.md に記録
```

役割を分けている理由：ニュースを調べて書く仕事は Claude の利用量の範囲で、投稿する仕事は X の従量課金で、それぞれ一番安く済む。確認の時間がはさまるので、AI が誤った情報を書いても止められる。

ひな形一式は `assets/repo/` にある（中身は「ひな形の中身」の節）。

## 0. 最初にまとめて伝えること（作業を始める前に）

途中で「実はもう一つ登録が必要」となると、そこで止まってしまう。始める前に、次の3つを全部見せて了解をもらう。

**費用**（X API は 2026年2月から使った分だけ払う方式。無料枠はない）
| 内容 | 1回あたり | 1日1本×30日 |
|---|---|---|
| 文章だけの投稿 | 約0.015ドル（約2円） | 約70円 |
| リンク付きの投稿 | 約0.20ドル（約30円） | 約900円 |
| 接続確認（自分のアカウント名を聞く） | 約0.001ドル | ― |
| 画像付き（スクショ） | 画像の送信そのものは料金表に項目なし（2026年10月時点） | 約70円 |
| 画像付き（fal で図を作る日） | fal 1枚 約0.08ドル（約12円）が上乗せ | 全部 fal でも約450円 |

料金は年内に何度か変わっている。正しい金額は console.x.com の画面で確かめてもらう。最初に $5 ほど買えば数か月もつ。ニュースを調べる Claude は、今入っている Claude のプランの利用量を使う（追加料金なし）。

**必要な登録**
1. X の開発者サイト（https://console.x.com）の登録と、クレジットの購入（カードが要る）
2. GitHub のアカウント（無料）と、そこに入れる「Claude」アプリの許可（https://github.com/apps/claude）
3. Claude の有料プラン（クラウドで決まった時刻に動かす「routine」機能を使うため）
4. （画像を付ける場合だけ）fal（https://fal.ai）のアカウントと API キー、少しのクレジット。スクショだけでよければ不要

**長い投稿について**：型どおりだと 400〜600 字になる。X Premium に入っていないと 140 字（全角）までしか投稿できない。入っていなければ、型を短くするか Premium を検討してもらう。

無料でやりたい人には「Claude で投稿文を作り、X の予約投稿機能（投稿画面の時計マーク）で時刻指定する」方法を先に伝える。手作業は残るが、費用も登録もいらない。

## 1. 聞き取り

次を聞く。答えは news_routine.md と queue.md の `{{…}}` に入れる。
- 発信者の名前（X の表示名）と、どんな人か（例：公立小学校の教員。学校現場の生成AI活用を発信）
- 読者は誰か（例：AIに詳しくない先生）
- 最後の「一言」をどの目線で書くか（例：学校や先生の仕事にどう効きそうか）
- AI 企業のほかに調べたい機関（例：文部科学省）
- 投稿案を作る時刻と投稿する時刻（既定 5:00 と 7:00。間が確認の時間になる）

投稿の型を変えたいと言われたら、「2. 投稿文を書く（型）」の節を書き換える。参考にしたい人の投稿があれば、構成（見出し・箇条書き・一言・補足・出典の並び）だけを借り、文章は写さない。

## 2. 保管場所（GitHub リポジトリ）を作る

1. `assets/repo/` の中身（`.github` と `.gitignore` も含む）を、作業フォルダに写す
2. `news_routine.md` と `queue.md` の `{{…}}` を聞き取った内容で埋める。残っていないか確かめる：
   ```bash
   grep -rn "{{" news_routine.md queue.md
   ```
3. 時刻を変えた場合は、`.github/workflows/post.yml` の `cron` を**世界標準時**に直す（日本時間 − 9時間。7:00 → `0 22 * * *`）
4. 手元で動作確認（投稿はしない）：
   ```bash
   printf 'テスト\n' > /tmp/t.md && python3 post_next.py --add /tmp/t.md && DRY_RUN=1 python3 post_next.py
   ```
   確かめたら queue.md を元に戻す
5. 使う人の「OK」をもらってから、**非公開**で作って送る：
   ```bash
   git init -b main && git add -A && git commit -m "X自動投稿の仕組み"
   gh repo create <アカウント>/x-auto-post --private --source=. --push
   ```
   - 同じ名前の保管場所がもうある、と言われたら中身を見る（前に作りかけた自動投稿の可能性が高い）。入れ替えるなら、古い記録を残したまま上に重ねる：`git remote add origin …` → `git fetch origin` → `git reset --soft origin/main` → コミット → `git push`
   - Claude Code の安全確認で送信が止められたら、無理に回り道をせず、同じコマンドを使う人に実行してもらう

## 3. X 側の準備

使う人に https://console.x.com を開いてもらう。Claude のアプリ内ブラウザでログインできていれば、画面を見ながら案内できる。

1. 「クレジットを購入する」で $5 ほど買う
2. 「アプリの管理」→ アプリを開く（なければ「アプリを作成」）
3. **「プロジェクトアクセス」→「管理」→ Pay Per Use のプロジェクトの「ここに移動・Production」を押す**
   - ここが一番つまずく所。古い無料プラン（Free / Standard Basic）のプロジェクトにつながったままだと、クレジットを買っても `403 client-not-enrolled` で断られる
   - Pay Per Use のプロジェクトがなければ「新しいプロジェクトを開始」で作る
4. 「Keys & Tokens」で権限が「読み取りと書き込み」か確かめる。違えば直してから、アクセストークンを**作り直す**（作った時点の権限が合言葉に焼き付くため）
5. 合言葉4つを GitHub に入れる。**チャットには貼らせない。** 使う人に1行ずつ実行してもらう（貼った文字は画面に出ない）：
   ```bash
   gh secret set X_API_KEY -R <アカウント>/x-auto-post
   gh secret set X_API_SECRET -R <アカウント>/x-auto-post
   gh secret set X_ACCESS_TOKEN -R <アカウント>/x-auto-post
   gh secret set X_ACCESS_TOKEN_SECRET -R <アカウント>/x-auto-post
   ```
   対応：コンシューマーキー＝API_KEY / API_SECRET、アクセストークン＝ACCESS_TOKEN / ACCESS_TOKEN_SECRET
6. つながるか確かめる（投稿はしない。約0.001ドル）：
   ```bash
   gh workflow run post.yml -R <アカウント>/x-auto-post -f mode=Xにつながるか確認
   ```
   ログに「Xにつながりました: 表示名（@ID）」と出れば成功。**出てきた @ID が投稿したいアカウントか、使う人に確かめる**（合言葉は作ったときのアカウント用になる）

## 4. クラウドの Claude に保管場所を使わせる

1. GitHub に「Claude」アプリが入っているか：https://github.com/settings/installations で「Claude」→「Configure」→「Repository access」を見る
   - 入っていなければ https://github.com/apps/claude/installations/new から入れる。「Only select repositories」で x-auto-post だけ選ぶのが安全
   - 「All repositories」なら、そのままでも動く
2. クラウド環境のネットワーク：https://claude.ai/code の入力欄の上「☁ Default」→「クラウド ＞」→「Default」の右の歯車 → ネットワークアクセスを **Full** にする
   - 制限つきのままだと、OpenAI や Google の公式サイトが開けず、ニュースを見落とす

## 5. 毎朝の予定（routine）を作る

Claude Code なら `RemoteTrigger` で作る（`/schedule` の手順）。ブラウザ版なら https://claude.ai/code/routines から同じ内容で作る。

- 名前：Xニュース投稿づくり
- 時刻：投稿案を作る時刻を世界標準時の cron に（5:00 → `0 20 * * *`）
- モデル：Sonnet（速くて利用量が少ない）
- 保管場所：`https://github.com/<アカウント>/x-auto-post`
- 使える道具：Bash・Read・Write・Edit・Glob・Grep・WebSearch・WebFetch
- 指示文：
  > このリポジトリの news_routine.md を最初に全部読み、その指示に厳密に従って、今日のAIニュース投稿を1本作り queue.md のいちばん上に追加してください。今日の日付は `TZ=Asia/Tokyo date` で確認すること。posted.md と queue.md を読んで重複を避けること。完了したら main ブランチに直接 commit して push すること（claude/ で始まる別ブランチやプルリクエストは作らない）。main への push が拒否された場合は、その旨と拒否メッセージを最後に報告すること。公式ページが開けないときは大手報道2つ以上で確かめてよい。72時間以内に確かなニュースが1つもない日は、無理に作らず何も変更せず、その理由を一言報告して終わること。

**作ったあと、Gmail・Google ドライブなどの連携が自動で付いていたら外す**（`clear_mcp_connections: true`）。この予定はウェブの記事を読むので、メールに触れる状態にしておくと危ない。

## 5.5 画像を付ける（使う人が望んだときだけ）

ひな形はもう画像に対応している。画像を付けたくない人は、news_routine.md の「2.5 画像を付ける」の節を消すだけでよい。

- **5:00 の係**が `make_image.py shot {URL}` で発表ページを撮る（Playwright：プログラムでブラウザを動かす道具。毎回クラウドの中で自動で入れる、無料）。撮った画像は自分で開いて確かめ、エラー画面・ロボット確認・人物写真が大きいページなどは使わない
- 撮れない・使えないときは `make_image.py fal "{英語の説明}"` で fal の nano-banana-2 に図を作らせる。**文字・ロゴ・実在の人物は入れない**よう指示する（変な文字が出やすいため）
- 投稿案の最後に `画像: images/YYYY-MM-DD.png` の1行。7:00 の post_next.py がこの行を外し、X の `/2/media/upload` に画像を送ってから、その番号を付けて投稿する
- スクショは「引用」として載せる：文章が主役で画像は補助、出典を必ず書く

準備：
1. fal の API キーを、クラウド環境「Default」の環境変数に `FAL_KEY=…` で**使う人に貼ってもらう**（チャットには貼らせない）。claude.ai/code →「☁ Default」→ 歯車 → 環境変数
2. routine の指示文に「news_routine.md の『2.5 画像を付ける』に従い、まず make_image.py で発表ページのスクショを撮り、使えなければ fal で図を作ること（環境変数 FAL_KEY を使う）。画像は queue.md と一緒に commit すること。」を足す
3. 画像を送れるか確かめる（投稿はしない）：
   ```bash
   gh workflow run post.yml -R <アカウント>/x-auto-post -f "mode=画像を送れるか確認（投稿しない）"
   ```
   ログに「画像を送れました（投稿はしていません）」と出れば成功。今までの X の合言葉（OAuth 1.0a）のままで送れる
4. 手元で確かめたいときは、作業用の仮の環境（venv）に `pip install playwright==1.48.0` → `python -m playwright install chromium` で `make_image.py shot` を試せる

分かっていること：openai.com は本物のブラウザで開いても 403 で断られる（OpenAI のニュースの日は fal になりやすい）。anthropic.com・blog.google は撮れる。blog.google のクッキーの帯は make_image.py が自動で消す。

## 6. 試運転

1. 予定を1回すぐ動かす（`RemoteTrigger` の `run`）。2〜3分で投稿案が queue.md に入る
2. `git pull` して `DRY_RUN=1 python3 post_next.py` で中身を見せる。実行の記録（`get_run_log`）で、どこを調べたかも確かめる
   - 投稿案が入らなかった → 記録の最後の報告を読む（ネタなし・サイトが開けない など）。`references/troubleshooting.md`
   - 中身の書き方を直したい → news_routine.md を直して送り、もう一度動かす
3. 試しの投稿案は、使う人に聞いて消す（残すと翌朝の投稿案の下にたまり、翌々日に古い話題が出る）
4. 使う人の「OK」と文章をもらって、テスト投稿を1本：
   ```bash
   # 文章を queue.md の一番上に入れて送ってから
   gh workflow run post.yml -R <アカウント>/x-auto-post -f "mode=本番（投稿する）"
   ```
   ログの「投稿しました: https://x.com/i/status/…」を伝え、posted.md に記録されたかも見る

## 7. 渡すときに伝えること

- 毎朝の流れ（何時に何が起き、本人は何をすればいいか）を表で
- 確認しなかった日も投稿されること。止めたい日は queue.md のその投稿を消す
- queue.md の URL（`https://github.com/<持ち主>/<保管場所>/blob/main/queue.md`）を渡し、ブックマークしてもらう。非公開なので、GitHub にログインしていないブラウザでは404になることも先に伝える
- 投稿案が空のまま60日たつと、GitHub が毎日の自動実行を止める
- 指示書（news_routine.md）を直せば、調べ方・書き方を変えられる

## ひな形の中身（assets/repo/）

| ファイル | 役割 |
|---|---|
| `queue.md` | 投稿待ちリスト。投稿どうしは `---` だけの行で区切る。`+++` だけの行で区切るとリプライとして続けて投稿する（URL をリプライに分けたいとき用） |
| `posted.md` | 投稿した日時・URL・本文の記録 |
| `post_next.py` | 一番上の1本を投稿して posted.md へ移す。`--add 下書き.md` で一番上に入れる。`DRY_RUN=1` は表示だけ、`CHECK=1` は接続確認だけ、`CHECK_IMAGE=画像のパス` は画像を送れるかだけ。本投稿の中の `画像: images/…png` の行は、その画像を付ける合図（行は投稿されない） |
| `make_image.py` | 投稿に付ける画像を作る。`shot URL 保存先` でスクショ（無料）、`fal "説明" 保存先` で fal に図を作らせる（約12円） |
| `images/check.png` | 「画像を送れるか確認」で使う試しの画像 |
| `.github/workflows/post.yml` | 毎朝の投稿。手動実行では「お試し／Xにつながるか確認／画像を送れるか確認／本番」を選べる |
| `news_routine.md` | クラウドの Claude への指示書。ネタの選び方・投稿の型・画像の付け方・やってはいけないこと |

投稿の型（既定）は「【速報/新機能】見出し → 1〜2文の説明 → 箇条書き3〜5個 → 発信者の一言 → ■補足 → ■出典（文字だけ・URLなし）」を1本にまとめたもの。URL を入れないのは、リンク付きの投稿が約15倍の料金になるため。

困ったとき（エラー・投稿されない・ネタを見落とす）は `references/troubleshooting.md` を読む。
