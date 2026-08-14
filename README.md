# MyPersonal Bible App

A beautiful, user-friendly web application for reading, searching, and exploring the Holy Bible online. Built with Flask and designed to help you draw closer to God's Word every day with audio support for listening on the go.

**Live Demo**: [https://mypersonal-bible-app.onrender.com](https://mypersonal-bible-app.onrender.com)

## ✨ Features

### Reading & Study
- **📖 Verse of the Day** — A new inspiring verse every day (cached for consistency)
- **🎲 Random Verse** — Tap "Surprise Me" for a random verse from anywhere in Scripture
- **🔍 Powerful Search** — Find any verse, keyword, or phrase instantly across the Bible
- **📚 Browse by Book** — Select any of the 66 books of the Bible with chapter navigation
- **📝 Read Full Chapters** — View complete chapters with clean, readable formatting
- **🌍 1000+ Bible Versions** — Premium support for NKJV, NIV, NLT + access to ESV, NASB, CSB, and 1000+ more translations
- **🎯 Smart Multi-API System** — Intelligently routes requests between API.Bible, Bible.com, and free fallback API for reliability
- **🌐 Multiple Languages** — Portuguese, Chinese, Romanian, Czech, Tamil, Malayalam, Latin, Cherokee, and more
- **🆚 Compare Versions** — Read any chapter in two translations side by side
- **⚡ Quick Verse Lookup** — Instantly view specific verses or verse ranges with audio support
- **⚡ Quick Reference Jump** — Type any reference (e.g. "John 3:16") and jump straight there
- **🔎 In-Chapter Filter** — Search within the current chapter to find a verse instantly
- **🖼️ Share Verse Cards** — Generate beautiful verse images and share on WhatsApp, X, Facebook & Telegram

### Audio
- **🎧 Audio Playback** — Listen to chapters or selected verses with high-quality text-to-speech powered by Voice RSS
- **⬇️ MP3 Downloads** — Download audio versions of chapters or verse selections for offline listening

### Personalisation & Growth
- **📚 Guided Reading Plans** — Bible in 90 Days, New Testament in 30 Days, Psalms in 30, Proverbs in 31, the Gospels in 14 and more — with day-by-day progress tracking
- **📅 Daily Devotional** — A new devotional every day: verse, reflection, prayer and action step (31-day cycle)
- **💡 Bible Topics** — 20 curated verse collections (love, faith, hope, healing, wisdom...) for every season of life
- **❓ Bible Quiz** — Test your Bible knowledge with trivia, instant answers and score tracking
- **📝 Verse Notes** — Write personal study notes on any verse (synced to your account)
- **🎨 Multi-colour Highlights** — Highlight verses in 5 colours
- **🔖 Bookmarks** — Save favourite verses and jump back to them anytime
- **🙏 Prayer Journal** — Write down prayer requests and mark them answered
- **🏅 Achievements** — Earn badges for streaks, plans, quizzes and study habits
- **🔥 Reading Streaks** — Track your current and longest reading streaks
- **📊 Profile Analytics** — Beautiful charts of your yearly reading activity
- **📤 Export Your Data** — Download bookmarks, highlights, notes & prayers as JSON, Markdown or text

### Platform
- **📱 Responsive Design** — Works perfectly on mobile, tablet, and desktop devices
- **📴 Offline Reading** — Previously read chapters stay available offline (PWA service worker)
- **☁️ Cross-device Sync** — Sign in with Google to sync bookmarks, highlights, notes, plans and prayers
- **📧 Contact Form** — Send feedback or sponsorship inquiries directly through the app
- **🔒 Privacy Focused** — No ads, no tracking, completely free to use

## 🛠 Tech Stack

- **Backend**: Python 3 + Flask
- **Frontend**: Bootstrap 5, Font Awesome, Google Fonts (Crimson Text, Lora)
- **Bible APIs** (Multi-tier):
  - [API.Bible](https://api.bible/) - Premium versions (NKJV, NIV, NLT) + 1000+ translations
  - [Bible.com/YouVersion](https://www.youversion.com/developer) - Extended versions (ESV, NASB, CSB) + thousands more
  - [bible-api.com](https://bible-api.com) - Free public domain fallback (KJV, WEB, ASV, etc.)
- **Text-to-Speech**: [Voice RSS API](https://www.voicerss.org/) for high-quality audio generation
- **Email**: SMTP integration for contact form submissions
- **Deployment**: Render.com with Gunicorn

## 🚀 Local Development

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git

### Setup Instructions

1. **Clone the repository**
```bash
git clone https://github.com/olatideenoch/MyPersonal-bible-app.git
cd MyPersonal-bible-app
```

2. **Create a virtual environment**
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
Create a .env file in the root directory with the following variables:

**Bible APIs (Optional but recommended - unlock 1000+ versions)**
```bash
# API.Bible - Get free key: https://api.bible/sign-up/starter
API_BIBLE_KEY=pk_live_your_api_bible_key_here

# Bible.com - Get free key: https://www.youversion.com/developer
BIBLE_COM_KEY=your_youversion_api_token_here

# Note: The app works WITHOUT these keys (uses free fallback API)
# But WITH keys, users get access to premium versions (NKJV, NIV, NLT, ESV, NASB, CSB)
```

**Bible Search API (optional - for search functionality)**
```bash
API_KEY=your_bible_api_key_here
```

**Email Configuration (for contact form)**
```bash
MAIL_HOST=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password_here
MAIL_TO=recipient_email@gmail.com
MAIL_USE_TLS=true
MAIL_USE_SSL=false
```

**Voice RSS API Key (for audio features)**
```bash
VOICE_RSS_API_KEY=your_voice_rss_api_key_here
```

**Google OAuth (for user authentication)**
```bash
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
APP_SECRET_KEY=your_secret_key_for_sessions
```

5. **Get API Keys (Optional)** - *Unlock premium Bible versions*

To access premium versions (NKJV, NIV, NLT, ESV, NASB, CSB), get free API keys:

**API.Bible** (Free tier - 5,000 calls/month):
- Visit: https://api.bible/sign-up/starter
- Sign up and choose 3 versions
- Copy your API key to `API_BIBLE_KEY` in `.env`

**Bible.com** (Free developer tier):
- Visit: https://www.youversion.com/developer
- Create an application
- Copy your token to `BIBLE_COM_KEY` in `.env`

**Note**: The app works fine without these keys (uses free fallback API with 16 versions).

6. Run the app
```bash
python main.py
```

7. Open in your browser
```bash
http://127.0.0.1:5000/
```

## 🆕 New Features (v2)

All new features work **without any additional API keys**:
- **Reading Plans** (`/plans`) — plan content is generated locally from the built-in book/chapter index
- **Bible Topics** (`/topics`) — 20 curated KJV verse collections stored in `main.py`
- **Bible Quiz** (`/quiz`) — 57 curated trivia questions, scores saved to your account
- **Compare Versions** (`/compare`) — uses the same smart multi-API fetcher as the reader
- **Daily Devotional** (`/devotional`) — 31 original devotionals on a monthly cycle
- **Prayer Journal** (`/prayer-journal`) — local-first, syncs when signed in
- **Verse Notes, coloured highlights, share cards, quick jump, in-chapter filter** — built into the reader page
- **Achievements & data export** — on your Profile page
- **Offline mode** — `static/sw.js` service worker caches previously-read pages and chapters

No changes to `requirements.txt` or environment variables are needed. Deploy as usual.

## 📖 Available Bible Versions

### Premium Versions (API.Bible & Bible.com)
- ⭐ **NKJV** - New King James Version
- ⭐ **NIV** - New International Version
- ⭐ **NLT** - New Living Translation
- **ESV** - English Standard Version
- **NASB** - New American Standard Bible
- **CSB** - Christian Standard Bible

### Public Domain Versions (Always Available)
- **KJV** - King James Version
- **WEB** - World English Bible
- **ASV** - American Standard Version
- **BBE** - Bible in Basic English
- **Darby** - Darby Bible
- **DRA** - Douay-Rheims
- **YLT** - Young's Literal Translation
- **OEB** - Open English Bible (US & UK)
- **And 16+ more...**

### Regional Versions
- Portuguese (Almeida)
- Romanian (Cornilescu)
- Chinese (Union Version)
- Czech (Kralická)
- Tamil, Malayalam, Latin, and more
## 🌐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/books` | GET | List all Bible books with metadata |
| `/api/versions` | GET | List available Bible versions (25+ with APIs, 16+ without) |
| `/api/daily-verse` | GET | Get the verse of the day |
| `/api/search` | GET | Search Bible verses by keyword |
| `/api/chapter/<book>/<chapter>` | GET | Get full chapter data with optional filtering |
| `/api/verse/<book>/<chapter>/<verse>` | GET | Get a single verse |
| `/api/play-audio` | POST | Stream MP3 audio for text playback |
| `/api/download-audio` | POST | Download MP3 audio file |
| `/login/google` | GET | Google OAuth authentication |
| `/api/sync` | POST/GET | Sync user bookmarks, highlights, and progress |
| `/api/user` | GET | Get current user information |

## Query Parameters

**`/api/books`**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `testament` | string | `all` | Filter by testament: `old`, `new`, or `all` |

**`/api/search`**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | *required* | Search query (keyword or phrase) |
| `version` | string | `en-kjv` | Bible version ID |
| `limit` | integer | `20` | Maximum number of results |

**`/api/chapter/<book>/<chapter>`**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `version` | string | `en-kjv` | Bible version ID |
| `verse_start` | integer | *none* | Starting verse number |
| `verse_end` | integer | *none* | Ending verse number |
| `format` | string | `full` | Response format: `full` or `simple` |

**`/api/verse/<book>/<chapter>/<verse>`**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `version` | string | `en-kjv` | Bible version ID |

**`/api/play-audio`** (POST)
| Body Field | Type | Required | Description |
|------------|------|----------|-------------|
| `text` | string | Yes | Text to convert to speech |

**`/api/download-audio`** (POST)
| Body Field | Type | Required | Description |
|------------|------|----------|-------------|
| `text` | string | Yes | Text to convert to speech |
| `filename` | string | No | Custom filename for download |

## Example Requests

**Get all New Testament books:**
```bash
GET /api/books?testament=new
```

**Search for "love":**
GET /api/search?q=love&limit=10

**Get full chapter:**
GET /api/chapter/John/3?version=en-kjv

**Get verse range (Psalm 23:1-4):**
GET /api/chapter/Psalm/23?verse_start=1&verse_end=4

**Get single verse:**
GET /api/verse/John/3/16?version=en-web

**Get daily verse:**
GET /api/daily-verse

**Play audio:**
POST /api/play-audio
Content-Type: application/json

{
  "text": "For God so loved the world that he gave his one and only Son..."
}

**Download audio:**
POST /api/download-audio
Content-Type: application/json

{
  "text": "For God so loved the world...",
  "filename": "john-3-16.mp3"
}

## Example Responses

**`/api/books`**

{
  "total": 66,
  "testament": "all",
  "books": [
    {
      "name": "Genesis",
      "slug": "genesis",
      "chapters": 50,
      "testament": "Old"
    }
  ]
}

**`/api/daily-verse`**

{
  "date": "2024-01-15",
  "verse": {
    "text": "For God so loved the world...",
    "reference": "John 3:16"
  }
}

**`/api/chapter/John/3`**

{
  "book": "John",
  "book_full": "John",
  "chapter": 3,
  "total_chapters": 21,
  "version": "en-kjv",
  "version_name": "King James Version (KJV)",
  "verse_count": 36,
  "filtered_count": 36,
  "chapter_text": "There was a man of the Pharisees...",
  "verses": [
    {
      "verse": "1",
      "reference": "John 3:1",
      "text": "There was a man of the Pharisees, named Nicodemus..."
    }
  ],
  "has_filter": false,
  "verse_range": null
}

**`/api/version`s**

{
  "total": 25,
  "versions": [
    {
      "id": "en-nkjv",
      "version": "New King James Version (NKJV) ⭐"
    },
    {
      "id": "en-niv",
      "version": "New International Version (NIV) ⭐"
    },
    {
      "id": "en-nlt",
      "version": "New Living Translation (NLT) ⭐"
    },
    {
      "id": "en-kjv",
      "version": "King James Version (KJV)"
    }
  ]
}

**`/api/daily-verse`**

{
  "date": "2024-01-15",
  "verse": {
    "text": "For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life.",
    "reference": "John 3:16"
  }
}

**`/api/search?q=love`**

{
  "query": "love",
  "version": "en-kjv",
  "total": 10,
  "results": [
    {
      "text": "For God so loved the world...",
      "reference": "John 3:16"
    }
  ]
}

**`/api/verse/John/3/16`**

{
  "book": "John",
  "chapter": 3,
  "verse": 16,
  "reference": "John 3:16",
  "text": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.",
  "version": "en-kjv"
}

## 🎵 Audio Features
The app includes two audio options for each chapter or verse selection:
- **Play Button**: Streams audio directly in the browser with play/pause, skip forward/backward (10 seconds), and speed controls (0.5x - 1.5x)
- **Download MP3**: Generates and downloads an MP3 file for offline listening
- Audio is powered by Voice RSS API with the following specifications:
  - Voice: US English
  - Format: MP3, 44kHz, 16-bit stereo
  - Character limit: 5000 characters per request

## 🔄 Smart API Routing System

The app uses intelligent routing to provide the best user experience:

1. **Try Primary API** - Fetches from API.Bible (for NKJV, NIV, NLT) or Bible.com (for ESV, NASB, CSB)
2. **Fallback to Secondary API** - If primary fails, tries the backup API
3. **Final Fallback** - Uses free bible-api.com (always available)

**Result**: Users always get their verses, even if one API is down!

### API Rate Limits
- **API.Bible**: 5,000 calls/month (free tier)
- **Bible.com**: Based on usage tier
- **bible-api.com**: 15 requests per 30 seconds

## 🤝 Contributing
Contributions are welcome! Feel free to:
- Fork the repository
- Create a feature branch (git checkout -b feature/amazing-feature)
- Commit your changes (git commit -m 'Add amazing feature')
- Push to the branch (git push origin feature/amazing-feature)
- Open a Pull Request

## 📄 License
This project is open source and available under the MIT License.

## 🙏 Acknowledgments
Bible text provided by:
- [API.Bible](https://api.bible/) - Premium Bible versions
- [Bible.com/YouVersion](https://www.youversion.com/) - Extensive translation library
- [bible-api.com](https://bible-api.com/) - Free public domain versions
- Text-to-speech powered by [Voice RSS API](https://www.voicerss.org/)
- Icons by [Font Awesome](https://fontawesome.com/)
- Fonts: Crimson Text and Lora from [Google Fonts](https://fonts.google.com/)
- UI framework: [Bootstrap 5](https://getbootstrap.com/)

## � Documentation

For detailed setup and configuration of Bible APIs, see:
- **START_HERE.md** - Quick start guide
- **BIBLE_APIS_SETUP.md** - Complete API setup instructions
- **QUICK_REFERENCE.md** - API versions and configuration reference
- **IMPLEMENTATION_SUMMARY.md** - Technical implementation details

## �📧 Contact
Have questions, feedback, or interested in sponsorship?
- Use the Contact Form on the live site
- Email: mypersonalbibleapp@gmail.com
- GitHub: @olatideenoch
