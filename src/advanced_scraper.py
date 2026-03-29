#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت استخراج المباريات المتقدم - Mauritanie Sport
يتعامل مع المحتوى الديناميكي ويحلل بنية الصفحة بشكل شامل
"""

import asyncio
import json
import logging
import os
import random
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Page, Browser, Playwright, Response
from bs4 import BeautifulSoup, NavigableString, Comment

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

# ثوابت
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
DATA_DIR = BASE_DIR / "data"

@dataclass
class Match:
    """نموذج بيانات المباراة"""
    id: str = ""
    home_team: str = ""
    away_team: str = ""
    home_logo: str = ""
    away_logo: str = ""
    time: str = ""
    league: str = ""
    channel: str = ""
    frequency: str = ""
    polarization: str = ""  # H (Horizontal) or V (Vertical)
    encryption: str = ""  # FTA or Encrypted
    date: str = ""
    sport_type: str = "Football"
    source_url: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class AdvancedScraper:
    """مزيل استخراج البيانات المتقدم"""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright: Optional[Playwright] = None
        self.base_url = "https://www.sporteventz.com"
        self.context = None
        self.page: Optional[Page] = None
        self.matches_found: Set[str] = set()

        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        ]

        # أنماط CSS للبحث
        self.match_selectors = [
            'table.magictable',
            'table.schedule',
            'div.match-card',
            'div.event-card',
            'div.match-item',
            'tr.match-row',
            'div[data-match]',
            'article.match',
            '.fixture',
            '.event',
        ]

        # شعارات القنوات المعروفة
        self.known_channels = [
            'beIN Sports', 'beIN', 'SSC', 'Abu Dhabi Sports',
            'Dubai Sports', 'MBC', 'Sky Sports', 'ESPN',
            'Canal+', 'DAZN', 'TNT Sports', 'BT Sport',
            'SuperSport', 'StarTimes', 'startv', 'RTS',
            'Arryadia', 'SNRT', 'ANN', 'Marrakech',
        ]

    async def init(self) -> bool:
        """تهيئة المتصفح والسياق"""
        try:
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
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-images',
                    '--disable-javascript',
                ]
            )

            self.context = await self.browser.new_context(
                user_agent=random.choice(self.user_agents),
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                ignore_https_errors=True
            )

            self.page = await self.context.new_page()
            logger.info("✅ تم تهيئة المتصفح بنجاح")
            return True

        except Exception as e:
            logger.error(f"فشل تهيئة المتصفح: {e}")
            return False

    async def close(self):
        """إغلاق الموارد"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("تم إغلاق جميع الموارد")
        except Exception as e:
            logger.error(f"خطأ في الإغلاق: {e}")

    async def wait_for_random(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """انتظار عشوائي"""
        await asyncio.sleep(random.uniform(min_sec, max_sec))

    async def fetch_url(self, url: str, wait_load: bool = True) -> Optional[str]:
        """جلب صفحة مع معالجة الأخطاء"""
        for attempt in range(3):
            try:
                logger.info(f"جاري جلب: {url} (المحاولة {attempt + 1})")
                await self.wait_for_random()

                response = await self.page.goto(url, wait_until="domcontentloaded", timeout=45000)

                if response and response.ok:
                    if wait_load:
                        await self.page.wait_for_timeout(3000)

                    content = await self.page.content()
                    logger.info(f"✅ تم جلب {url} بنجاح")
                    return content

                logger.warning(f"استجابة غير ناجحة: {response.status if response else 'None'}")

            except Exception as e:
                logger.warning(f"خطأ في المحاولة {attempt + 1}: {e}")
                await asyncio.sleep(2 ** attempt)

        return None

    def fix_url(self, url: str) -> str:
        """تصحيح URL"""
        if not url:
            return ""
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/') and not url.startswith('//'):
            return self.base_url + url
        return url

    def generate_match_id(self, match: Match) -> str:
        """توليد معرف فريد للمباراة"""
        key = f"{match.home_team}-{match.away_team}-{match.time}-{match.date}"
        return str(abs(hash(key)))[:12]

    def parse_html(self, html: str) -> BeautifulSoup:
        """تحليل HTML"""
        return BeautifulSoup(html, 'html.parser')

    def extract_match_id_from_element(self, elem) -> Optional[str]:
        """استخراج معرف المباراة من العنصر"""
        for attr in ['data-match-id', 'data-id', 'id', 'data-event-id']:
            if elem.get(attr):
                return str(elem[attr])
        return None

    def extract_team_from_text(self, text: str) -> Optional[str]:
        """استخراج اسم الفريق من النص"""
        if not text or len(text) > 60:
            return None

        # إزالة الأرقام والأحرف الخاصة
        cleaned = re.sub(r'[^\w\s\-]', '', text).strip()
        if cleaned and len(cleaned) > 1:
            return cleaned
        return None

    def extract_time(self, text: str) -> Optional[str]:
        """استخراج الوقت من النص"""
        patterns = [
            r'(\d{1,2}:\d{2})',
            r'(\d{1,2})h\s*(\d{2})?',
            r'(\d{1,2})\s*:\s*(\d{2})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) >= 2 and match.group(2):
                    return f"{match.group(1)}:{match.group(2)}"
                return match.group(1)
        return None

    def extract_channel(self, text: str) -> Optional[str]:
        """استخراج اسم القناة"""
        for channel in self.known_channels:
            if channel.lower() in text.lower():
                return channel

        # نمط عام لأسماء القنوات
        match = re.search(r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s*(?:TV|CHANNEL|SPORTS)?)', text)
        if match:
            return match.group(1).strip()
        return None

    def extract_frequency(self, text: str) -> Dict[str, str]:
        """استخراج التردد والاستقطاب"""
        result = {}

        # نمط التردد: 11000, 11559, 12322, etc
        freq_match = re.search(r'(\d{4,5})\s*([HVhv])', text)
        if freq_match:
            result['frequency'] = freq_match.group(1)
            result['polarization'] = freq_match.group(2).upper()

        # نمط معدل التشفير
        if 'encrypted' in text.lower() or 'scrambled' in text.lower():
            result['encryption'] = 'Encrypted'
        elif 'fta' in text.lower():
            result['encryption'] = 'FTA'

        return result

    def extract_league(self, elem) -> str:
        """استخراج اسم الدوري"""
        league_elem = elem.find(['span', 'div', 'a'],
                               class_=re.compile(r'league|tournament|competition|competition-name', re.I))
        if league_elem:
            return league_elem.get_text(strip=True)

        # البحث في عناصر قريبة
        parent = elem.find_parent(['div', 'section', 'article'])
        if parent:
            league_elem = parent.find(['span', 'div'],
                                    class_=re.compile(r'league', re.I))
            if league_elem:
                return league_elem.get_text(strip=True)

        return "Unknown League"

    def parse_table_matches(self, soup: BeautifulSoup) -> List[Match]:
        """تحليل المباريات من الجداول"""
        matches = []

        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue

                match = self.process_row_cells(cells)
                if match and match.home_team and match.away_team:
                    match.id = self.generate_match_id(match)
                    match.source_url = self.base_url
                    matches.append(match)

        return matches

    def process_row_cells(self, cells) -> Optional[Match]:
        """معالجة خلايا الصف"""
        match = Match()

        for cell in cells:
            # استخراج الصور (شعارات الفرق)
            imgs = cell.find_all('img')
            for img in imgs:
                src = img.get('src', '') or img.get('data-src', '')
                if src:
                    if 'logo' in src.lower() or 'team' in src.lower() or 'flag' in src.lower():
                        if not match.home_logo:
                            match.home_logo = self.fix_url(src)
                        elif not match.away_logo:
                            match.away_logo = self.fix_url(src)

            text = cell.get_text(separator=' ', strip=True)

            # استخراج الأسماء
            if not match.home_team:
                team = self.extract_team_from_text(text)
                if team and 'vs' not in team.lower():
                    match.home_team = team
            elif not match.away_team:
                team = self.extract_team_from_text(text)
                if team and team != match.home_team and 'vs' not in team.lower():
                    match.away_team = team

            # استخراج الوقت
            if not match.time:
                match.time = self.extract_time(text)

            # استخراج القناة
            if not match.channel:
                match.channel = self.extract_channel(text)

            # استخراج التردد
            freq_info = self.extract_frequency(text)
            if freq_info.get('frequency') and not match.frequency:
                match.frequency = freq_info.get('frequency')
                match.polarization = freq_info.get('polarization', '')
            if freq_info.get('encryption'):
                match.encryption = freq_info.get('encryption')

        return match if match.home_team else None

    def parse_card_matches(self, soup: BeautifulSoup) -> List[Match]:
        """تحليل المباريات من البطاقات"""
        matches = []

        # البحث عن جميع البطاقات المحتملة
        for selector in self.match_selectors[2:]:
            cards = soup.select(selector)
            for card in cards:
                match = self.process_match_card(card)
                if match and match.home_team and match.away_team:
                    match.id = self.generate_match_id(match)
                    match.source_url = self.base_url
                    matches.append(match)

        return matches

    def process_match_card(self, card) -> Optional[Match]:
        """معالجة بطاقة المباراة"""
        match = Match()

        # البحث عن العناصر النصية
        text_content = card.get_text(separator=' ', strip=True)

        # البحث عن شعارات الفرق
        imgs = card.find_all('img')
        for img in imgs:
            src = img.get('src', '') or img.get('data-src', '')
            alt = img.get('alt', '')

            if src and ('logo' in src.lower() or 'team' in src.lower() or
                       'flag' in src.lower() or 'club' in src.lower()):
                if not match.home_logo:
                    match.home_logo = self.fix_url(src)
                elif not match.away_logo:
                    match.away_logo = self.fix_url(src)

        # البحث عن أسماء الفرق في العناصر النصية
        team_spans = card.find_all(['span', 'div', 'a'],
                                   class_=re.compile(r'team|name|team-name|team-name-home|team-name-away', re.I))

        if len(team_spans) >= 2:
            match.home_team = team_spans[0].get_text(strip=True)
            match.away_team = team_spans[1].get_text(strip=True)
        else:
            # محاولة استخراج الفرق من النص الكامل
            parts = re.split(r'\s*(?:vs?|VS?|-)\s*', text_content)
            if len(parts) >= 2:
                match.home_team = self.extract_team_from_text(parts[0]) or ""
                match.away_team = self.extract_team_from_text(parts[-1]) or ""

        # استخراج الوقت
        time_elem = card.find(['span', 'div', 'time'],
                            class_=re.compile(r'time|kickoff', re.I))
        if time_elem:
            match.time = self.extract_time(time_elem.get_text()) or ""
        else:
            match.time = self.extract_time(text_content) or ""

        # استخراج القناة
        channel_elem = card.find(['span', 'div', 'a'],
                               class_=re.compile(r'channel|broadcast|tv', re.I))
        if channel_elem:
            match.channel = channel_elem.get_text(strip=True)
        else:
            match.channel = self.extract_channel(text_content) or ""

        # استخراج التردد
        freq_info = self.extract_frequency(text_content)
        if freq_info.get('frequency'):
            match.frequency = freq_info.get('frequency')
            match.polarization = freq_info.get('polarization', '')
        match.encryption = freq_info.get('encryption', '')

        # استخراج الدوري
        match.league = self.extract_league(card)

        # استخراج التاريخ
        date_elem = card.find(['span', 'div'],
                            class_=re.compile(r'date|day', re.I))
        if date_elem:
            match.date = date_elem.get_text(strip=True)
        else:
            match.date = datetime.now().strftime("%Y-%m-%d")

        return match if match.home_team and match.away_team else None

    def deduplicate_matches(self, matches: List[Match]) -> List[Match]:
        """إزالة المباريات المكررة"""
        seen = set()
        unique = []

        for match in matches:
            key = f"{match.home_team}|{match.away_team}|{match.time}|{match.date}"
            if key not in seen and match.home_team and match.away_team:
                seen.add(key)
                unique.append(match)

        return unique

    async def scrape_main_page(self) -> List[Match]:
        """استخراج المباريات من الصفحة الرئيسية"""
        matches = []
        url = f"{self.base_url}/en/"

        html = await self.fetch_url(url)
        if not html:
            logger.error("فشل جلب الصفحة الرئيسية")
            return matches

        soup = self.parse_html(html)

        # تحليل الجداول
        table_matches = self.parse_table_matches(soup)
        matches.extend(table_matches)
        logger.info(f"تم استخراج {len(table_matches)} مباراة من الجداول")

        # تحليل البطاقات
        card_matches = self.parse_card_matches(soup)
        matches.extend(card_matches)
        logger.info(f"تم استخراج {len(card_matches)} مباراة من البطاقات")

        return matches

    async def scrape_sport_pages(self, sport: str = "football") -> List[Match]:
        """استخراج المباريات من صفحات الرياضات"""
        matches = []
        url = f"{self.base_url}/en/sport-eventz.html"

        html = await self.fetch_url(url)
        if not html:
            return matches

        soup = self.parse_html(html)

        # استخراج الروابط ديناميكياً
        links = soup.find_all('a', href=re.compile(r'sport|event|match', re.I))
        unique_urls = set()

        for link in links[:20]:  # تحديد الحد الأقصى
            href = link.get('href', '')
            if href and href not in unique_urls:
                full_url = urljoin(self.base_url, href)
                if self.base_url in full_url:
                    unique_urls.add(full_url)

        logger.info(f"تم العثور على {len(unique_urls)} رابط للاستكشاف")

        for page_url in unique_urls:
            await self.wait_for_random(0.5, 1.5)
            html = await self.fetch_url(page_url)
            if html:
                soup = self.parse_html(html)
                page_matches = self.parse_table_matches(soup)
                page_matches.extend(self.parse_card_matches(soup))
                matches.extend(page_matches)

        return matches

    def save_data(self, matches: List[Match], filename: str = "matches.json") -> str:
        """حفظ البيانات"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        output_file = OUTPUT_DIR / filename
        data = {
            "timestamp": datetime.now().isoformat(),
            "date": date.today().isoformat(),
            "total_matches": len(matches),
            "matches": [m.to_dict() for m in matches]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"تم حفظ {len(matches)} مباراة في {output_file}")
        return str(output_file)

    async def run(self) -> List[Match]:
        """تشغيل المستخرج"""
        logger.info("=" * 60)
        logger.info("🏆 بدء سكريبت استخراج مباريات SportEventz")
        logger.info("=" * 60)

        all_matches = []

        try:
            if not await self.init():
                raise Exception("فشل تهيئة المتصفح")

            # استخراج من الصفحة الرئيسية
            main_matches = await self.scrape_main_page()
            all_matches.extend(main_matches)
            logger.info(f"✅ إجمالي المباريات من الصفحة الرئيسية: {len(main_matches)}")

            # استخراج من صفحات الرياضات
            sport_matches = await self.scrape_sport_pages()
            all_matches.extend(sport_matches)
            logger.info(f"✅ إجمالي المباريات من صفحات الرياضة: {len(sport_matches)}")

            # إزالة التكرارات
            unique_matches = self.deduplicate_matches(all_matches)
            logger.info(f"✅ المباريات الفريدة: {len(unique_matches)}")

            # حفظ البيانات
            if unique_matches:
                self.save_data(unique_matches)
                print(f"\n" + "=" * 50)
                print(f"✅ تم استخراج {len(unique_matches)} مباراة بنجاح!")
                print(f"📁 الملف: {OUTPUT_DIR / 'matches.json'}")
                print("=" * 50)

        except Exception as e:
            logger.error(f"خطأ في التشغيل: {e}")
            raise

        finally:
            await self.close()

        return unique_matches


async def main():
    """الدالة الرئيسية"""
    scraper = AdvancedScraper()
    matches = await scraper.run()
    return matches


if __name__ == "__main__":
    asyncio.run(main())
