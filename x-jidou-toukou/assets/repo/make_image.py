"""投稿に付ける画像を作る（5時の係が使う道具）。

スクショを撮る（無料）:
    python make_image.py shot https://発表ページ images/2026-10-13.png
    下にお知らせの帯が残ったら、高さを指定して上の部分だけ撮り直す（例：600）:
    python make_image.py shot https://発表ページ images/2026-10-13.png 600
falで図を作る（1枚 約0.08ドル。スクショが撮れなかった日だけ使う）:
    python make_image.py fal "図の説明" images/2026-10-13.png

shot を初めて使う前に、一度だけ次を実行する:
    pip install playwright==1.48.0 && python -m playwright install --with-deps chromium
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

FAL_MODEL = "fal-ai/nano-banana-2"


def shot(url, out, height=None):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 675}, locale="ja-JP")
        res = page.goto(url, wait_until="networkidle", timeout=45000)
        if res is None or res.status >= 400:
            sys.exit(f"ページを開けませんでした（{res.status if res else '応答なし'}）。falで作ってください。")
        page.wait_for_timeout(1500)
        # クッキーの確認など、画面に貼りついたお知らせの帯を消す
        page.evaluate("""() => {
            for (const el of document.querySelectorAll('body *')) {
                const pos = getComputedStyle(el).position;
                if ((pos === 'fixed' || pos === 'sticky') && /cookie|クッキー|consent/i.test(el.textContent || '')) el.remove();
            }
        }""")
        if height:  # 下に残った帯を切り落とす
            page.screenshot(path=out, clip={"x": 0, "y": 0, "width": 1200, "height": int(height)})
        else:
            page.screenshot(path=out)  # 画面に見えている上の部分だけ（16:9）
        browser.close()
    print(f"スクショを保存しました: {out}")


def fal(prompt, out):
    key = os.environ.get("FAL_KEY")
    if not key:
        sys.exit("FAL_KEY が設定されていません。画像なしで投稿してください。")
    req = urllib.request.Request(
        f"https://fal.run/{FAL_MODEL}",
        data=json.dumps({
            "prompt": prompt,
            "aspect_ratio": "16:9",
            "resolution": "1K",
            "num_images": 1,
            "output_format": "png",
        }).encode(),
        headers={"Authorization": f"Key {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        image_url = json.load(r)["images"][0]["url"]
    with urllib.request.urlopen(image_url, timeout=60) as r:
        Path(out).write_bytes(r.read())
    print(f"falで画像を作りました: {out}")


def main():
    ok = (sys.argv[1:2] == ["shot"] and len(sys.argv) in (4, 5)) or (sys.argv[1:2] == ["fal"] and len(sys.argv) == 4)
    if not ok:
        sys.exit(__doc__)
    Path(sys.argv[3]).parent.mkdir(parents=True, exist_ok=True)
    {"shot": shot, "fal": fal}[sys.argv[1]](*sys.argv[2:])


if __name__ == "__main__":
    main()
