# scraping/tiktok_discovery.py
import asyncio, re, sys, json, csv
from datetime import datetime
from pathlib import Path
import pandas as pd
from playwright.async_api import async_playwright

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.idgen import make_id

# ---------------- CONFIG ----------------
HASHTAGS = ["kbeauty, koreanskincare"]#["kbeautymakeup","koreanmakeup", "kmakeup", "koreanskincare","koreanskincareproducts", "kbeauty","koreanskincaretips","koreanskincareproducts", "koreanskincareroutine"]
MAX_VIDEOS_PER_TAG = 200
MAX_SCROLLS = 500
SCROLL_PAUSE = 2.5
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
        return int(s)
    except:
        return val

async def accept_cookies_if_present(page):
    try:
        await page.wait_for_selector('button:has-text("Accept all")', timeout=4000)
        await page.click('button:has-text("Accept all")')
        await page.wait_for_timeout(400)
    except:
        try:
            await page.click('button:has-text("Accept")', timeout=1500)
            await page.wait_for_timeout(400)
        except:
            pass

async def collect_video_links(page, max_items=200, max_scrolls=200, pause=2.0):
    urls = set()
    last_count = -1
    stagnant_loops = 0

    for i in range(max_scrolls):
        anchors = await page.query_selector_all('a[href*="/video/"]')
        for a in anchors:
            href = await a.get_attribute("href")
            if href and "/video/" in href:
                urls.add(href.split("?")[0])

        if len(urls) >= max_items:
            break

        if len(urls) == last_count:
            stagnant_loops += 1
        else:
            stagnant_loops = 0

        if stagnant_loops >= 3:
            break

        await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        await asyncio.sleep(pause)
        last_count = len(urls)

    return list(urls)[:max_items]

async def scrape_video_page(context, url):
    page = await context.new_page()
    await page.goto(url, timeout=60000)
    await page.wait_for_load_state("domcontentloaded")

    data = {"URL": url}
    data["TikTok_Video_ID"] = url.split("/")[-1].split("?")[0]

    caption = None
    for attempt in range(5):
        try:
            s = await page.query_selector('script#SIGI_STATE')
            if s:
                raw = await s.inner_text()
                state = json.loads(raw)
                item_mod = state.get("ItemModule") or {}
                if item_mod:
                    first_id = next(iter(item_mod.keys()))
                    caption = (item_mod.get(first_id) or {}).get("desc")
                    if caption and "Sign up for an account" not in caption:
                        break
        except Exception:
            pass
        await asyncio.sleep(1)

    if not caption:
        try:
            m = await page.query_selector('meta[name="description"]')
            if m:
                caption = await m.get_attribute("content")
        except:
            pass

    if not caption:
        caption = "[WARNING] Caption missing or blocked"

    data["Caption"] = caption
    hashtags = extract_hashtags_from_text(caption or "")
    data["Hashtags"] = ",".join(sorted(set(hashtags)))

    # author
    author = None
    for sel in [
        'a[href^="/@"] span[data-e2e="browse-username"]',
        'span[data-e2e="browse-username"]',
        'a[href^="/@"]'
    ]:
        try:
            el = await page.query_selector(sel)
            if el:
                txt = (await el.inner_text() or "").strip()
                if txt:
                    author = txt.lstrip("@")
                    break
        except:
            continue
    data["Author"] = author

    # upload date
    upload_date = None
    try:
        t = await page.query_selector("span time")
        if t:
            iso = await t.get_attribute("datetime")
            if iso:
                upload_date = iso
    except:
        pass
    data["Upload_Date"] = upload_date

    async def get_text(selectors):
        for sel in selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    txt = await el.inner_text()
                    if txt:
                        return txt.strip()
            except:
                continue
        return None

    like_txt = await get_text(['strong[data-e2e="like-count"]'])
    comment_txt = await get_text(['strong[data-e2e="comment-count"]'])
    share_txt = await get_text(['strong[data-e2e="share-count"]'])

    data["Like_Count"] = normalize_count(like_txt)
    data["Comment_Count"] = normalize_count(comment_txt)
    data["Share_Count"] = normalize_count(share_txt)

    await page.close()
    return data

