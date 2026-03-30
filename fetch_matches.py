import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError
import re

async def fetch_channel_details(page, btn_element):
    """Fetches channel details by clicking the button and parsing the resulting modal."""
    try:
        name = await btn_element.inner_text()
        
        # Check if the button is actually clickable (not locked/disabled)
        is_disabled = await btn_element.get_attribute("disabled")
        if is_disabled:
            return {"name": name.strip(), "details": "Locked/Disabled"}

        # Click the button. Playwright's click() method automatically waits for the element
        # to be visible, enabled, and receive events.
        await btn_element.click(timeout=5000)
        
        # Wait for the modal to appear
        modal_selector = ".modal-content, #MagicTableModal"
        try:
            await page.wait_for_selector(modal_selector, state="visible", timeout=5000)
            await asyncio.sleep(0.5) # Allow animation to finish
        except TimeoutError:
            # If modal doesn't appear, it might be a non-detail button or a temporary issue
            return {"name": name.strip(), "details": "No details available or modal did not appear"}

        # Extract details from the modal
        modal = await page.query_selector(modal_selector)
        if not modal:
            return {"name": name.strip(), "details": "Modal element not found after appearing"}

        modal_text = await modal.inner_text()
        
        details = {}
        for line in modal_text.split("\n"):
            if ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    k, v = parts
                    details[k.strip()] = v.strip()
        
        # Close the modal using Escape key (most reliable)
        await page.keyboard.press("Escape")
        await asyncio.sleep(0.3)
        
        return {"name": name.strip(), "details": details}
    except TimeoutError as e:
        print(f"Timeout fetching channel details for {name}: {e}")
        return {"name": name.strip(), "details": "Timeout during interaction"}
    except Exception as e:
        print(f"Error fetching channel details for {name}: {e}")
        return {"name": name.strip(), "details": None}

async def fetch_match(page, row_element):
    """Fetches data for a single match row."""
    # Extract basic info
    league_el = await row_element.query_selector(".MagicTableRowHeadline")
    league = await league_el.inner_text() if league_el else "Unknown League"

    homeTeam_el = await row_element.query_selector(".MagicTableRowMainHomeTeamName")
    homeTeam = await homeTeam_el.inner_text() if homeTeam_el else "Unknown Home"

    awayTeam_el = await row_element.query_selector(".MagicTableRowMainAwayTeamName")
    awayTeam = await awayTeam_el.inner_text() if awayTeam_el else "Unknown Away"

    time_el = await row_element.query_selector("h3")
    time = await time_el.inner_text() if time_el else "Unknown Time"

    # Flag logic (simplified, as it was working previously)
    def get_flag_url(style_str):
        if not style_str: return None
        match_ = re.search(r"url\(\"?(.+?)\"?\)", style_str)
        if match_:
            url = match_.group(1)
            return url if url.startswith("http") else "https://www.sporteventz.com" + url
        return None

    homeDiv = await row_element.query_selector(".MagicTableLeftFlag")
    homeFlag = get_flag_url(await homeDiv.evaluate("el => el.style.background")) if homeDiv else None

    awayDiv = await row_element.query_selector(".MagicTableRightFlag")
    awayFlag = get_flag_url(await awayDiv.evaluate("el => el.style.background")) if awayDiv else None

    # Channel buttons
    channel_btn_elements = await row_element.query_selector_all("button[id^=\"btnsub\"]")
    
    channels = []
    for btn_el in channel_btn_elements:
        ch_detail = await fetch_channel_details(page, btn_el)
        if ch_detail:
            channels.append(ch_detail)

    return {
        "league": league.strip(),
        "homeTeam": homeTeam.strip(),
        "awayTeam": awayTeam.strip(),
        "homeFlag": homeFlag,
        "awayFlag": awayFlag,
        "time": time.strip(),
        "channels": channels
    }

async def run_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            viewport={\'width\': 1280, \'height\': 800}
        )
        page = await context.new_page()
        
        print("Navigating to SportEventz...")
        await page.goto("https://www.sporteventz.com/en/", wait_until="domcontentloaded")
        
        # Handle cookie consent if present
        try:
            cookie_button = await page.wait_for_selector("a:has-text(\"Ok, I've understood!\")", timeout=5000)
            if cookie_button:
                await cookie_button.click()
                print("Accepted cookie consent.")
                await page.wait_for_load_state("networkidle") # Wait for page to settle after cookie click
        except TimeoutError:
            print("No cookie consent banner found or it disappeared.")

        # Wait for the main table to load. Use a more general selector if specific one fails.
        print("Waiting for match data to load...")
        match_table_selector = "table.jtable"
        try:
            await page.wait_for_selector(match_table_selector, state="visible", timeout=30000)
        except TimeoutError:
            print("Timeout waiting for match table. Saving screenshot for debugging.")
            await page.screenshot(path="debug_screenshot_no_table.png")
            await browser.close()
            return

        # Now get the rows within the table
        rows = await page.query_selector_all(f"{match_table_selector} tr.jtable-data-row")
        
        num_matches = len(rows)
        print(f"Found {num_matches} matches. Extracting top 5 for validation...")

        matches = []
        limit = min(num_matches, 5) 
        for i in range(limit):
            print(f"Processing match {i+1}/{limit}...")
            match_data = await fetch_match(page, rows[i]) # Pass the element directly
            if match_data:
                matches.append(match_data)
        
        await browser.close()

        output = {
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "matches": matches
        }
        
        with open("matches_fixed.json", "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=4)

        print(f"Successfully saved {len(matches)} matches to matches_fixed.json")
        return matches

if __name__ == "__main__":
    asyncio.run(run_scraper())
