#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت استخراج مباريات اليوم من موقع SportEventz
موريتاني سبورت -Mauritanie Sport
"""

import asyncio
import json
import logging
import os
import random
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from playwright.async_api import async_playwright, Page, Browser, Playwright
from bs4 import BeautifulSoup

# إعدادات التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# مسارات الملفات
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
DATA_DIR = BASE_DIR / "data"

class SportEventzScraper:
    """فئة استخراج البيانات من موقع SportEventz"""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright: Optional[Playwright] = None
        self.base_url = "https://www.sporteventz.com"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        ]

    async def init_browser(self) -> Browser:
        """تهيئة المتصفح"""
        logger.info("جاري تهيئة المتصفح...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        )
        return self.browser

    async def close(self):
        """إغلاق المتصفح"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def get_random_user_agent(self) -> str:
        """الحصول على وكيل مستخدم عشوائي"""
        return random.choice(self.user_agents)

    async def fetch_page(self, url: str, retries: int = 3) -> Optional[str]:
        """جلب صفحة مع إعادة المحاولة"""
        for attempt in range(retries):
            try:
                context = await self.browser.new_context(
                    user_agent=self.get_random_user_agent(),
                    viewport={"width": 1920, "height": 1080},
                    locale="en-US"
                )
                page = await context.new_page()

                # إضافة انتظار عشوائي
                await asyncio.sleep(random.uniform(1, 3))

                logger.info(f"جاري جلب: {url} (المحاولة {attempt + 1})")
                response = await page.goto(url, wait_until="networkidle", timeout=30000)

                if response and response.ok:
                    # انتظار المحتوى الديناميكي
                    await page.wait_for_timeout(3000)
                    content = await page.content()
                    await context.close()
                    return content

                await context.close()
            except Exception as e:
                logger.warning(f"فشل المحاولة {attempt + 1}: {e}")
                await asyncio.sleep(2 ** attempt)

        return None

    def parse_match_data(self, html: str) -> List[Dict[str, Any]]:
        """تحليل بيانات المباريات من HTML"""
        matches = []
        soup = BeautifulSoup(html, 'html.parser')

        # البحث عن جدول المباريات
        tables = soup.find_all('table', class_=re.compile(r'magictable|match|schedule', re.I))

        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3:
                    continue

                match = self.extract_match_info(cells)
                if match:
                    matches.append(match)

        # البحث عن divs مع بطاقات المباريات
        cards = soup.find_all('div', class_=re.compile(r'match|card|event', re.I))
        for card in cards:
            match = self.extract_match_from_card(card)
            if match:
                matches.append(match)

        # إزالة التكرارات
        seen = set()
        unique_matches = []
        for match in matches:
            key = f"{match.get('home_team', '')}-{match.get('away_team', '')}-{match.get('time', '')}"
            if key not in seen and match.get('home_team') and match.get('away_team'):
                seen.add(key)
                unique_matches.append(match)

        return unique_matches

    def extract_match_info(self, cells) -> Optional[Dict[str, Any]]:
        """استخراج معلومات المباراة من خلايا الجدول"""
        try:
            match = {}

            for i, cell in enumerate(cells):
                text = cell.get_text(strip=True)
                img = cell.find('img')

                if img and img.get('src'):
                    src = img['src']
                    if 'logo' in src.lower() or 'team' in src.lower():
                        if match.get('home_logo') is None:
                            match['home_logo'] = self.fix_image_url(src)
                        else:
                            match['away_logo'] = self.fix_image_url(src)

                # استخراج اسم الفريق
                if text and not text.startswith(('+', '-', '#')):
                    if match.get('home_team') is None:
                        if len(text) < 50 and not text.isdigit():
                            match['home_team'] = text
                    elif match.get('away_team') is None:
                        if len(text) < 50 and not text.isdigit() and text != match.get('home_team'):
                            match['away_team'] = text

                # استخراج الوقت
                time_match = re.search(r'(\d{1,2}):(\d{2})', text)
                if time_match and match.get('time') is None:
                    match['time'] = time_match.group(0)

            # استخراج القناة والتردد
            for cell in cells:
                channel_info = self.extract_channel_info(str(cell))
                if channel_info:
                    match.update(channel_info)

            if match.get('home_team') and match.get('away_team'):
                return match

        except Exception as e:
            logger.debug(f"خطأ في استخراج البيانات: {e}")

        return None

    def extract_match_from_card(self, card) -> Optional[Dict[str, Any]]:
        """استخراج معلومات المباراة من بطاقة"""
        try:
            match = {}

            # البحث عن شعارات الفرق
            logos = card.find_all('img')
            for i, img in enumerate(logos):
                src = img.get('src', '')
                if src and ('logo' in src.lower() or 'team' in src.lower() or 'flag' in src.lower()):
                    if i == 0:
                        match['home_logo'] = self.fix_image_url(src)
                    else:
                        match['away_logo'] = self.fix_image_url(src)

            # البحث عن أسماء الفرق
            team_names = card.find_all(['span', 'div', 'a'], class_=re.compile(r'team|name|team-name', re.I))
            for i, name in enumerate(team_names[:2]):
                text = name.get_text(strip=True)
                if text and len(text) < 50:
                    if i == 0:
                        match['home_team'] = text
                    else:
                        match['away_team'] = text

            # البحث عن الوقت
            time_elem = card.find(['span', 'div', 'time'], class_=re.compile(r'time', re.I))
            if time_elem:
                time_match = re.search(r'(\d{1,2}):(\d{2})', time_elem.get_text())
                if time_match:
                    match['time'] = time_match.group(0)

            # البحث عن القناة
            channel_elem = card.find(['span', 'div', 'a'], class_=re.compile(r'channel|broadcast', re.I))
            if channel_elem:
                match['channel'] = channel_elem.get_text(strip=True)

            if match.get('home_team') and match.get('away_team'):
                return match

        except Exception as e:
            logger.debug(f"خطأ في استخراج البطاقة: {e}")

        return None

    def extract_channel_info(self, cell_html: str) -> Dict[str, str]:
        """استخراج معلومات القناة والتردد"""
        info = {}

        try:
            soup = BeautifulSoup(cell_html, 'html.parser')
            text = soup.get_text(strip=True)

            # استخراج اسم القناة
            channel_match = re.search(r'([A-Z][a-zA-Z\s]+(?:TV|Channel|Sports|Bein|SSC|OSN|Sky))', text)
            if channel_match:
                info['channel'] = channel_match.group(1)

            # استخراج التردد
            freq_match = re.search(r'(\d{4,5})\s*(?:H|V)', text)
            if freq_match:
                info['frequency'] = freq_match.group(1)

            # استخراج معدل التشفير
            if 'encrypted' in text.lower() or 'FTA' in text:
                info['encryption'] = 'Encrypted' if 'encrypted' in text.lower() else 'FTA'

        except Exception as e:
            logger.debug(f"خطأ في استخراج معلومات القناة: {e}")

        return info

    def fix_image_url(self, url: str) -> str:
        """تصحيح رابط الصورة"""
        if not url:
            return ""
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/'):
            return self.base_url + url
        return url

    async def scrape_all_matches(self) -> List[Dict[str, Any]]:
        """استخراج جميع المباريات"""
        all_matches = []

        urls = [
            f"{self.base_url}/en/sport-eventz.html",
            f"{self.base_url}/en/",
        ]

        for url in urls:
            content = await self.fetch_page(url)
            if content:
                matches = self.parse_match_data(content)
                all_matches.extend(matches)
                logger.info(f"تم استخراج {len(matches)} مباراة من {url}")

        return all_matches

    def save_to_json(self, matches: List[Dict], filename: str = "matches.json"):
        """حفظ البيانات في ملف JSON"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        output_file = OUTPUT_DIR / filename
        data = {
            "timestamp": datetime.now().isoformat(),
            "count": len(matches),
            "matches": matches
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"تم حفظ {len(matches)} مباراة في {output_file}")
        return str(output_file)


async def main():
    """الدالة الرئيسية"""
    logger.info("=" * 50)
    logger.info("بدء سكريبت استخراج المباريات")
    logger.info("=" * 50)

    scraper = SportEventzScraper()

    try:
        await scraper.init_browser()
        matches = await scraper.scrape_all_matches()

        if matches:
            output_file = scraper.save_to_json(matches)
            logger.info(f"تمت العملية بنجاح! تم استخراج {len(matches)} مباراة")
            print(f"\n✅ تم استخراج {len(matches)} مباراة")
            print(f"📁 الملف: {output_file}")
        else:
            logger.warning("لم يتم العثور على مباريات")

    except Exception as e:
        logger.error(f"خطأ: {e}")
        raise

    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
