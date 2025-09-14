# 🏡 Interior Design Assistant:

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Framework-Streamlit-ff4b4b)
![Groq](https://img.shields.io/badge/AI-Groq%20LLaMA%204-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

An AI-powered interior design web application built with **Streamlit**.  
Users can upload room images, apply redesign prompts, and chat with an assistant for real-time suggestions.  
Powered by **Groq’s LLaMA 4 API** and enhanced with a custom floating chatbot UI.

## 🚀 Steps to Run:

1. **Clone the repository**  
   ```bash
   git clone https://github.com/HridikDev/Xynapse_Interior-Design-AI
   cd interior-design-app
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
3. **Run the app**
   ```bash
   streamlit run app.py

## 📂 Project Structure:

```bash
interior-design-app/
│
├── app.py                # Main Streamlit app
├── requirements.txt      # Dependencies
├── assets/               # Static files (icons, styles)
├── utils/                # Helper functions (image processing, chat handling)
├── .env                  # Example environment file
├── README.md             # Documentation
```

## ✨ Features:

🖼️ Upload and redesign room images with AI style prompts

🎨 Before/After slider for visual comparison

💬 Floating chatbot with Groq-powered LLaMA 4 model

🖥️ Clean, modern UI with auto-scroll and closeable sidebar chat

🔒 Secure API key management using .env file

## 🛠️Technologies Used:

Python 3.9+

Streamlit for frontend & app framework

Groq API (LLaMA 4 Scout model) for AI responses

PIL (Pillow) for image processing

HTML/CSS for custom UI styling


