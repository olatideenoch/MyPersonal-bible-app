# MyPersonal Bible App

A beautiful, user-friendly web application for reading, searching, and exploring the Holy Bible online. Built with Flask and designed to help you draw closer to God's Word every day.

**Live Demo**: [https://mypersonal-bible-app.onrender.com](https://mypersonal-bible-app.onrender.com) 

## Features

- **Verse of the Day** — A new inspiring verse every time you visit
- **Powerful Search** — Find any verse, keyword, or phrase instantly
- **Browse by Book** — Select any of the 66 books of the Bible
- **Read Full Chapters** — View complete chapters with clean formatting
- **Multiple Bible Versions** — Choose from popular translations (KJV, WEB, ASV, and more)
- **Responsive Design** — Works perfectly on mobile, tablet, and desktop
- **No ads, no tracking** — Completely free and privacy-focused

## Tech Stack

- **Backend**: Python + Flask
- **Frontend**: Bootstrap 5, Font Awesome, Google Fonts
- **Bible Data**: Powered by the free [wldeh/bible-api](https://github.com/wldeh/bible-api) (public domain & modern translations)
- **Deployment**: Render.com

## Local Development

1. Clone the repository
```bash
git clone https://github.com/olatideenoch/MyPersonal-bible-app.git
cd MyPersonal-bible-app
```

2. Create a virtual environment 
```bash
python -m venv venv
source venv/Scripts/activate  
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Run the app
```bash
python main.py
```

5. Open in your browser
```bash
http://127.0.0.1:5000/