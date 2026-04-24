!pip install streamlit vaderSentiment textblob plotly pyngrok --quiet
!python -m textblob.download_corpora

APP_CODE = '''
import streamlit as st
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
import plotly.graph_objects as go
import re

# ── Page config ─────────────────────────────────────────────
st.set_page_config(page_title="Sentiment Analyzer", layout="centered")

# ── Emotion keyword dictionary (replaces NRCLex) ────────────
EMOTION_WORDS = {
    "joy":      ["happy","happiness","joy","love","wonderful","great","amazing","enjoy",
                 "delight","cheerful","glad","pleased","excited","fantastic","excellent","bliss",
                 "jubilee", "zest", "radiant", "triumph", "feast", "harmony", "playful", "sunbeam",
                  "whimsical", "heartfelt",
                  "thrive", "windfall", "oasis", "celebrate", "elated", "jubilant", "lighthearted",
                  "prosperous", "content", "blessed", "cheer", "jovial", "rapture", "serene", "vibrant",
                   "euphoria", "rejoice", "optimum", "paradise"],
    "anger":    ["angry","hate","rage","furious","annoyed","mad","outrage","hostile",
                 "irritated","aggressive","bitter","disgusted","resentment", "animosity", "indignation", "venom", "provoke",
                  "feud", "revolt", "spike",
                  "clash", "fierce", "bitter", "burning", "inferno", "grapple", "seethe", "fury", "wrath",
                 "outraged", "hostility", "vengeful", "agitated",
                  "belligerent", "hateful", "vicious", "explosive", "ire", "spite", "tempest",
                  "ferocity", "offended"],
    "fear":     ["afraid","scared","fear","terrified","anxious","worried","nervous",
                 "panic","dread","frightened","uneasy","horror","trepidation", "peril",
                  "haunt", "suspicion", "quiver", "phantom", "looming", "fragile",
                   "precarious", "nightmare", "shudder", "wary", "chilling", "abyss", "terror",
                 "menacing", "panic", "dread", "horror", "startled", "unsafe", "intimidated",
                  "cowardly", "vulnerable", "fright", "hysteria", "distress", "alarmed"],
    "sadness":  ["sad","cry","depressed","unhappy","miserable","sorrow","grief",
                 "heartbroken","disappointed","gloomy","hopeless","lonely","melancholy",
                  "bleak", "yearning", "desolate", "ache", "weary", "hollow", "vanished",
                   "wilt", "burden", "shadow", "fragile", "debris", "tearful", "orphan",
                  "sorrow", "gloomy", "mournful", "misery", "heartache", "rejected",
                   "unhappy", "hopeless", "somber", "dejected", "lonely", "pitiful", "anguish"],
    "surprise": ["surprised","shocked","astonished","unexpected","amazing","sudden",
                 "wow","unbelievable","incredible","startled","bolt", "flicker", "anomaly",
                  "startling", "jolt", "revelation", "out-of-the-blue", "marvel", "quirk",
                   "epiphany", "abrupt", "curious", "staggering", "shocker",
                  "unexpected", "astonished", "bewildered", "astounded", "miracle",
                   "unforeseen", "startle", "spectacular", "jarring", "unusual", "stunning"],
    "trust":    ["trust","reliable","honest","safe","secure","faithful","confident",
                 "believe","certain","dependable","loyal","advocacy", "alliance", "anchor", "backbone", "certitude",
                  "kinship", "mentor", "pact", "stewardship", "unwavering", "verify", "sanctuary", "principled", "guaranty",
                   "integrity", "confidant", "devoted",
                  "authentic", "stable", "honorable", "ethical", "solidarity", "dependable",
                   "legit", "truthful", "custody", "conviction"],
    "disgust":  ["disgusting","gross","revolting","nasty","awful","terrible","horrible",
                 "yuck","repulsive","offensive","vile","loathing", "slimy", "foul",
                  "rancid", "stagnant", "putrid", "nauseous", "sickly", "contaminated",
                   "cringe", "tainted", "warped", "grotty", "repulsive", "vile",
                  "revolting", "abhorrent", "gross", "distasteful", "repelled",
                  "shameful", "obscene", "rank", "loathsome", "stinking", "scummy", "offensive"],
}

INTENSITY_WORDS = ["very","extremely","absolutely","incredibly","super","really",
                   "totally","utterly","highly","deeply","massively"]

# ── Core analysis functions ──────────────────────────────────
analyzer = SentimentIntensityAnalyzer()

def get_sentiment(text):
    """Returns VADER scores: compound, pos, neg, neu"""
    return analyzer.polarity_scores(text)

def get_emotions(text):
    """Count emotion words in text and return frequencies"""
    words = re.findall(r"\\b\\w+\\b", text.lower())
    scores = {}
    for emotion, keywords in EMOTION_WORDS.items():
        count = sum(1 for w in words if w in keywords)
        scores[emotion] = count
    return scores

def get_word_weights(text):
    """Get per-word VADER scores for the Details expander"""
    words = text.split()
    weights = {}
    for word in words:
        clean = re.sub(r"[^a-zA-Z]", "", word).lower()
        if clean and clean in analyzer.lexicon:
            weights[clean] = round(analyzer.lexicon[clean], 2)
    return weights

def get_intensity_highlights(text):
    """Return HTML with intensity words highlighted"""
    words = text.split()
    result = []
    for word in words:
        clean = re.sub(r"[^a-zA-Z]", "", word).lower()
        if clean in INTENSITY_WORDS or word.count("!") >= 2:
            result.append(f'<mark style="background:#FFD700;padding:1px 3px;border-radius:3px">{word}</mark>')
        else:
            result.append(word)
    return " ".join(result)

def get_header_color(compound):
    """Return color based on compound score"""
    if compound >= 0.5:
        return "#2ecc71", "😊 Positive Sentiment"
    elif compound <= -0.5:
        return "#e74c3c", "😠 Negative Sentiment"
    else:
        return "#95a5a6", "😐 Neutral Sentiment"

# ── UI Layout ────────────────────────────────────────────────
st.title("🧠 Sentiment Analysis Dashboard")
st.markdown("Type anything below and watch the analysis update live.")

text = st.text_area("Enter your text here:", height=150,
                    placeholder="e.g. The food was not bad at all! I absolutely loved it.")

if text.strip():
    # Run analysis
    sentiment  = get_sentiment(text)
    emotions   = get_emotions(text)
    compound   = sentiment["compound"]
    blob       = TextBlob(text)

    # ── Dynamic color header ─────────────────────────────────
    color, label = get_header_color(compound)
    st.markdown(
        f"""<div style="background:{color};color:white;padding:14px 20px;
        border-radius:10px;font-size:18px;font-weight:600;margin-bottom:16px">
        {label} &nbsp; | &nbsp; Score: {compound:+.3f}</div>""",
        unsafe_allow_html=True
    )

    # ── Metrics row ──────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Compound",    f"{compound:+.3f}")
    col2.metric("Positive",    f"{sentiment['pos']:.2f}")
    col3.metric("Negative",    f"{sentiment['neg']:.2f}")
    col4.metric("Subjectivity",f"{blob.sentiment.subjectivity:.2f}")

    st.markdown("---")

    # ── Radar (Spider) Chart ─────────────────────────────────
    emotion_labels = list(emotions.keys())
    emotion_values = list(emotions.values())
    emotion_values_closed = emotion_values + [emotion_values[0]]
    emotion_labels_closed = emotion_labels + [emotion_labels[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=emotion_values_closed,
        theta=emotion_labels_closed,
        fill="toself",
        fillcolor="rgba(100, 149, 237, 0.3)",
        line=dict(color="cornflowerblue", width=2),
        name="Emotions"
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, max(max(emotion_values), 1)])),
        showlegend=False,
        title="Emotion Radar",
        height=400,
        margin=dict(t=50, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Intensity Highlights ─────────────────────────────────
    st.markdown("**Intensity word highlights:**")
    highlighted = get_intensity_highlights(text)
    st.markdown(
        f'<div style="background:var(--secondary-background-color);padding:10px;'
        f'border-radius:8px;line-height:1.8">{highlighted}</div>',
        unsafe_allow_html=True
    )

    # ── Explainable AI — Details Expander ────────────────────
    with st.expander("🔍 Why did the AI give this score? (Word Weights)"):
        weights = get_word_weights(text)
        if weights:
            st.markdown("Words found in the VADER sentiment lexicon:")
            for word, score in sorted(weights.items(), key=lambda x: abs(x[1]), reverse=True):
                bar_color = "#2ecc71" if score > 0 else "#e74c3c"
                width_pct  = min(abs(score) / 4 * 100, 100)
                st.markdown(
                    f"""<div style="display:flex;align-items:center;gap:10px;margin:4px 0">
                    <span style="width:80px;font-weight:600">{word}</span>
                    <div style="background:{bar_color};width:{width_pct}%;height:14px;
                    border-radius:4px"></div>
                    <span style="color:{bar_color};font-weight:600">{score:+.2f}</span>
                    </div>""",
                    unsafe_allow_html=True
                )
        else:
            st.info("No scored words found in this text. Try words like 'love', 'hate', 'good', 'terrible'.")

        st.markdown("---")
        st.markdown(f"**TextBlob Polarity:** `{blob.sentiment.polarity:.3f}`")
        st.markdown(f"**TextBlob Subjectivity:** `{blob.sentiment.subjectivity:.3f}` (0=objective, 1=subjective)")

else:
    st.info("👆 Start typing in the box above to see the live analysis.")
    st.markdown("""
    **Try these test sentences:**
    - `The food was not bad at all!` — tests double negative handling
    - `I absolutely love this! It\'s incredibly amazing!!!` — tests intensity
    - `I am so angry and disgusted by this terrible service` — tests negative emotions
    """)
'''

# Write the app file
with open("app.py", "w") as f:
    f.write(APP_CODE)

print("✅ app.py created successfully!")

# , add your token, then run
import subprocess, time
from pyngrok import ngrok

from google.colab import userdata
from pyngrok import ngrok

NGROK_TOKEN = userdata.get("NGROK_TOKEN")

ngrok.set_auth_token(NGROK_TOKEN)

# 2. Start Streamlit in the background
proc = subprocess.Popen(
    ["streamlit", "run", "app.py", "--server.port=8501", "--server.headless=true"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

# 3. Wait for Streamlit to boot, then open tunnel
time.sleep(4)
public_url = ngrok.connect(8501)
print("=" * 50)
print(f"  🚀 Your Dashboard is LIVE at:")
print(f"  {public_url}")
print("=" * 50)
print("Share this URL with anyone. Keep this cell running.")
