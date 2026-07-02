"""
EduAI Guardian v8 — Expressive AI Teacher
==========================================
Keep Dashboard + Risk Detector UNCHANGED.
New: animated face expressions, Sarvam TTS/STT two-way voice,
Gemini AI, 8 interactive suggestion cards (6 categories), YouTube API.
"""
import streamlit as st
import streamlit.components.v1 as components
import json, requests, re, random
from pathlib import Path

st.set_page_config(page_title="EduAI Guardian v8", page_icon="\U0001f393",
                   layout="wide", initial_sidebar_state="expanded")

CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');
html,body,[class*="css"]{font-family:"DM Sans",sans-serif;background:#07080f;}
.block-container{padding:1.2rem 1.4rem 2rem!important;}
.stButton>button{border-radius:10px;font-size:12px;transition:all .2s;}
.stTextInput>div>div>input{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);border-radius:12px;color:#e8e6f0;padding:10px 14px;}
[data-testid="stSidebar"]{background:rgba(7,8,15,0.95);border-right:1px solid rgba(255,255,255,0.06);}
.stTab [data-baseweb="tab-list"]{background:rgba(0,0,0,0.3);border-radius:12px;padding:4px;}
.stTab [aria-selected="true"]{background:linear-gradient(135deg,rgba(124,92,252,0.3),rgba(252,92,125,0.2));border-radius:9px;}
.msg-t{background:rgba(17,17,30,0.9);border:1px solid rgba(124,92,252,0.12);border-radius:18px 18px 18px 4px;padding:14px 18px;margin-bottom:10px;max-width:82%;}
.msg-s{background:linear-gradient(135deg,rgba(124,92,252,0.2),rgba(252,92,125,0.12));border:1px solid rgba(124,92,252,0.25);border-radius:18px 18px 4px 18px;padding:12px 16px;margin-bottom:10px;max-width:70%;margin-left:auto;}
@keyframes wave-bar{0%,100%{height:4px;opacity:.4}50%{height:18px;opacity:1}}
@keyframes float-y{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}
</style>"""
st.markdown(CSS, unsafe_allow_html=True)

defs = dict(messages=[], subject="Mathematics", lessons=0, xp=0, streak=7,
            emotion="enthusiastic", is_speaking=False,
            yt_suggestions=[], hf_suggestions=[], hf_course=None, risk_result=None,
            api_keys=dict(gemini="", groq="", sarvam="", youtube=""),
            model_priority="gemini", sugg_cat="all", auto_speak=True,
            voice_engine="Sarvam AI")
for k, v in defs.items():
    if k not in st.session_state:
        st.session_state[k] = v

EMOTIONS = {
    "enthusiastic": {"emoji":"\U0001f60a","color":"#43e97b","mood":"Enthusiastic","label":"Ready to teach!","curve":8,"brow":0},
    "curious":      {"emoji":"\U0001f914","color":"#7c5cfc","mood":"Curious",      "label":"Thinking...","curve":2,"brow":-4},
    "excited":      {"emoji":"\U0001f389","color":"#fc5c7d","mood":"Excited",      "label":"Amazing!","curve":12,"brow":3},
    "patient":      {"emoji":"\U0001f9d8","color":"#22d3ee","mood":"Patient",      "label":"Take your time...","curve":5,"brow":1},
    "proud":        {"emoji":"\U0001f979","color":"#f7971e","mood":"Proud",        "label":"You did it!","curve":9,"brow":2},
    "thinking":     {"emoji":"\U0001f4ad","color":"#818cf8","mood":"Thinking",     "label":"Processing...","curve":0,"brow":-2},
    "speaking":     {"emoji":"\U0001f5e3","color":"#43e97b","mood":"Speaking",     "label":"Teaching now...","curve":6,"brow":0},
}

SUBJECTS = [
    ("\U0001f4d0","Mathematics"),("\u269b\ufe0f","Physics"),("\U0001f9ea","Chemistry"),
    ("\U0001f4bb","Computer Science"),("\U0001f9ec","Biology"),("\U0001f3db\ufe0f","History"),
    ("\U0001f4da","Literature"),("\U0001f30d","Geography"),("\U0001f3b5","Music Theory"),
]

# ─── AVATAR SVG ──────────────────────────────────────────────────────────────
def avatar_svg(emotion: str, speaking: bool = False) -> str:
    e = EMOTIONS.get(emotion, EMOTIONS["enthusiastic"])
    c = e["color"]; curve = e["curve"]; brow = e["brow"]
    dur = "2s" if speaking else "4s"
    # Talking mouth animation
    if speaking:
        mouth_anim = (
            "<animate attributeName='d'"
            " values='M 36 65 Q 50 " + str(60+curve) + " 64 65;"
            "M 36 62 Q 50 " + str(74+curve) + " 64 62;"
            "M 36 65 Q 50 " + str(60+curve) + " 64 65'"
            " dur='0.45s' repeatCount='indefinite'/>"
        )
        wave_bars = "".join([
            f'<rect x="{42+i*5}" y="89" width="3" height="4" rx="1.5" fill="{c}" opacity=".75">'
            f'<animate attributeName="height" values="4;{10+i*4};4" dur="{0.4+i*0.1}s" repeatCount="indefinite"/>'
            f'<animate attributeName="y" values="89;{85-i};89" dur="{0.4+i*0.1}s" repeatCount="indefinite"/>'
            f'</rect>'
            for i in range(4)
        ])
    else:
        mouth_anim = ""
        wave_bars = ""

    blush = (
        f'<ellipse cx="32" cy="60" rx="5" ry="3" fill="#fc5c7d" opacity=".18"/>'
        f'<ellipse cx="68" cy="60" rx="5" ry="3" fill="#fc5c7d" opacity=".18"/>'
    ) if emotion in ["proud","excited"] else ""

    thinking_dots = (
        f'<circle cx="50" cy="40" r="1.5" fill="{c}" opacity=".9">'
        f'<animate attributeName="opacity" values="0;1;0" dur="1s" repeatCount="indefinite"/></circle>'
        f'<circle cx="44" cy="36" r="1" fill="{c}" opacity=".7">'
        f'<animate attributeName="opacity" values="0;1;0" dur="1.3s" repeatCount="indefinite"/></circle>'
    ) if emotion == "thinking" else ""

    mouth_d = f"M 36 65 Q 50 {60+curve} 64 65"

    return (
        f'<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" width="145" height="145">'
        f'<defs>'
        f'<radialGradient id="rg{emotion}" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0%" style="stop-color:{c};stop-opacity:.18"/>'
        f'<stop offset="100%" style="stop-color:#07080f;stop-opacity:0"/>'
        f'</radialGradient>'
        f'<radialGradient id="fg{emotion}" cx="38%" cy="32%" r="65%">'
        f'<stop offset="0%" style="stop-color:#fde8c8"/>'
        f'<stop offset="100%" style="stop-color:#e8a870"/>'
        f'</radialGradient>'
        f'</defs>'
        # Glow bg
        f'<circle cx="50" cy="50" r="48" fill="url(#rg{emotion})">'
        f'<animate attributeName="r" values="46;50;46" dur="3s" repeatCount="indefinite"/></circle>'
        # Orbit ring
        f'<circle cx="50" cy="50" r="46" fill="none" stroke="{c}" stroke-width=".8"'
        f' stroke-dasharray="5 4" opacity=".4" transform-origin="50 50">'
        f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="10s" repeatCount="indefinite"/>'
        f'</circle>'
        # Speaking waves below avatar
        + wave_bars +
        # Floating head group
        f'<g><animateTransform attributeName="transform" type="translate"'
        f' values="0,0;0,-5;0,0" dur="{dur}" repeatCount="indefinite" additive="sum"/>'
        # Face
        f'<ellipse cx="50" cy="52" rx="24" ry="26" fill="url(#fg{emotion})"/>'
        # Hair
        f'<ellipse cx="50" cy="32" rx="24" ry="13" fill="#2d1b69"/>'
        f'<ellipse cx="29" cy="38" rx="8" ry="9" fill="#2d1b69"/>'
        f'<ellipse cx="71" cy="38" rx="8" ry="9" fill="#2d1b69"/>'
        f'<ellipse cx="50" cy="27" rx="18" ry="7" fill="#3d2484"/>'
        f'<ellipse cx="43" cy="28" rx="5" ry="2.5" fill="#5c3ab5" opacity=".5"/>'
        # Eyebrows (move with emotion)
        f'<line x1="33" y1="{46+brow}" x2="42" y2="{43+brow}" stroke="#2d1b69" stroke-width="1.8" stroke-linecap="round"/>'
        f'<line x1="58" y1="{43+brow}" x2="67" y2="{46+brow}" stroke="#2d1b69" stroke-width="1.8" stroke-linecap="round"/>'
        # Left eye
        f'<ellipse cx="38" cy="52" rx="4.5" ry="5" fill="white"/>'
        f'<ellipse cx="38" cy="52" rx="3" ry="3.5" fill="#2d1b69"/>'
        f'<ellipse cx="39.5" cy="50.5" rx="1" ry="1" fill="white"/>'
        # Right eye
        f'<ellipse cx="62" cy="52" rx="4.5" ry="5" fill="white"/>'
        f'<ellipse cx="62" cy="52" rx="3" ry="3.5" fill="#2d1b69"/>'
        f'<ellipse cx="63.5" cy="50.5" rx="1" ry="1" fill="white"/>'
        # Nose
        f'<ellipse cx="50" cy="60" rx="2" ry="1.5" fill="#d4956a" opacity=".5"/>'
        # Mouth (animated when speaking)
        f'<path d="{mouth_d}" fill="none" stroke="{c}" stroke-width="2.5" stroke-linecap="round">'
        + mouth_anim +
        f'</path>'
        + blush + thinking_dots +
        f'</g>'
        f'</svg>'
    )


# ─── AI CALL ─────────────────────────────────────────────────────────────────
def call_ai(messages: list, subject: str) -> str:
    sys_prompt = (
        f"You are Prof. Aura, a warm enthusiastic AI teacher for {subject}. "
        "Teaching style: start with a hook, explain core concept, give a real-world example, end with a question. "
        "Use markdown. 1-2 emojis. 3-5 paragraphs. Always end with one engaging question to deepen thinking."
    )
    keys = st.session_state.api_keys
    priority = st.session_state.model_priority
    recent = [{"role": m["role"], "content": m["content"]} for m in messages[-10:]]

    # Gemini 1.5 Flash
    if priority == "gemini" and keys.get("gemini"):
        try:
            gem_msgs = []
            for m in recent[:-1]:
                gem_msgs.append({
                    "role": "user" if m["role"] == "user" else "model",
                    "parts": [{"text": m["content"]}]
                })
            last_text = recent[-1]["content"] if recent else "Hello"
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={keys['gemini']}",
                json={
                    "system_instruction": {"parts": [{"text": sys_prompt}]},
                    "contents": gem_msgs + [{"role": "user", "parts": [{"text": last_text}]}],
                    "generationConfig": {"maxOutputTokens": 900, "temperature": 0.75},
                },
                timeout=30,
            )
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            pass  # fall through to Groq

    # Groq fallback
    if keys.get("groq"):
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {keys['groq']}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "max_tokens": 900,
                    "messages": [{"role": "system", "content": sys_prompt}] + recent,
                },
                timeout=30,
            )
            return r.json()["choices"][0]["message"]["content"]
        except Exception:
            pass

    # Demo
    import random as _r
    return _r.choice([
        f"**Great question about {subject}!** \U0001f31f\n\nThis is **demo mode** — add your Gemini or Groq API key in the sidebar to unlock real AI teaching.\n\n{subject} builds critical thinking that transfers everywhere. The secret is consistent, curious engagement!\n\n*What part of {subject} are you most curious about?*",
        f"**Interesting!** \U0001f4a1\n\n**{subject}** mastery comes from strong foundations before complex topics.\n\n\U0001f4a1 **Top study techniques:**\n- Spaced repetition (2-3x more effective than re-reading)\n- Active recall (test yourself constantly)\n- Teaching others (deepens your own understanding)\n\n*Add a Gemini key in the sidebar for real personalized teaching!*",
    ])


# ─── TTS ─────────────────────────────────────────────────────────────────────
def _clean_tts(text: str, limit: int = 600) -> str:
    t = re.sub(r'[*#`_\[\]()\n]', ' ', text)
    t = re.sub(r'\s+', ' ', t).strip()
    return t[:limit]

def speak_sarvam(text: str, api_key: str) -> bool:
    clean = _clean_tts(text)
    try:
        r = requests.post(
            "https://api.sarvam.ai/text-to-speech",
            headers={"api-subscription-key": api_key, "Content-Type": "application/json"},
            json={
                "inputs": [clean],
                "target_language_code": "en-IN",
                "speaker": "meera",
                "pitch": 0, "pace": 1.0, "loudness": 1.5,
                "speech_sample_rate": 22050,
                "enable_preprocessing": True,
                "model": "bulbul:v1",
            },
            timeout=20,
        )
        d = r.json()
        if d.get("audios"):
            b64 = d["audios"][0]
            components.html(
                f"<script>(function(){{const a=new Audio('data:audio/wav;base64,{b64}');a.play().catch(()=>{{}});}})();</script>",
                height=0,
            )
            return True
    except Exception:
        pass
    return False

def speak_browser(text: str):
    clean = _clean_tts(text, 500)
    # Escape for JS single-quoted string
    clean = clean.replace("\\", "\\\\").replace("'", "\\'")
    js = (
        "<script>(function(){"
        "if(!window.speechSynthesis)return;"
        "window.speechSynthesis.cancel();"
        f"const u=new SpeechSynthesisUtterance('{clean}');"
        "const vs=window.speechSynthesis.getVoices();"
        "const eng=vs.find(v=>v.lang.startsWith('en-')&&(v.name.includes('Female')||v.name.includes('Samantha')||v.name.includes('Karen')))||vs.find(v=>v.lang.startsWith('en'))||vs[0];"
        "if(eng)u.voice=eng;"
        "u.rate=0.95;u.pitch=1.1;"
        "window.speechSynthesis.speak(u);"
        "})();</script>"
    )
    components.html(js, height=0)

def do_tts(text: str):
    keys = st.session_state.api_keys
    if keys.get("sarvam") and "Sarvam" in st.session_state.get("voice_engine",""):
        if not speak_sarvam(text, keys["sarvam"]):
            speak_browser(text)
    else:
        speak_browser(text)


# ─── VOICE INPUT HTML ────────────────────────────────────────────────────────
VOICE_HTML = (
    "<style>"
    ".vw{display:flex;flex-direction:column;gap:8px;font-family:sans-serif;}"
    ".vb{padding:10px 18px;border:none;border-radius:12px;cursor:pointer;font-size:13px;font-weight:600;width:100%;transition:all .2s;}"
    ".vb.start{background:linear-gradient(135deg,#7c5cfc,#fc5c7d);color:white;}"
    ".vb.stop{background:linear-gradient(135deg,#f43f5e,#f97316);color:white;}"
    ".vst{font-size:11px;color:#8880a8;text-align:center;padding:4px;}"
    ".vwv{display:none;justify-content:center;gap:3px;align-items:center;height:22px;}"
    ".wv{width:3px;border-radius:2px;background:linear-gradient(180deg,#7c5cfc,#fc5c7d);animation:wv .6s ease-in-out infinite;}"
    "@keyframes wv{0%,100%{height:4px;opacity:.4}50%{height:18px;opacity:1}}"
    ".vres{background:rgba(124,92,252,.08);border:1px solid rgba(124,92,252,.2);border-radius:10px;padding:10px;font-size:12px;color:#c4b5fd;min-height:32px;display:none;word-break:break-word;}"
    ".vuse{background:linear-gradient(135deg,#43e97b,#22d3ee);color:#07080f;padding:8px 12px;border:none;border-radius:10px;cursor:pointer;font-size:12px;font-weight:600;width:100%;display:none;margin-top:4px;}"
    "</style>"
    "<div class='vw'>"
    "<div id='vst' class='vst'>🎤 Click to speak to Prof. Aura</div>"
    "<div id='vwv' class='vwv'>"
    "<div class='wv' style='animation-delay:0s'></div>"
    "<div class='wv' style='animation-delay:.1s'></div>"
    "<div class='wv' style='animation-delay:.2s'></div>"
    "<div class='wv' style='animation-delay:.3s'></div>"
    "</div>"
    "<button id='vbtn' class='vb start' onclick='toggleRec()'>🎤 Start Speaking</button>"
    "<div id='vres' class='vres'></div>"
    "<button id='vuse' class='vuse' onclick='sendVoice()'>✅ Send to Prof. Aura →</button>"
    "</div>"
    "<script>"
    "let mr,chunks=[],rec=false,_vt='';"
    "async function toggleRec(){"
    "if(!rec){"
    "try{"
    "const s=await navigator.mediaDevices.getUserMedia({audio:true});"
    "mr=new MediaRecorder(s);chunks=[];"
    "mr.ondataavailable=e=>chunks.push(e.data);"
    "mr.onstop=()=>{s.getTracks().forEach(t=>t.stop());runSTT();};"
    "mr.start();rec=true;"
    "document.getElementById('vbtn').className='vb stop';"
    "document.getElementById('vbtn').textContent='\\u23F9\\uFE0F Stop Recording';"
    "document.getElementById('vwv').style.display='flex';"
    "document.getElementById('vst').textContent='\\uD83D\\uDD34 Listening — speak now';"
    "}catch(e){document.getElementById('vst').textContent='\\u274C Mic denied. Allow microphone in browser settings.';}"
    "}else{"
    "rec=false;"
    "if(mr&&mr.state!=='inactive')mr.stop();"
    "document.getElementById('vbtn').className='vb start';"
    "document.getElementById('vbtn').textContent='\\uD83C\\uDF99\\uFE0F Start Speaking';"
    "document.getElementById('vwv').style.display='none';"
    "document.getElementById('vst').textContent='\\u23F3 Processing...';"
    "}"
    "}"
    "function runSTT(){"
    "if(!('webkitSpeechRecognition' in window||'SpeechRecognition' in window)){"
    "document.getElementById('vst').textContent='\\u274C Browser STT not supported. Use Chrome.';"
    "return;"
    "}"
    "const SR=window.SpeechRecognition||window.webkitSpeechRecognition;"
    "const r=new SR();r.lang='en-US';r.maxAlternatives=1;r.interimResults=false;"
    "r.onresult=e=>{"
    "_vt=e.results[0][0].transcript;"
    "document.getElementById('vres').style.display='block';"
    "document.getElementById('vres').textContent='\\uD83D\\uDDE3\\uFE0F \\\"'+_vt+'\\\"';"
    "document.getElementById('vuse').style.display='block';"
    "document.getElementById('vst').textContent='\\u2705 Tap Send to ask Prof. Aura';"
    "};"
    "r.onerror=e=>{document.getElementById('vst').textContent='\\u274C '+e.error+'. Try Chrome browser.';};"
    "r.start();"
    "}"
    "function sendVoice(){"
    "if(!_vt)return;"
    "const p=new URLSearchParams(window.parent.location.search);"
    "p.set('vq',encodeURIComponent(_vt));"
    "window.parent.location.search=p.toString();"
    "}"
    "</script>"
)


# ─── YOUTUBE ─────────────────────────────────────────────────────────────────
def get_yt(query: str, api_key: str = "") -> list:
    """Fetch YouTube videos. Uses API if key provided, else keyword-matched fallback library."""
    if api_key:
        try:
            r = requests.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={"part": "snippet", "q": query, "type": "video",
                        "maxResults": 4, "videoDuration": "medium",
                        "relevanceLanguage": "en", "key": api_key},
                timeout=8,
            )
            items = r.json().get("items", [])
            if items:
                return [
                    {"title": i["snippet"]["title"][:60],
                     "channel": i["snippet"]["channelTitle"],
                     "vid": i["id"]["videoId"]}
                    for i in items
                ]
        except Exception:
            pass

    # Keyword-matched fallback library — matches on query keywords
    q_low = query.lower()
    subj  = st.session_state.subject

    ALL_VIDEOS = {
        # Mathematics
        "calculus":        [{"title":"3Blue1Brown — Essence of Calculus","channel":"3Blue1Brown","vid":"WUvTyaaNkzM"},
                            {"title":"MIT 18.01 Single Variable Calculus","channel":"MIT OpenCourseWare","vid":"7K1sB05pE0A"}],
        "algebra":         [{"title":"Math Antics — Algebra Basics","channel":"mathantics","vid":"NybHckSEQBI"},
                            {"title":"Algebra Introduction — Khan Academy","channel":"Khan Academy","vid":"vcFBwt1nu2U"}],
        "linear algebra":  [{"title":"3Blue1Brown — Essence of Linear Algebra","channel":"3Blue1Brown","vid":"fNk_zzaMoSs"},
                            {"title":"MIT 18.06 Linear Algebra","channel":"MIT OpenCourseWare","vid":"ZK3O402wf1c"}],
        "probability":     [{"title":"Statistics and Probability — Khan Academy","channel":"Khan Academy","vid":"uzkc-qNVoOk"},
                            {"title":"Harvard Statistics 110","channel":"Harvard","vid":"KbB0FoWK1EE"}],
        "geometry":        [{"title":"Geometry — Khan Academy","channel":"Khan Academy","vid":"302OBzgBfKI"},
                            {"title":"Euclidean Geometry — CrashCourse","channel":"CrashCourse","vid":"IL3UCuXSUaM"}],
        # Physics
        "quantum":         [{"title":"Quantum Mechanics for Beginners","channel":"Veritasium","vid":"MzRCDLre1b4"},
                            {"title":"Quantum Physics Full Course","channel":"Physics Videos","vid":"p7bzE1E5PMY"}],
        "relativity":      [{"title":"Special Relativity — MinutePhysics","channel":"MinutePhysics","vid":"ajhFNcUTJI0"},
                            {"title":"General Relativity — PBS Space Time","channel":"PBS Space Time","vid":"HnETCBOlzJs"}],
        "mechanics":       [{"title":"Classical Mechanics — MIT 8.01","channel":"MIT OpenCourseWare","vid":"wWnfJ0-xXRE"},
                            {"title":"Physics of Motion — CrashCourse","channel":"CrashCourse","vid":"ZM8ECpBuQYE"}],
        "thermodynamics":  [{"title":"Thermodynamics Explained","channel":"Veritasium","vid":"7UMiKGBRhN8"},
                            {"title":"Heat and Thermodynamics","channel":"Khan Academy","vid":"7UMiKGBRhN8"}],
        # Computer Science
        "python":          [{"title":"Python for Everybody — Full Course","channel":"freeCodeCamp","vid":"8DvywoWv6fI"},
                            {"title":"Python Tutorial — Corey Schafer","channel":"Corey Schafer","vid":"YYXdXT2l-Gg"}],
        "machine learning":[{"title":"Machine Learning Course — Andrew Ng","channel":"Coursera","vid":"PPLop4L2eGk"},
                            {"title":"ML for Beginners — freeCodeCamp","channel":"freeCodeCamp","vid":"NWONeJKn6kc"}],
        "algorithm":       [{"title":"Algorithms — Abdul Bari","channel":"Abdul Bari","vid":"0IAPZzGSbME"},
                            {"title":"Data Structures — MIT 6.006","channel":"MIT OpenCourseWare","vid":"HtSuA80QTyo"}],
        "deep learning":   [{"title":"Deep Learning Specialization","channel":"DeepLearning.AI","vid":"CS4cs9xVecg"},
                            {"title":"Neural Networks from Scratch","channel":"Sentdex","vid":"Wo5dMEP_BbI"}],
        "database":        [{"title":"SQL Tutorial — freeCodeCamp","channel":"freeCodeCamp","vid":"HXV3zeQKqGY"},
                            {"title":"Database Design — Caleb Curry","channel":"Caleb Curry","vid":"e7QAvw5X-8I"}],
        # Chemistry
        "organic":         [{"title":"Organic Chemistry — Khan Academy","channel":"Khan Academy","vid":"bSMx0NS0ze8"},
                            {"title":"Organic Chemistry Crash Course","channel":"CrashCourse","vid":"FSyAehMdpyI"}],
        "periodic":        [{"title":"Periodic Table Explained — TED-Ed","channel":"TED-Ed","vid":"0RRVV4Diomg"},
                            {"title":"Chemistry of Elements","channel":"Periodic Videos","vid":"YkYeYhXUeDA"}],
        "reaction":        [{"title":"Chemical Reactions — CrashCourse","channel":"CrashCourse","vid":"uXg0H6nSJQ0"},
                            {"title":"Balancing Chemical Equations","channel":"Khan Academy","vid":"RnGe8-h3xhg"}],
        # Biology
        "genetics":        [{"title":"DNA and Genetics — CrashCourse","channel":"CrashCourse","vid":"8m6hHRlKwxY"},
                            {"title":"Genetics — Khan Academy","channel":"Khan Academy","vid":"CBezq1fFUEA"}],
        "evolution":       [{"title":"Evolution Explained — TED-Ed","channel":"TED-Ed","vid":"GhHOjC4oxh8"},
                            {"title":"Darwin and Natural Selection","channel":"CrashCourse","vid":"aTftyFboC_M"}],
        "cell":            [{"title":"Cell Biology — CrashCourse","channel":"CrashCourse","vid":"8IlzKri08kk"},
                            {"title":"Inside the Cell — TED-Ed","channel":"TED-Ed","vid":"Hmwvj9X4GNY"}],
        # History
        "world war":       [{"title":"World War II — Oversimplified","channel":"Oversimplified","vid":"_uk_6vfqwTA"},
                            {"title":"WWII Documentary — CrashCourse","channel":"CrashCourse","vid":"Q78COTwT7nE"}],
        "ancient":         [{"title":"Ancient Civilizations — CrashCourse","channel":"CrashCourse","vid":"D8qfzBQI0Jo"},
                            {"title":"Ancient History Documentary","channel":"TED-Ed","vid":"ybE6IMtqDkc"}],
        # Default by subject
        "Mathematics":     [{"title":"Khan Academy Mathematics","channel":"Khan Academy","vid":"EKvHQc3QEA0"},
                            {"title":"3Blue1Brown Math Playlist","channel":"3Blue1Brown","vid":"OkmNXy7er84"},
                            {"title":"Numberphile — Fun Math","channel":"Numberphile","vid":"YtkIWDE36qU"},
                            {"title":"Math Explained — CrashCourse","channel":"CrashCourse","vid":"IL3UCuXSUaM"}],
        "Physics":         [{"title":"Physics — CrashCourse","channel":"CrashCourse","vid":"ZM8ECpBuQYE"},
                            {"title":"Veritasium Physics","channel":"Veritasium","vid":"MzRCDLre1b4"},
                            {"title":"PBS Space Time","channel":"PBS Space Time","vid":"HnETCBOlzJs"},
                            {"title":"MinutePhysics","channel":"MinutePhysics","vid":"ajhFNcUTJI0"}],
        "Computer Science":[{"title":"CS50 — Harvard Computer Science","channel":"Harvard","vid":"8mAITcNt710"},
                            {"title":"Python for Beginners","channel":"freeCodeCamp","vid":"eWRfhZUzrAc"},
                            {"title":"How Computers Work","channel":"Code.org","vid":"Dxcc6ycZ73M"},
                            {"title":"Algorithms Explained","channel":"Abdul Bari","vid":"0IAPZzGSbME"}],
        "Chemistry":       [{"title":"Chemistry — CrashCourse","channel":"CrashCourse","vid":"FSyAehMdpyI"},
                            {"title":"Periodic Table — TED-Ed","channel":"TED-Ed","vid":"0RRVV4Diomg"},
                            {"title":"Khan Academy Chemistry","channel":"Khan Academy","vid":"9r9PCF-STYM"},
                            {"title":"Tyler DeWitt Chemistry","channel":"Tyler DeWitt","vid":"0gPKQLitqhc"}],
        "Biology":         [{"title":"Biology — CrashCourse","channel":"CrashCourse","vid":"QnQe0xW_JY4"},
                            {"title":"DNA Replication — TED-Ed","channel":"TED-Ed","vid":"TNKWgcFPHqw"},
                            {"title":"Cell Biology","channel":"Kurzgesagt","vid":"1Rvg3n6-sTs"},
                            {"title":"Khan Academy Biology","channel":"Khan Academy","vid":"CBezq1fFUEA"}],
        "History":         [{"title":"History — CrashCourse","channel":"CrashCourse","vid":"Yocja_N5s1I"},
                            {"title":"Oversimplified History","channel":"Oversimplified","vid":"_uk_6vfqwTA"},
                            {"title":"TED-Ed History","channel":"TED-Ed","vid":"ybE6IMtqDkc"},
                            {"title":"Kings and Generals","channel":"Kings and Generals","vid":"WhnkSjFkYlk"}],
        "Literature":      [{"title":"Literature — CrashCourse","channel":"CrashCourse","vid":"MSYw502dJNY"},
                            {"title":"How to Analyze Literature","channel":"TED-Ed","vid":"2zhBQNMpa_8"},
                            {"title":"Writing Skills","channel":"Oxford Academic","vid":"G8v2Y2gjqZw"},
                            {"title":"Literary Devices Explained","channel":"The School of Life","vid":"3hWj-FbJxaA"}],
        "Geography":       [{"title":"Geography — CrashCourse","channel":"CrashCourse","vid":"fMinvFNpJmA"},
                            {"title":"Physical Geography","channel":"Khan Academy","vid":"i-VW5nFqjbg"},
                            {"title":"World Geography","channel":"TED-Ed","vid":"O_1fIqk7Bfk"},
                            {"title":"Geography Now!","channel":"Geography Now","vid":"6VXrMSXl2zM"}],
        "Music Theory":    [{"title":"Music Theory in 16 Minutes","channel":"Adam Neely","vid":"_eKTOMhpy2w"},
                            {"title":"Music Theory Crash Course","channel":"TED-Ed","vid":"d-KFR3bJKuA"},
                            {"title":"Learn Music Theory","channel":"musictheory.net","vid":"rgaTLrZGlk0"},
                            {"title":"Harmony Explained","channel":"David Bennett Piano","vid":"eRkgK4jfi6M"}],
    }

    # Try keyword match first
    for keyword, videos in ALL_VIDEOS.items():
        if keyword in q_low:
            # Combine keyword matches with subject defaults
            subject_vids = ALL_VIDEOS.get(subj, [])
            combined = videos + [v for v in subject_vids if v not in videos]
            return combined[:4]

    # Fall back to subject default
    default_vids = ALL_VIDEOS.get(subj, [
        {"title": f"Learn {subj} — Khan Academy", "channel": "Khan Academy", "vid": "dQw4w9WgXcQ"},
        {"title": f"{subj} Full Course", "channel": "freeCodeCamp", "vid": "8mAITcNt710"},
        {"title": f"{subj} Explained — CrashCourse", "channel": "CrashCourse", "vid": "eVm063xmnow"},
        {"title": f"{subj} for Beginners", "channel": "TED-Ed", "vid": "0gPKQLitqhc"},
    ])
    return default_vids[:4]



# ─── HUGGINGFACE COURSE SUGGESTIONS ─────────────────────────────────────────
HF_LIBRARY = {
    # ML/AI
    "machine learning":  [{"name":"ml-course","author":"huggingface","url":"https://huggingface.co/learn/ml-course/chapter1/1","task":"🎓 ML Course","desc":"Official HuggingFace ML course"},
                           {"name":"Llama-3-8B-Instruct","author":"meta-llama","url":"https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct","task":"💬 LLM","desc":"Meta Llama 3 instruction model"}],
    "deep learning":     [{"name":"deep-learning-pytorch","author":"fastai","url":"https://huggingface.co/fastai","task":"🧠 Deep Learning","desc":"fast.ai deep learning models"},
                           {"name":"bert-base-uncased","author":"google-bert","url":"https://huggingface.co/google-bert/bert-base-uncased","task":"📝 NLP","desc":"BERT for text understanding"}],
    "nlp":               [{"name":"NLP Course","author":"huggingface","url":"https://huggingface.co/learn/nlp-course/chapter1/1","task":"📚 NLP Course","desc":"Official HuggingFace NLP course"},
                           {"name":"bert-base-uncased","author":"google-bert","url":"https://huggingface.co/google-bert/bert-base-uncased","task":"📝 BERT","desc":"Classic BERT model"}],
    "python":            [{"name":"starcoder2-15b","author":"bigcode","url":"https://huggingface.co/bigcode/starcoder2-15b","task":"💻 Code","desc":"State-of-art code model"},
                           {"name":"CodeLlama-13b","author":"meta-llama","url":"https://huggingface.co/codellama/CodeLlama-13b-hf","task":"💻 Code","desc":"Code generation model"}],
    "math":              [{"name":"mathstral-7B","author":"mistralai","url":"https://huggingface.co/mistralai/mathstral-7B-v0.1","task":"🔢 Math","desc":"Specialized math reasoning"},
                           {"name":"deepseek-math-7b","author":"deepseek-ai","url":"https://huggingface.co/deepseek-ai/deepseek-math-7b-rl","task":"🔢 Math","desc":"RL-trained math solver"}],
    "image":             [{"name":"stable-diffusion-xl","author":"stabilityai","url":"https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0","task":"🎨 Image Gen","desc":"SDXL image generation"},
                           {"name":"ViT-Base","author":"google","url":"https://huggingface.co/google/vit-base-patch16-224","task":"👁️ Vision","desc":"Vision Transformer"}],
    "speech":            [{"name":"whisper-large-v3","author":"openai","url":"https://huggingface.co/openai/whisper-large-v3","task":"🎙️ STT","desc":"Best-in-class speech recognition"},
                           {"name":"mms-tts-eng","author":"facebook","url":"https://huggingface.co/facebook/mms-tts-eng","task":"🔊 TTS","desc":"Text-to-speech model"}],
    "physics":           [{"name":"SciPhi-Self-RAG-Mistral","author":"SciPhi-AI","url":"https://huggingface.co/SciPhi-AI/SciPhi-Self-RAG-Mistral-7B-32k","task":"🔬 Science","desc":"Science-specialized LLM"},
                           {"name":"sci-phi-mistral","author":"SciPhi-AI","url":"https://huggingface.co/SciPhi-AI/SciPhi-Mistral-7B-32k","task":"⚛️ Physics","desc":"Scientific reasoning"}],
    "chemistry":         [{"name":"ChemBERTa","author":"seyonec","url":"https://huggingface.co/seyonec/ChemBERTa-zinc-base-v1","task":"🧪 Chemistry","desc":"BERT trained on molecules"},
                           {"name":"MolT5","author":"GT4SD","url":"https://huggingface.co/GT4SD/multitask-text-and-chemistry-t5-base-standard","task":"⚗️ Chemistry","desc":"Text + chemistry model"}],
    "biology":           [{"name":"BioMedLM","author":"stanford-crfm","url":"https://huggingface.co/stanford-crfm/BioMedLM","task":"🧬 BioMed","desc":"Biomedical language model"},
                           {"name":"BioGPT","author":"microsoft","url":"https://huggingface.co/microsoft/BioGPT-Large","task":"🧬 Biology","desc":"Biomedical text generation"}],
    "history":           [{"name":"Mistral-7B-Instruct","author":"mistralai","url":"https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3","task":"📖 General","desc":"Strong general knowledge LLM"},
                           {"name":"Llama-3.1-8B","author":"meta-llama","url":"https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct","task":"📚 History","desc":"History and humanities LLM"}],
    "music":             [{"name":"musicgen-large","author":"facebook","url":"https://huggingface.co/facebook/musicgen-large","task":"🎵 Music Gen","desc":"AI music generation"},
                           {"name":"whisper-base","author":"openai","url":"https://huggingface.co/openai/whisper-base","task":"🎙️ Audio","desc":"Audio transcription"}],
    "default":           [{"name":"Llama-3.1-8B-Instruct","author":"meta-llama","url":"https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct","task":"💬 LLM","desc":"Best open-source LLM"},
                           {"name":"Mistral-7B-Instruct","author":"mistralai","url":"https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3","task":"🤖 AI","desc":"Fast instruction-tuned LLM"}],
}

HF_COURSES = {
    "machine learning":  {"name":"HuggingFace ML Course","url":"https://huggingface.co/learn/ml-course","desc":"Free end-to-end ML course"},
    "nlp":               {"name":"HuggingFace NLP Course","url":"https://huggingface.co/learn/nlp-course","desc":"Natural Language Processing"},
    "deep learning":     {"name":"fast.ai Deep Learning","url":"https://course.fast.ai","desc":"Practical deep learning"},
    "computer science":  {"name":"CS50 on HuggingFace","url":"https://huggingface.co/datasets/cs50","desc":"Harvard CS50 datasets"},
    "math":              {"name":"DeepMind Math Dataset","url":"https://huggingface.co/datasets/deepmind/math_dataset","desc":"Mathematics problem dataset"},
    "python":            {"name":"Python Code Datasets","url":"https://huggingface.co/datasets/codeparrot/github-code","task":"Code datasets on HF"},
}

def get_hf_suggestions(query: str) -> list:
    """Return HuggingFace models + courses matching the query keywords."""
    q_low = query.lower()
    subj  = st.session_state.subject.lower()

    matched = []
    # Keyword match
    for keyword, models in HF_LIBRARY.items():
        if keyword in q_low or keyword in subj:
            for m in models:
                if m not in matched:
                    matched.append(m)

    # Always add default if we have less than 2
    if len(matched) < 2:
        for m in HF_LIBRARY["default"]:
            if m not in matched:
                matched.append(m)

    return matched[:3]

def get_hf_course(query: str) -> dict | None:
    """Return a relevant HuggingFace course if one matches."""
    q_low = query.lower()
    subj  = st.session_state.subject.lower()
    for keyword, course in HF_COURSES.items():
        if keyword in q_low or keyword in subj:
            return course
    return None


# ─── SUGGESTIONS ─────────────────────────────────────────────────────────────
SUGG_BANK = {
    "🧠 Concept":    ["Explain {s} like I'm 10 years old",
                      "What's the single most important idea in {s}?",
                      "What is the most counterintuitive thing in {s}?",
                      "Break down the hardest concept in {s} step by step"],
    "💡 Apply":      ["How is {s} used in the real world right now?",
                      "Give me a step-by-step real example of {s}",
                      "What careers use {s} every day?",
                      "Show me how a professional uses {s} in their work"],
    "📝 Quiz Me":    ["Give me 3 MCQs on {s} with answer explanations",
                      "Quiz me on {s} with increasing difficulty levels",
                      "Create a mini-test on the basics of {s}",
                      "Ask me one hard question in {s} and grade my answer"],
    "🔍 Deep Dive":  ["What are the unsolved problems in {s}?",
                      "What is the history and origin of {s}?",
                      "What do experts debate about in {s}?",
                      "What is cutting-edge research in {s} right now?"],
    "🚀 Study Tips": ["What is the #1 mistake students make in {s}?",
                      "Give me a 30-day study plan for {s}",
                      "What should I learn first in {s} as a beginner?",
                      "How do experts think differently about {s}?"],
    "🎯 Challenge":  ["Give me a hard problem to solve in {s}",
                      "Tell me a fascinating paradox or puzzle in {s}",
                      "What would a PhD student work on in {s}?",
                      "Challenge me with an advanced {s} scenario"],
}

CAT_COLORS = {
    "🧠 Concept": "#7c5cfc",
    "💡 Apply":   "#43e97b",
    "📝 Quiz Me": "#f7971e",
    "🔍 Deep Dive": "#22d3ee",
    "🚀 Study Tips": "#fc5c7d",
    "🎯 Challenge": "#818cf8",
}

def get_suggestions(subj: str, cat: str = "all") -> list:
    """Generate stable suggestions — cached in session_state so buttons don't shift on rerun."""
    cache_key = f"sugg_cache_{subj}_{cat}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    cats = list(SUGG_BANK.keys()) if cat == "all" else [cat]
    out = []
    for c in cats:
        qs = SUGG_BANK.get(c, [])
        chosen = random.sample(qs, min(2, len(qs)))
        for q in chosen:
            out.append({"cat": c, "q": q.replace("{s}", subj)})
    random.shuffle(out)
    result = out[:8]
    st.session_state[cache_key] = result
    return result

def refresh_suggestions():
    """Clear suggestion cache so next render picks new ones."""
    keys_to_del = [k for k in st.session_state if k.startswith("sugg_cache_")]
    for k in keys_to_del:
        del st.session_state[k]



def render_dashboard():
    st.markdown("""
<div style="background:linear-gradient(135deg,rgba(124,92,252,0.1),rgba(252,92,125,0.06));
  border:1px solid rgba(124,92,252,0.2);border-radius:20px;padding:24px;margin-bottom:20px;">
  <div style="font-size:26px;font-weight:900;color:#e8e6f0;font-family:Georgia,serif;">
    📊 Student Analytics <span style="background:linear-gradient(90deg,#7c5cfc,#fc5c7d);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Dashboard</span>
  </div>
  <div style="color:#6b7280;font-size:13px;margin-top:6px;">Real insights · 8,000 students · AI Impact on Learning Performance</div>
</div>
""", unsafe_allow_html=True)

    # KPI row
    kpis = [("8,000", "Total Students", "#7c5cfc"),
            ("64.2", "Avg Final Score", "#43e97b"),
            ("18.3%", "High Risk", "#f43f5e"),
            ("5.84", "Avg Concept Score", "#22d3ee"),
            ("88.9%", "Pass Rate", "#f7971e")]
    cols = st.columns(5)
    for col, (val, lbl, color) in zip(cols, kpis):
        with col:
            st.markdown(f"""
<div style="background:rgba(0,0,0,0.3);border:1px solid {color}30;border-radius:14px;
  padding:16px;text-align:center;">
  <div style="font-size:28px;font-weight:900;color:{color};font-family:'Georgia',serif;">{val}</div>
  <div style="font-size:10px;color:#6b7280;margin-top:4px;text-transform:uppercase;letter-spacing:1px;">{lbl}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # Charts
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        import plotly.express as px
        PLOT_BG = "rgba(0,0,0,0)"
        GRID = "rgba(255,255,255,0.05)"
        FONT = {"color": "#8880a8", "size": 11}

        def styled_fig(fig):
            fig.update_layout(
                paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG,
                font=FONT, margin=dict(t=30,b=10,l=10,r=10),
                height=220,
                xaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
                yaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
            )
            return fig

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("<div style='font-size:11px;color:#6b7280;letter-spacing:1px;margin-bottom:6px;'>📈 SCORE DISTRIBUTION</div>", unsafe_allow_html=True)
            fig = go.Figure(go.Bar(
                x=["0-20","21-40","41-60","61-80","81-100"],
                y=[320,1240,2680,2890,870],
                marker_color=["#f43f5e","#f59e0b","#6366f1","#22d3ee","#43e97b"],
                marker_line_width=0, text=[320,1240,2680,2890,870],
                textposition="outside", textfont=dict(color="#8880a8",size=9),
            ))
            st.plotly_chart(styled_fig(fig), use_container_width=True)

        with c2:
            st.markdown("<div style='font-size:11px;color:#6b7280;letter-spacing:1px;margin-bottom:6px;'>🤖 AI USAGE → SCORE</div>", unsafe_allow_html=True)
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=["0-20%","21-40%","41-60%","61-80%","81-100%"],
                y=[72.1,68.4,64.8,59.2,51.0], name="Avg Score",
                line=dict(color="#7c5cfc",width=2), fill="tozeroy",
                fillcolor="rgba(124,92,252,0.08)"))
            fig2.add_trace(go.Scatter(x=["0-20%","21-40%","41-60%","61-80%","81-100%"],
                y=[94,89,84,76,62], name="Pass Rate %",
                line=dict(color="#43e97b",width=2), fill="tozeroy",
                fillcolor="rgba(67,233,123,0.06)"))
            fig2.update_layout(legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color="#8880a8",size=9)))
            st.plotly_chart(styled_fig(fig2), use_container_width=True)

        with c3:
            st.markdown("<div style='font-size:11px;color:#6b7280;letter-spacing:1px;margin-bottom:6px;'>⚠️ RISK DISTRIBUTION</div>", unsafe_allow_html=True)
            fig3 = go.Figure(go.Pie(
                labels=["Low Risk","Medium Risk","High Risk"],
                values=[4820,2713,467], hole=0.62,
                marker=dict(colors=["#43e97b","#f59e0b","#f43f5e"],
                            line=dict(color="#0a0a0f",width=2)),
                textfont=dict(color="white",size=10),
            ))
            fig3.add_annotation(text="8,000<br>Students", x=0.5, y=0.5,
                                font=dict(size=11,color="#e8e6f0"), showarrow=False)
            fig3.update_layout(paper_bgcolor=PLOT_BG, height=220, margin=dict(t=10,b=10,l=10,r=10),
                               font=FONT, legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color="#8880a8",size=10)))
            st.plotly_chart(fig3, use_container_width=True)

        c4, c5 = st.columns(2)
        with c4:
            st.markdown("<div style='font-size:11px;color:#6b7280;letter-spacing:1px;margin-bottom:6px;'>📚 STUDY HOURS → SCORE</div>", unsafe_allow_html=True)
            fig4 = go.Figure(go.Bar(
                x=["<1h","1-2h","2-3h","3-4h","4-5h","5h+"],
                y=[44.2,56.8,64.3,72.1,76.8,79.4],
                marker=dict(color=["#f43f5e","#f59e0b","#6366f1","#7c5cfc","#22d3ee","#43e97b"]),
                text=[44.2,56.8,64.3,72.1,76.8,79.4], textposition="outside",
                textfont=dict(color="#8880a8",size=9),
            ))
            st.plotly_chart(styled_fig(fig4), use_container_width=True)

        with c5:
            st.markdown("<div style='font-size:11px;color:#6b7280;letter-spacing:1px;margin-bottom:6px;'>🧠 HIGH PERFORMERS vs AT-RISK (RADAR)</div>", unsafe_allow_html=True)
            categories = ["Concept Score","Study Hours","Attendance","Exam Score","Consistency","Participation"]
            fig5 = go.Figure()
            fig5.add_trace(go.Scatterpolar(r=[8.2,4.1,88,82,7.8,7.5], theta=categories,
                fill="toself", name="High Performers",
                line=dict(color="#43e97b"), fillcolor="rgba(67,233,123,0.1)"))
            fig5.add_trace(go.Scatterpolar(r=[3.1,1.8,62,41,3.2,3.8], theta=categories,
                fill="toself", name="At-Risk Students",
                line=dict(color="#f43f5e"), fillcolor="rgba(244,63,94,0.1)"))
            fig5.update_layout(
                polar=dict(bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(visible=True,range=[0,100],gridcolor=GRID,color="#6b7280",showticklabels=False),
                    angularaxis=dict(gridcolor=GRID,color="#8880a8")),
                paper_bgcolor=PLOT_BG, height=220, margin=dict(t=20,b=10,l=20,r=20),
                font=FONT, showlegend=True,
                legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color="#8880a8",size=9)),
            )
            st.plotly_chart(fig5, use_container_width=True)

    except ImportError:
        st.info("Install plotly for charts: `pip install plotly`")

    # Insight cards
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    insights = [
        ("#43e97b", "🥇 Top Success Driver", "Concept Understanding has the strongest positive correlation (+0.424) with final scores across 8,000 students.", "r = +0.424"),
        ("#f43f5e", "⚠️ AI Dependency Risk", "Overdependent students avg only 51.0 vs 74.3 for Smart Users — a massive 23-point performance gap.", "−23 pts gap"),
        ("#22d3ee", "📈 Smart AI Lift", "Strategic AI adoption leads to average +3.9 point grade improvement. 88.9% overall pass rate.", "+3.9 pts avg"),
    ]
    cols = st.columns(3)
    for col, (color, title, body, num) in zip(cols, insights):
        with col:
            st.markdown(f"""
<div style="background:rgba(0,0,0,0.2);border:1px solid rgba(255,255,255,0.06);
  border-left:3px solid {color};border-radius:14px;padding:16px;">
  <div style="font-size:12px;font-weight:700;color:#e8e6f0;margin-bottom:6px;">{title}</div>
  <div style="font-size:11px;color:#6b7280;line-height:1.5;">{body}</div>
  <div style="font-size:22px;font-weight:900;color:{color};margin-top:8px;font-family:Georgia,serif;">{num}</div>
</div>""", unsafe_allow_html=True)


# ─── RISK DETECTOR PAGE ───────────────────────────────────────────────────────

def render_risk():
    st.markdown("""
<div style="background:linear-gradient(135deg,rgba(244,63,94,0.08),rgba(247,151,30,0.05));
  border:1px solid rgba(244,63,94,0.2);border-radius:20px;padding:20px;margin-bottom:20px;">
  <div style="font-size:24px;font-weight:900;color:#e8e6f0;font-family:Georgia,serif;">
    ⚠️ Student <span style="color:#f43f5e;">Risk</span> Detector
  </div>
  <div style="color:#6b7280;font-size:12px;margin-top:4px;">ML-calibrated · 8,000-student dataset · 6-factor model · Personalized action plan</div>
</div>
""", unsafe_allow_html=True)

    col_in, col_out = st.columns([1, 1.4])
    with col_in:
        st.markdown("**Student Profile**")
        concept = st.slider("🧠 Concept Understanding (0–10)", 0.0, 10.0, 5.0, 0.1)
        ai_pct  = st.slider("🤖 AI-Generated Content % (0–100)", 0.0, 100.0, 40.0, 1.0)
        study   = st.slider("📚 Study Hours/Day (0–10)", 0.0, 10.0, 3.0, 0.1)
        exam    = st.slider("📝 Last Exam Score (0–100)", 0.0, 100.0, 60.0, 1.0)
        attend  = st.slider("🏫 Attendance % (0–100)", 0.0, 100.0, 75.0, 1.0)
        sleep   = st.slider("😴 Sleep Hours/Night (0–12)", 0.0, 12.0, 7.0, 0.5)

        analyze = st.button("🔍 Analyze Risk Profile", use_container_width=True, type="primary")

    with col_out:
        if analyze or st.session_state.risk_result:
            if analyze:
                risk = max(0.02, min(0.98,
                    0.35 * (10 - concept) / 10 +
                    0.22 * ai_pct / 100 +
                    0.15 * (10 - study) / 10 +
                    0.12 * (100 - exam) / 100 +
                    0.08 * (100 - attend) / 100 +
                    0.08 * max(0, 1 - (sleep - 4) / 5)
                ))
                st.session_state.risk_result = {
                    "risk": risk, "concept": concept, "ai_pct": ai_pct,
                    "study": study, "exam": exam, "attend": attend, "sleep": sleep,
                }

            r = st.session_state.risk_result
            risk = r["risk"]; pct = int(risk * 100)

            if risk >= 0.60:   color, level, advice = "#f43f5e", "HIGH RISK 🔴", "Immediate support needed. Focus on concept building."
            elif risk >= 0.35: color, level, advice = "#f59e0b", "MEDIUM RISK 🟡", "Monitor closely. Balance AI with active learning."
            else:              color, level, advice = "#43e97b", "LOW RISK 🟢",    "Strong profile! Maintain your excellent habits."

            # Gauge
            st.markdown(f"""
<div style="background:rgba(0,0,0,0.2);border:1px solid {color}30;border-radius:16px;padding:20px;text-align:center;">
  <div style="font-size:52px;font-weight:900;color:{color};font-family:Georgia,serif;line-height:1;">{pct}%</div>
  <div style="font-size:14px;font-weight:700;color:{color};margin-top:4px;">{level}</div>
  <div style="font-size:11px;color:#6b7280;margin-top:6px;line-height:1.5;">{advice}</div>
  <div style="margin-top:14px;">
    <div style="display:flex;justify-content:space-between;font-size:9px;color:#6b7280;margin-bottom:4px;">
      <span>Low Risk</span><span>Medium</span><span>High Risk</span>
    </div>
    <div style="height:8px;background:linear-gradient(90deg,#43e97b,#f59e0b,#f43f5e);border-radius:4px;position:relative;">
      <div style="position:absolute;top:-4px;left:{pct}%;width:16px;height:16px;
        background:white;border-radius:50%;transform:translateX(-50%);
        box-shadow:0 0 8px {color};transition:left 0.8s;"></div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

            # Factor bars
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            factors = [
                ("🧠 Concept Gap", (10 - r["concept"]) / 10, "#818cf8"),
                ("🤖 AI Overuse",  r["ai_pct"] / 100,        "#f43f5e"),
                ("⏰ Low Study",   (10 - r["study"]) / 10,   "#f59e0b"),
                ("📝 Exam Perf.",  (100 - r["exam"]) / 100,  "#22d3ee"),
                ("🏫 Attendance",  (100 - r["attend"]) / 100,"#f97316"),
                ("😴 Sleep Def.",  max(0, 1-(r["sleep"]-4)/5),"#a855f7"),
            ]
            st.markdown("**Factor Breakdown**")
            for lbl, val, col in factors:
                w = int(val * 100)
                st.markdown(f"""
<div style="margin:6px 0;">
  <div style="display:flex;justify-content:space-between;font-size:11px;color:#8880a8;margin-bottom:3px;">
    <span>{lbl}</span><span style="color:{col};font-weight:700;">{w}% risk</span>
  </div>
  <div style="background:rgba(255,255,255,0.04);border-radius:4px;height:6px;overflow:hidden;">
    <div style="width:{w}%;background:{col};height:100%;border-radius:4px;opacity:0.85;"></div>
  </div>
</div>""", unsafe_allow_html=True)

        else:
            st.info("👈 Set your profile and click **Analyze Risk Profile**")

    # Action plan
    if st.session_state.risk_result:
        r = st.session_state.risk_result
        st.markdown("---")
        st.markdown("**📋 Personalized Action Plan**")
        actions = []
        if r["concept"] < 5:    actions.append(("🔴", "#f43f5e", "Rebuild Concepts", "Use Beginner Friendly mode. Ask Prof. Aura to explain with analogies and examples daily."))
        if r["ai_pct"] > 60:    actions.append(("🟡", "#f59e0b", "Reduce AI Over-use", "Draft your own answers first. Use AI to verify — target max 40% AI content."))
        if r["study"] < 2:      actions.append(("🟡", "#f59e0b", "Increase Study Time", "Target 3+ hours/day. Pomodoro: 25min focus + 5min break."))
        if r["attend"] < 70:    actions.append(("🔴", "#f43f5e", "Improve Attendance", "Aim for 80%+. Use Prof. Aura to catch up on missed content."))
        if r["exam"] < 50:      actions.append(("🔴", "#f43f5e", "Boost Exam Skills", "Use Quiz mode daily. Active recall beats re-reading 2-3×."))
        if r["sleep"] < 6:      actions.append(("🟡", "#f59e0b", "Fix Sleep Schedule", "7-8 hours/night improves memory consolidation by 40%."))
        if not actions:         actions.append(("🟢", "#43e97b", "Excellent Profile!", "Keep up your great habits. Consider teaching others — it deepens your own mastery."))

        cols = st.columns(min(len(actions), 3))
        for i, (icon, color, title, body) in enumerate(actions):
            with cols[i % 3]:
                st.markdown(f"""
<div style="background:rgba(0,0,0,0.2);border:1px solid {color}25;border-left:3px solid {color};
  border-radius:12px;padding:12px;margin-bottom:8px;">
  <div style="font-size:12px;font-weight:700;color:#e8e6f0;">{icon} {title}</div>
  <div style="font-size:11px;color:#6b7280;margin-top:4px;line-height:1.4;">{body}</div>
</div>""", unsafe_allow_html=True)


# ─── LEARN PAGE ───────────────────────────────────────────────────────────────
# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown(
            "<div style='text-align:center;padding:8px 0 12px;'>"
            "<div style='font-size:28px;'>🎓</div>"
            "<div style='font-family:Syne,sans-serif;font-size:16px;font-weight:800;"
            "background:linear-gradient(135deg,#c4b5fd,#f9a8d4);"
            "-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>EduAI Guardian</div>"
            "<div style='font-size:9px;color:#6b7280;letter-spacing:2px;'>v8 · EXPRESSIVE EDITION</div>"
            "</div>",
            unsafe_allow_html=True,
        )

        emo = st.session_state.emotion
        spk = st.session_state.is_speaking
        e   = EMOTIONS[emo]
        svg = avatar_svg(emo, spk)

        wave_html = "".join([
            f"<div style='width:2px;height:{4+i*3}px;background:{e['color']};border-radius:1px;"
            f"animation:wave-bar .5s ease-in-out infinite;animation-delay:{i*0.1}s'></div>"
            for i in range(4)
        ]) if spk else ""

        st.markdown(
            f"<div style='text-align:center;margin:4px 0;'>"
            f"<div style='display:inline-block;filter:drop-shadow(0 0 16px {e['color']}55);'>{svg}</div>"
            f"<div style='font-size:13px;font-weight:700;color:{e['color']};font-family:Syne,sans-serif;margin-top:2px;'>Prof. Aura</div>"
            f"<div style='font-size:10px;color:#8880a8;'>{e['label']}</div>"
            f"<div style='display:inline-flex;align-items:center;gap:5px;background:{e['color']}18;"
            f"border:1px solid {e['color']}35;border-radius:20px;padding:3px 12px;"
            f"font-size:10px;color:{e['color']};margin-top:5px;'>"
            f"{e['emoji']} {e['mood']}{wave_html}"
            f"</div></div>"
            "<hr style='border:none;border-top:1px solid rgba(255,255,255,0.06);margin:10px 0;'>",
            unsafe_allow_html=True,
        )

        sn  = [s[1] for s in SUBJECTS]
        idx = sn.index(st.session_state.subject) if st.session_state.subject in sn else 0
        sel = st.selectbox("📚 Subject", sn, index=idx)
        if sel != st.session_state.subject:
            st.session_state.subject = sel
            st.rerun()

        st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.06);margin:10px 0;'>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                f"<div style='text-align:center;background:rgba(124,92,252,0.1);"
                f"border:1px solid rgba(124,92,252,0.2);border-radius:10px;padding:10px;'>"
                f"<div style='font-size:22px;font-weight:700;color:#c4b5fd;'>{st.session_state.lessons}</div>"
                f"<div style='font-size:9px;color:#6b7280;'>Lessons</div></div>",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"<div style='text-align:center;background:rgba(67,233,123,0.1);"
                f"border:1px solid rgba(67,233,123,0.2);border-radius:10px;padding:10px;'>"
                f"<div style='font-size:22px;font-weight:700;color:#43e97b;'>{st.session_state.streak}🔥</div>"
                f"<div style='font-size:9px;color:#6b7280;'>Streak</div></div>",
                unsafe_allow_html=True,
            )
        st.markdown(
            f"<div style='text-align:center;background:rgba(247,151,30,0.1);"
            f"border:1px solid rgba(247,151,30,0.2);border-radius:10px;padding:10px;margin-top:6px;'>"
            f"<div style='font-size:18px;font-weight:700;color:#f7971e;'>⚡ {st.session_state.xp} XP</div></div>",
            unsafe_allow_html=True,
        )

        st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.06);margin:10px 0;'>", unsafe_allow_html=True)

        with st.expander("⚙️ AI & API Keys"):
            st.session_state.model_priority = st.selectbox(
                "Primary AI Model",
                ["gemini", "groq", "demo"],
                index=["gemini","groq","demo"].index(st.session_state.model_priority),
            )
            st.session_state.api_keys["gemini"]  = st.text_input("🔮 Gemini Key",  value=st.session_state.api_keys["gemini"],  type="password", placeholder="AIza...")
            st.session_state.api_keys["groq"]    = st.text_input("⚡ Groq Key",    value=st.session_state.api_keys["groq"],    type="password", placeholder="gsk_...")
            st.session_state.api_keys["sarvam"]  = st.text_input("🔊 Sarvam Key",  value=st.session_state.api_keys["sarvam"],  type="password", placeholder="sarvam-...")
            st.session_state.api_keys["youtube"] = st.text_input("📺 YouTube Key", value=st.session_state.api_keys["youtube"], type="password", placeholder="AIza...")
            if st.button("💾 Save Keys", use_container_width=True):
                st.success("Keys saved! ✅")

        with st.expander("🔊 Voice Settings"):
            st.session_state["auto_speak"]    = st.toggle("Auto-speak every reply", value=st.session_state.get("auto_speak", True))
            st.session_state["voice_engine"]  = st.radio(
                "TTS Engine",
                ["Sarvam AI (Indian English — Meera)", "Browser TTS (works anywhere)"],
                index=0 if st.session_state.api_keys.get("sarvam") else 1,
            )


