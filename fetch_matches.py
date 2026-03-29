import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright
import re

async def fetch_channel_details(page, btn):
    """جلب تفاصيل القناة مع تعامل مرن مع أي popup"""
    name = await btn.inner_text()
    try:
        await btn.click()
        await asyncio.sleep(1.5)  # انتظر ظهور أي popup ديناميكي
        
        # البحث عن أي modal محتمل
        possible_modal = await page.query_selector("div.modal, div.modal-content")
        if possible_modal:
            modal_text = await possible_modal.inner_text()
            details = {}
            for line in modal_text.split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    details[k.strip()] = v.strip()
        else:
            details = None
        
        # اغلاق أي popup إذا ظهر
        close_btn = await page.query_selector("div.modal button.close, div.modal-footer button")
        if close_btn:
            await close_btn.click()
        await page.wait_for_timeout(300)
        
        return {"name": name.strip(), "details": details}
    except:
        return {"name": name.strip(), "details": None}

async def fetch_match(page, row):
    """جلب بيانات مباراة واحدة مع قنواتها بشكل متوازي"""
    league_el = await row.query_selector('.MagicTableRowHeadline')
    league = await league_el.inner_text() if league_el else None

    homeTeam_el = await row.query_selector('.MagicTableRowMainHomeTeamName')
    homeTeam = await homeTeam_el.inner_text() if homeTeam_el else None

    awayTeam_el = await row.query_selector('.MagicTableRowMainAwayTeamName')
    awayTeam = await awayTeam_el.inner_text() if awayTeam_el else None

    time_el = await row.query_selector('h3')
    time = await time_el.inner_text() if time_el else None

    # الأعلام
    homeFlag = None
    homeDiv = await row.query_selector('.MagicTableLeftFlag')
    if homeDiv:
        style = await homeDiv.evaluate('el => el.style.background')
        match_ = re.search(r'url\("?(.+?)"?\)', style)
        if match_:
            url = match_.group(1)
            homeFlag = url if url.startswith('http') else 'https://www.sporteventz.com' + url

    awayFlag = None
    awayDiv = await row.query_selector('.MagicTableRightFlag')
    if awayDiv:
        style = await awayDiv.evaluate('el => el.style.background')
        match_ = re.search(r'url\("?(.+?)"?\)', style)
        if match_:
            url = match_.group(1)
            awayFlag = url if url.startswith('http') else 'https://www.sporteventz.com' + url

    # القنوات بشكل متوازي
    channel_buttons = await row.query_selector_all('button[id^="btnsub"]')
    channels = await asyncio.gather(*[fetch_channel_details(page, btn) for btn in channel_buttons])

    return {
        "league": league,
        "homeTeam": homeTeam,
        "awayTeam": awayTeam,
        "homeFlag": homeFlag,
        "awayFlag": awayFlag,
        "time": time,
        "channels": channels
    }

async def fetch_matches():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Navigating to SportEventz...")
        await page.goto("https://www.sporteventz.com/", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        
        await page.wait_for_selector("tr.jtable-data-row", state="attached", timeout=30000)
        rows = await page.query_selector_all("tr.jtable-data-row")
        print(f"Found {len(rows)} matches. Fetching in parallel...")

        # كل المباريات تعمل بشكل متوازي مع قنواتها
        matches = await asyncio.gather(*[fetch_match(page, row) for row in rows])
        
        await browser.close()

        # حفظ JSON
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
