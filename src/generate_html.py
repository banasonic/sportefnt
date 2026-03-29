#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت توليد صفحة HTML من بيانات المباريات
Mauritanie Sport - Mauritanie Sport
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# مسارات الملفات
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
TEMPLATE_FILE = BASE_DIR / "templates" / "index.html"


def load_matches_data() -> List[Dict[str, Any]]:
    """تحميل بيانات المباريات من ملف JSON"""
    json_file = OUTPUT_DIR / "matches.json"

    if not json_file.exists():
        print(f"⚠️ ملف البيانات غير موجود: {json_file}")
        return []

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('matches', [])
    except Exception as e:
        print(f"❌ خطأ في قراءة الملف: {e}")
        return []


def get_sport_emoji(sport_type: str) -> str:
    """الحصول على رمز الرياضة"""
    emojis = {
        'football': '⚽',
        'basketball': '🏀',
        'tennis': '🎾',
        'volleyball': '🏐',
        'handball': '🤾',
        'hockey': '🏒',
        'rugby': '🏉',
        'baseball': '⚾',
        'cricket': '🏏',
        'golf': '⛳',
        'boxing': '🥊',
        'mma': '🥋',
        'athletics': '🏃',
        'swimming': '🏊',
        'other': '🏆'
    }
    return emojis.get(sport_type.lower() if sport_type else '', '🏆')


def get_team_emoji(team_name: str) -> str:
    """الحصول على رمز الفريق"""
    if not team_name:
        return '⚽'

    team_lower = team_name.lower()

    if 'أهلي' in team_lower or 'al ahly' in team_lower:
        return '🔴'
    elif 'زمالك' in team_lower or 'zamalek' in team_lower:
        return '⚪'
    elif 'ريال' in team_lower or 'real' in team_lower:
        return '👑'
    elif 'برشلونة' in team_lower or 'barcelona' in team_lower:
        return '🔵🔴'
    elif 'مانشستر' in team_lower or 'manchester' in team_lower:
        return '🔴'
    elif 'ليفربول' in team_lower or 'liverpool' in team_lower:
        return '🔴'
    elif 'باريس' in team_lower or 'psg' in team_lower or 'paris' in team_lower:
        return '🔵🔴'
    elif 'بايرن' in team_lower or 'bayern' in team_lower:
        return '🔴'
    elif 'دورتموند' in team_lower or 'dortmund' in team_lower:
        return '🟡'
    elif 'يوفنتوس' in team_lower or 'juventus' in team_lower:
        return '⚫⚪'
    elif 'إنتر' in team_lower or 'inter' in team_lower:
        return '🔵⚫'
    elif ' ميلان' in team_lower or 'milan' in team_lower:
        return '🔴⚫'
    else:
        return '⚽'


def create_match_card(match: Dict[str, Any]) -> str:
    """إنشاء بطاقة مباراة واحدة"""
    home_team = match.get('home_team', 'الفريق المضيف')
    away_team = match.get('away_team', 'الفريق الضيف')
    home_logo = match.get('home_logo', '')
    away_logo = match.get('away_logo', '')
    time = match.get('time', '---')
    league = match.get('league', 'غير محدد')
    channel = match.get('channel', '')
    frequency = match.get('frequency', '')
    polarization = match.get('polarization', 'H')
    encryption = match.get('encryption', '')
    sport_type = match.get('sport_type', 'football')

    # إنشاء HTML للصور
    home_img = f'<img class="team-logo" src="{home_logo}" alt="{home_team}" onerror="this.style.display=\'none\'; this.nextElementSibling.textContent=\'{get_team_emoji(home_team)}\'">' if home_logo else ''
    away_img = f'<img class="team-logo" src="{away_logo}" alt="{away_team}" onerror="this.style.display=\'none\'; this.nextElementSibling.textContent=\'{get_team_emoji(away_team)}\'">' if away_logo else ''

    # معلومات القناة
    channel_html = ''
    if channel:
        channel_details = []
        if frequency:
            channel_details.append(f'<div class="channel-detail"><span class="label">التردد:</span><span class="value">{frequency} {polarization}</span></div>')
        if encryption:
            icon = '🔓' if encryption.upper() == 'FTA' else '🔒'
            text = 'مفتوح' if encryption.upper() == 'FTA' else 'مشفّر'
            channel_details.append(f'<span class="encryption-badge {encryption.lower()}">{icon} {text}</span>')

        if channel_details:
            channel_html = f'''
            <div class="channel-section">
                <div class="channel-header">
                    <span class="channel-icon">📺</span>
                    <span class="channel-name">{channel}</span>
                </div>
                <div class="channel-details">
                    {"".join(channel_details)}
                </div>
            </div>
            '''

    return f'''
                <article class="match-card" data-sport="{sport_type}">
                    <div class="match-header">
                        <div class="league-badge">
                            <span class="league-icon">{get_sport_emoji(sport_type)}</span>
                            <span class="league-name">{league}</span>
                        </div>
                        <div class="match-time-badge">
                            <span>🕐</span>
                            <span>{time}</span>
                        </div>
                    </div>
                    <div class="match-body">
                        <div class="teams-container">
                            <div class="team">
                                {home_img}
                                <span class="team-name">{home_team}</span>
                            </div>
                            <div class="vs-container">
                                <div class="vs-text">VS</div>
                                <div class="vs-label">مباراة</div>
                            </div>
                            <div class="team">
                                {away_img}
                                <span class="team-name">{away_team}</span>
                            </div>
                        </div>
                        {channel_html}
                    </div>
                </article>
    '''


