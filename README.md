<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/Gemini_AI-3.1_Flash_Lite-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Gemini AI" />
  <img src="https://img.shields.io/badge/Neon-00E599?style=for-the-badge&logo=neon&logoColor=black" alt="Neon" />
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
  <img src="https://img.shields.io/badge/Cloudinary-3448C5?style=for-the-badge&logo=cloudinary&logoColor=white" alt="Cloudinary" />
  <img src="https://img.shields.io/badge/Jinja2-B41717?style=for-the-badge&logo=jinja&logoColor=white" alt="Jinja2" />
  <img src="https://img.shields.io/badge/ReportLab-PDF-red?style=for-the-badge" alt="ReportLab" />
</p>

<h1 align="center">🎓 EduWise</h1>

<p align="center">
  <strong>AI-Powered Study Material Generator</strong><br/>
  <em>Turn any topic into presentations, study notes, quizzes, flashcards & more — in seconds.</em>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#%EF%B8%8F-tech-stack">Tech Stack</a> •
  <a href="#-getting-started">Getting Started</a> •
  <a href="#-project-structure">Project Structure</a> •
  <a href="#-api-keys--services">API Keys</a>
</p>

<p align="center">
  🚀 <strong>Live App:</strong> <a href="https://eduwise-i8v3.onrender.com/">https://eduwise-i8v3.onrender.com/</a>
</p>

---

## ✨ Features

EduWise is a full-stack web application that leverages **Google Gemini AI** to instantly generate high-quality educational content from any topic.

### 📊 AI-Generated Presentations (PPTX)
- Generate complete slide decks with a single prompt
- AI-driven dynamic theming — colors, fonts, and layout are automatically matched to your topic
- Auto-fetched images from Google Custom Search for every slide
- Full customization: slide count (3–10), intro/thank-you slides, dark/light themes, color overrides, serif/sans-serif fonts, and custom visual instructions

### 📄 AI-Generated Study Notes (PDF)
- Comprehensive, multi-page study notes rendered as beautifully formatted PDFs
- Markdown-to-PDF pipeline with support for headings, bullet points, code blocks, tables, and inline images
- Custom typography with four bundled font families (Roboto, Lato, Montserrat, Merriweather)
- Adjustable page count (2–15 pages) with dark mode support

### 🧠 Quizzes
- Auto-generate multiple-choice quizzes from any topic or uploaded document (PDF, DOCX, TXT)
- Instant scoring with a detailed results breakdown
- Session-based quiz state for seamless answer tracking

### 🃏 Flashcards
- Generate interactive Q&A flashcards from any topic or pasted text
- Flip-card interface for active recall practice

### 💡 Explain Like a Teacher
- Get warm, conversational explanations on any concept
- No jargon — just clear, human-like teaching with simple analogies

### 📝 Text Summarizer
- Paste any block of text and receive a concise, readable summary
- Great for condensing lecture notes, articles, or research papers

### 👤 User Accounts & Dashboard
- Full authentication system: signup, login, logout, password reset via email
- User profile with display name, bio, and avatar color
- Personal dashboard with a history of every resource you've generated
- Favorite and delete resources; search and filter by type
- Cloudinary integration for persistent file storage


---

