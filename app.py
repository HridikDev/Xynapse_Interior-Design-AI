import streamlit as st
from PIL import Image
from modules.image_processor import segment_room, generate_stylized_image
from modules.product_search import fetch_products

st.set_page_config(page_title="AI Interior Design Assistant", layout="wide")
st.title("🧠 AI-Powered Interior Design Assistant")
st.write("Upload your room photo and describe the style you want to see.")

# Sidebar inputs
st.sidebar.header("Step 1: Upload Room Photo")
image_file = st.sidebar.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])

st.sidebar.header("Step 2: Describe Your Desired Style")
style_prompt = st.sidebar.text_area("e.g., Scandinavian style with minimalist warm tones")

if image_file and style_prompt:
    image = Image.open(image_file).convert("RGB")
    st.subheader("📷 Original Room Image")
    st.image(image, use_column_width=True)

    with st.spinner("Applying style transformation..."):
        segmented = segment_room(image)
        stylized_image = generate_stylized_image(segmented, style_prompt)

    st.subheader("🎨 Redesigned Room")
    st.image(stylized_image, use_column_width=True)

    st.subheader("🛍️ Recommended Products")
    products = fetch_products(style_prompt)
    for product in products:
        st.markdown(f"- [{product['name']}]({product['url']})")

else:
    st.info("Upload a room image and describe your style to begin.")
