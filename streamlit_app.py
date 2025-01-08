import streamlit as st
import requests
import base64
import os
from dotenv import load_dotenv
from PIL import Image
from pillow_heif import register_heif_opener
import io

# Načtení proměnných prostředí
load_dotenv()

# Získání API klíče buď z .env nebo ze Streamlit secrets
API_KEY = st.secrets["ANTHROPIC_API_KEY"] if "ANTHROPIC_API_KEY" in st.secrets else os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    st.error("Není nastaven API klíč pro Anthropic Claude")
    st.stop()

API_URL = "https://api.anthropic.com/v1/messages"

# Registrace HEIF/HEIC handleru
register_heif_opener()

# Konfigurace stránky
st.set_page_config(
    page_title="Analyzátor jídla",
    layout="centered"
)

# Nadpis
st.title("Co máš na talíři?")

# Upload souboru
uploaded_file = st.file_uploader("Nahrajte fotografii", type=['jpg', 'jpeg', 'png', 'heic', 'HEIC'])

def process_image(uploaded_file):
    """Funkce pro zpracování různých formátů obrázků"""
    try:
        if uploaded_file.type in ['image/heic', 'image/heif']:
            # Načtení HEIC souboru
            temp_bytes = uploaded_file.getvalue()
            image = Image.open(io.BytesIO(temp_bytes))
        else:
            image = Image.open(uploaded_file)

        # Kontrola a aplikace orientace z EXIF
        try:
            if hasattr(image, '_getexif'):
                exif = image._getexif()
                if exif is not None:
                    orientation = exif.get(274)  # 274 je tag pro orientaci
                    if orientation is not None:
                        # Rotace podle EXIF orientace
                        if orientation == 3:
                            image = image.rotate(180, expand=True)
                        elif orientation == 6:
                            image = image.rotate(270, expand=True)
                        elif orientation == 8:
                            image = image.rotate(90, expand=True)

        except Exception as e:
            st.warning(f"Nelze určit orientaci obrázku: {str(e)}")

        # Konverze do JPEG pro další zpracování
        with io.BytesIO() as bio:
            # Zachování EXIF dat při ukládání
            if 'exif' in image.info:
                image.save(bio, format='JPEG', exif=image.info['exif'])
            else:
                image.save(bio, format='JPEG')
            return bio.getvalue()

    except Exception as e:
        st.error(f"Chyba při zpracování obrázku: {str(e)}")
        return None

if uploaded_file is not None:
    try:
        # Zpracování obrázku
        image_data = process_image(uploaded_file)
        
        # Zobrazení náhledu
        image = Image.open(io.BytesIO(image_data))
        st.image(image, caption="Náhled obrázku", use_container_width=True)
        
        # Odstraníme všechny debugovací výpisy
        
        # Tlačítko pro analýzu
        if st.button("Chci si přečíst popisek"):
            with st.spinner('Probíhá analýza...'):
                base64_image = base64.b64encode(image_data).decode("utf-8")
                
                prompt = """Here is the food image you need to analyze:

<food_image>
{{IMAGE}}
</food_image>

Please examine the image carefully, paying close attention to the following aspects:
- Visible ingredients
- Preparation method
- Portion size
- Overall appearance and presentation

Based on your observations, complete the following tasks:

1. Suggest an appropriate name for the dish in Czech.
2. Estimate the approximate caloric value of the depicted meal.
3. Provide basic information about the dish.
4. List potential health benefits associated with consuming this meal.
5. Identify any potential health risks or concerns related to this dish.

Before providing your final output, wrap your analysis inside <image_analysis> tags. In your analysis, include the following steps:

1. List all visible ingredients, prepending each with a number (e.g., 1. Tomatoes, 2. Lettuce, etc.).
2. Describe the likely preparation methods used for the dish.
3. Estimate the portion size, considering standard serving sizes.
4. Note any notable nutritional aspects (e.g., high protein, low fat, etc.) based on the visible ingredients.
5. Estimate the nutritional content (protein, carbs, fats) based on the visible ingredients.
6. Consider potential health benefits associated with the ingredients or preparation method.
7. Identify any potential health risks (e.g., high sodium, excessive calories, allergens).
8. Think about the cultural context and Czech cuisine to suggest an appropriate name for the dish.

After your analysis, provide your final output in the following format:

Název jídla:
[Suggested name for the dish in Czech]

Kalorická hodnota:
[Estimated caloric value of the meal in Czech, including a brief explanation of your estimate]

Poznámky:
[Basic information about the dish]

Zdravotní přínosy:
[List of potential health benefits associated with the meal]

Možná zdravotní rizika:
[List of potential health risks or concerns related to the dish]

Please ensure that your response is in Czech and provides comprehensive, well-reasoned information based on your analysis of the image.
"""

                try:
                    headers = {
                        "x-api-key": API_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    }

                    data = {
                        "model": "claude-3-5-sonnet-20241022",
                        "max_tokens": 5000,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": prompt
                                    },
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": uploaded_file.type if not uploaded_file.type.startswith('image/heic') else "image/jpeg",
                                            "data": base64_image
                                        }
                                    }
                                ]
                            }
                        ]
                    }

                    response = requests.post(API_URL, headers=headers, json=data)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success("Analýza dokončena!")
                        st.write(result['content'][0]['text'])
                    else:
                        st.error(f"Chyba API: {response.status_code} - {response.text}")
                    
                except Exception as e:
                    st.error(f"Došlo k chybě při analýze: {str(e)}")

    except Exception as e:
        st.error(f"Chyba při zpracování obrázku: {str(e)}")
