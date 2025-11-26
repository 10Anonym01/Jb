# === ИМПОРТЫ ===
import os
import re
from flask_cors import CORS
import google.generativeai as genai
import requests
from datetime import datetime
from sympy import sympify
from deep_translator import GoogleTranslator
from langdetect import detect
from flask import Flask, request, jsonify

# === FLASK ===
app = Flask(__name__)
CORS(app)

# === GEMINI ===
genai.configure(api_key="AIzaSyC85prT5UV_9rmdNvup6E_sO8mb2TBPuC4")
model = genai.GenerativeModel("gemini-1.5-pro")

# === ЯЗЫК ===
def detect_language(text):
    try:
        lang = detect(text)
        return 'ru' if lang.startswith('ru') else 'en'
    except:
        return 'en'

# === ПЕРЕВОД ===
def translate(text, target_lang):
    try:
        if target_lang == 'ru':
            return GoogleTranslator(source='en', target='ru').translate(text)
        elif target_lang == 'en':
            return GoogleTranslator(source='ru', target='en').translate(text)
        else:
            return text
    except:
        return text

# === ПОГОДА ===
def extract_city(text):
    match = re.search(r"(в|in)\s+([a-zA-Zа-яА-ЯёЁ\- ]+)", text)
    return match.group(2).strip() if match else text.split()[-1]

def get_weather(command, lang='en'):
    try:
        api_key = "9c12f42c7f94de5fff10ac8b877b10b1"
        city = extract_city(command)
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang={lang}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            desc = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            return f"{desc.capitalize()}, {temp}°C"
        return "Город не найден." if lang == 'ru' else "City not found."
    except:
        return "Ошибка при получении погоды." if lang == 'ru' else "Error fetching weather."

# === ВРЕМЯ ===
def get_time(command):
    try:
        city = extract_city(command)
        response = requests.get("https://worldtimeapi.org/api/timezone")
        zones = response.json()
        for zone in zones:
            if city.lower() in zone.lower().split("/")[-1].lower():
                time_data = requests.get(f"https://worldtimeapi.org/api/timezone/{zone}").json()
                dt = datetime.fromisoformat(time_data["datetime"])
                return dt.strftime("%Y-%m-%d %H:%M:%S")
        return "Не удалось найти часовой пояс."
    except:
        return "Ошибка при получении времени."

# === МАТЕМАТИКА ===
def calculate_expression(expr):
    try:
        result = sympify(expr).evalf()
        return f"Результат: {result}"
    except:
        return "Неверное выражение."

# === GEMINI ===
def chat_with_gemini(prompt, lang='en'):
    try:
        response = model.generate_content(prompt)
        content = response.text.strip()
        if lang == 'ru' and detect(content) != 'ru':
            return translate(content, 'ru')
        return content
    except Exception as e:
        return f"Ошибка Gemini: {e}"

# === ОБРАБОТКА КОМАНД ===
def process_command(command):
    lang = detect_language(command)
    cmd = command.lower()
    if "погода" in cmd or "weather" in cmd:
        return get_weather(command, lang)
    elif "время" in cmd or "time" in cmd:
        return get_time(command)
    elif any(op in cmd for op in ["+", "-", "*", "/", "^"]):
        return calculate_expression(command)
    else:
        return chat_with_gemini(command, lang)

# === СЕРВЕР ===
@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    query = data.get("query", "")
    print(">>> Запрос:", query)
    answer = process_command(query)
    return jsonify({"answer": answer})

# === ЗАПУСК ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