def generate_html(matches: List[Dict[str, Any]], timestamp: str = None) -> str:
    """توليد صفحة HTML الكاملة"""

    # حساب الإحصائيات
    channel_list = [match.get('channel', '') for match in matches if match.get('channel')]
    channels = len(set(channel_list))
    leagues = set(m.get('league', '') for m in matches if m.get('league'))
    leagues_count = len([l for l in leagues if l])

    # إنشاء بطاقات المباريات
    matches_html = ''.join([create_match_card(match) for match in matches])

    # وقت التحديث
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            update_time = dt.strftime('%A, %d %B %Y, %H:%M')
        except:
            update_time = timestamp
    else:
        update_time = datetime.now().strftime('%A, %d %B %Y, %H:%M')

    # البطاقات الفارغة
    if not matches:
        matches_html = '''
                <div class="empty-state">
                    <div class="empty-icon">🔍</div>
                    <h3 class="empty-title">لا توجد مباريات</h3>
                    <p class="empty-text">لم يتم العثور على مباريات في هذا التصنيف. يرجى المحاولة لاحقاً.</p>
                </div>
        '''

    html_content = f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="مباريات اليوم - تابع جميع المباريات والقنوات الناقلة بالترددات">
    <meta name="author" content="Mauritanie Sport">
    <meta name="robots" content="index, follow">
    <title>مباريات اليوم | Mauritanie Sport</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --secondary: #10b981;
            --accent: #f43f5e;
            --dark: #0f172a;
            --gray-900: #1e293b;
            --gray-800: #334155;
            --gray-600: #475569;
            --gray-400: #94a3b8;
            --gray-200: #e2e8f0;
            --gray-100: #f1f5f9;
            --gray-50: #f8fafc;
            --white: #ffffff;
            --card-bg: #ffffff;
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
            --shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
            --shadow-xl: 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04);
            --radius: 16px;
            --radius-lg: 24px;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Cairo', sans-serif;
            background: linear-gradient(135deg, var(--gray-100) 0%, var(--gray-50) 100%);
            color: var(--dark);
            min-height: 100vh;
            direction: rtl;
            line-height: 1.6;
        }}

        /* Header */
        .header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}

        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
            opacity: 0.5;
        }}

        .header-content {{
            position: relative;
            z-index: 1;
            max-width: 800px;
            margin: 0 auto;
        }}

        .header h1 {{
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        .header h1 .icon {{
            font-size: 3.5rem;
        }}

        .header p {{
            font-size: 1.2rem;
            opacity: 0.95;
            margin-bottom: 20px;
        }}

        .live-badge {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: rgba(255,255,255,0.2);
            backdrop-filter: blur(10px);
            padding: 12px 28px;
            border-radius: 50px;
            font-weight: 600;
            border: 1px solid rgba(255,255,255,0.3);
        }}

        .live-dot {{
            width: 12px;
            height: 12px;
            background: #ef4444;
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; transform: scale(1); box-shadow: 0 0 0 0 rgba(239,68,68,0.7); }}
            50% {{ opacity: 0.8; transform: scale(1.1); box-shadow: 0 0 0 8px rgba(239,68,68,0); }}
        }}

        /* Stats Section */
        .stats-section {{
            max-width: 1200px;
            margin: -30px auto 0;
            padding: 0 20px;
            position: relative;
            z-index: 10;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}

        .stat-card {{
            background: var(--white);
            border-radius: var(--radius);
            padding: 25px;
            text-align: center;
            box-shadow: var(--shadow-lg);
            transition: transform 0.3s, box-shadow 0.3s;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: var(--shadow-xl);
        }}

        .stat-icon {{
            font-size: 2.5rem;
            margin-bottom: 10px;
        }}

        .stat-value {{
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--primary);
            line-height: 1;
        }}

        .stat-label {{
            color: var(--gray-600);
            font-size: 0.95rem;
            margin-top: 8px;
        }}

        /* Filters */
        .filters-section {{
            max-width: 1200px;
            margin: 40px auto;
            padding: 0 20px;
        }}

        .filters-container {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            justify-content: center;
        }}

        .filter-btn {{
            padding: 12px 28px;
            border: 2px solid var(--gray-200);
            background: var(--white);
            color: var(--gray-600);
            border-radius: 50px;
            cursor: pointer;
            font-family: inherit;
            font-size: 0.95rem;
            font-weight: 600;
            transition: all 0.3s;
        }}

        .filter-btn:hover {{
            border-color: var(--primary);
            color: var(--primary);
        }}

        .filter-btn.active {{
            background: var(--primary);
            border-color: var(--primary);
            color: white;
        }}

        /* Main Content */
        .main-content {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}

        .section-title {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 30px;
            padding: 0 10px;
        }}

        .section-title h2 {{
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--dark);
        }}

        .section-title .line {{
            flex: 1;
            height: 3px;
            background: linear-gradient(90deg, var(--primary), transparent);
            border-radius: 2px;
        }}

        /* Matches Grid */
        .matches-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 25px;
        }}

        /* Match Card */
        .match-card {{
            background: var(--card-bg);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            overflow: hidden;
            transition: all 0.3s;
            border: 1px solid var(--gray-100);
            animation: fadeIn 0.3s ease;
        }}

        .match-card:hover {{
            transform: translateY(-8px);
            box-shadow: var(--shadow-xl);
            border-color: var(--primary);
        }}

        .match-header {{
            background: linear-gradient(135deg, var(--gray-900) 0%, var(--gray-800) 100%);
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .league-badge {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .league-icon {{
            font-size: 1.2rem;
        }}

        .league-name {{
            font-size: 0.9rem;
            font-weight: 600;
        }}

        .match-time-badge {{
            background: var(--accent);
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .match-body {{
            padding: 25px 20px;
        }}

        .teams-container {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}

        .team {{
            display: flex;
            flex-direction: column;
            align-items: center;
            flex: 1;
        }}

        .team-logo {{
            width: 80px;
            height: 80px;
            object-fit: contain;
            margin-bottom: 12px;
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));
            transition: transform 0.3s;
        }}

        .team:hover .team-logo {{
            transform: scale(1.1);
        }}

        .team-name {{
            font-size: 1.1rem;
            font-weight: 700;
            text-align: center;
            color: var(--dark);
            max-width: 130px;
        }}

        .vs-container {{
            padding: 0 15px;
        }}

        .vs-text {{
            font-size: 1.5rem;
            font-weight: 800;
            color: var(--gray-400);
        }}

        .vs-label {{
            font-size: 0.8rem;
            color: var(--gray-400);
        }}

        /* Channel Info */
        .channel-section {{
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            border-radius: 14px;
            padding: 18px;
            margin-top: 15px;
        }}

        .channel-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 12px;
        }}

        .channel-icon {{
            font-size: 1.5rem;
        }}

        .channel-name {{
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--primary);
        }}

        .channel-details {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            align-items: center;
        }}

        .channel-detail {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.9rem;
        }}

        .channel-detail .label {{
            color: var(--gray-600);
        }}

        .channel-detail .value {{
            font-weight: 700;
            color: var(--dark);
            background: white;
            padding: 4px 12px;
            border-radius: 8px;
            font-size: 0.85rem;
        }}

        .encryption-badge {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 5px 12px;
            border-radius: 10px;
            font-size: 0.8rem;
            font-weight: 600;
        }}

        .encryption-badge.fta {{
            background: #dcfce7;
            color: #16a34a;
        }}

        .encryption-badge.encrypted {{
            background: #fee2e2;
            color: #dc2626;
        }}

        /* Empty State */
        .empty-state {{
            text-align: center;
            padding: 80px 20px;
            grid-column: 1 / -1;
        }}

        .empty-icon {{
            font-size: 4rem;
            margin-bottom: 20px;
        }}

        .empty-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--dark);
            margin-bottom: 10px;
        }}

        .empty-text {{
            color: var(--gray-600);
        }}

        /* Footer */
        .footer {{
            background: var(--dark);
            color: white;
            text-align: center;
            padding: 40px 20px;
            margin-top: 60px;
        }}

        .footer-content {{
            max-width: 600px;
            margin: 0 auto;
        }}

        .footer-logo {{
            font-size: 2rem;
            margin-bottom: 15px;
        }}

        .footer-links {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}

        .footer-link {{
            color: var(--gray-400);
            text-decoration: none;
            transition: color 0.3s;
        }}

        .footer-link:hover {{
            color: white;
        }}

        .footer-copyright {{
            color: var(--gray-400);
            font-size: 0.9rem;
        }}

        /* Update Time */
        .update-time {{
            text-align: center;
            padding: 20px;
            color: var(--gray-600);
            font-size: 0.85rem;
        }}

        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2rem;
            }}

            .header h1 .icon {{
                font-size: 2.5rem;
            }}

            .stats-section {{
                margin-top: -20px;
            }}

            .matches-grid {{
                grid-template-columns: 1fr;
            }}

            .teams-container {{
                flex-direction: column;
                gap: 20px;
            }}

            .vs-container {{
                transform: rotate(90deg);
            }}

            .team-logo {{
                width: 60px;
                height: 60px;
            }}

            .channel-details {{
                flex-direction: column;
                gap: 10px;
                align-items: flex-start;
            }}
        }}
    </style>