# ─── HANDLE SEND ─────────────────────────────────────────────────────────────
def handle_send(text: str, via_voice: bool = False):
    st.session_state.messages.append({"role": "user", "content": text, "via_voice": via_voice})

    # Detect emotion
    tl = text.lower()
    emo = "enthusiastic"
    if any(w in tl for w in ["why","how","what","where","which","explain"]): emo = "curious"
    if any(w in tl for w in ["wow","amazing","quiz","test","challenge","game"]): emo = "excited"
    if any(w in tl for w in ["help","confused","don't understand","stuck","hard","difficult"]): emo = "patient"
    if any(w in tl for w in ["great","thanks","got it","correct","i understand","perfect"]): emo = "proud"
    if any(w in tl for w in ["think","define","describe","analyze","compare"]): emo = "thinking"

    st.session_state.emotion    = "thinking"
    st.session_state.is_speaking = False
    st.session_state.last_question = text

    reply = call_ai(st.session_state.messages, st.session_state.subject)
    st.session_state.messages.append({"role": "assistant", "content": reply, "emotion": emo})

    st.session_state.emotion     = "speaking"
    st.session_state.is_speaking = True
    st.session_state.lessons    += 1
    st.session_state.xp         += random.randint(10, 25)

    yt_key = st.session_state.api_keys.get("youtube","")
    st.session_state.yt_suggestions = get_yt(f"{st.session_state.subject} {text}", yt_key)
    st.session_state.hf_suggestions = get_hf_suggestions(text)
    st.session_state.hf_course      = get_hf_course(text)

    if st.session_state.get("auto_speak", True):
        do_tts(reply)

    st.session_state.emotion     = emo
    st.rerun()


