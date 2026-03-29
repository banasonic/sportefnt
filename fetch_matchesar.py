import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright
from deep_translator import GoogleTranslator

# Initialize translator
translator = GoogleTranslator(source='auto', target='ar')

def translate_text(text):
    if not text:
        return text
    try:
        return translator.translate(text)
    except Exception as e:
        print(f"Translation error for '{text}': {e}")
        return text

async def fetch_matches():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Navigating to SportEventz...")
        await page.goto("https://www.sporteventz.com/", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000) # Wait for JS to run
        
        # Wait for the table to load
        await page.wait_for_selector("tr.jtable-data-row", timeout=30000)
        
        print("Extracting matches...")
        matches = await page.evaluate("""() => {
            const results = [];
            const rows = document.querySelectorAll('tr.jtable-data-row');
            
            rows.forEach(row => {
                const headline = row.querySelector('.MagicTableRowHeadline')?.textContent.trim();
                const homeTeam = row.querySelector('.MagicTableRowMainHomeTeamName')?.textContent.trim();
                const awayTeam = row.querySelector('.MagicTableRowMainAwayTeamName')?.textContent.trim();
                const time = row.querySelector('h3')?.textContent.trim();
                
                // Extract flags
                const homeFlagDiv = row.querySelector('.MagicTableLeftFlag');
                const awayFlagDiv = row.querySelector('.MagicTableRightFlag');
                
                const getFlagUrl = (div) => {
                    if (!div) return null;
                    const style = div.style.background;
                    const match = style.match(/url\\("?(.+?)"?\\)/);
                    if (match) {
                        const url = match[1];
                        return url.startsWith('http') ? url : 'https://www.sporteventz.com' + url;
                    }
                    return null;
                };
                
                const homeFlag = getFlagUrl(homeFlagDiv);
                const awayFlag = getFlagUrl(awayFlagDiv);
                
                // Extract channels - they are buttons
                const channels = Array.from(row.querySelectorAll('button[id^="btnsub"]')).map(btn => btn.textContent.trim());
                
                results.push({
                    league: headline,
                    homeTeam,
                    awayTeam,
                    homeFlag,
                    awayFlag,
                    time,
                    channels
                });
            });
            
            return results;
        }""")
        
        await browser.close()
        
        print(f"Translating {len(matches)} matches to Arabic...")
        for match in matches:
            match['league_ar'] = translate_text(match['league'])
            match['homeTeam_ar'] = translate_text(match['homeTeam'])
            match['awayTeam_ar'] = translate_text(match['awayTeam'])
            # We don't translate channels as they are usually technical names
            
        # Save to JSON
        output = {
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "matches": matches
        }
        
        with open("matches_ar.json", "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=4)
        
        print(f"Successfully fetched and translated {len(matches)} matches.")
        return matches

if __name__ == "__main__":
    asyncio.run(fetch_matches())
