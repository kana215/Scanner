import streamlit as st
from openai import OpenAI
from PIL import Image
import base64
import io
import json
import os  
import streamlit as st

# Получаем ключ из Secrets
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# Инициализация клиента OpenAI (оставляем)
client = OpenAI(api_key=OPENAI_API_KEY)
st.set_page_config(page_title="OCR 2.0", layout="wide")
st.title("OCR 2.0 Scanner для банковских документов")
st.write("Загрузите или Перетащите фото и получите JSON с ключевыми полями.")

def resize_image(image: Image.Image, max_width=1024):
    w, h = image.size
    if w > max_width:
        ratio = max_width / w
        new_size = (int(w * ratio), int(h * ratio))
        image = image.resize(new_size, Image.LANCZOS)
    return image

def encode_image(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def gpt4mini_ocr(image: Image.Image):
    img_b64 = encode_image(image)
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "Ты OCR-система. Верни строго JSON с ключами: date, address, amount."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Извлеки дату, адрес и сумму из документа:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                ]
            }
        ]
    )
    return response.choices[0].message.content

uploaded_file = st.file_uploader(
    "Загрузите или Перетащите документ",
    type=["png", "jpg", "jpeg"]
)

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Загруженный документ", use_container_width=True)

    if st.button("Извлечь поля"):
        with st.spinner("Выполняется Scan OCR..."):
            try:
                result_text = gpt4mini_ocr(resize_image(image, max_width=1024))

                try:
                    json_output = json.loads(result_text)
                    result_str = json.dumps(json_output, ensure_ascii=False, indent=2)
                except:
                    result_str = result_text.strip()

                st.session_state["ocr_result"] = result_str

            except Exception as e:
                st.error(f"Ошибка при OCR: {e}")

if "ocr_result" in st.session_state:
    result_str = st.session_state["ocr_result"]

    st.subheader("Результат сканирования")
    st.code(result_str, language="json")

    col1, col2 = st.columns(2)


    with col2:
        st.download_button(
            label="💾 Скачать JSON",
            data=result_str,
            file_name="ocr_result.json",
            mime="application/json"
        )





