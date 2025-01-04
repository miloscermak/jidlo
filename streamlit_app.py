import streamlit as st
import anthropic
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

# Inicializace Anthropic klienta
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

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

            Svou odpověď napiš v následujícím formátu:

            <odpoved>
            <nazev_jidla>
            [Zde uveď navržený název jídla v češtině]
            </nazev_jidla>

            <kaloricka_hodnota>
            [Zde uveď odhadovanou kalorickou hodnotu jídla v češtině, včetně zdůvodnění svého odhadu]
            </kaloricka_hodnota>
            </odpoved>"""

            try:
                message = client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=1000,
                    messages=[{
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
                    }]
                )
                
                # Zobrazení výsledku
                st.success("Analýza dokončena!")
                st.write(message.content[0].text)
                
            except Exception as e:
                st.error(f"Došlo k chybě při analýze: {str(e)}") 