## ⚙️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.10+, Flask 3.x |
| **AI Engine** | Google Gemini 3.1 Flash Lite (REST API) |
| **Database** | SQLite (local dev) / Neon PostgreSQL (production) |
| **ORM & Migrations** | SQLAlchemy + Flask-Migrate (Alembic) |
| **PDF Generation** | ReportLab |
| **PPTX Generation** | python-pptx |
| **Image Search** | Google Custom Search API |
| **File Storage** | Cloudinary |
| **Email** | Gmail SMTP (password reset) |
| **Security** | Flask-WTF CSRF, Flask-Limiter (rate limiting), Werkzeug password hashing |
| **Scheduler** | Flask-APScheduler |
| **Frontend** | Jinja2 templates, vanilla CSS & JS |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** installed
- A **Google Gemini API key** ([Get one here](https://aistudio.google.com/app/apikey))
- A **Google Custom Search API key** + **Search Engine ID** ([Set up here](https://programmablesearchengine.google.com/))
- A **Cloudinary account** (free tier works) for file uploads
- *(Optional)* A Gmail address with an **App Password** for the password-reset email flow

### 1. Clone the repository

```bash
git clone https://github.com/Abhinav-Muralidhar/EduWise.git
cd EduWise
```

### 2. Create & activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your credentials:

```env
GEMINI_API_KEY=your-gemini-api-key
CUSTOM_SEARCH_API_KEY=your-google-search-api-key
CUSTOM_SEARCH_CX_ID=your-search-engine-id
SECRET_KEY=generate-a-random-secret-key

CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-cloudinary-key
CLOUDINARY_API_SECRET=your-cloudinary-secret

APP_BASE_URL=http://127.0.0.1:5000

# Email config (Gmail SMTP with App Password)
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

> **Tip:** Generate a secure `SECRET_KEY` with:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

### 5. Run the application

```bash
python run.py
```

The app will start at **http://127.0.0.1:5000** 🎉

---

## 📁 Project Structure

```
EduWise/
├── run.py                    # Application entry point
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── .gitignore
│
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── config.py             # Configuration (env vars, fonts, scheduler)
│   ├── extensions.py         # Flask extensions (DB, CSRF, Limiter, etc.)
│   │
│   ├── models/
│   │   ├── user.py           # User model (auth, profile, password reset)
│   │   └── resource.py       # Resource model (generated content tracking)
│   │
│   ├── routes/
│   │   ├── auth.py           # Signup, Login, Logout, Password Reset, Profile
│   │   ├── dashboard.py      # Dashboard, Downloads, Favorites, Keep-alive
│   │   └── generation.py     # PPTX, PDF, Quiz, Flashcard, Explain, Summarize
│   │
│   ├── services/
│   │   ├── gemini.py         # Gemini AI integration (all prompt engineering)
│   │   ├── pptx_builder.py   # PowerPoint file construction
│   │   ├── pdf_builder.py    # PDF file construction with ReportLab
│   │   ├── email.py          # Gmail SMTP for password reset emails
│   │   └── image_search.py   # Google Custom Search image fetching
│   │
│   ├── utils/
│   │   ├── decorators.py     # @login_required decorator
│   │   ├── text.py           # Text extraction from uploaded files
│   │   ├── colors.py         # Hex ↔ RGB color conversion utilities
│   │   ├── resource_helper.py# Save generated resources to DB + Cloudinary
│   │   └── jobs.py           # Scheduled background tasks
│   │
│   ├── templates/            # Jinja2 HTML templates
│   │   ├── index.html        # Landing page
│   │   ├── dashboard.html    # Main dashboard
│   │   ├── login.html        # Login page
│   │   ├── signup.html       # Signup page
│   │   ├── profile.html      # User profile
│   │   ├── quiz.html         # Quiz interface
│   │   ├── result.html       # Quiz results
│   │   ├── flashcards.html   # Flashcard viewer
│   │   ├── explain.html      # Explanation viewer
│   │   ├── summary.html      # Summary viewer
│   │   └── ...               # Error pages, layouts, partials
│   │
│   └── static/
│       └── css/              # Stylesheets
│
├── fonts/                    # Bundled font families (Roboto, Lato, etc.)
├── migrations/               # Alembic database migrations
└── uploads/                  # Temporary file uploads (gitignored)
```

---

## 🔑 API Keys & Services

| Service | Required | Purpose | Free Tier |
|---------|----------|---------|-----------|
| **Google Gemini** | ✅ Yes | AI content generation (presentations, notes, quizzes, etc.) | ✅ Yes |
| **Google Custom Search** | ✅ Yes | Fetching relevant images for slides and PDFs | ✅ 100 queries/day |
| **Cloudinary** | ✅ Yes | Persistent cloud storage for generated files | ✅ 25 GB |
| **Gmail SMTP** | ⚠️ Optional | Sending password reset emails | ✅ Yes |

---

## 🔒 Security

EduWise implements several security best practices:

- **Password hashing** with Werkzeug (PBKDF2 + salt)
- **CSRF protection** on all forms via Flask-WTF
- **Rate limiting** on sensitive endpoints (login, signup, generation)
- **Secure session cookies** (HttpOnly, SameSite=Lax, 1-hour expiry)
- **Input validation** and file-type whitelisting for uploads
- **Constant-time password reset** responses (no email enumeration)
- **Token-based password reset** with 1-hour expiration


---
---
<p align="center">
  <strong>Built by Abhinav M</strong>
</p>
