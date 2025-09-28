# scraping/tiktok_discovery.py
import asyncio
import random
import re
import sys
import json
from datetime import datetime
from pathlib import Path
import pandas as pd
from playwright.async_api import async_playwright

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.idgen import make_id

# ---------------- CONFIG ----------------
HASHTAGS = ["kbeauty", "koreanskincare", "koreanskincareproducts"]
MAX_VIDEOS_PER_TAG = 5     # change to 20+ for full runs
MAX_SCROLLS = 10
SCROLL_PAUSE = 1.2
SIGI_RETRY = 10            # increased retry attempts (step 1)
MIN_INTERACTION_DELAY = 0.6
MAX_INTERACTION_DELAY = 1.8
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

async def human_pause(min_s=MIN_INTERACTION_DELAY, max_s=MAX_INTERACTION_DELAY):
    await asyncio.sleep(random.uniform(min_s, max_s))

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

async def dismiss_open_app_popup(page):
    try:
        await page.wait_for_selector('button:has-text("Not now")', timeout=3000)
        await page.click('button:has-text("Not now")')
        await page.wait_for_timeout(400)
    except:
        pass

async def dismiss_interest_popup(page):
    try:
        await page.wait_for_selector('button:has-text("Skip")', timeout=3000)
        await page.click('button:has-text("Skip")')
        await page.wait_for_timeout(400)
    except:
        pass

async def mimic_human_on_page(page):
    # Add small mouse movements and scrolls to look human
    try:
        # tiny random mouse moves
        for _ in range(random.randint(1, 3)):
            x = random.randint(100, 900)
            y = random.randint(100, 700)
            steps = random.randint(6, 12)
            await page.mouse.move(x, y, steps=steps)
            await human_pause(0.05, 0.2)

        # small scroll
        await page.mouse.wheel(0, random.choice([200, 400, 600]))
        await human_pause()
        # sometimes scroll back a bit
        if random.random() < 0.35:
            await page.mouse.wheel(0, -random.choice([100, 200]))
            await human_pause(0.2, 0.6)
    except Exception:
        pass

async def collect_video_links(page, max_items=20, max_scrolls=60, pause=1.2):
    urls, seen = set(), 0
    for _ in range(max_scrolls):
        anchors = await page.query_selector_all('a[href*="/video/"]')
        for a in anchors:
            href = await a.get_attribute("href")
            if href and "/video/" in href:
                urls.add(href.split("?")[0])
        if len(urls) >= max_items:
            break
        if len(urls) == seen:
            await page.mouse.wheel(0, 2000)
            await asyncio.sleep(pause)
            anchors = await page.query_selector_all('a[href*="/video/"]')
            for a in anchors:
                href = await a.get_attribute("href")
                if href and "/video/" in href:
                    urls.add(href.split("?")[0])
            if len(urls) == seen:
                print("No new videos, stopping scroll early.")
                break
        seen = len(urls)
        await page.mouse.wheel(0, 4000)
        await asyncio.sleep(pause + random.uniform(0, 0.6))
    return list(urls)[:max_items]

async def scrape_video_page(context, url):
    page = await context.new_page()

    # Inject small stealth script to hide webdriver and some automation signs
    try:
        await page.add_init_script(
            """
            // hide webdriver
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            // pretend to have plugins/languages
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
            """
        )
    except Exception:
        pass

    await page.goto(url, timeout=60000)
    await page.wait_for_load_state("domcontentloaded")
    await human_pause(0.4, 1.0)
    await mimic_human_on_page(page)

    data = {"URL": url}
    data["TikTok_Video_ID"] = url.split("/")[-1].split("?")[0]

    caption = None

    # --- Retry loop for JSON state (increased attempts) ---
    for attempt in range(SIGI_RETRY):
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

    # --- Fallbacks if caption still missing ---
    if not caption:
        try:
            m = await page.query_selector('meta[name="description"]')
            if m:
                caption = await m.get_attribute("content")
        except:
            pass

    if not caption:
        try:
            btn_more = await page.query_selector('button[data-e2e="expand-desc"], button:has-text("More")')
            if btn_more:
                try:
                    await btn_more.click()
                    await page.wait_for_timeout(300)
                except:
                    pass
            for sel in [
                'h1[data-e2e="browse-video-desc"]',
                'div[data-e2e="browse-video-desc"]',
                'span[data-e2e="browse-video-desc"]',
                'div[data-e2e="video-desc"]',
            ]:
                el = await page.query_selector(sel)
                if el:
                    txt = (await el.inner_text() or "").strip()
                    if txt and "Sign up for an account" not in txt:
                        caption = txt
                        break
        except:
            pass

    if not caption:
        caption = "[WARNING] Caption missing or blocked"

    data["Caption"] = caption

    hashtags = []
    try:
        tag_links = await page.query_selector_all('a[href*="/tag/"]')
        for t in tag_links:
            txt = await t.inner_text()
            if txt and txt.startswith("#"):
                hashtags.append(txt.strip("#").lower())
    except:
        pass
    if not hashtags and caption:
        hashtags = extract_hashtags_from_text(caption)
    data["Hashtags"] = ",".join(sorted(set(hashtags)))

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

    upload_date = None
    try:
        t = await page.query_selector("span time")
        if t:
            iso = await t.get_attribute("datetime")
            if iso:
                upload_date = iso
    except:
        pass
    if not upload_date:
        try:
            info = await page.query_selector('span[data-e2e="browser-nickname"]')
            if info:
                spans = await info.query_selector_all("span")
                if spans:
                    last = spans[-1]
                    txt = (await last.inner_text() or "").strip()
                    if re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", txt):
                        upload_date = txt
                    elif re.fullmatch(r"\d{1,2}-\d{1,2}", txt):
                        y = datetime.now().year
                        m, d = [int(x) for x in txt.split("-")]
                        upload_date = f"{y:04d}-{m:02d}-{d:02d}"
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

    like_txt = await get_text(['strong[data-e2e="like-count"]', 'button[data-e2e="like-icon"] strong'])
    comment_txt = await get_text(['strong[data-e2e="comment-count"]', 'button[data-e2e="comment-icon"] strong'])
    share_txt = await get_text(['strong[data-e2e="share-count"]', 'button[data-e2e="share-icon"] strong'])

    data["Like_Count"] = normalize_count(like_txt)
    data["Comment_Count"] = normalize_count(comment_txt)
    data["Share_Count"] = normalize_count(share_txt)

    # small human-like pause before closing
    await human_pause(0.2, 0.8)
    await page.close()
    return data

