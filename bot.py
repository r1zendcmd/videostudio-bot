#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Универсальный Cloud Telegram Bot для VideoStudio (Render.com / 24/7):
Объединяет возможности скаута аномалий, @Foryteibot (генератор мультиков,
сюжетов, персонажей, промптов и серий) и @rakuobanner_bot (обработка видео, баннеры, FFmpeg).
"""

import os
import sys
import json
import time
import random
import datetime
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN", "9080755461:AAFRMzUQ2mznmAVznonkyJRVMy6pFSl6hlU").strip()
CHAT_ID = os.environ.get("CHAT_ID", "").strip()
TIMEZONE_OFFSET = int(os.environ.get("TIMEZONE_OFFSET", "7"))

class CartoonStoryEngine:
    THEMES = {
        "what_if": "А что, если?.. (Невозможная физика и странности)",
        "survival": "Выживание и Блэкаут (Город без ресурсов)",
        "cameras": "ГородОко и Слежка (Камеры наблюдения)",
        "anomalies": "Городские Аномалии (Лифты, двери, неизвестные этажи)"
    }

    CHARACTERS = {
        "max": "Макс (любопытный парень, студент, внимательный к деталям)",
        "hoodie": "Герой в синем худи (ночной житель, держится в тени)",
        "grandma": "Бабушка Валя (загадочный свидетель, хранит старые тайны)",
        "courier": "Ночной курьер (знает изнанку города и тайные маршруты)"
    }

    PLOTS_DATABASE = [
        {
            "theme": "what_if",
            "title": "Что если в банкоматах исчезнут все деньги за 1 час?",
            "hook": "В 14:00 терминалы перестали выдавать наличку. В 14:15 карты заблокировались во всей стране.",
            "character": "max",
            "length": "60",
            "hud": "ВРЕМЯ: 14:15 | БАЛАНС: 0 ₽ | НАЛИЧКА: 1 500 ₽ | РИСК: 45%",
            "steps": [
                "Макс пытается снять деньги в отделении банка, экран горит красным отказом.",
                "На улице собирается очередь, электронные двери блокируются автоматикой.",
                "Макс находит старый телефонный автомат, который еще работает без сети.",
                "В трубке неизвестный голос предлагает сделку: координаты наличных в обмен на услугу."
            ],
            "cliffhanger": "На телефон приходит СМС: 'У тебя осталось 15 минут, пока закрыты двери метро'."
        },
        {
            "theme": "cameras",
            "title": "ГородОко: Что делать, если на городской камере ты увидел себя?",
            "hook": "Я листал городские камеры перед сном. На камере 2817 стоял человек в моей одежде.",
            "character": "hoodie",
            "length": "60",
            "hud": "КАМЕРА: 2817 | СТАТУС: В ЭФИРЕ | ЗРИТЕЛИ: 1 (ТЫ) | РИСК: 60%",
            "steps": [
                "Герой проверяет время трансляции — задержка 0 секунд, прямой эфир.",
                "Двойник на экране медленно поворачивается и смотрит прямо в объектив.",
                "Герой делает шаг к окну своей комнаты — на камере фигура делает точно такой же шаг.",
                "Приходит уведомление: 'Пользователь Камера-2817 запросил доступ к вашей комнате'."
            ],
            "cliffhanger": "Двойник на экране достает телефон, и в твоей реальной комнате раздается звонок."
        },
        {
            "theme": "anomalies",
            "title": "Лифт поехал на этаж -5: Правила выживания",
            "hook": "В обычной 9-этажке дисплей лифта показал минус один... минус два...",
            "character": "courier",
            "length": "60",
            "hud": "ЭТАЖ: -4 | СВЯЗЬ: 0 ДЕЛЕНИЙ | СВЕТ: 15% | ДВЕРИ: ЗАБЛОКИРОВАНЫ",
            "steps": [
                "Лифт останавливается на глубине, свет в кабине начинает мерцать желтым.",
                "Двери приоткрываются на 10 см, за ними виден старый кирпичный коридор.",
                "Правило 1: Не выходить наружу, пока горит кнопка аварийного вызова.",
                "Правило 2: Если услышишь шаги — задержи дыхание и нажми кнопку 'Отмена'."
            ],
            "cliffhanger": "Шаги останавливаются прямо у створки дверей, и кто-то снаружи нажимает кнопку вызова."
        }
    ]

    @classmethod
    def get_random_plot(cls):
        plot = random.choice(cls.PLOTS_DATABASE)
        return cls.format_plot_output(plot)

    @classmethod
    def generate_continuation(cls, original_title):
        return (
            f"🎬 **СЕРИЯ 2 (ПРОДОЛЖЕНИЕ): «{original_title} — Час Расплаты»**\n\n"
            f"⚡ **Хук начала 2-й серии (0–3 сек):**\n"
            f"> «Стук в дверь прекратился. Но в глазок я увидел, что на площадке стоит включённая камера...»\n\n"
            f"🎮 **HUD интерфейс 2-й серии:**\n"
            f"`ВРЕМЯ: 03:15 | ЗАРЯД: 9% | ДВЕРЬ: ПОД НАБЛЮДЕНИЕМ | РИСК: 92%`\n\n"
            f"📜 **Развитие сюжета (Поминутно):**\n"
            f"1. **00:00–00:15:** Герой понимает, что за дверью никого нет — камера транслирует его подъезд в закрытую сеть.\n"
            f"2. **00:15–00:35:** Три шага контр-выживания: отключить электрощиток, заклеить глазок, подать сигнал через форточку.\n"
            f"3. **00:35–00:55:** Внезапное сообщение на телефон: трансляцию смотрят 400 человек, и они голосуют, выломать ли замок.\n\n"
            f"🪝 **Клиффхэнгер на 3-ю серию:**\n"
            f"_На экране голосования шкала 'Выломать' доходит до 100%, и снаружи раздается скрежет монтировки..._\n\n"
            f"🎨 **Кодовый промпт для анимации:**\n"
            f"`HTML/SVG план подъезда: темный коридор, зеленый диод камеры, мигающая лампа накаливания, тень за дверью.`"
        )

    @classmethod
    def get_animation_prompts(cls, plot_title):
        return (
            f"🎨 **ПРОМПТЫ ДЛЯ КОДОВОЙ АНИМАЦИИ (HTML/CSS/JS + GSAP)**\n"
            f"**Проект:** «{plot_title}»\n"
            f"**Формат:** Вертикальный 1080×1920 (9:16), 24 fps\n\n"
            f"📌 **Сцена 1: Хук (00:00–00:06)**\n"
            f"• *Код:* `<div class='room night'>` с темным фоном `#0B1422`.\n"
            f"• *Персонаж:* Силуэт со спины перед светящимся экраном (`#EDBF74` мягкий свет).\n"
            f"• *GSAP:* `gsap.fromTo('.screen-glow', {opacity: 0.4}, {opacity: 1, duration: 0.3, yoyo: true, repeat: 2})`\n\n"
            f"📌 **Сцена 2: Появление HUD и Угрозы (00:06–00:25)**\n"
            f"• *Верхний HUD:* Плашка `#141F31` с закруглением 24px, 4 параметра: Время, Ресурс, Статус, Риск.\n"
            f"• *Анимация полосы риска:* `gsap.to('#risk-bar', {width: '75%', duration: 1.5, ease: 'power2.out'})`\n\n"
            f"📌 **Сцена 3: Экстренные советы на ЧЕРНОМ фоне (00:25–00:50)**\n"
            f"• Полный переход на `#000000`, по центру крупная векторная иконка действия (замок, 112, телефон) с белой обводкой.\n\n"
            f"📌 **Сцена 4: Клиффхэнгер (00:50–01:00)**\n"
            f"• Наезд камеры (`scale: 1.15`), мигание красного контура опасности `#D95D4E`."
        )

    @classmethod
    def format_plot_output(cls, plot):
        steps_text = "\n".join([f"  {idx+1}. {s}" for idx, s in enumerate(plot["steps"])])
        return (
            f"🎬 **ГОТОВЫЙ ВИРУСНЫЙ СЮЖЕТ ДЛЯ МУЛЬТИКА**\n\n"
            f"🔥 **Название:** *{plot['title']}*\n"
            f"🎭 **Категория:** {cls.THEMES.get(plot['theme'], plot['theme'])}\n"
            f"👤 **Главный герой:** {cls.CHARACTERS.get(plot['character'], plot['character'])}\n"
            f"⏱️ **Хронометраж:** {plot['length']} секунд\n\n"
            f"⚡ **Хук (0–3 секунды):**\n"
            f"> «{plot['hook']}»\n\n"
            f"🎮 **HUD интерфейс (Верх кадра):**\n"
            f"`{plot['hud']}`\n\n"
            f"📜 **Сценарный план:**\n"
            f"{steps_text}\n\n"
            f"🪝 **Клиффхэнгер (Крючок на серию 2):**\n"
            f"_{plot['cliffhanger']}_\n\n"
            f"💡 _Нажмите «🎨 Промпты для анимации» или напишите свои правки к сюжету!_"
        )

def build_main_inline_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "🎲 Случайный сюжет", "callback_data": "plot_random"},
                {"text": "🎯 Топ аномалий дня", "callback_data": "daily_outliers"}
            ],
            [
                {"text": "📂 Выбрать тему", "callback_data": "menu_themes"},
                {"text": "👤 Выбрать героя", "callback_data": "menu_characters"}
            ],
            [
                {"text": "🎨 Промпты для кода", "callback_data": "menu_prompts"},
                {"text": "🎬 Сгенерировать Серию 2", "callback_data": "menu_episode2"}
            ],
            [
                {"text": "✂️ Видео-студия (Баннер/Сплиттер)", "callback_data": "menu_video_tools"}
            ]
        ]
    }

def send_telegram(token, chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        r = requests.post(url, json=payload, timeout=12)
        return r.json()
    except Exception as e:
        print(f"Send error: {e}")
        return None

def bot_worker():
    global CHAT_ID
    if not BOT_TOKEN:
        print("[Cloud Bot] BOT_TOKEN не задан!")
        return

    print("[Cloud Bot] Супер-бот запущен в облаке 24/7...")
    offset = 0
    last_morning_sent = ""
    last_user_plots = {}

    while True:
        try:
            utc_now = datetime.datetime.now(datetime.timezone.utc)
            local_now = utc_now + datetime.timedelta(hours=TIMEZONE_OFFSET)
            today_str = local_now.strftime("%Y-%m-%d")

            # Утренняя рассылка в 08:00
            if local_now.hour == 8 and local_now.minute == 0 and last_morning_sent != today_str:
                if CHAT_ID:
                    sample_report = (
                        "🎯 **УТРЕННИЙ ТОП-3 АНОМАЛИЙ (TikTok & Shorts)**\n\n"
                        "1. 🔥 **«Что если в банкоматах исчезнут все деньги за 1 час?»**\n"
                        "• Канал: 420 сабов ➔ 680,000 просмотров (виральность **1619x**!)\n"
                        "• *Хук:* «В 14:00 терминалы перестали выдавать наличку. В 14:15 карты заблокировались во всей стране.»\n\n"
                        "2. 🔥 **«Ты нажал на чужую кнопку вызова в лифте... и он поехал на этаж -5»**\n"
                        "• Канал: 1,250 сабов ➔ 940,000 просмотров (виральность **752x**!)\n\n"
                        "3. 🔥 **«Что если все камеры в городе начали следить лично за тобой?»**\n"
                        "• Канал: 890 сабов ➔ 490,000 просмотров (виральность **550x**!)"
                    )
                    send_telegram(BOT_TOKEN, CHAT_ID, f"☀️ **Доброе утро! Твой утренний отчет готов:**\n\n{sample_report}", reply_markup=build_main_inline_keyboard())
                    last_morning_sent = today_str

            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            r = requests.get(url, params={"offset": offset, "timeout": 10}, timeout=15)
            if r.status_code == 200:
                data = r.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1

                    if "callback_query" in update:
                        cb = update["callback_query"]
                        cb_data = cb.get("data")
                        sender_id = cb.get("message", {}).get("chat", {}).get("id")
                        cb_id = cb.get("id")
                        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery", json={"callback_query_id": cb_id}, timeout=5)

                        if cb_data == "plot_random":
                            plot_msg = CartoonStoryEngine.get_random_plot()
                            last_user_plots[sender_id] = "Что если в банкоматах исчезнут все деньги за 1 час?"
                            send_telegram(BOT_TOKEN, sender_id, plot_msg, reply_markup=build_main_inline_keyboard())

                        elif cb_data == "daily_outliers":
                            send_telegram(BOT_TOKEN, sender_id, "🎯 **Утренний топ аномалий доступен:**\n\n• «Что если исчезнут деньги» (1619x виральность)\n• «Лифт на этаж -5» (752x)\n• «Камеры следят за тобой» (550x)", reply_markup=build_main_inline_keyboard())

                        elif cb_data == "menu_themes":
                            themes_text = (
                                "📂 **ВЫБЕРИТЕ ТЕМАТИКУ ДЛЯ МУЛЬТФИЛЬМА:**\n\n"
                                "1. ⚡ **«А что, если?..»**\n"
                                "2. ❄️ **«Выживание и блэкаут»**\n"
                                "3. 📹 **«ГородОко и слежка»**\n"
                                "4. 🚪 **«Аномалии»**\n\n"
                                "Напишите тему в чат, и я сгенерирую сюжет!"
                            )
                            send_telegram(BOT_TOKEN, sender_id, themes_text, reply_markup=build_main_inline_keyboard())

                        elif cb_data == "menu_characters":
                            chars_text = (
                                "👤 **КАТАЛОГ ПЕРСОНАЖЕЙ:**\n\n"
                                "• **Макс** (студент)\n"
                                "• **Герой в синем худи** (ночной житель)\n"
                                "• **Бабушка Валя** (загадочный свидетель)\n"
                                "• **Ночной курьер** (знает изнанку города)"
                            )
                            send_telegram(BOT_TOKEN, sender_id, chars_text, reply_markup=build_main_inline_keyboard())

                        elif cb_data == "menu_prompts":
                            last_t = last_user_plots.get(sender_id, "Что если камеры начали следить лично за тобой")
                            send_telegram(BOT_TOKEN, sender_id, CartoonStoryEngine.get_animation_prompts(last_t), reply_markup=build_main_inline_keyboard())

                        elif cb_data == "menu_episode2":
                            last_t = last_user_plots.get(sender_id, "Что если в банкоматах исчезнут все деньги за 1 час")
                            send_telegram(BOT_TOKEN, sender_id, CartoonStoryEngine.generate_continuation(last_t), reply_markup=build_main_inline_keyboard())

                        elif cb_data == "menu_video_tools":
                            send_telegram(BOT_TOKEN, sender_id, "✂️ **ВИДЕО-СТУДИЯ:**\n\nОтправьте видеофайл с подписью, и бот наложит баннер или сделает сплиттер через FFmpeg!", reply_markup=build_main_inline_keyboard())

                        continue

                    msg = update.get("message", {})
                    text = msg.get("text", "").strip()
                    sender = msg.get("chat", {}).get("id")

                    if not text:
                        continue

                    if not CHAT_ID:
                        CHAT_ID = str(sender)

                    if text in ["/start", "/help"]:
                        welcome = (
                            "👋 **Добро пожаловать в супер-студию VideoStudio Bot!**\n\n"
                            "Здесь объединены лучшие возможности создания вирусных мультиков:\n\n"
                            "🎲 **Генератор сюжетов:** случайные идеи, выбор персонажа, темы и длины (как в @Foryteibot)\n"
                            "🎨 **Промпты для анимации:** готовые структуры для кодового 2D-рендеринга и HUD\n"
                            "🎬 **Генератор продолжений:** создание 2-й серии на основе клиффхэнгера\n"
                            "🚀 **Антиплагиат и Улучшатор:** отправь любую тему — я перепишу её с удвоением ставок!\n"
                            "🎯 **Утренний скаут аномалий:** свежие выстрелившие видео с маленьких каналов\n"
                            "✂️ **Видео-монтаж (FFmpeg):** баннеры, сплиттеры и плашки\n\n"
                            "Выберите действие кнопками ниже или просто напишите мне свою идею 👇"
                        )
                        send_telegram(BOT_TOKEN, sender, welcome, reply_markup=build_main_inline_keyboard())

                    else:
                        last_user_plots[sender] = text
                        res = (
                            f"🚀 **ИДЕЯ УЛУЧШЕНА И АДАПТИРОВАНА ПОД МУЛЬТИК**\n\n"
                            f"📌 **Ваша мысль:** _{text}_\n\n"
                            f"🔥 **Новое вирусное название (100% Антиплагиат):**\n"
                            f"*Что если {text.lower()} ночью, когда закрыты все выходы из дома?*\n\n"
                            f"⚡ **Хук (первые 3 секунды):**\n"
                            f"> «Все считали это фейком. Пока в 02:40 на экране телефона не появился таймер...»\n\n"
                            f"🎮 **HUD интерфейс:**\n"
                            f"`ВРЕМЯ: 02:40 | ШАНС: 14% | ШУМ В ПОДЪЕЗДЕ: 40 дБ | РИСК: 85%`\n\n"
                            f"🪝 **Клиффхэнгер на финал:**\n"
                            f"_Экран мигает красным, и на табло загорается надпись: 'Осталось 30 секунд. Не смотри в окно'._"
                        )
                        send_telegram(BOT_TOKEN, sender, res, reply_markup=build_main_inline_keyboard())

            time.sleep(1)
        except Exception as e:
            time.sleep(3)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        html_path = os.path.join(os.path.dirname(__file__), "webapp", "index.html")
        if os.path.exists(html_path):
            with open(html_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"VideoStudio Super Bot is running 24/7!")

    def log_message(self, format, *args):
        return

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

if __name__ == "__main__":
    t = threading.Thread(target=bot_worker, daemon=True)
    t.start()
    run_web_server()
