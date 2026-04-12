# MyPersonal Bible App

A beautiful, user-friendly web application for reading, searching, and exploring the Holy Bible online. Built with Flask and designed to help you draw closer to God's Word every day with audio support for listening on the go.

**Live Demo**: [https://mypersonal-bible-app.onrender.com](https://mypersonal-bible-app.onrender.com)

## ✨ Features

- **📖 Verse of the Day** — A new inspiring verse every day (cached for consistency)
- **🔍 Powerful Search** — Find any verse, keyword, or phrase instantly across the Bible
- **📚 Browse by Book** — Select any of the 66 books of the Bible with chapter navigation
- **📝 Read Full Chapters** — View complete chapters with clean, readable formatting
- **🌍 Multiple Bible Versions** — Choose from KJV, WEB, OEB, Clementine Latin Vulgate, Portuguese Almeida, and Romanian Cornilescu
- **🎧 Audio Playback** — Listen to chapters or selected verses with high-quality text-to-speech powered by Voice RSS
- **⬇️ MP3 Downloads** — Download audio versions of chapters or verse selections for offline listening
- **⚡ Quick Verse Lookup** — Instantly view specific verses or verse ranges with audio support
- **📱 Responsive Design** — Works perfectly on mobile, tablet, and desktop devices
- **📧 Contact Form** — Send feedback or sponsorship inquiries directly through the app
- **🔒 Privacy Focused** — No ads, no tracking, completely free to use

## 🛠 Tech Stack

- **Backend**: Python 3 + Flask
- **Frontend**: Bootstrap 5, Font Awesome, Google Fonts (Crimson Text, Lora)
- **Bible Data**: [bible-api.com](https://bible-api.com) (Tim Morgan's free Bible API)
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

*Bible Search API (optional - for search functionality)*
API_KEY=your_bible_api_key_here

*Email Configuration (for contact form)*
MAIL_HOST=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password_here
MAIL_TO=recipient_email@gmail.com
MAIL_USE_TLS=true
MAIL_USE_SSL=false

*Voice RSS API Key*
VOICE_RSS_API_KEY=your_voice_rss_api_key_here

5. Run the app
```bash
python main.py
```

6. Open in your browser
```bash
http://127.0.0.1:5000/
```
## 🌐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/books` | GET | List all Bible books with metadata |
| `/api/versions` | GET | List available Bible versions |
| `/api/daily-verse` | GET | Get the verse of the day |
| `/api/search` | GET | Search Bible verses by keyword |
| `/api/chapter/<book>/<chapter>` | GET | Get full chapter data with optional filtering |
| `/api/verse/<book>/<chapter>/<verse>` | GET | Get a single verse |
| `/api/play-audio` | POST | Stream MP3 audio for text playback |
| `/api/download-audio` | POST | Download MP3 audio file |

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
  "total": 6,
  "versions": [
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
- Play Button: Streams audio directly in the browser with play/pause, skip forward/backward (10 seconds), and speed controls (0.5x - 1.5x)
- Download MP3: Generates and downloads an MP3 file for offline listening
- Audio is powered by Voice RSS API with the following specifications:
- Voice: US English
- Format: MP3, 44kHz, 16-bit stereo
- Character limit: 5000 characters per request

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
Bible text provided by bible-api.com
- Text-to-speech powered by Voice RSS
- Icons by Font Awesome
- Fonts: Crimson Text and Lora from Google Fonts
- UI framework: Bootstrap

## 📧 Contact
Have questions, feedback, or interested in sponsorship?
- Use the Contact Form on the live site
- Email: mypersonalbibleapp@gmail.com
- GitHub: @olatideenoch
