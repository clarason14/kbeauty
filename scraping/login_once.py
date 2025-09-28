# scraping/login_once.py
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

PROFILE_DIR = Path.home() / "tiktok_profiles" / "scraper1"

async def main():
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        # Persistent context = real user profile stored on disk
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await context.new_page()
        await page.goto("https://www.tiktok.com", timeout=60000)

        print("\n[Login] In the opened Chromium window:")
        print("- Click Log in.")
        print("- Either enter TikTok credentials OR click 'Continue with Google' and complete OAuth.")
        print("- Solve any CAPTCHA.")
        print("- When you can see your feed or profile, come back to this terminal and press Enter.\n")
        input("Press Enter here ONLY after you've finished logging in... ")

        # Optionally verify we have tiktok cookies
        cookies = await context.cookies()
        has_tt = any("tiktok.com" in c.get("domain","") for c in cookies)
        print(f"[Login] Cookies saved for TikTok domain: {has_tt}")

        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
