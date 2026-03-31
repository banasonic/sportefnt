import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError
import re

async def fetch_channel_details(page, btn_element):
    """Fetches channel details by clicking the button and parsing the resulting modal/content."""
    try:
        name = await btn_element.inner_text()
        
        # Check if the button is locked (has a lock icon)
        is_locked = await btn_element.query_selector("i.fa-lock, .fa-lock")
        if is_locked:
            return {"name": name.strip(), "details": "Locked/Requires Subscription"}

        # Click the button to expand/show details
        # We use scroll_into_view_if_needed to ensure the button is visible before clicking
        await btn_element.scroll_into_view_if_needed()
        await btn_element.click(timeout=5000)
        
        # Give some time for the content to appear
        await asyncio.sleep(1.0)
        
        # Find the expanded details container
        # The container is often added to the bottom of the body or as a sibling
        details_container_selector = ".MagicTableChannels, .MagicTableSubEntryRowWrap, .modal-content"
        
        try:
            # Wait for any of the potential details containers to be visible
            await page.wait_for_selector(details_container_selector, state="visible", timeout=3000)
            
            # Extract content from the visible container
            container = await page.query_selector(details_container_selector)
            if not container:
                return {"name": name.strip(), "details": "Details container not found after click"}

            # Get the details as structured data
            details = {}
            # Try specific sub-entry structure first
            sub_entries = await container.query_selector_all(".MagicTableSubEntry")
            
            if sub_entries:
                for entry in sub_entries:
                    text = await entry.inner_text()
                    if "\n" in text:
                        parts = text.split("\n", 1)
                        if len(parts) == 2:
                            k, v = parts
                            details[k.strip()] = v.strip()
            
            # If no structured details found, try parsing the whole text
            if not details:
                full_text = await container.inner_text()
                lines = [line.strip() for line in full_text.split("\n") if line.strip()]
                # Look for common patterns like "Label\nValue"
                for i in range(0, len(lines) - 1):
                    label = lines[i]
                    value = lines[i+1]
                    if label in ["Name", "Position", "Frequency", "Polarisation", "SR", "FEC", "System", "Modulation", "Crypt"]:
                        details[label] = value

            # Close the details to avoid overlapping with next clicks
            close_btn = await page.query_selector(".MagicTableChannelsClose, .close-modal, button:has-text('Close')")
            if close_btn:
                await close_btn.click()
            else:
                # Press Escape as a fallback to close modals
                await page.keyboard.press("Escape")
            
            await asyncio.sleep(0.5)
            
            return {"name": name.strip(), "details": details if details else "No structured details found"}
            
        except TimeoutError:
            # Try one last fallback: check if clicking again toggles it off
            await btn_element.click()
            return {"name": name.strip(), "details": "Details did not appear after click"}

    except Exception as e:
        return {"name": name.strip() if 'name' in locals() else "Unknown", "details": None}

async def fetch_match(page, row_element):
    """Fetches data for a single match row."""
    try:
        # Extract basic info
        league_el = await row_element.query_selector(".MagicTableRowHeadline")
        league = await league_el.inner_text() if league_el else "Unknown League"

        homeTeam_el = await row_element.query_selector(".MagicTableRowMainHomeTeamName")
        homeTeam = await homeTeam_el.inner_text() if homeTeam_el else "Unknown Home"

        awayTeam_el = await row_element.query_selector(".MagicTableRowMainAwayTeamName")
        awayTeam = await awayTeam_el.inner_text() if awayTeam_el else "Unknown Away"

        time_el = await row_element.query_selector("h3")
        time = await time_el.inner_text() if time_el else "Unknown Time"

        # Flag logic
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
    except Exception as e:
        print(f"Error fetching match: {e}")
        return None

async def run_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()
        
        print("Navigating to SportEventz...")
        await page.goto("https://www.sporteventz.com/en/", wait_until="domcontentloaded")
        
        # Handle cookie consent
        try:
            cookie_button = await page.wait_for_selector("a:has-text(\"Ok, I've understood!\")", timeout=5000)
            if cookie_button:
                await cookie_button.click()
                print("Accepted cookie consent.")
                await page.wait_for_load_state("networkidle")
        except:
            pass

        print("Waiting for match data to load...")
        try:
            await page.wait_for_selector("tr.jtable-data-row", state="visible", timeout=30000)
        except:
            print("Match rows not found. Page might be loading differently.")
            await page.screenshot(path="error_page_load.png")
            await browser.close()
            return

        rows = await page.query_selector_all("tr.jtable-data-row")
        print(f"Found {len(rows)} matches. Processing...")

        matches = []
        # Limit to top 5 for demonstration, remove limit for full scrape
        limit = min(len(rows), 5) 
        for i in range(limit):
            print(f"Processing match {i+1}/{limit}...")
            match_data = await fetch_match(page, rows[i])
            if match_data:
                matches.append(match_data)
        
        await browser.close()

        output = {
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "matches": matches
        }
        
        with open("matches_final.json", "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=4)

        print(f"Successfully saved {len(matches)} matches to matches_final.json")
        return matches

if __name__ == "__main__":
    asyncio.run(run_scraper())
