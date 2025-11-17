# ✈️ AI Travel Agent

Free AI-powered travel planning using Groq's fast LLM API with intelligent web research.

## 🚀 Features

- **100% Free AI** - Uses Groq's Llama 3.1 model
- **Ultra-fast** - Sub-second response times
- **Web Research** - Optional SerpAPI integration
- **Calendar Export** - Download as .ics files
- **Mobile-Friendly** - Responsive design

## 🎯 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get Free API Keys**
   - Groq API: https://console.groq.com/ (Required)
   - SerpAPI: https://serpapi.com/ (Optional for web search)

3. **Run Application**
   ```bash
   streamlit run app.py
   ```

## 🐳 Docker

```bash
docker build -t travel-planner .
docker run -p 8501:8501 travel-planner
```

## 📱 Usage

1. Enter Groq API key
2. Add destination and preferences
3. Generate AI-powered itinerary
4. Download calendar or text file

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **AI**: Groq (Llama 3.1)
- **Search**: SerpAPI
- **Calendar**: iCalendar

---

**Made with ❤️ using Groq AI**