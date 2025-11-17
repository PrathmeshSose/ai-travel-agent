import streamlit as st
import requests
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import json
import os

@st.cache_data(ttl=86400)
def get_user_location():
    try:
        response = requests.get('https://ipapi.co/json/', timeout=5)
        data = response.json()
        return f"{data.get('city', 'Unknown')}, {data.get('country_name', 'Unknown')}"
    except:
        return None

# Page config
st.set_page_config(
    page_title="AI Travel Agent",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Enhanced CSS
st.markdown("""
<style>
    .main { padding-top: 2rem; }
    .stApp { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .main-container {
        background: white;
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        margin: 1rem;
    }
    .header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #667eea;
        margin: 1rem 0;
        transition: transform 0.2s;
    }
    .feature-card:hover { transform: translateY(-2px); }
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: bold;
        width: 100%;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    .success-box {
        background: linear-gradient(135deg, #d4edda, #c3e6cb);
        border: none;
        color: #155724;
        padding: 1rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
    .stSelectbox > div > div { border-radius: 10px; }
    .stTextInput > div > div { border-radius: 10px; }
    .stNumberInput > div > div { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

def generate_ics_content(plan_text: str, destination: str, start_date=None) -> bytes:
    cal = Calendar()
    cal.add('prodid', '-//AI Travel Agent//github.com//')
    cal.add('version', '2.0')
    
    if start_date is None:
        start_date = datetime.today().date()
    elif hasattr(start_date, 'date'):
        start_date = start_date.date()
    
    lines = plan_text.split('\n')
    current_day = 0
    
    for line in lines:
        if line.strip().startswith('**Day '):
            current_day += 1
            day_date = start_date + timedelta(days=current_day - 1)
            
            event = Event()
            event.add('summary', f"{destination} - Day {current_day}")
            event.add('description', line.strip())
            event.add('dtstart', day_date)
            event.add('dtend', day_date)
            event.add('dtstamp', datetime.now())
            cal.add_component(event)
    
    return cal.to_ical()

@st.cache_data(ttl=3600)
def search_destination(destination: str, serp_key: str) -> tuple:
    if not serp_key:
        return f"Basic travel information for {destination}. Add SerpAPI key for detailed research.", []
    
    try:
        url = "https://serpapi.com/search"
        params = {
            "engine": "google",
            "q": f"{destination} travel guide attractions restaurants",
            "api_key": serp_key,
            "num": 6
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        results = []
        sources = []
        if "organic_results" in data:
            for result in data["organic_results"]:
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                link = result.get('link', '')
                results.append(f"• {title}: {snippet}")
                sources.append(f"- [{title}]({link})")
        
        return "\n".join(results) if results else "No search results found.", sources
    except:
        return "Search unavailable.", []

def generate_itinerary_with_groq(destination: str, days: int, search_results: str, 
                                budget: str, travel_style: str, interests: list, groq_key: str, sources: list, departure: str = None) -> str:
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json"
        }
        
        travel_info = f"""Create a detailed {days}-day travel itinerary for {destination}.

Trip Details:
- From: {departure or 'Not specified'}
- Destination: {destination}
- Duration: {days} days
- Budget: {budget}
- Travel Style: {travel_style}
- Interests: {', '.join(interests)}

Research Information:
{search_results}

Create a comprehensive itinerary with:
1. Transportation from departure location to destination (flights, trains, etc.)
2. Day-by-day breakdown using **Day X:** format
3. Morning, afternoon, evening activities
4. Specific attractions, restaurants, accommodations
5. Budget-appropriate suggestions
6. Local transportation options
7. Return journey information

Format in markdown with clear sections."""
        
        prompt = travel_info

        data = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            itinerary = result["choices"][0]["message"]["content"]
            
            # Add sources section if available
            if sources:
                itinerary += "\n\n---\n\n## 📚 Sources\n\n" + "\n".join(sources)
            
            return itinerary
        else:
            return f"Error: {result.get('error', {}).get('message', 'Unknown error')}"
            
    except Exception as e:
        return f"Error generating itinerary: {str(e)}"

# Initialize session state with API keys from environment or secrets
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = None
if 'groq_api_key' not in st.session_state:
    st.session_state.groq_api_key = os.getenv('GROQ_API_KEY', st.secrets.get('GROQ_API_KEY', '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'))
if 'serp_api_key' not in st.session_state:
    st.session_state.serp_api_key = os.getenv('SERP_API_KEY', st.secrets.get('SERP_API_KEY', '0e9e1ee215e49a5a3373994115defcffae8c206fab133715a934fee8aaa39e3c'))

# Header
st.markdown("""
<div class="main-container">
    <div class="header">
        <h1>✈️ AI Travel Agent</h1>
        <p>Create personalized travel itineraries with free AI</p>
    </div>
""", unsafe_allow_html=True)

# Main layout
col1, col2 = st.columns([2, 1])

with col1:
    # Use stored API keys
    groq_api_key = st.session_state.groq_api_key
    serp_api_key = st.session_state.serp_api_key
    
    st.markdown("### 🎯 Trip Planning")
    
    # Auto-detect user location
    user_location = get_user_location()
    if user_location:
        st.info(f"📍 Detected location: {user_location}")
    
    col_from, col_to = st.columns(2)
    with col_from:
        departure = st.text_input("🏠 From", value=user_location or "", placeholder="Your location")
    with col_to:
        destination = st.text_input("🌍 To", placeholder="e.g., Paris, France")
    
    col_days, col_budget = st.columns(2)
    with col_days:
        num_days = st.number_input("📅 Days", min_value=1, max_value=14, value=3)
    with col_budget:
        budget = st.selectbox("💰 Budget", ["Budget", "Mid-range", "Luxury"])
    
    col_style, col_interests = st.columns(2)
    with col_style:
        travel_style = st.selectbox("🎨 Style", 
                                   ["Explorer", "Relaxed", "Adventure", "Cultural", "Foodie"])
    with col_interests:
        interests = st.multiselect("🎯 Interests", 
                                  ["culture", "food", "adventure", "nature", "nightlife", "shopping"],
                                  default=["culture", "food"])

with col2:
    st.markdown("""
    <div class="feature-card">
        <h4>🚀 Why This Planner?</h4>
        <ul>
            <li>✅ <strong>100% Free AI</strong></li>
            <li>✅ <strong>Ultra-fast</strong> responses</li>
            <li>✅ <strong>Web research</strong> integration</li>
            <li>✅ <strong>Calendar export</strong></li>
            <li>✅ <strong>No OpenAI costs</strong></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if not groq_api_key:
        st.warning("⚠️ No Groq API key configured. Use settings below to add one.")
    else:
        st.success("✅ API keys configured")

# Generate button
if st.button("🎯 Generate My Perfect Itinerary", type="primary"):
    if not destination:
        st.error("Please enter a destination")
    elif not groq_api_key:
        st.error("Please configure your Groq API key in settings below")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Search
            status_text.text("🔍 Researching your destination...")
            progress_bar.progress(33)
            
            search_results, sources = search_destination(destination, serp_api_key)
            
            # Step 2: Generate with Groq
            status_text.text("🤖 Creating your personalized itinerary...")
            progress_bar.progress(66)
            
            itinerary = generate_itinerary_with_groq(
                destination, num_days, search_results, 
                budget, travel_style, interests, groq_api_key, sources, departure
            )
            
            # Step 3: Complete
            status_text.text("✅ Your itinerary is ready!")
            progress_bar.progress(100)
            
            st.session_state.itinerary = itinerary
            st.session_state.destination = destination
            st.session_state.start_date = datetime.today()
            
            progress_bar.empty()
            status_text.empty()
            
            st.markdown("""
            <div class="success-box">
                🎉 <strong>Success!</strong> Your AI-powered itinerary is ready!
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Display results
if st.session_state.itinerary:
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ics_content = generate_ics_content(
            st.session_state.itinerary,
            st.session_state.get('destination', 'Trip'),
            st.session_state.get('start_date', datetime.today())
        )
        
        st.download_button(
            label="📅 Download Calendar",
            data=ics_content,
            file_name=f"{st.session_state.get('destination', 'trip').replace(' ', '_')}_itinerary.ics",
            mime="text/calendar"
        )
    
    with col2:
        st.download_button(
            label="📄 Download Text",
            data=st.session_state.itinerary,
            file_name=f"{st.session_state.get('destination', 'trip').replace(' ', '_')}_itinerary.txt",
            mime="text/plain"
        )
    
    with col3:
        if st.button("🔄 Create New Trip"):
            st.session_state.itinerary = None
            st.rerun()
    
    st.markdown("## 📋 Your Personalized Itinerary")
    st.markdown(st.session_state.itinerary)

st.markdown("</div>", unsafe_allow_html=True)

# Settings Panel at Bottom
st.markdown("---")
with st.expander("⚙️ API Settings", expanded=False):
    st.markdown("### 🔑 Configure API Keys")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_groq_key = st.text_input(
            "Groq API Key", 
            value=groq_api_key, 
            type="password",
            help="Get free key at console.groq.com",
            key="groq_input"
        )
        
        if st.button("💾 Save Groq Key"):
            st.session_state.groq_api_key = new_groq_key
            st.success("✅ Groq API key saved!")
            st.rerun()
    
    with col2:
        new_serp_key = st.text_input(
            "SerpAPI Key (Optional)", 
            value=serp_api_key, 
            type="password",
            help="For web search - serpapi.com",
            key="serp_input"
        )
        
        if st.button("💾 Save SerpAPI Key"):
            st.session_state.serp_api_key = new_serp_key
            st.success("✅ SerpAPI key saved!")
            st.rerun()
    
    if groq_api_key or serp_api_key:
        st.markdown("### 🗑️ Clear Keys")
        if st.button("🗑️ Clear All API Keys", type="secondary"):
            st.session_state.groq_api_key = ""
            st.session_state.serp_api_key = ""
            st.success("🗑️ All API keys cleared!")
            st.rerun()

# Footer
st.markdown("""
<div style="text-align: center; color: white; padding: 2rem; margin-top: 2rem;">
    <p>Powered by <strong>Groq AI</strong> 🚀 | Free & Fast Travel Planning</p>
</div>
""", unsafe_allow_html=True)