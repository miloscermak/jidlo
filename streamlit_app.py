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
st.title("Co vidím?")

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
                
                prompt = """Prohlédni si pozorně následující fotografii jídla:
<image>
{{IMAGE}}
</image>
Pečlivě si prohlédni všechny detaily zobrazené na fotografii. Zaměř se na ingredience, způsob přípravy, velikost porce a celkový vzhled jídla.
Na základě svého pozorování proveď následující úkoly:
1. Navrhni vhodný název pro toto jídlo v češtině. Název by měl být výstižný a popisný.
2. Odhadni přibližnou kalorickou hodnotu zobrazeného jídla. Vezmi v úvahu viditelné ingredience, velikost porce a předpokládaný způsob přípravy.
3. Promysli si dané jídlo a napiš o něm základní informaci.
Svou odpověď napiš v následujícím formátu:
Název jídla:
[Zde uveď navržený název jídla v češtině]
Kalorická hodnota:
[Zde uveď odhadovanou kalorickou hodnotu jídla v češtině, včetně zdůvodnění svého odhadu]
Poznámky:
[Zde napiš vše, co o jídle víš]
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
