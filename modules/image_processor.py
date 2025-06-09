import random
from PIL import Image
import requests
import io
import base64
import os
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_VISION_API_KEY")

API_CONFIG = {
    "sd": {
        "url": "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
        "headers": {"Authorization": f"Bearer {HF_TOKEN}"}
    }
}

def image_to_text_google_vision(image: Image.Image) -> dict:
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    image_base64 = base64.b64encode(buffered.getvalue()).decode()

    url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_API_KEY}"
    body = {
        "requests": [
            {
                "image": {"content": image_base64},
                "features": [
                    {"type": "LABEL_DETECTION"},
                    {"type": "OBJECT_LOCALIZATION"},
                    {"type": "IMAGE_PROPERTIES"},
                    {"type": "TEXT_DETECTION"},
                ]
            }
        ]
    }

    response = requests.post(url, json=body)
    response.raise_for_status()
    data = response.json()["responses"][0]

    def extract_box(vertices):
        return [(v.get("x", 0), v.get("y", 0)) for v in vertices]

    return {
        "objects": [
            {
                "name": obj["name"],
                "score": obj["score"],
                "box": extract_box(obj["boundingPoly"]["normalizedVertices"])
            }
            for obj in data.get("localizedObjectAnnotations", [])
        ],
        "labels": [
            {"description": label["description"], "score": label["score"]}
            for label in data.get("labelAnnotations", [])
        ],
        "colors": [
            {
                "r": c["color"].get("red", 0),
                "g": c["color"].get("green", 0),
                "b": c["color"].get("blue", 0),
                "fraction": c["pixelFraction"]
            }
            for c in data.get("imagePropertiesAnnotation", {}).get("dominantColors", {}).get("colors", [])
        ],
        "text": [
            {
                "text": text["description"],
                "box": extract_box(text["boundingPoly"]["vertices"])
            }
            for text in data.get("textAnnotations", [])[1:]
        ] if data.get("textAnnotations") else []
    }

def generate_powerful_prompt(image_analysis: dict, user_prompt: str) -> str:
    objects_desc = []
    for obj in sorted(image_analysis["objects"], key=lambda x: -x["score"])[:3]:
        box = obj["box"]
        objects_desc.append(f"{obj['name']} at {box}")

    top_color = image_analysis["colors"][0] if image_analysis["colors"] else {"r": 0, "g": 0, "b": 0}
    rgb_str = f"RGB({int(top_color['r'])}, {int(top_color['g'])}, {int(top_color['b'])})"

    style_enhancements = {
        "warm lighting": "golden hour, cozy tones",
        "cold lighting": "cool lighting, icy palette",
        "modern": "sleek, clean lines, minimalist",
        "vintage": "nostalgic, retro furniture, soft shadows"
    }
    enhanced_style = next((v for k, v in style_enhancements.items() if k in user_prompt.lower()), "")

    text_desc = [f'Text "{t["text"]}" at {t["box"]}' for t in image_analysis["text"][:2]]

    prompt_lines = [
        "Interior render of a real room.",
        "Preserve all structural elements: walls, ceiling, flooring, lighting, and windows.",
        "Do not remove existing elements like furniture, shelves, plants, or décor.",
        "Keep the existing layout and perspective intact.",
        "Add only the necessary furniture, colors, and decorations matching the requested style.",
        f"Style to apply: {user_prompt}. {enhanced_style}",
        f"Scene includes: {', '.join(objects_desc)}." if objects_desc else "",
        f"Text elements: {'; '.join(text_desc)}" if text_desc else "",
        f"Color reference: {rgb_str}",
        "Do not introduce empty spaces or large blank walls.",
        "Do not alter the room's lighting setup or geometry.",
        "Render at ultra high resolution with natural light, realistic materials, soft shadows.",
    ]

    negative_prompt = (
        "blurry, deformed, low quality, empty room, white walls, low realism, bad lighting, "
        "wrong proportions, missing objects, flat textures, simplified geometry"
    )

    return (
        f"{' '.join(filter(None, prompt_lines))}\n"
        f"Negative prompt: {negative_prompt}\n"
        "Steps: 50, Sampler: DPM++ 2M Karras, CFG scale: 7.5, Size: 1024x1024"
    )

def generate_high_quality_image(image: Image.Image, style_description: str) -> Image.Image:
    try:
        width, height = (image.width // 16) * 16, (image.height // 16) * 16
        if (width, height) != (image.width, image.height):
            image = image.resize((width, height))

        prompt = generate_powerful_prompt(
            image_analysis=image_to_text_google_vision(image),
            user_prompt=style_description
        )

        payload = {
            "inputs": prompt,
            "parameters": {
                "negative_prompt": prompt.split("\n")[1].replace("Negative prompt: ", ""),
                "width": width,
                "height": height,
                "num_inference_steps": 60,
                "guidance_scale": 8.0,
                "seed": random.randint(0,99999),
            }
        }

        response = requests.post(
            API_CONFIG["sd"]["url"],
            headers=API_CONFIG["sd"]["headers"],
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        return Image.open(io.BytesIO(response.content))

    except Exception as e:
        print(f"Generation failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"API response: {e.response.text}")
        raise