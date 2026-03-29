import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

async def fetch_matches():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Navigating to SportEventz...")
        await page.goto("https://www.sporteventz.com/", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)  # انتظر لتحميل JS
        
        # انتظر تحميل جدول المباريات
        await page.wait_for_selector("tr.jtable-data-row", state="attached", timeout=30000)
        
        print("Extracting matches...")
        rows = await page.query_selector_all("tr.jtable-data-row")
        matches = []

        for row in rows:
            league = await row.query_selector_eval('.MagicTableRowHeadline', 'el => el.textContent.trim()') if await row.query_selector('.MagicTableRowHeadline') else None
            homeTeam = await row.query_selector_eval('.MagicTableRowMainHomeTeamName', 'el => el.textContent.trim()') if await row.query_selector('.MagicTableRowMainHomeTeamName') else None
            awayTeam = await row.query_selector_eval('.MagicTableRowMainAwayTeamName', 'el => el.textContent.trim()') if await row.query_selector('.MagicTableRowMainAwayTeamName') else None
            time = await row.query_selector_eval('h3', 'el => el.textContent.trim()') if await row.query_selector('h3') else None

            # استخراج الأعلام
            def get_flag(div_selector):
                try:
                    style = await row.eval_on_selector(div_selector, 'el => el.style.background') if await row.query_selector(div_selector) else None
                    if style:
                        match = style.match(r'url\("?(.+?)"?\)')
                        if match:
                            url = match.group(1)
                            return url if url.startswith('http') else 'https://www.sporteventz.com' + url
                except:
                    return None
                return None

            homeFlag = await get_flag('.MagicTableLeftFlag')
            awayFlag = await get_flag('.MagicTableRightFlag')

            # استخراج القنوات مع التفاصيل
            channel_buttons = await row.query_selector_all('button[id^="btnsub"]')
            channels = []

            for btn in channel_buttons:
                name = await btn.inner_text()

                try:
                    await btn.click()
                    await page.wait_for_selector(".modal-content", timeout=10000)

                    modal_text = await page.inner_text(".modal-content")

                    # تحويل التفاصيل الى dict
                    details = {}
                    for line in modal_text.split("\n"):
                        if ":" in line:
                            k, v = line.split(":", 1)
                            details[k.strip()] = v.strip()

                    channels.append({
                        "name": name.strip(),
                        "details": details
                    })

                    # اغلاق البوب اب
                    close_btn = await page.query_selector(".modal-header button.close, .modal-footer button")
                    if close_btn:
                        await close_btn.click()

                    await page.wait_for_timeout(500)  # لتجنب مشاكل JS
                except Exception as e:
                    channels.append({
                        "name": name.strip(),
                        "details": None
                    })

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
