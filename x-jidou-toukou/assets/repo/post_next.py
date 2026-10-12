"""queue.md の一番上の投稿を X に1本投稿し、posted.md に移す。

1つの投稿の中に「+++」だけの行があると、そこで区切って
2つ目以降を自分の投稿へのリプライとして続けて投稿する（補足・出典用）。

本投稿の中に「画像: images/xxx.png」だけの行があると、その画像を付けて投稿する（行そのものは投稿されない）。

DRY_RUN=1 のときは投稿せず、何が投稿されるかを表示するだけ。
CHECK=1 のときは投稿せず、Xの合言葉が使えるか（自分のアカウント名が取れるか）だけ確かめる。
`python post_next.py --add 下書き.md` で、下書きを投稿待ちリストの一番上に入れる。
"""
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).parent
QUEUE = HERE / "queue.md"
POSTED = HERE / "posted.md"
SEPARATOR = "---"
REPLY_SEPARATOR = "+++"
IMAGE_PREFIX = "画像:"
JST = timezone(timedelta(hours=9))


def read_queue():
    """queue.md を「説明文」と「投稿のリスト」に分ける。"""
    blocks, current = [], []
    for line in QUEUE.read_text(encoding="utf-8").splitlines():
        if line.strip() == SEPARATOR:
            blocks.append("\n".join(current).strip())
            current = []
        else:
            current.append(line)
    blocks.append("\n".join(current).strip())
    header, posts = blocks[0], [b for b in blocks[1:] if b]
    return header, posts


def write_queue(header, posts):
    parts = [header] + posts
    QUEUE.write_text(("\n\n" + SEPARATOR + "\n\n").join(parts) + "\n\n" + SEPARATOR + "\n", encoding="utf-8")


def split_thread(post):
    parts, current = [], []
    for line in post.splitlines():
        if line.strip() == REPLY_SEPARATOR:
            parts.append("\n".join(current).strip())
            current = []
        else:
            current.append(line)
    parts.append("\n".join(current).strip())
    return [p for p in parts if p]


def split_image(text):
    """投稿文から「画像: パス」の行を取り出す。(画像を除いた文章, 画像のパス or None)"""
    image, lines = None, []
    for line in text.splitlines():
        if line.strip().replace("：", ":").startswith(IMAGE_PREFIX):
            image = line.strip().replace("：", ":")[len(IMAGE_PREFIX):].strip()
        else:
            lines.append(line)
    if image and not (HERE / image).is_file():
        sys.exit(f"画像が見つかりません: {image}")
    return "\n".join(lines).strip(), image


def x_session():
    from requests_oauthlib import OAuth1Session

    return OAuth1Session(
        os.environ["X_API_KEY"],
        client_secret=os.environ["X_API_SECRET"],
        resource_owner_key=os.environ["X_ACCESS_TOKEN"],
        resource_owner_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
    )


def check_x():
    res = x_session().get("https://api.x.com/2/users/me")
    if res.status_code != 200:
        sys.exit(f"Xにつながりませんでした（{res.status_code}）: {res.text}")
    user = res.json()["data"]
    print(f"Xにつながりました: {user['name']}（@{user['username']}）")


def upload_image(path):
    with open(HERE / path, "rb") as f:
        res = x_session().post(
            "https://api.x.com/2/media/upload",
            files={"media": f},
            data={"media_category": "tweet_image"},
        )
    if res.status_code not in (200, 201):
        raise RuntimeError(f"画像の送信に失敗しました（{res.status_code}）: {res.text}")
    return res.json()["data"]["id"]


def post_to_x(text, reply_to=None, image=None):
    session = x_session()
    body = {"text": text}
    if image:
        body["media"] = {"media_ids": [upload_image(image)]}
    if reply_to:
        body["reply"] = {"in_reply_to_tweet_id": reply_to}
    res = session.post("https://api.x.com/2/tweets", json=body)
    if res.status_code != 201:
        raise RuntimeError(f"投稿に失敗しました（{res.status_code}）: {res.text}")
    return res.json()["data"]["id"]


def add_to_top(draft_path):
    header, posts = read_queue()
    draft = Path(draft_path).read_text(encoding="utf-8").strip()
    if any(line.strip() == SEPARATOR for line in draft.splitlines()):
        sys.exit("下書きに「---」だけの行があります。リプライとの区切りは「+++」を使ってください。")
    write_queue(header, [draft] + posts)
    print(f"投稿待ちリストの一番上に入れました（全 {len(posts) + 1} 本）")


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--add":
        add_to_top(sys.argv[2])
        return
    if os.environ.get("CHECK") == "1":
        check_x()
        return
    if os.environ.get("CHECK_IMAGE"):
        print(f"画像を送れました（投稿はしていません）: media id {upload_image(os.environ['CHECK_IMAGE'])}")
        return
    header, posts = read_queue()
    if not posts:
        print("投稿待ちが空なので、今日は何もしません。")
        return

    text = posts[0]
    thread = split_thread(text)
    thread[0], image = split_image(thread[0])
    if os.environ.get("DRY_RUN") == "1":
        print("【お試し】次に投稿される文章:")
        print(f"画像: {image or 'なし'}")
        for i, part in enumerate(thread):
            print(f"\n--- {'本投稿' if i == 0 else 'リプライ'}（{len(part)}文字）---\n{part}")
        print(f"\n（残り {len(posts) - 1} 本）")
        return

    tweet_id = reply_to = None
    failed = False
    for i, part in enumerate(thread):
        if "http://" in part or "https://" in part:
            print("注意: リンク付きの投稿は1回あたり約0.20ドルかかります。")
        try:
            reply_to = post_to_x(part, reply_to, image if i == 0 else None)
        except RuntimeError as e:
            if tweet_id is None:
                sys.exit(str(e))
            # 本投稿は出ているので、同じ投稿が翌日また出ないよう記録は残す
            print(f"リプライだけ失敗しました。手動で補足してください。\n{e}")
            failed = True
            break
        tweet_id = tweet_id or reply_to
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M")
    with POSTED.open("a", encoding="utf-8") as f:
        f.write(f"\n## {now}\nhttps://x.com/i/status/{tweet_id}\n\n{text}\n")
    write_queue(header, posts[1:])
    print(f"投稿しました: https://x.com/i/status/{tweet_id}（残り {len(posts) - 1} 本）")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
