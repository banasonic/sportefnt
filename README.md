# 🏆 سكريبت استخراج مباريات SportEventz

## موريتاني سبورت - Mauritanie Sport

سكريبت Python متقدم لاستخراج بيانات المباريات من موقع [SportEventz.com](https://www.sporteventz.com) وتشغيله تلقائياً على GitHub Actions كل 15 دقيقة.

---

## ✨ المميزات

- ⚽ **استخراج المباريات**: جميع مباريات اليوم من مختلف الدوريات
- 👕 **شعارات الفرق**: استخراج شعارات جميع الفرق المشاركة
- 📺 **القنوات الناقلة**: أسماء القنوات ومعلومات البث
- 📡 **الترددات**: بيانات التردد والاستقطاب للقنوات الفضائية
- 🔒 **نوع التشفير**: تحديد إذا كانت القناة مفتوحة (FTA) أو مشفرة
- 🤖 **تحديث تلقائي**: تشغيل كل 15 دقيقة على GitHub Actions
- 📱 **تصميم متجاوب**: واجهة عربية جميلة تعمل على جميع الأجهزة

---

## 📁 هيكل المشروع

```
sport-eventz-scraper/
├── .github/
│   └── workflows/
│       └── scrape.yml      # ملف GitHub Actions
├── src/
│   ├── scraper.py           # السكريبت الأساسي
│   └── advanced_scraper.py  # السكريبت المتقدم
├── templates/
│   └── matches.html         # قالب عرض المباريات
├── output/
│   └── matches.json         # ملف النتائج
├── data/                    # بيانات إضافية
├── requirements.txt         # المتطلبات
└── README.md               # هذا الملف
```

---

## 🚀 التشغيل المحلي

### 1. المتطلبات

- Python 3.8+
- Playwright
- BeautifulSoup4

### 2. التثبيت

```bash
# استنساخ المشروع
git clone https://github.com/YOUR_USERNAME/sport-eventz-scraper.git
cd sport-eventz-scraper

# تثبيت المتطلبات
pip install -r requirements.txt

# تثبيت متصفح Playwright
playwright install chromium
```

### 3. التشغيل

```bash
# تشغيل السكريبت المتقدم
python src/advanced_scraper.py

# أو تشغيل السكريبت الأساسي
python src/scraper.py
```

---

## ⚙️ إعداد GitHub Actions

### 1. رفع المشروع إلى GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/sport-eventz-scraper.git
git push -u origin main
```

### 2. تفعيل GitHub Actions

1. اذهب إلى مستودع GitHub
2. اضغط على **Actions** Tab
3. سيبدأ التشغيل تلقائياً أو اختر "Scrape Sport Events" workflow
4. اضغط **Run workflow** للتفعيل اليدوي

### 3. تفعيل GitHub Pages (لعرض النتائج)

1. اذهب إلى **Settings** > **Pages**
2. اختر **Source**: Deploy from a branch
3. اختر **Branch**: gh-pages
4. اضغط **Save**

---

## ⏰ جدول التشغيل

السكريبت يعمل تلقائياً كل **15 دقيقة**. يمكنك تعديل الجدول في ملف `.github/workflows/scrape.yml`:

```yaml
schedule:
  - cron: '*/15 * * * *'  # كل 15 دقيقة
```

### خيارات الجدولة الأخرى:

```yaml
# كل ساعة
cron: '0 * * * *'

# كل 6 ساعات
cron: '0 */6 * * *'

# يومياً في منتصف الليل
cron: '0 0 * * *'

# كل يوم جمعة الساعة 8 مساءً
cron: '0 20 * * 5'
```

---

## 📊 بيانات التشغيل

البيانات المستخرجة تشمل:

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "date": "2024-01-15",
  "total_matches": 45,
  "matches": [
    {
      "id": "1234567890",
      "home_team": "النادي الأهلي",
      "away_team": "نادي الزمالك",
      "home_logo": "https://sporteventz.com/logos/al_ahly.png",
      "away_logo": "https://sporteventz.com/logos/zamalek.png",
      "time": "21:00",
      "league": "الدوري المصري",
      "channel": "beIN Sports",
      "frequency": "11013",
      "polarization": "H",
      "encryption": "Encrypted",
      "date": "2024-01-15",
      "sport_type": "Football"
    }
  ]
}
```

---

## 🔧 التخصيص

### إضافة رياضات جديدة

عدّل ملف `advanced_scraper.py`:

```python
async def scrape_sport_pages(self, sport: str = "football") -> List[Match]:
    urls = {
        "football": f"{self.base_url}/en/sport-eventz.html",
        "basketball": f"{self.base_url}/en/other-sport/basketball.html",
        "tennis": f"{self.base_url}/en/other-sport/tennis.html",
    }
```

### إضافة قنوات جديدة

عدّل قائمة `known_channels`:

```python
self.known_channels = [
    'beIN Sports',
    'Your New Channel',
    # ...
]
```

---

## 🛡️ معالجة الأخطاء

السكريبت يتضمن:

- ✨ إعادة المحاولة التلقائية (3 محاولات)
- ⏱️ انتظار عشوائي بين الطلبات
- 🕵️ التبديل بين User Agents
- 📝 تسجيل مفصل للأخطاء
- 🔄 إزالة التكرارات تلقائياً

---

## ⚠️ ملاحظات مهمة

1. **احترام حقوق الموقع**: استخدم السكريبت للأغراض الشخصية فقط
2. **الحد الأقصى للطلبات**: لا تشغل السكريبت بشكل متكرر جداً
3. **تحديث البنية**: قد يتغير موقع SportEventz، وقد تحتاج لتحديث المحددات (Selectors)

---

## 📝 المساهمة

نرحب بمساهماتكم! يرجى:

1. Fork المشروع
2. إنشاء فرع جديد (`git checkout -b feature/amazing`)
3. Commit التغييرات (`git commit -m 'Add amazing feature'`)
4. Push للفرع (`git push origin feature/amazing`)
5. فتح Pull Request

---

## 📜 الترخيص

هذا المشروع مرخص بموجب [MIT License](LICENSE).

---

## 👨‍💻 المطور

**Mauritanie Sport Team**

- 🌐 الموقع: [mauritaniesport.com](https://mauritaniesport.com)
- 📧 البريد: contact@mauritaniesport.com

---

<div align="center">
  <p>⭐ إذا أعجبك المشروع، لا تنسَ إعطائه نجمة! ⭐</p>
  <p>صُنع بـ ❤️ لموريتانيا</p>
</div>
