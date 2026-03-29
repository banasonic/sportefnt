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
                
                // Extract channels
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