async def scrape_hashtag(context, tag, max_items, seen_ids):
    page = await context.new_page()
    await page.goto(f"https://www.tiktok.com/tag/{tag}", timeout=60000)
    await accept_cookies_if_present(page)

    urls = await collect_video_links(page, max_items=max_items, max_scrolls=MAX_SCROLLS, pause=SCROLL_PAUSE)
    await page.close()

    filtered = []
    for u in urls:
        vid = u.split("/")[-1].split("?")[0]
        if vid not in seen_ids:
            filtered.append(u)
            seen_ids.add(vid)

    print(f"{tag}: {len(filtered)} video links to scrape")

    results = []
    for i, url in enumerate(filtered, 1):
        print(f"  [{i}/{len(filtered)}] {url}")
        details = await scrape_video_page(context, url)
        details["Hashtag_Seed"] = tag
        results.append(details)

    return results

async def main():
    project_root = Path(__file__).resolve().parents[1]
    out_path = project_root / "data" / "raw" / "tiktok_discovery.csv"

    seen_ids = set()
    gid = 1

    # Read existing CSV to keep track of seen IDs and gid counter
    if out_path.exists():
        existing = pd.read_csv(out_path, quoting=csv.QUOTE_ALL)
        existing = existing.loc[:, ~existing.columns.str.contains("^Unnamed")]
        if "TikTok_Video_ID" in existing.columns:
            seen_ids = set(existing["TikTok_Video_ID"].astype(str))
        if "Video_ID" in existing.columns and not existing.empty:
            def _extract_num(s):
                m = re.search(r"(\d+)$", str(s))
                return int(m.group(1)) if m else 0
            gid = int(existing["Video_ID"].dropna().map(_extract_num).max() or 0) + 1

    columns = [
        "Video_ID","TikTok_Video_ID","Hashtag_Seed","Author","Caption",
        "Hashtags","Like_Count","Comment_Count","Share_Count","Upload_Date","URL"
    ]

    async with async_playwright() as p:
        PROFILE_DIR = Path.home() / "tiktok_profiles" / "scraper1"
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/140.0.0.0 Safari/537.36")
        )

        for tag in HASHTAGS:
            rows = []
            items = await scrape_hashtag(context, tag, MAX_VIDEOS_PER_TAG, seen_ids)
            for r in items:
                r["Video_ID"] = make_id(gid)
                rows.append(r)
                gid += 1

            # ✅ Only save if we actually scraped something
            if rows:
                df = pd.DataFrame(rows, columns=columns).dropna(how="all")
                df.drop_duplicates(subset=["TikTok_Video_ID"], inplace=True)

                if out_path.exists():
                    with open(out_path, "a", newline="") as f:
                        if f.tell() > 0:
                            f.write("\n")
                        df.to_csv(f, index=False, header=False,
                                quoting=csv.QUOTE_ALL, escapechar="\\")
                    print(f"Appended {len(df)} rows from #{tag} -> {out_path}")
                else:
                    df.to_csv(out_path, index=False,
                            quoting=csv.QUOTE_ALL, escapechar="\\")
                    print(f"Wrote {len(df)} rows from #{tag} -> {out_path}")

                print("\nPreview of first 5 rows just collected:")
                print(df.head(5).to_string(index=False))
            else:
                print(f"(no new rows from #{tag})")



        await context.close()


    columns = [
        "Video_ID","TikTok_Video_ID","Hashtag_Seed","Author","Caption",
        "Hashtags","Like_Count","Comment_Count","Share_Count","Upload_Date","URL"
    ]
    df = pd.DataFrame(rows, columns=columns).dropna(how="all")

    if not df.empty:
        df.drop_duplicates(subset=["TikTok_Video_ID"], inplace=True)

    print("\nPreview of first 5 rows collected:")
    if not df.empty:
        print(df.head(5).to_string(index=False))
    else:
        print("(no new rows)")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    if df.empty:
        print(f"No new rows to append -> {out_path}")
        return

    if out_path.exists():
        existing = pd.read_csv(out_path, quoting=csv.QUOTE_ALL)
        df = df[existing.columns]  # enforce same order
        df.to_csv(out_path, index=False, mode="a", header=False,
                  quoting=csv.QUOTE_ALL, escapechar="\\")
        print(f"Appended {len(df)} new rows -> {out_path}")
    else:
        df.to_csv(out_path, index=False, quoting=csv.QUOTE_ALL, escapechar="\\")
        print(f"Wrote {len(df)} rows -> {out_path}")

if __name__ == "__main__":
    asyncio.run(main())
