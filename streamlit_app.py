import streamlit as st
import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()

# Konfigurace stránky
st.set_page_config(
    page_title="Analyzátor jídla",
    layout="centered"
)

# Nadpis
st.title("Analyzátor jídla")

API_KEY = os.getenv("ANTHROPIC_API_KEY")
API_URL = "https://api.anthropic.com/v1/messages"

# Upload souboru
uploaded_file = st.file_uploader("Nahrajte fotografii jídla", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    # Zobrazení náhledu
    st.image(uploaded_file, caption="Náhled obrázku", use_column_width=True)
    
    # Tlačítko pro analýzu
    if st.button("Analyzovat"):
        with st.spinner('Probíhá analýza...'):
            # Načtení a zakódování obrázku do base64
            contents = uploaded_file.getvalue()
            base64_image = base64.b64encode(contents).decode("utf-8")
            
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
                                        "media_type": uploaded_file.type,
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