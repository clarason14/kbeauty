import asyncio, argparse, json, re, sys
from datetime import datetime, timezone
import pandas as pd
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def to_iso_date(ts: Optional[str]) -> Optional[str]:
    if not ts: return None
    try:
        sec = int(str(ts).strip().strip('"'))
        return datetime.fromtimestamp(sec, tz=timezone.utc).date().isoformat()
    except Exception:
        return None

async def extract_date_from_page(page) -> Optional[str]:
    try:
        handle = page.locator('script#SIGI_STATE')
        if await handle.count() > 0:
            txt = await handle.first.text_content()
            if txt:
                try:
                    state = json.loads(txt)
                    item_module = state.get("ItemModule") or {}
                    for k, v in item_module.items():
                        if isinstance(v, dict) and ("createTime" in v):
                            d = to_iso_date(v.get("createTime"))
                            if d: return d
                except Exception:
                    pass
        html = await page.content()
        m = re.search(r'"createTime"\s*:\s*"?(?P<sec>\d{9,})"?', html)
        if m:
            return to_iso_date(m.group("sec"))
        try:
            t = await page.locator("time").first.get_attribute("datetime")
            if t and len(t) >= 10:
                return t[:10]
        except Exception:
            pass
        m2 = re.search(r'"create_time"\s*:\s*(?P<sec>\d{9,})', html)
        if m2:
            return to_iso_date(m2.group("sec"))
    except Exception:
        pass
    return None

async def fetch_date(context, url: str, timeout_ms: int) -> Optional[str]:
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        await page.wait_for_timeout(1500)
        try:
            await page.keyboard.press("Escape")
        except Exception:
            pass
        d = await extract_date_from_page(page)
        return d
    except PlaywrightTimeoutError:
        return None
    except Exception:
        return None
    finally:
        await page.close()

async def run(in_csv: Path, out_csv: Path, timeout_ms: int, delay_s: float, checkpoint: int):
    df = pd.read_csv(in_csv)
    if "URL" not in df.columns:
        print("Missing URL column.")
        sys.exit(2)
    if "Upload_Date" not in df.columns:
        df["Upload_Date"] = None

    mask_missing = df["Upload_Date"].isna() | (df["Upload_Date"].astype(str).str.strip() == "") | (df["Upload_Date"].astype(str) == "nan")
    jobs = [(i, str(df.at[i, "URL"])) for i, ok in enumerate(mask_missing) if ok and isinstance(df.at[i, "URL"], str) and df.at[i, "URL"].startswith("http")]

    if not jobs:
        print("No rows to process.")
        df.to_csv(out_csv, index=False)
        return

    processed = 0
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent=UA,
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        try:
            for i, url in jobs:
                d = await fetch_date(context, url, timeout_ms)
                df.at[i, "Upload_Date"] = d
                status = d if d else "FAILED"
                processed += 1
                print(f"[{processed}] {url} -> {status}")
                if checkpoint and (processed % checkpoint == 0):
                    checkpoint_file = out_csv.with_name(f"{out_csv.stem}_checkpoint.csv")
                    df.to_csv(checkpoint_file, index=False)
                    print(f"Checkpoint saved: {checkpoint_file}")
                await asyncio.sleep(delay_s)
        finally:
            await context.close()
            await browser.close()

    df.to_csv(out_csv, index=False)
    print(f"Final saved: {out_csv}")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="in_csv", required=True)
    p.add_argument("--out", dest="out_csv", required=True)
    p.add_argument("--timeout_ms", type=int, default=20000)
    p.add_argument("--delay_s", type=float, default=1.5)
    p.add_argument("--checkpoint", type=int, default=50)
    args = p.parse_args()

    asyncio.run(run(
        in_csv=Path(args.in_csv),
        out_csv=Path(args.out_csv),
        timeout_ms=args.timeout_ms,
        delay_s=args.delay_s,
        checkpoint=args.checkpoint,
    ))

if __name__ == "__main__":
    main()
