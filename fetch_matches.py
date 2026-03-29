import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def fetch_matches():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Navigating to SportEventz...")
        await page.goto("https://www.sporteventz.com/", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000) # Wait for JS to run
        
        # Wait for the table to load
        await page.wait_for_selector("tr.jtable-data-row", state="attached", timeout=30000)
        
        print("Extracting matches...")

matches = []

rows = await page.query_selector_all("tr.jtable-data-row")

for row in rows:
    headline_el = await row.query_selector(".MagicTableRowHeadline")
    home_el = await row.query_selector(".MagicTableRowMainHomeTeamName")
    away_el = await row.query_selector(".MagicTableRowMainAwayTeamName")
    time_el = await row.query_selector("h3")

    league = await headline_el.inner_text() if headline_el else None
    homeTeam = await home_el.inner_text() if home_el else None
    awayTeam = await away_el.inner_text() if away_el else None
    time = await time_el.inner_text() if time_el else None

    # flags
    homeFlagDiv = await row.query_selector(".MagicTableLeftFlag")
    awayFlagDiv = await row.query_selector(".MagicTableRightFlag")

    async def get_flag(div):
        if not div:
            return None
        style = await div.get_attribute("style")
        if style and "url" in style:
            import re
            match = re.search(r'url\\("?(.+?)"?\\)', style)
            if match:
                url = match.group(1)
                return url if url.startswith("http") else "https://www.sporteventz.com" + url
        return None

    homeFlag = await get_flag(homeFlagDiv)
    awayFlag = await get_flag(awayFlagDiv)

    # القنوات + التردد
    channel_buttons = await row.query_selector_all('button[id^="btnsub"]')

    channels = []

    for btn in channel_buttons:
        name = await btn.inner_text()

        # اضغط لفتح التفاصيل
        await btn.click(force=True)
        await page.wait_for_timeout(1500)

        modal = await page.query_selector(".modal-body")
        details = await modal.inner_text() if modal else None

        channels.append({
            "name": name.strip(),
            "details": details.strip() if details else None
        })

        # اغلاق popup
        close_btn = await page.query_selector(".close")
        if close_btn:
            await close_btn.click()
            await page.wait_for_timeout(500)

    matches.append({
        "league": league,
        "homeTeam": homeTeam,
        "awayTeam": awayTeam,
        "homeFlag": homeFlag,
        "awayFlag": awayFlag,
        "time": time,
        "channels": channels
    })
        
        await browser.close()
        
        # Save to JSON
        output = {
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "matches": matches
        }
        
        with open("matches.json", "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=4)
        
        print(f"Successfully fetched {len(matches)} matches.")
        return matches

if __name__ == "__main__":
    asyncio.run(fetch_matches())
