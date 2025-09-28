# scraping/tiktok_discovery.py
import asyncio, re, sys, json
from datetime import datetime
from pathlib import Path
import pandas as pd
from playwright.async_api import async_playwright

# allow "from utils.idgen import make_id"
sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.idgen import make_id

# ---------------- CONFIG ----------------
HASHTAGS = ["kbeauty", "viralkbeauty", "koreanskincareproducts"]
MAX_VIDEOS_PER_TAG = 200
MAX_SCROLLS = 60
SCROLL_PAUSE = 1.2
OUT_PATH = Path("tiktok_discovery.csv")
# ---------------------------------------

def extract_hashtags_from_text(text: str):
    return [h.lower() for h in re.findall(r"#([A-Za-z0-9_]+)", text or "")]

def normalize_count(val):
    if val is None:
        return None
    s = str(val).strip().upper().replace(",", "")
    try:
        if s.endswith("K"):
            return int(float(s[:-1]) * 1_000)
        if s.endswith("M"):
            return int(float(s[:-1]) * 1_000_000)
        if s.endswith("B"):
            return int(float(s[:-1]) * 1_000_000_000)
        return int(float(s))
    except:
        return None

async def accept_cookies_if_present(page):
    try:
        btn = await page.query_selector('button:has-text("Accept all")')
        if btn:
            await btn.click()
            await page.wait_for_timeout(500)
    except:
        pass

async def dismiss_open_app_popup(page):
    try:
        btn = await page.query_selector('div[data-e2e="popup-close"]')
        if btn:
            await btn.click()
            await page.wait_for_timeout(500)
    except:
        pass

async def dismiss_interest_popup(page):
    try:
        btn = await page.wait_for_selector('button:has-text("Skip")', timeout=5000)
        if btn:
            await btn.click()
            await page.wait_for_timeout(1000)
            print("[Popup] Dismissed interests screen")
    except:
        pass

async def scrape_video_page(context, url):
    page = await context.new_page()
    await page.goto(url, timeout=60000)
    await page.wait_for_load_state("domcontentloaded")

    # Handle popups
    await dismiss_interest_popup(page)
    await accept_cookies_if_present(page)
    await dismiss_open_app_popup(page)
    await page.wait_for_timeout(1200)

    data = {"URL": url}
    video_id = url.split("/")[-1].split("?")[0]
    data["TikTok_Video_ID"] = video_id

    caption, author, upload_date = None, None, None
    like_txt, comment_txt, share_txt = None, None, None
    hashtags = []

    # --- JSON parsing from SIGI_STATE ---
    for attempt in range(3):
        try:
            await page.wait_for_selector("script#SIGI_STATE", timeout=8000)
            s = await page.query_selector("script#SIGI_STATE")
            if s:
                raw = await s.inner_text()
                state = json.loads(raw)

                # ItemModule first
                item_mod = state.get("ItemModule") or {}
                vid_data = item_mod.get(video_id)

                # fallback: ItemList
                if not vid_data:
                    vid_data = (
                        state.get("ItemList", {})
                             .get("video", {})
                             .get("list", [{}])[0]
                    )

                if vid_data:
                    # Caption
                    caption = vid_data.get("desc") or caption

                    # Author (use best available)
                    author = (
                        vid_data.get("authorName")
                        or vid_data.get("nickname")
                        or vid_data.get("author")
                        or author
                    )
                    if author:
                        author = author.lstrip("@")

                    # Stats
                    stats = vid_data.get("stats") or {}
                    like_txt = like_txt or stats.get("diggCount")
                    comment_txt = comment_txt or stats.get("commentCount")
                    share_txt = share_txt or stats.get("shareCount")

                    # Upload date
                    create_time = vid_data.get("createTime")
                    if create_time:
                        upload_date = datetime.fromtimestamp(int(create_time)).strftime("%Y-%m-%d")

            if caption or author:
                break

        except Exception:
            pass

        await page.wait_for_timeout(2000)

    # --- Fallbacks if JSON parsing fails ---
    if not caption:
        try:
            meta = await page.query_selector('meta[name="description"]')
            if meta:
                caption = await meta.get_attribute("content")
        except:
            pass

    if not hashtags and caption:
        hashtags = extract_hashtags_from_text(caption)

    if not author:
        try:
            el = await page.query_selector('a[href^="/@"]')
            if el:
                txt = (await el.inner_text() or "").strip()
                author = txt.lstrip("@")
        except:
            pass

    # --- Final normalization ---
    data["Caption"] = caption
    data["Author"] = author
    data["Upload_Date"] = upload_date
    data["Like_Count"] = normalize_count(like_txt)
    data["Comment_Count"] = normalize_count(comment_txt)
    data["Share_Count"] = normalize_count(share_txt)
    data["Hashtags"] = ",".join(sorted(set(hashtags)))

    await page.close()
    return data


async def scrape_hashtag(context, tag, max_videos, seen_ids):
    url = f"https://www.tiktok.com/tag/{tag}"
    page = await context.new_page()
    await page.goto(url, timeout=60000)

    await accept_cookies_if_present(page)
    await dismiss_open_app_popup(page)
    await dismiss_interest_popup(page)

    collected = []
    video_links = set()
    scrolls = 0

    while len(video_links) < max_videos and scrolls < MAX_SCROLLS:
        links = await page.query_selector_all("a[href*='/video/']")
        for link in links:
            href = await link.get_attribute("href")
            if href and "/video/" in href:
                video_links.add(href)
        await page.mouse.wheel(0, 2000)
        await page.wait_for_timeout(int(SCROLL_PAUSE * 1000))
        scrolls += 1
        if not links:
            break

    print(f"{tag}: {len(video_links)} video links to scrape")
    for i, vurl in enumerate(list(video_links)[:max_videos], start=1):
        vid = vurl.split("/")[-1]
        if vid in seen_ids:
            continue
        print(f"  [{i}/{len(video_links)}] {vurl}")
        details = await scrape_video_page(context, vurl)
        collected.append(details)
        seen_ids.add(vid)

        # DEBUG: show first 10 results in terminal
        if i <= 10:
            print(json.dumps(details, indent=2, ensure_ascii=False))

    await page.close()
    return collected

async def main():
    existing = []
    seen_ids = set()

    if OUT_PATH.exists():
        existing = pd.read_csv(OUT_PATH).to_dict("records")
        seen_ids = set([r["TikTok_Video_ID"] for r in existing if "TikTok_Video_ID" in r])
        print(f"[Init] Loaded {len(existing)} existing rows. De-dup seeded.")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()

        new_records = []
        for tag in HASHTAGS:
            items = await scrape_hashtag(context, tag, MAX_VIDEOS_PER_TAG, seen_ids)
            new_records.extend(items)

        await browser.close()

    if new_records:
        all_data = existing + new_records
        df = pd.DataFrame(all_data)
        df.to_csv(OUT_PATH, index=False)
        print(f"Progress saved (+{len(new_records)}). Total={len(df)}")
    else:
        print("No new videos collected.")

if __name__ == "__main__":
    asyncio.run(main())