# ─── LEARN PAGE ──────────────────────────────────────────────────────────────
def render_learn():
    subj = st.session_state.subject

    st.markdown(
        f"<div style='display:flex;align-items:center;gap:12px;margin-bottom:14px;"
        f"background:rgba(124,92,252,0.06);border:1px solid rgba(124,92,252,0.12);"
        f"border-radius:16px;padding:14px 18px;'>"
        f"<div style='font-size:26px;'>🎓</div>"
        f"<div><div style='font-family:Syne,sans-serif;font-size:17px;font-weight:700;color:#e8e6f0;'>"
        f"Prof. Aura — <span style='background:linear-gradient(90deg,#7c5cfc,#fc5c7d);"
        f"-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>{subj}</span></div>"
        f"<div style='font-size:11px;color:#6b7280;margin-top:1px;'>"
        f"🗣️ Real-time voice · 💬 Text chat · 📺 YouTube · 🤖 {st.session_state.model_priority.title()} AI</div></div>"
        f"<div style='margin-left:auto;'>"
        f"<div style='background:rgba(247,151,30,0.1);border:1px solid rgba(247,151,30,0.2);"
        f"border-radius:20px;padding:3px 12px;font-size:10px;color:#f7971e;font-weight:600;'>⚡ {st.session_state.xp} XP</div>"
        f"</div></div>",
        unsafe_allow_html=True,
    )

    # ── Text input row ──
    st.markdown(
        "<div style='background:rgba(17,17,30,0.9);border:1px solid rgba(124,92,252,0.15);"
        "border-radius:16px;padding:14px 16px;margin-bottom:14px;'>"
        "<div style='font-size:10px;color:#6b7280;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;'>✏️ Type your question</div>",
        unsafe_allow_html=True,
    )
    ci, cs = st.columns([9, 1])
    with ci:
        user_text = st.text_input(
            "", placeholder=f"Ask anything about {subj}... or use voice below 🎤",
            label_visibility="collapsed", key="learn_text_input",
        )
    with cs:
        send_btn = st.button("➤", use_container_width=True, type="primary")
    st.markdown("</div>", unsafe_allow_html=True)

    if send_btn and user_text.strip():
        handle_send(user_text.strip())

    # ── Voice + controls ──
    vc1, vc2 = st.columns([1, 1])
    with vc1:
        st.markdown(
            "<div style='background:rgba(17,17,30,0.9);border:1px solid rgba(124,92,252,0.1);"
            "border-radius:14px;padding:14px;'>"
            "<div style='font-size:10px;color:#6b7280;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;'>"
            "🎤 VOICE INPUT (Chrome)</div>",
            unsafe_allow_html=True,
        )
        components.html(VOICE_HTML, height=200)
        st.markdown("</div>", unsafe_allow_html=True)

    with vc2:
        st.markdown(
            "<div style='background:rgba(17,17,30,0.9);border:1px solid rgba(124,92,252,0.1);"
            "border-radius:14px;padding:14px;'>"
            "<div style='font-size:10px;color:#6b7280;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;'>"
            "🔊 VOICE CONTROLS</div>",
            unsafe_allow_html=True,
        )
        if st.button("🔊 Replay last reply", use_container_width=True):
            last_ai = next(
                (m for m in reversed(st.session_state.messages) if m["role"] == "assistant"),
                None,
            )
            if last_ai:
                st.session_state.is_speaking = True
                do_tts(last_ai["content"])

        if st.button("🔇 Stop speaking", use_container_width=True):
            st.session_state.is_speaking = False
            components.html(
                "<script>if(window.speechSynthesis)window.speechSynthesis.cancel();</script>",
                height=0,
            )

        keys = st.session_state.api_keys
        engine_name = "Sarvam AI (Meera)" if keys.get("sarvam") and "Sarvam" in st.session_state.get("voice_engine","") else "Browser TTS"
        speaking_txt = "🔊 Speaking..." if st.session_state.is_speaking else "⏸️ Ready"
        st.markdown(
            f"<div style='background:rgba(7,8,15,0.6);border:1px solid rgba(255,255,255,0.06);"
            f"border-radius:10px;padding:10px;font-size:11px;color:#8880a8;margin-top:6px;'>"
            f"<div style='color:#43e97b;font-weight:600;margin-bottom:4px;'>{speaking_txt}</div>"
            f"Engine: {engine_name}<br>"
            f"Auto-speak: {'ON' if st.session_state.get('auto_speak',True) else 'OFF'}"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Suggestions ──
    st.markdown(
        "<div style='margin:14px 0 10px;'>"
        "<div style='font-size:10px;color:#6b7280;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;'>"
        "💡 QUICK QUESTIONS — Click any card to ask instantly</div>",
        unsafe_allow_html=True,
    )

    # Category filter
    all_cats = ["all"] + list(SUGG_BANK.keys())
    cat_cols = st.columns(len(all_cats))
    for i, cat in enumerate(all_cats):
        with cat_cols[i]:
            label = "🌟 All" if cat == "all" else cat
            active = st.session_state.sugg_cat == cat
            if st.button(label[:12], key=f"cat_filter_{i}",
                         use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.sugg_cat = cat
                refresh_suggestions()  # clear cache so new category loads fresh
                st.rerun()

    # Suggestion grid
    suggestions = get_suggestions(subj, st.session_state.sugg_cat)
    s_cols = st.columns(4)
    # Use stable slot-index keys (0-7) so Streamlit tracks clicks correctly
    for i, s in enumerate(suggestions[:8]):
        with s_cols[i % 4]:
            color = CAT_COLORS.get(s["cat"], "#7c5cfc")
            st.markdown(
                f"<div style='font-size:9px;color:{color};font-weight:600;"
                f"letter-spacing:.3px;margin-bottom:2px;'>{s['cat']}</div>",
                unsafe_allow_html=True,
            )
            q_short = s["q"][:44] + ("…" if len(s["q"]) > 44 else "")
            # Key is stable: slot index (0-7) — never changes between reruns
            if st.button(q_short, key=f"sq_slot_{i}",
                         use_container_width=True, help=s["q"]):
                handle_send(s["q"])

    if st.button("🔄 New suggestions", key="refresh_sugg"):
        refresh_suggestions()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Chat history ──
    st.markdown(
        "<div style='font-size:10px;color:#6b7280;letter-spacing:1px;"
        "text-transform:uppercase;margin-bottom:10px;'>💬 CONVERSATION WITH PROF. AURA</div>",
        unsafe_allow_html=True,
    )

    if not st.session_state.messages:
        e = EMOTIONS[st.session_state.emotion]
        st.markdown(
            f"<div class='msg-t'>"
            f"<div style='font-size:10px;color:#6b7280;margin-bottom:6px;'>Prof. Aura · Just now</div>"
            f"<div style='display:inline-flex;align-items:center;gap:6px;"
            f"background:{e['color']}18;border:1px solid {e['color']}30;border-radius:10px;"
            f"padding:2px 10px;font-size:10px;color:{e['color']};margin-bottom:8px;'>"
            f"{e['emoji']} {e['mood']}</div>"
            f"<div style='font-size:14px;color:#e8e6f0;line-height:1.7;'>"
            f"<strong>Hello, brilliant learner!</strong> I'm Prof. Aura — your expressive, voice-enabled AI teacher! 🎓<br><br>"
            f"I <strong>speak every reply aloud</strong> using Sarvam AI (Meera voice) or your browser's TTS. "
            f"I also <strong>understand your spoken questions</strong> via the 🎤 voice button above.<br><br>"
            f"Choose <strong>text or voice</strong> — or use both together! "
            f"Pick a question below or ask me anything about <strong>{subj}</strong>! 🚀"
            f"</div></div>",
            unsafe_allow_html=True,
        )
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                icon = "🎤" if msg.get("via_voice") else "✏️"
                st.markdown(
                    f"<div style='display:flex;flex-direction:row-reverse;margin-bottom:10px;'>"
                    f"<div class='msg-s'>"
                    f"<div style='font-size:9px;color:#8880a8;margin-bottom:4px;'>You {icon}</div>"
                    f"<div style='font-size:14px;color:#e8e6f0;line-height:1.6;'>{msg['content']}</div>"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )
            else:
                e = EMOTIONS.get(msg.get("emotion", "enthusiastic"), EMOTIONS["enthusiastic"])
                st.markdown(
                    f"<div class='msg-t'>"
                    f"<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;'>"
                    f"<div style='font-size:10px;color:#6b7280;'>Prof. Aura · {st.session_state.model_priority.title()}</div>"
                    f"<div style='display:inline-flex;align-items:center;gap:4px;"
                    f"background:{e['color']}18;border:1px solid {e['color']}30;"
                    f"border-radius:10px;padding:2px 9px;font-size:10px;color:{e['color']};'>"
                    f"{e['emoji']} {e['mood']}</div></div>"
                    f"<div style='font-size:14px;color:#e8e6f0;line-height:1.7;'>"
                    + msg["content"].replace("\n", "<br>") +
                    f"</div></div>",
                    unsafe_allow_html=True,
                )

    # ── YouTube ──
    if st.session_state.yt_suggestions:
        st.markdown("---")
        st.markdown(
            "<div style='font-size:11px;color:#6b7280;letter-spacing:1px;"
            "text-transform:uppercase;margin-bottom:10px;'>📺 YOUTUBE — Watch & Learn More</div>",
            unsafe_allow_html=True,
        )
        yc = st.columns(min(len(st.session_state.yt_suggestions), 4))
        for col, vid in zip(yc, st.session_state.yt_suggestions):
            with col:
                url = f"https://youtube.com/watch?v={vid['vid']}"
                st.markdown(
                    f"<a href='{url}' target='_blank' style='text-decoration:none;'>"
                    f"<div style='background:rgba(17,17,30,0.9);border:1px solid rgba(255,0,0,0.2);"
                    f"border-radius:12px;padding:12px;cursor:pointer;transition:all .2s;'>"
                    f"<div style='font-size:20px;margin-bottom:6px;'>▶️</div>"
                    f"<div style='font-size:11px;font-weight:600;color:#e8e6f0;line-height:1.3;margin-bottom:4px;'>{vid['title'][:52]}</div>"
                    f"<div style='font-size:10px;color:#6b7280;'>{vid['channel']}</div>"
                    f"<div style='font-size:9px;color:#f43f5e;margin-top:4px;'>▶ Watch on YouTube</div>"
                    f"</div></a>",
                    unsafe_allow_html=True,
                )

    # ── HuggingFace Models + Courses ──────────────────────────────────────────
    if st.session_state.hf_suggestions or st.session_state.hf_course:
        st.markdown(
            "<div style='font-size:11px;color:#6b7280;letter-spacing:1px;"
            "text-transform:uppercase;margin:14px 0 10px;'>🤗 HUGGINGFACE — Models & Courses</div>",
            unsafe_allow_html=True,
        )
        hf_items = list(st.session_state.hf_suggestions or [])
        # Add course card if available
        course = st.session_state.hf_course
        hf_cols = st.columns(min(len(hf_items) + (1 if course else 0), 4))
        col_idx = 0
        # Course card first
        if course:
            with hf_cols[col_idx]:
                st.markdown(
                    f"<a href='{course['url']}' target='_blank' style='text-decoration:none;'>"
                    f"<div style='background:rgba(17,17,30,0.9);border:1px solid rgba(255,220,0,0.35);"
                    f"border-radius:12px;padding:12px;cursor:pointer;'>"
                    f"<div style='font-size:18px;margin-bottom:5px;'>🎓</div>"
                    f"<div style='font-size:9px;background:rgba(255,220,0,0.15);color:#fde047;"
                    f"border-radius:4px;padding:1px 6px;display:inline-block;margin-bottom:5px;font-weight:600;'>FREE COURSE</div>"
                    f"<div style='font-size:11px;font-weight:600;color:#e8e6f0;margin-bottom:3px;'>{course['name']}</div>"
                    f"<div style='font-size:10px;color:#6b7280;'>{course.get('desc','')}</div>"
                    f"<div style='font-size:9px;color:#fde047;margin-top:4px;'>→ Open free course</div>"
                    f"</div></a>",
                    unsafe_allow_html=True,
                )
            col_idx += 1
        # Model cards
        for model in hf_items[:3]:
            if col_idx < len(hf_cols):
                with hf_cols[col_idx]:
                    st.markdown(
                        f"<a href='{model['url']}' target='_blank' style='text-decoration:none;'>"
                        f"<div style='background:rgba(17,17,30,0.9);border:1px solid rgba(255,180,0,0.2);"
                        f"border-radius:12px;padding:12px;cursor:pointer;'>"
                        f"<div style='font-size:18px;margin-bottom:5px;'>🤗</div>"
                        f"<div style='font-size:9px;background:rgba(255,180,0,0.1);color:#f59e0b;"
                        f"border-radius:4px;padding:1px 6px;display:inline-block;margin-bottom:5px;font-weight:600;'>"
                        f"{model.get('task','Model')}</div>"
                        f"<div style='font-size:11px;font-weight:600;color:#e8e6f0;margin-bottom:2px;'>{model['name'][:28]}</div>"
                        f"<div style='font-size:10px;color:#6b7280;margin-bottom:2px;'>by {model['author']}</div>"
                        f"<div style='font-size:10px;color:#8880a8;'>{model.get('desc','')[:40]}</div>"
                        f"<div style='font-size:9px;color:#f59e0b;margin-top:4px;'>→ Open on HuggingFace</div>"
                        f"</div></a>",
                        unsafe_allow_html=True,
                    )
                col_idx += 1


# ─── MAIN ────────────────────────────────────────────────────────────────────
def main():
    render_sidebar()
    t1, t2, t3 = st.tabs(["💬 Learn with Prof. Aura", "📊 Analytics Dashboard", "⚠️ Risk Detector"])
    with t1: render_learn()
    with t2: render_dashboard()
    with t3: render_risk()


if __name__ == "__main__":
    main()
