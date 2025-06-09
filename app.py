import os
import requests
import streamlit as st
import tempfile
from dotenv import load_dotenv
from PIL import Image
import base64
from io import BytesIO
from modules.image_processor import generate_high_quality_image
from modules.product_search import fetch_products

# ─── Initialize session_state keys ──────────────────────────────────────────
if "chat_open" not in st.session_state:
    st.session_state.chat_open = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "chat_input" not in st.session_state:
    st.session_state.chat_input = ""

# ─── Load .env ───────────────────────────────────────────────────────────────
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if GROQ_API_KEY is None:
    st.error("🔑 GROQ_API_KEY not found in .env. Please add it before running.")
    st.stop()
API_KEY = os.getenv("GOOGLE_VISION_API_KEY")
if API_KEY is None:
    st.error("🔑 GOOGLE_VISION_API_KEY not found in .env. Please add it before running.")
    st.stop()


# ─── Background and header styling ───────────────────────────────────────────
st.markdown("""
    <style>
    .reportview-container {
        background: url("https://i.imgur.com/3R2gX7A.jpg") no-repeat center center fixed;
        background-size: cover;
    }
    h1, h3 { color: #DA4D7F; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# ─── App Title ───────────────────────────────────────────────────────────────
st.markdown("<h1>✨ SpaceLogic</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#777;'>Upload your room image and describe your ideal style.<br>We’ll redesign your space and recommend decor items.</p>", unsafe_allow_html=True)

# ─── Upload + Prompt ─────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 1])
with col1:
    uploaded_image = st.file_uploader("📷 Upload Room Image", type=["png", "jpg", "jpeg"])
with col2:
    style_prompt = st.text_input("🎨 Describe Your Desired Style", placeholder="e.g. Natural tones, Scandinavian simplicity...")

# ─── Trending Styles ─────────────────────────────────────────────────────────
st.markdown("### ✨ Need Inspiration? Try a Trending Style:")
for style in ["Scandinavian Minimalism", "Boho Chic", "Modern Farmhouse", "Japandi", "Industrial Loft", "Mid-century Modern", "Contemporary Luxe"]:
    st.markdown(f"- {style}")

# ─── Image Processing ─────────────────────────────────────────────────────────
def to_base64(img):
    buff = BytesIO()
    img.save(buff, format="PNG")
    return base64.b64encode(buff.getvalue()).decode()

def save_image(image):
    path = "RedesignedRoom.png"
    image.save(path)
    return path

def detect_labels(img: Image.Image):
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp:
        img.save(temp.name)
        with open(temp.name, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

    url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
    payload = {
        "requests": [{
            "image": {"content": encoded_image},
            "features": [{"type": "LABEL_DETECTION", "maxResults": 10}]
        }]
    }

    response = requests.post(url, json=payload)
    result = response.json()

    if "responses" not in result:
        st.error(f"Google Vision API error: Missing 'responses' key.\nFull response: {result}")
        return []

    if not result["responses"]:
        st.error(f"Google Vision API error: Empty 'responses' list.\nFull response: {result}")
        return []

    response0 = result["responses"][0]
    if "error" in response0:
        err = response0["error"]
        st.error(f"Google Vision API error: {err.get('message', str(err))}")
        return []

    labels = [annotation["description"] for annotation in response0.get("labelAnnotations", [])]
    return labels


if st.button("✨ Generate Redesign"):
    if uploaded_image and style_prompt:
        if "orig_img" not in st.session_state:
            st.session_state.orig_img = Image.open(uploaded_image).convert("RGB")
        if "stylized_img" not in st.session_state or st.session_state.get("last_prompt") != style_prompt:
            st.session_state.stylized_img = generate_high_quality_image(st.session_state.orig_img, style_prompt)
            st.session_state.last_prompt = style_prompt

        orig_img = st.session_state.orig_img
        stylized_img = st.session_state.stylized_img

        before_b64 = to_base64(orig_img)
        after_b64 = to_base64(stylized_img)

        st.markdown("### 🔄 Before & After Slider")
        st.components.v1.html(f"""
            <div style='position:relative;max-width:900px;margin:auto;'>
                <input type='range' min='0' max='100' value='50' style='width:100%;height:8px;appearance:none;background:linear-gradient(to right,#DA4D7F 0%,#5A47C2 100%);border-radius:5px;margin-bottom:15px;' oninput='document.getElementById("sliderImg2").style.clipPath = "inset(0 " + (100-this.value) + "% 0 0)"' />
                <div style='position:relative;overflow:hidden;'>
                    <img src='data:image/png;base64,{before_b64}' style='width:100%;display:block;' />
                    <img id='sliderImg2' src='data:image/png;base64,{after_b64}' style='width:100%;position:absolute;top:0;left:0;clip-path:inset(0 50% 0 0);transition:clip-path 0.1s;' />
                </div>
            </div>
        """, height=500)

        st.markdown("### 🛋 Recommended Products")
        before_labels = set(detect_labels(orig_img))
        after_labels = set(detect_labels(stylized_img))
        room_keywords = {
            "wall", "floor", "ceiling", "room", "house", "lighting", "wood", "window",
            "interior design", "home", "architecture", "tile", "fixture",
            "living room", "dining room", "bedroom", "kitchen", "bathroom",
            "hallway", "office", "study", "closet", "garage", "laundry room"
        }

        new_items = [
            label for label in after_labels - before_labels
            if not any(room in label.lower() for room in room_keywords)
        ]
        if new_items:
            st.success("Newly added items: " + ", ".join(new_items))
            for item in new_items:
                products = fetch_products(item)
                for p in products:
                    st.markdown(f"- *{item}* → [{p['name']}]({p['url']})")
        else:
            st.info("No new relevant items detected.")

        # Save once and read to memory to prevent rerun side effects
        output_path = save_image(stylized_img)
        with open(output_path, "rb") as f:
            image_bytes = f.read()

        st.download_button(
            label="⬇ Download Redesigned Image",
            data=image_bytes,
            file_name="RedesignedRoom.png",
            mime="image/png"
        )
    else:
        st.warning("Please upload an image and enter a style description.")

# ─── Chat Assistant Toggle ────────────────────────────────────────────────────
st.markdown("")
if st.button("💬 Chat with Assistant"):
    st.session_state.chat_open = True

def chat_with_groq(user_message, history):
    """
    Sends the full conversation (history + new user message) to Groq’s
    chat completions endpoint using the Llama 4 Scout model, returning the reply.
    """
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    # Build messages payload:
    messages = [
        {"role": "system", "content": "You are a helpful interior-design assistant."}
    ]
    for entry in history:
        messages.append({"role": entry["role"], "content": entry["content"]})
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 512,
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


# ─── Callback: When user presses Enter in chat_input ─────────────────────────
def submit_message():
    user_msg = st.session_state.chat_input.strip()
    if not user_msg:
        return  # ignore empty

    # Append user message
    st.session_state.chat_history.append({"role": "user", "content": user_msg})

    # Call Groq for assistant reply
    try:
        assistant_reply = chat_with_groq(
            user_msg, st.session_state.chat_history[:-1]
        )
    except Exception as e:
        assistant_reply = f"⚠ Error contacting Groq: {e}"

    # Append assistant reply
    st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})

    # Clear input
    st.session_state.chat_input = ""


# ─── CSS: Hide or Float Sidebar Based on chat_open ─────────────────────────
if st.session_state.chat_open:
    # When chat_open=True → show & float the sidebar as a bottom-right popup
    st.markdown(
        """
        <style>
        /* Hide the default sidebar toggle button */
        button[title="Toggle sidebar"] {
          visibility: hidden;
        }
        /* Reposition and restyle the sidebar itself */
        section[data-testid="stSidebar"] {
          position: fixed !important;
          top: auto !important;
          bottom: 20px !important;
          left: auto !important;
          right: 20px !important;
          width: 320px !important;
          height: 440px !important;
          padding: 10px !important;
          background-color: #ffffff !important;
          box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
          border-radius: 10px !important;
          overflow-y: auto !important;
          z-index: 1000 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    # When chat_open=False → completely hide the sidebar
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] {
          display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# ─── Chat Interface Inside Sidebar (now “floating”) ──────────────────────────
if st.session_state.chat_open:
    st.markdown("""
    <style>
    button[title="Toggle sidebar"] {
        display: none;
    }
    section[data-testid="stSidebar"] {
        position: fixed !important;
        bottom: 20px !important;
        right: 20px !important;
        width: 360px !important;
        height: 500px !important;
        border-radius: 20px !important;
        background: rgba(255, 255, 255, 0.9) !important;
        backdrop-filter: blur(12px);
        box-shadow: 0 12px 28px rgba(0, 0, 0, 0.15);
        padding: 16px 20px !important;
        overflow: hidden;
        z-index: 1000;
        border: 1px solid rgba(200,200,200,0.3);
    }

    .chat-wrapper {
        display: flex;
        flex-direction: column;
        height: 100%;
    }

    .chat-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-weight: 600;
        font-size: 17px;
        color: #333;
        margin-bottom: 10px;
    }

    .chat-scroll {
        flex-grow: 1;
        overflow-y: auto;
        padding-right: 5px;
        margin-bottom: 12px;
        scroll-behavior: smooth;
    }

    .chat-bubble {
        padding: 10px 14px;
        border-radius: 14px;
        margin: 6px 0;
        max-width: 85%;
        font-size: 14px;
        word-wrap: break-word;
        display: inline-block;
        line-height: 1.4;
        animation: fadeIn 0.3s ease-in;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
    }

    .chat-user {
        background-color: #dceeff;
        color: #1a73e8;
        margin-left: auto;
        text-align: right;
    }

    .chat-assistant {
        background-color: #f1f1f1;
        color: #222;
        margin-right: auto;
        text-align: left;
    }

    .chat-input-box input {
        border-radius: 8px;
        border: 1px solid #ccc;
        padding: 8px;
        width: 100%;
    }

    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-thumb {
        background-color: #ccc;
        border-radius: 3px;
    }

    @keyframes fadeIn {
        from {opacity: 0; transform: translateY(4px);}
        to {opacity: 1; transform: translateY(0);}
    }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:

        # Chat header with real Streamlit close button
        # Container for header with aligned title and close button
        header_cols = st.columns([9, 1])  # Wide for title, small for button

        with header_cols[0]:
            st.markdown('<span style="font-size:17px; font-weight:600; color:#333;">💬 Design Chatbot</span>',
                        unsafe_allow_html=True)

        with header_cols[1]:
            if st.button("✖", key="close_chat_btn", help="Close chat"):
                st.session_state.chat_open = False
                st.session_state.chat_input = ""
                # st.experimental_rerun()

        # Detect manual JS trigger
        if st.query_params.get("close_chat"):
            st.session_state.chat_open = False
            st.session_state.chat_input = ""

        # Scrollable messages
        st.markdown("<div class='chat-scroll' id='chat-scroll-box'>", unsafe_allow_html=True)
        for msg in st.session_state.chat_history:
            role_class = "chat-user" if msg["role"] == "user" else "chat-assistant"
            st.markdown(
                f"<div class='chat-bubble {role_class}'>{msg['content']}</div>",
                unsafe_allow_html=True
            )
        st.markdown("</div>", unsafe_allow_html=True)

        # Input
        st.markdown("<div class='chat-input-box'>", unsafe_allow_html=True)
        st.text_input(
            label="",
            placeholder="Type a message and press Enter…",
            key="chat_input",
            on_change=submit_message
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Auto-scroll JS
        st.markdown("""
        <script>
        const chatScroll = document.getElementById('chat-scroll-box');
        if (chatScroll) {
            chatScroll.scrollTop = chatScroll.scrollHeight;
        }
        </script>
        """, unsafe_allow_html=True)