async def scrape_hashtag(context, tag, max_items, seen_ids):
    page = await context.new_page()
    await page.goto(f"https://www.tiktok.com/tag/{tag}", timeout=60000)
    await accept_cookies_if_present(page)
    await dismiss_open_app_popup(page)
    await dismiss_interest_popup(page)
    await human_pause()
    await mimic_human_on_page(page)

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
        # small randomized delay between video scrapes to look human
        await human_pause(0.8, 2.0)
    return results

async def main():
    project_root = Path(__file__).resolve().parents[1]
    out_path = project_root / "data" / "raw" / "tiktok_discovery.csv"

    seen_ids = set()
    gid = 1

    # load existing file to seed seen ids and the gid counter
    if out_path.exists():
        try:
            existing = pd.read_csv(out_path, usecols=["Video_ID", "TikTok_Video_ID"])
        except Exception:
            existing = pd.read_csv(out_path)
        if "TikTok_Video_ID" in existing.columns:
            seen_ids = set(existing["TikTok_Video_ID"].astype(str))
        def _extract_num(s):
            m = re.search(r"(\d+)$", str(s))
            return int(m.group(1)) if m else 0
        if "Video_ID" in existing.columns and not existing.empty:
            gid = int(existing["Video_ID"].dropna().map(_extract_num).max() or 0) + 1

    rows = []
    warning_count = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=str(Path.home() / "tiktok_profile"),
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = await browser.new_page()
        await page.goto("https://www.tiktok.com", timeout=60000)


        # create a slightly randomized user agent to vary runs
        ua_base = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
        if random.random() < 0.3:
            ua = ua_base.replace("140.0.0.0", str(140 + random.randint(0, 4)) + ".0.0")
        else:
            ua = ua_base

        context = await browser.new_context(
            user_agent=ua,
            viewport={"width": 1280, "height": 800},
            locale="en-US"
        )

        # (optional) small initial delay to look less robotic
        await human_pause(0.5, 1.5)

        for tag in HASHTAGS:
            items = await scrape_hashtag(context, tag, MAX_VIDEOS_PER_TAG, seen_ids)
            for r in items:
                r["Video_ID"] = make_id(gid)
                rows.append(r)
                if r.get("Caption", "").startswith("[WARNING]"):
                    warning_count += 1
                gid += 1

        await context.close()
        await browser.close()

    df = pd.DataFrame(rows, columns=[
        "Video_ID","TikTok_Video_ID","Hashtag_Seed","Author","Caption",
        "Hashtags","Like_Count","Comment_Count","Share_Count","Upload_Date","URL"
    ]).dropna(how="all")

    # dedup within the new batch just in case
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
        print(f"Run summary: 0 new rows, {warning_count} warnings")
        return

    # append-only write (no overwrite)
    if out_path.exists():
        df.to_csv(out_path, index=False, mode="a", header=False)
        total_after = None
        try:
            total_after = len(pd.read_csv(out_path))
        except Exception:
            total_after = "unknown"
        print(f"Appended {len(df)} new rows -> {out_path}")
        print(f"Run summary: {len(df)} new rows, {warning_count} warnings, total rows after append = {total_after}")
    else:
        df.to_csv(out_path, index=False)
        print(f"Wrote {len(df)} rows -> {out_path}")
        print(f"Run summary: {len(df)} new rows, {warning_count} warnings")

if __name__ == "__main__":
    asyncio.run(main())