</head>
<body>
    <!-- Header -->
    <header class="header">
        <div class="header-content">
            <h1>
                <span class="icon">⚽</span>
                مباريات اليوم
            </h1>
            <p>تابع جميع المباريات والقنوات الناقلة بالترددات</p>
            <div class="live-badge">
                <span class="live-dot"></span>
                <span>تحديث تلقائي كل 15 دقيقة</span>
            </div>
        </div>
    </header>

    <!-- Stats Section -->
    <section class="stats-section">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">🏟️</div>
                <div class="stat-value">{len(matches)}</div>
                <div class="stat-label">إجمالي المباريات</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📺</div>
                <div class="stat-value">{channels}</div>
                <div class="stat-label">القنوات الناقلة</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🌍</div>
                <div class="stat-value">{leagues_count}</div>
                <div class="stat-label">الدوريات</div>
            </div>
        </div>
    </section>

    <!-- Filters -->
    <section class="filters-section">
        <div class="filters-container">
            <button class="filter-btn active" data-filter="all">الكل</button>
            <button class="filter-btn" data-filter="football">⚽ كرة القدم</button>
            <button class="filter-btn" data-filter="basketball">🏀 كرة السلة</button>
            <button class="filter-btn" data-filter="tennis">🎾 التنس</button>
            <button class="filter-btn" data-filter="other">⚾ رياضات أخرى</button>
        </div>
    </section>

    <!-- Main Content -->
    <main class="main-content">
        <div class="section-title">
            <h2>📅 جدول المباريات</h2>
            <div class="line"></div>
        </div>

        <!-- Matches Grid -->
        <div class="matches-grid" id="matchesContainer">
            {matches_html}
        </div>
    </main>

    <!-- Update Time -->
    <div class="update-time">
        آخر تحديث: {update_time}
    </div>

    <!-- Footer -->
    <footer class="footer">
        <div class="footer-content">
            <div class="footer-logo">🏆 Mauritanie Sport</div>
            <div class="footer-links">
                <a href="https://www.sporteventz.com" target="_blank" class="footer-link">SportEventz</a>
                <a href="#" class="footer-link">سياسة الخصوصية</a>
                <a href="#" class="footer-link">اتصل بنا</a>
            </div>
            <p class="footer-copyright">
                جميع الحقوق محفوظة © 2024 Mauritanie Sport
            </p>
        </div>
    </footer>

    <script>
        // Filtros
        document.addEventListener('DOMContentLoaded', function() {{
            const buttons = document.querySelectorAll('.filter-btn');
            const cards = document.querySelectorAll('.match-card');

            buttons.forEach(btn => {{
                btn.addEventListener('click', () => {{
                    buttons.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');

                    const filter = btn.dataset.filter;
                    cards.forEach(card => {{
                        if (filter === 'all' || card.dataset.sport === filter) {{
                            card.style.display = 'block';
                        }} else {{
                            card.style.display = 'none';
                        }}
                    }});
                }});
            }});
        }});
    </script>
</body>
</html>
'''

    return html_content


def main():
    """الدالة الرئيسية"""
    print("=" * 60)
    print("🏆 Mauritanie Sport - توليد صفحة HTML")
    print("=" * 60)

    # تحميل البيانات
    matches = load_matches_data()
    print(f"📊 تم تحميل {len(matches)} مباراة")

    # قراءة الوقت
    json_file = OUTPUT_DIR / "matches.json"
    timestamp = None
    if json_file.exists():
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                timestamp = data.get('timestamp')
        except:
            pass

    # توليد HTML
    html_content = generate_html(matches, timestamp)

    # حفظ الملف
    output_file = OUTPUT_DIR / "index.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ تم توليد الصفحة: {output_file}")
    print(f"📁 عدد المباريات: {len(matches)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
