#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VideoStudio Super Bot (Render 24/7):
 - В 08:00 (UTC+7): реальный TikTok-радар в нише + сводка жёстких новостей
 - /start — мгновенное главное меню (инлайн + постоянные кнопки)
 - Генератор сюжетов: 8 тем, 8 героев, 12 стилей, 6 голосов, правки, серия 2
 - Промпты: нейросеть-видео, кодовая анимация, озвучка, обложка
 - Улучшатор идей (антиплагиат)
 - Видео-студия: баннер и сплиттер 9:16 через FFmpeg
 - REST API для Telegram Mini App
"""
import os, re, json, time, random, hmac, hashlib, threading, datetime, tempfile, subprocess, html, traceback, shutil
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from email.utils import parsedate_to_datetime
from urllib.parse import quote, parse_qsl, urlparse, parse_qs
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("CHAT_ID", "1496935964").strip()
TZ = int(os.environ.get("TIMEZONE_OFFSET", "7"))
DIGEST_HOUR = int(os.environ.get("DIGEST_HOUR", "8"))
PROXY = os.environ.get("TG_PROXY", "").strip()
SELF_URL = os.environ.get("RENDER_EXTERNAL_URL", "").strip().rstrip("/")
APP_URL = os.environ.get("APP_URL", "https://r1zendcmd.github.io/videostudio-bot/").strip()
BASE = os.path.dirname(os.path.abspath(__file__))
API = f"https://api.telegram.org/bot{BOT_TOKEN}"
PROXIES = {"http": PROXY, "https": PROXY} if PROXY else None
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"}


def log(*a):
    print(time.strftime("[%H:%M:%S]"), *a, flush=True)


def now_local():
    return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=TZ)


# ============================================================
# 1. ДАННЫЕ: темы, герои, стили, голоса
# ============================================================
THEMES = {
    "what_if":   ("⚡", "Что если?..", "Невозможное в обычной жизни"),
    "survival":  ("❄️", "Выживание", "Город без света, воды, тепла"),
    "cameras":   ("📹", "ГородОко", "Камеры, эфиры, двойники"),
    "anomalies": ("🚪", "Аномалии", "Лифты, этажи, двери, звуки"),
    "internet":  ("🌐", "Интернет и ИИ", "Отключения, блокировки, алгоритмы"),
    "money":     ("💸", "Деньги и цены", "Банки, карты, наличка"),
    "nature":    ("🌋", "Стихия и космос", "Катастрофы, небо, погода"),
    "rules":     ("📜", "Правила выживания", "Если видишь это — делай так"),
}

CHARS = {
    "max":        ("Макс", "студент, любопытный и внимательный", "young man in his 20s, messy dark hair, grey jacket"),
    "hoodie":     ("Парень в синем худи", "ночной житель, держится в тени", "faceless silhouette of a person in a blue hoodie, hood up"),
    "grandma":    ("Бабушка Валя", "загадочный свидетель, хранит тайны дома", "elderly woman with a headscarf and warm cardigan, sharp eyes"),
    "courier":    ("Ночной курьер", "знает изнанку города и тайные маршруты", "delivery courier with a thermal backpack and a reflective vest"),
    "nika":       ("Ника", "школьница-блогер, снимает всё на телефон", "teenage girl with a ponytail holding a phone, oversized sweater"),
    "palych":     ("Инженер Палыч", "спокойный практик, чинит всё подряд", "middle-aged engineer with a mustache, work overalls, flashlight"),
    "dispatcher": ("Диспетчер", "голос на связи, знает больше, чем говорит", "tired night dispatcher with a headset in front of glowing monitors"),
    "cat":        ("Кот Бублик", "чувствует аномалии раньше людей", "fluffy ginger cat with wide reflective eyes"),
}

STYLES = {
    "code2d": ("💻", "Код-анимация 2D", "flat 2D vector animation, clean SVG shapes, limited palette navy #0B1422 / amber #EDBF74 / red #D95D4E, smooth eased motion, HUD overlay"),
    "flat":   ("🎨", "Плоская вектор", "flat vector cartoon, bold outlines, minimal shading, saturated colors"),
    "pixar":  ("🧸", "3D мульт", "stylized 3D animated movie look, soft global illumination, expressive characters, shallow depth of field"),
    "anime":  ("🌸", "Аниме", "anime style, cel shading, dramatic lighting, detailed backgrounds, speed lines"),
    "comic":  ("💥", "Комикс", "comic book style, halftone dots, thick ink lines, dynamic framing"),
    "noir":   ("🎞️", "Нуар ч/б", "black and white film noir, high contrast, hard shadows, rain, film grain"),
    "clay":   ("🧱", "Пластилин", "claymation stop-motion, visible fingerprints, handmade textures"),
    "pixel":  ("👾", "Пиксель-арт", "16-bit pixel art, limited palette, dithering, retro game camera"),
    "cctv":   ("📷", "Камера слежения", "found-footage CCTV look, grainy low-res, timestamp overlay, fisheye, scanlines"),
    "paper":  ("📄", "Бумажный театр", "layered paper cut-out diorama, handmade paper textures, soft shadows"),
    "neon":   ("🌃", "Неон-киберпанк", "cyberpunk neon, wet street reflections, magenta and cyan glow"),
    "water":  ("🖌️", "Акварель", "watercolor animation, soft bleeding edges, paper texture"),
}

VOICES = {
    "calm_m":  ("🎙️", "Спокойный мужской", "calm deep male narrator, slow pace, restrained tension, close-mic intimacy"),
    "whisper": ("🤫", "Шёпот", "intimate whisper, slow, breathy, ASMR-like close mic, rising tension"),
    "news":    ("📰", "Диктор новостей", "authoritative news anchor, clear diction, medium-fast pace, neutral urgency"),
    "young_f": ("👧", "Молодой женский", "young female voice, natural, slightly anxious, conversational"),
    "robot":   ("🤖", "Робот / ИИ", "synthetic AI voice, flat intonation, slight metallic reverb, precise"),
    "elder":   ("👵", "Пожилой голос", "elderly voice, warm and raspy, storyteller cadence"),
}

LENGTHS = [30, 45, 60, 75, 90]
NB = {30: 3, 45: 4, 60: 4, 75: 5, 90: 6}

THEME_HUD = {
    "what_if": "ВРЕМЯ: {t} | ШАНС: {c}% | СВИДЕТЕЛЕЙ: {n} | РИСК: {r}%",
    "survival": "ТЕМПЕРАТУРА: -{c}°C | ЗАПАС: {n}% | СВЯЗЬ: НЕТ | РИСК: {r}%",
    "cameras": "КАМЕРА: {n} | СТАТУС: В ЭФИРЕ | ЗРИТЕЛЕЙ: 1 | РИСК: {r}%",
    "anomalies": "ЭТАЖ: -{c} | СВЕТ: {n}% | ДВЕРИ: ЗАБЛОКИРОВАНЫ | РИСК: {r}%",
    "internet": "СЕТЬ: {n}% | ДНЕЙ БЕЗ ИНТЕРНЕТА: {c} | VPN: ОТКЛ | РИСК: {r}%",
    "money": "БАЛАНС: 0 ₽ | НАЛИЧКА: {n} ₽ | КАРТЫ: ЗАБЛОКИРОВАНЫ | РИСК: {r}%",
    "nature": "ВРЕМЯ ДО ПИКА: {t} | УРОВЕНЬ: {c}% | УКРЫТИЕ: {n} м | РИСК: {r}%",
    "rules": "ПРАВИЛО: {c}/7 | ВРЕМЯ: {t} | ШУМ: {n} дБ | РИСК: {r}%",
}

PREMISES = {
    "what_if": [
        ("Что если все банкоматы выдадут чужие деньги?",
         "В 14:00 банкомат выдал мне 50 000 ₽ — и это были не мои деньги.",
         "ВРЕМЯ: 14:03 | НА РУКАХ: 50 000 ₽ | ВОЗВРАТ: НЕТ | РИСК: 45%",
         ["{h} прячет пачку и замечает на купюрах метку времени и чужие отпечатки.",
          "На экране банкомата идёт обратный отсчёт: деньги надо вернуть до 15:00.",
          "Очередь за спиной замолкает: все получили такие же деньги и смотрят на {h}.",
          "Банк блокирует карты по всему району, наличка становится единственной валютой."],
         "На купюре проступает адрес, и он совпадает с домом {h}."),
        ("Что если завтра не наступит?",
         "Часы показали 23:59 и остановились. Но все вокруг продолжали двигаться.",
         "ВРЕМЯ: 23:59:59 | СЕКУНД: ∞ | В ДВИЖЕНИИ: 99% | РИСК: 38%",
         ["{h} замечает, что только его телефон показывает правильное время.",
          "Прохожие повторяют одни и те же жесты, как заевшая запись.",
          "Единственный, кто двигается иначе, — человек в конце улицы.",
          "{h} пытается дождаться полуночи, но секундная стрелка идёт назад."],
         "Человек в конце улицы поднимает руку и показывает {h} три пальца."),
    ],
    "survival": [
        ("Температура падает на 1°C каждые 5 минут: 24 часа холода",
         "В 18:00 было +2°C. В 19:00 уже −10°C. Батареи в квартире замёрзли.",
         "ТЕМПЕРАТУРА: -22°C | ВРЕМЯ ДО ПИКА: 3 ЧАСА | ТЕПЛО: 28% | РИСК: 80%",
         ["{h} строит укрытие из одеял и матрасов в центре комнаты.",
          "Пластиковые окна покрываются морозными трещинами.",
          "Попытка согреться свечами с контролем кислорода: форточка приоткрыта на два пальца.",
          "Связь пропадает, в подъезде слышен треск лопающихся труб."],
         "Термометр показывает −70°C, а в дверь кто-то яростно стучит."),
        ("Блэкаут на 72 часа: город без света и воды",
         "Свет моргнул три раза и погас. Во всём городе. Сразу.",
         "СВЕТ: 0% | ВОДА: 12 Л | ЗАРЯД: 41% | РИСК: 62%",
         ["{h} собирает набор: вода, фонарь, повербанк, радио.",
          "В магазинах гаснут кассы, люди берут товары без оплаты.",
          "Радио ловит один канал с мужским голосом, который читает числа.",
          "{h} понимает, что числа — это номера квартир."],
         "Голос в радио называет номер квартиры {h}."),
    ],
    "cameras": [
        ("ГородОко: на камере ты увидел себя",
         "Я листал городские камеры перед сном. На камере 2817 стоял человек в моей одежде.",
         "КАМЕРА: 2817 | СТАТУС: В ЭФИРЕ | ЗРИТЕЛЕЙ: 1 (ТЫ) | РИСК: 60%",
         ["Эфир с задержкой 0 секунд показывает перекрёсток у дома {h}.",
          "Двойник на экране поворачивается и смотрит прямо в объектив.",
          "{h} подходит к окну — фигура делает точно такой же шаг.",
          "На телефон приходит уведомление: «Вы обнаружены»."],
         "Двойник достаёт телефон, и в реальной комнате {h} раздаётся звонок."),
        ("Все камеры города повернулись к одному человеку",
         "Каждый раз, когда я прохожу мимо фонаря, объектив поворачивается на моё лицо.",
         "КАМЕР НА МНЕ: 14 | ДО ДОМА: 600 М | СВЯЗЬ: НЕТ | РИСК: 55%",
         ["{h} меняет маршрут, но камеры на столбах поворачиваются синхронно.",
          "В витринах мелькает его лицо с подписью «ИСКОМЫЙ».",
          "Телефон показывает карту, где точка {h} окружена красным.",
          "Единственная слепая зона — старый подземный переход."],
         "В подземном переходе висит одна камера. Она уже смотрит на {h}."),
    ],
    "anomalies": [
        ("Лифт поехал на этаж −5: правила выживания",
         "В обычной девятиэтажке дисплей лифта показал минус один… минус два…",
         "ЭТАЖ: -4 | СВЯЗЬ: НЕТ | СВЕТ: 15% | ДВЕРИ: ЗАБЛОКИРОВАНЫ | РИСК: 70%",
         ["Кабина застревает в сыром тоннеле, свет мерцает жёлтым.",
          "Двери приоткрываются на 10 см: за ними заброшенный кирпичный коридор.",
          "Правило 1: не выходить, пока горит аварийная кнопка.",
          "Правило 2: услышал шаги — задержи дыхание и нажми «Отмена»."],
         "Шаги замирают у дверей, и кто-то снаружи нажимает кнопку вызова."),
        ("Дверь в подъезде, которой вчера не было",
         "Вчера на первом этаже была стена. Сегодня там дверь. И она тёплая.",
         "ДВЕРЬ: ТЕПЛАЯ | ЗВУК: ДЫХАНИЕ | СВЕТ: 30% | РИСК: 48%",
         ["{h} спрашивает соседей, но они не помнят, что здесь была стена.",
          "Из-под двери тянет запахом свежего хлеба и озона.",
          "На ручке появляется табличка: «Не открывать до 03:00».",
          "В 02:59 из-за двери раздаётся стук изнутри."],
         "Табличка меняется: «Открывай. Мы уже вошли в твою квартиру»."),
    ],
    "internet": [
        ("Интернет отключили на 90 дней. День первый",
         "В 08:00 пропала сеть. В 08:05 — мобильная связь. В 08:10 — все сайты, кроме одного.",
         "СЕТЬ: 0% | ДНЕЙ БЕЗ ИНТЕРНЕТА: 1/90 | VPN: ОТКЛ | РИСК: 52%",
         ["{h} ищет работающий Wi-Fi и находит сеть без пароля с названием «ОСТАЛОСЬ 89».",
          "В магазинах не работают терминалы, люди возвращаются к наличным и бумажным картам.",
          "На рекламных экранах вместо роликов идёт один и тот же обратный отсчёт.",
          "{h} достаёт старый радиоприёмник и ловит голос, который диктует инструкцию."],
         "Инструкция заканчивается словами: «Никому не говорите, что вы это слышали»."),
        ("Алгоритм начал предсказывать твои мысли",
         "Приложение предложило мне фразу, которую я только подумал.",
         "ТОЧНОСТЬ: 94% | ЗАДЕРЖКА: -2 С | ПРИВАТНОСТЬ: ОТКЛ | РИСК: 66%",
         ["{h} проверяет: думает «яблоко» — на экране появляется «яблоко».",
          "Лента показывает видео, которого ещё нет, — завтрашнее, с участием {h}.",
          "Попытка выключить телефон: экран показывает «Не надо».",
          "Единственный способ обмануть алгоритм — сделать то, чего он не ждёт."],
         "Алгоритм пишет: «Я знал, что ты это сделаешь»."),
    ],
    "money": [
        ("Карты заблокировались по всей стране за 15 минут",
         "В 14:00 терминалы перестали принимать карты. В 14:15 деньги исчезли из приложений.",
         "БАЛАНС: 0 ₽ | НАЛИЧКА: 1 500 ₽ | КАРТЫ: ЗАБЛОКИРОВАНЫ | РИСК: 58%",
         ["{h} пытается купить воду, но терминал показывает красный крест.",
          "У банкоматов собирается очередь, электронные двери блокируются.",
          "{h} находит таксофон, который работает без сети.",
          "В трубке голос предлагает сделку: координаты наличных в обмен на услугу."],
         "Голос называет сумму — ровно столько, сколько осталось на счёте {h}."),
        ("Цены в магазине меняются, пока ты стоишь в очереди",
         "Хлеб стоил 50 ₽, когда я встал в очередь. На кассе — 400.",
         "ЦЕНА ХЛЕБА: 400 ₽ | ОЧЕРЕДЬ: 12 | НАЛИЧКА: 600 ₽ | РИСК: 44%",
         ["{h} снимает ценники на телефон — пока снимает, цифры растут.",
          "Люди скупают всё подряд, полки пустеют на глазах.",
          "Кассирша шепчет: «Бери меньше, они считают».",
          "На потолке мигает красная лампа, камера поворачивается к {h}."],
         "Кассирша кладёт ладонь на счётчик, и на нём — вес самого {h}."),
    ],
    "nature": [
        ("Небо стало зелёным: 40 минут до шторма",
         "В 16:00 небо позеленело. Птицы улетели. Собаки легли на землю.",
         "ВРЕМЯ ДО ПИКА: 0:40 | ДАВЛЕНИЕ: -38% | УКРЫТИЕ: 300 М | РИСК: 75%",
         ["{h} закрывает окна, ставит ёмкости с водой и ищет подвал.",
          "Сирены не звучат, вместо них — низкий гул из-под земли.",
          "Соседи спускаются в подвал и приносят банку с мигающим светом.",
          "{h} понимает, что гул идёт не сверху, а снизу."],
         "Земля трескается ровно под ногами {h}, и из трещины выходит свет."),
        ("Луна приблизилась на 10 000 км",
         "Сегодня Луна занимает полнеба. И она всё ещё приближается.",
         "РАССТОЯНИЕ: -10 000 КМ | ПРИЛИВЫ: +300% | ВРЕМЯ: 2:10 | РИСК: 63%",
         ["{h} видит на побережье отлив, которого не было никогда.",
          "Радио объявляет эвакуацию, но не называет, куда.",
          "Стаи птиц летят на запад — {h} решает идти за ними.",
          "В небе появляется вторая тень рядом с Луной."],
         "Тень поворачивается, и становится видно, что это не облако."),
    ],
    "rules": [
        ("7 правил ночной смены: ты не должен видеть шестого",
         "Правило 1: не отвечай на звонки после 03:00. Правило 6: если видишь его — не моргай.",
         "ПРАВИЛО: 1/7 | ВРЕМЯ: 02:58 | ШУМ: 31 дБ | РИСК: 40%",
         ["{h} читает памятку на двери: правила написаны разными почерками.",
          "В 03:00 звонит стационарный телефон, которого раньше не было.",
          "В коридоре гаснет свет, у стены виден чужой силуэт.",
          "Правило 6 исчезает с бумаги, остаётся пустая строка."],
         "На пустой строке проступает новое правило, написанное почерком {h}."),
        ("Правила для тех, кто остался в метро после закрытия",
         "Последний поезд ушёл. Табло показывает станцию, которой нет на схеме.",
         "ПРАВИЛО: 2/5 | ВРЕМЯ: 00:41 | ВЫХОДОВ: 0 | РИСК: 57%",
         ["На стене висят правила: «Не разговаривай с дежурным в красном».",
          "{h} слышит шаги по платформе и видит дежурного в красной жилетке.",
          "Дежурный просит помочь открыть решётку и называет {h} по имени.",
          "Ближайший выход на схеме отмечен, но стрелка ведёт обратно вглубь."],
         "Дежурный улыбается: «Я не дежурный. Но ты уже ответил»."),
    ],
}

GENERIC_BEATS = [
    "{h} находит подсказку, которую раньше не замечал.",
    "Связь пропадает, и {h} остаётся один на один с проблемой.",
    "Появляется второй таймер, и ставки удваиваются.",
    "{h} принимает решение, которое нельзя отменить.",
    "Звук в кадре обрывается, слышно только дыхание {h}.",
    "Экран телефона загорается сам и показывает то, чего {h} не ожидал.",
]

TWISTS = [
    "Выясняется, что {h} уже был здесь раньше — но ничего не помнит.",
    "Человек, который помогал {h}, оказывается тем, от кого надо бежать.",
    "Таймер на экране идёт не вниз, а вверх — это не обратный отсчёт.",
    "Все правила были написаны для того, чтобы {h} их нарушил.",
]

HOOK_ALT = [
    "Никто не заметил, как в {t} всё изменилось. Кроме меня.",
    "Правило номер один: не смотри на экран. Я посмотрел.",
    "У меня есть всего {m} минут, чтобы это объяснить.",
    "Это не шутка. В {t} на моём телефоне запустился таймер.",
    "Все делают вид, что ничего не происходит. Но посмотри на часы: {t}.",
]

CONT_BEATS = [
    "{h} приходит в себя там, где закончилась прошлая серия, но время сдвинулось на два часа вперёд.",
    "Ставки удваиваются: теперь за {h} наблюдают те, кто молчал раньше.",
    "{h} находит запись из прошлой серии — на ней есть кадры, которые он не снимал.",
    "Один из союзников признаётся, что знал об этом с самого начала.",
    "{h} решает использовать то, что считал слабостью, как оружие.",
    "Механика HUD меняется: появляется новая шкала, которую нельзя сбросить.",
]

CLIFFS_NEXT = [
    "Экран гаснет, и последняя надпись: «Следующая серия уже идёт без тебя».",
    "{h} открывает дверь и видит самого себя, только на два шага впереди.",
    "Таймер доходит до нуля, но вместо взрыва наступает тишина — и стук в стену.",
]

CAMERAS = ["slow push-in on the face", "handheld shaky medium shot", "static top-down shot", "extreme close-up on eyes and screen glow",
           "low angle looking up", "slow pan across the empty room", "dutch angle with a sudden zoom"]
LIGHT = {
    "what_if": "cold fluorescent light with one warm amber accent", "survival": "dim candlelight and blue moonlight, visible breath",
    "cameras": "monitor glow in the dark, green status LEDs", "anomalies": "flickering yellow emergency light, deep shadows",
    "internet": "cold screen glow, pulsing red indicator lights", "money": "harsh neon shop light, red error screens",
    "nature": "green stormy sky, dramatic backlight", "rules": "single flickering bulb, long shadows",
}

SENSITIVE = ["погиб", "убит", "убий", "теракт", "война", "обстрел", "жертв", "смерть", "умер", "трагед", "расстрел", "изнасил", "массовое убийство"]


# ============================================================
# 2. ДВИЖОК СЮЖЕТОВ
# ============================================================
def fmt_t(sec):
    return f"{int(sec) // 60}:{int(sec) % 60:02d}"


def timeline(length, nb):
    span = max(length - 3 - 7, nb * 3)
    seg = span / nb
    return [f"{fmt_t(3 + seg * i)}–{fmt_t(3 + seg * (i + 1))}" for i in range(nb)]


def retime(s):
    tl = timeline(s["length"], len(s["beats"]))
    for i, b in enumerate(s["beats"]):
        b["t"] = tl[i]
    s["cliff_t"] = f"{fmt_t(max(s['length'] - 7, 0))}–{fmt_t(s['length'])}"
    return s


def get_risk(hud):
    m = re.search(r"РИСК:\s*(\d+)%", hud)
    return int(m.group(1)) if m else 50


def set_risk(hud, r):
    if re.search(r"РИСК:\s*\d+%", hud):
        return re.sub(r"РИСК:\s*\d+%", f"РИСК: {r}%", hud)
    return hud + f" | РИСК: {r}%"


def finalize(s):
    th, ch, st = THEMES[s["theme"]], CHARS[s["char"]], STYLES[s["style"]]
    s["theme_icon"], s["theme_name"] = th[0], th[1]
    s["char_name"] = ch[0]
    s["style_icon"], s["style_name"] = st[0], st[1]
    s["voice_name"] = VOICES[s["voice"]][1]
    s["risk"] = get_risk(s["hud"])
    return retime(s)


def story_tags(theme):
    name = THEMES[theme][1].replace(" ", "").replace("?", "").replace(".", "").lower()
    return ["#shorts", "#мультик", "#" + name, "#сюжет"]


def build_story(theme=None, char=None, length=60, style="code2d", voice="calm_m"):
    theme = theme if theme in THEMES else random.choice(list(THEMES))
    char = char if char in CHARS else random.choice(list(CHARS))
    try:
        length = int(length)
    except Exception:
        length = 60
    length = length if length in LENGTHS else 60
    style = style if style in STYLES else "code2d"
    voice = voice if voice in VOICES else "calm_m"
    title, hook, hud, beats, cliff = random.choice(PREMISES[theme])
    name = CHARS[char][0]
    nb = NB[length]
    beats = [b.replace("{h}", name) for b in beats]
    extra = [g.replace("{h}", name) for g in GENERIC_BEATS]
    random.shuffle(extra)
    while len(beats) < nb:
        beats.append(extra.pop())
    s = {"theme": theme, "char": char, "length": length, "style": style, "voice": voice, "ep": 1,
         "title": title, "hook": hook, "hud": hud, "beats": [{"t": "", "text": b} for b in beats[:nb]],
         "cliff": cliff.replace("{h}", name), "cta": "Подпишись — завтра выйдет продолжение.", "changes": [], "tags": story_tags(theme)}
    return finalize(s)


def clean_idea(t):
    t = re.sub(r"https?://\S+", "", t or "")
    t = re.sub(r"#\S+", "", t)
    t = re.sub(r"\s+", " ", t).strip().strip('"«»“”')
    return t.rstrip(".!?… ")[:160]


def lower_first(t):
    return t if (len(t) > 1 and t[1].isupper()) else t[:1].lower() + t[1:]


def detect_theme(t):
    x = t.lower()
    rules = [("internet", ["интернет", "сеть", "vpn", "нейросет", "алгоритм", "сайт", "связь", "блокир", "мессенджер"]),
             ("money", ["деньг", "банк", "карт", "налич", "цен", "рубл", "доллар", "кредит", "зарплат"]),
             ("cameras", ["камер", "слеж", "наблюд", "эфир", "двойник"]),
             ("anomalies", ["лифт", "этаж", "двер", "подъезд", "звук", "шаги", "подвал", "аномал"]),
             ("survival", ["холод", "свет", "блэкаут", "вод", "тепл", "мороз", "электр", "отопле", "выжив"]),
             ("nature", ["землетр", "вулкан", "небо", "космос", "луна", "шторм", "наводн", "метеор", "солнц"]),
             ("rules", ["правил", "инструкц", "смен"])]
    for th, keys in rules:
        if any(k in x for k in keys):
            return th
    return "what_if"


def enhance_idea(text, char=None, length=60, style="code2d", voice="calm_m", src="idea", theme=None):
    idea = clean_idea(text)
    if not idea:
        return build_story(theme, char, length, style, voice)
    theme = theme if theme in THEMES else detect_theme(idea)
    char = char if char in CHARS else random.choice(list(CHARS))
    try:
        length = int(length)
    except Exception:
        length = 60
    length = length if length in LENGTHS else 60
    name = CHARS[char][0]
    n_min = random.choice([7, 12, 15, 20, 30])
    hhmm = f"{random.randint(0, 23):02d}:{random.choice([10, 15, 20, 40, 47, 52])}"
    low = lower_first(idea)
    if idea.lower().startswith("что если"):
        title = f"{idea[:1].upper()}{idea[1:]} — и у тебя {n_min} минут"
    else:
        title = f"Что если {low} — и у тебя всего {n_min} минут?"
    hooks = [f"Все считали это выдумкой: «{idea}». Пока в {hhmm} на экране не запустился таймер.",
             f"В {hhmm} это перестало быть шуткой: {low}.",
             f"У меня есть {n_min} минут. Началось с того, что {low}."]
    risk = random.choice([61, 68, 74, 81])
    hud = THEME_HUD[theme].format(t=f"0:{n_min:02d}", c=random.choice([3, 4, 5, 22, 30, 48]), n=random.choice([12, 28, 41, 64, 1500]), r=risk)
    if src == "news":
        first = f"{name} листает ленту и видит новость: «{idea}». Все вокруг пожимают плечами."
    elif src == "tiktok":
        first = f"{name} замечает тренд, над которым все смеялись: «{idea}». Но ситуация повторяется в реальности."
    else:
        first = f"{name} замечает, что это правда: {low}. Остальные делают вид, что всё нормально."
    beats = [first,
             "На экране появляется обратный отсчёт и первое правило, о котором никто не предупреждал.",
             "Попытка позвать на помощь удваивает риск: связь работает только в одну сторону.",
             f"{name} находит способ обойти правило, но цена выше, чем казалось.",
             "Второй таймер запускается, пока первый ещё идёт.",
             f"{name} понимает, что настоящая угроза — не то, что происходит, а тот, кто это запустил."]
    nb = NB[length]
    s = {"theme": theme, "char": char, "length": length, "style": style if style in STYLES else "code2d",
         "voice": voice if voice in VOICES else "calm_m", "ep": 1, "title": title, "hook": random.choice(hooks), "hud": hud,
         "beats": [{"t": "", "text": b} for b in beats[:nb]],
         "cliff": f"Экран мигает красным: «Осталось 30 секунд. Не смотри в окно, {name}».",
         "cta": "Подпишись — завтра выйдет продолжение.",
         "changes": ["Новое название и другой хук (без копирования оригинала)", "Сеттинг и герой адаптированы под кодовый мультик",
                     "Добавлены таймер обратного отсчёта и HUD", "Удвоены ставки и добавлен клиффхэнгер на серию 2"],
         "tags": story_tags(theme)}
    return finalize(s)


def pad_beats(s):
    name = s["char_name"]
    nb = NB[s["length"]]
    extra = [g.replace("{h}", name) for g in GENERIC_BEATS]
    random.shuffle(extra)
    while len(s["beats"]) < nb:
        s["beats"].append({"t": "", "text": extra.pop()})
    s["beats"] = s["beats"][:nb]


def edit_story(s, action, value=None):
    s = json.loads(json.dumps(s))
    name = s["char_name"]
    if action == "darker":
        s["hud"] = set_risk(s["hud"], min(99, get_risk(s["hud"]) + 15))
        if len(s["beats"]) > 1:
            s["beats"][1]["text"] += " Свет меркнет, звуки глохнут — слышно только дыхание."
        s["hook"] = s["hook"] + " И это только начало."
    elif action == "twist":
        s["beats"].append({"t": "", "text": random.choice(TWISTS).replace("{h}", name)})
    elif action == "hook":
        hhmm = f"{random.randint(0, 23):02d}:{random.choice([10, 15, 40, 47])}"
        s["hook"] = random.choice(HOOK_ALT).format(t=hhmm, m=random.choice([7, 12, 15]))
    elif action in ("shorter", "longer"):
        i = LENGTHS.index(s["length"]) if s["length"] in LENGTHS else 2
        i = max(0, i - 1) if action == "shorter" else min(len(LENGTHS) - 1, i + 1)
        s["length"] = LENGTHS[i]
        pad_beats(s)
    elif action == "hero":
        new = random.choice([k for k in CHARS if k != s["char"]])
        new_name = CHARS[new][0]
        for b in s["beats"]:
            b["text"] = b["text"].replace(name, new_name)
        s["cliff"] = s["cliff"].replace(name, new_name)
        s["char"] = new
    elif action == "style" and value in STYLES:
        s["style"] = value
    elif action == "voice" and value in VOICES:
        s["voice"] = value
    elif action == "length" and value and int(value) in LENGTHS:
        s["length"] = int(value)
        pad_beats(s)
    return finalize(s)


def continue_story(s):
    name = s["char_name"]
    pool = [c.replace("{h}", name) for c in CONT_BEATS]
    random.shuffle(pool)
    nb = NB[s["length"]]
    ep = s.get("ep", 1) + 1
    base_title = re.sub(r"^Серия \d+:\s*", "", s["title"])
    risk = min(99, get_risk(s["hud"]) + 12)
    cliff = s["cliff"].rstrip(".!?… ")
    hud = "СЕРИЯ: " + str(ep) + " | " + re.sub(r"^СЕРИЯ: \d+ \| ", "", set_risk(s["hud"], risk))
    n = {"theme": s["theme"], "char": s["char"], "length": s["length"], "style": s["style"], "voice": s["voice"], "ep": ep,
         "title": f"Серия {ep}: {base_title}", "hook": f"Прошлая серия закончилась так: «{cliff}». Но это было не всё.",
         "hud": hud, "beats": [{"t": "", "text": b} for b in pool[:nb]],
         "cliff": random.choice(CLIFFS_NEXT).replace("{h}", name), "cta": f"Подпишись — серия {ep + 1} уже монтируется.",
         "changes": [], "tags": s.get("tags", [])}
    return finalize(n)


def make_prompts(s, kind="video"):
    st, ch, vo = STYLES[s["style"]], CHARS[s["char"]], VOICES[s["voice"]]
    scenes = [("Хук", s["hook"], "0:00–0:03")] + [(f"Сцена {i + 1}", b["text"], b["t"]) for i, b in enumerate(s["beats"])] + [("Финал", s["cliff"], s["cliff_t"])]
    if kind == "video":
        out = [f"ПРОМПТЫ ДЛЯ НЕЙРОСЕТИ · стиль «{st[1]}»",
               "Вставляй по одной сцене в Higgsfield / Veo / Kling / Seedance / Sora (формат 9:16).", ""]
        for i, (nm, text, t) in enumerate(scenes):
            out.append(f"[{nm} · {t}]\n{st[2]}. Vertical 9:16. Main character: {ch[2]}. Camera: {CAMERAS[i % len(CAMERAS)]}. "
                       f"Lighting: {LIGHT[s['theme']]}. Action: {text} No subtitles, no logos, no watermark.\n")
        out.append("NEGATIVE: text artifacts, extra fingers, morphing faces, watermark, low quality, blurry")
        return "\n".join(out)
    if kind == "code":
        out = ["ПРОМПТ ДЛЯ КОДОВОЙ АНИМАЦИИ (HTML/CSS/GSAP)", "",
               f"Вертикальная сцена 1080×1920, {s['length']}с, 24 fps, GSAP-таймлайн. Стиль: {st[1]} ({st[2]}).",
               f"Герой: {s['char_name']} — {ch[1]}. Рисуй чистыми SVG-фигурами без внешних картинок.",
               f"Верхний HUD (#141F31, скругление 24px): {s['hud']}. Риск: {max(s['risk'] - 30, 5)}% -> {s['risk']}%.", "", "Раскадровка:"]
        for nm, text, t in scenes:
            out.append(f"• {t} — {nm}: {text}")
        return "\n".join(out)
    if kind == "voice":
        narr = [s["hook"]] + [b["text"] for b in s["beats"]] + [s["cliff"], s["cta"]]
        return f"ОЗВУЧКА · голос «{vo[1]}»\n\nНАСТРОЙКА TTS:\n{vo[2]}.\n\nТЕКСТ:\n" + "\n".join(narr)
    if kind == "cover":
        return (f"ОБЛОЖКА 9:16\n\n{st[2]}. Vertical 9:16 thumbnail. {ch[2]} in foreground, tense expression, "
                f"{LIGHT[s['theme']]}. Top HUD risk meter {s['risk']}%. Headline: «{s['title'][:42]}». High contrast, no watermark.")
    return ""


# ============================================================
# 3. РЕАЛЬНЫЙ TIKTOK OUTLIER SCOUT (в вашей нише)
# ============================================================
TT_QUERIES = [
    ('site:tiktok.com "что если"', 'm'),
    ('site:tiktok.com "а что если" анимация OR история', None),
    ('site:tiktok.com правила выживания', None),
    ('site:tiktok.com лифт этаж аномалия', None),
    ('site:tiktok.com выживание мультик', None),
    ('site:tiktok.com что если история', None),
    ('site:tiktok.com "what if" survival', 'm'),
    ('site:tiktok.com "what if" animation', 'm'),
]
TT_NICHE_WORDS = [
    "что если", "если", "выжив", "лифт", "аномал", "правил", "камер", "свет", "блэкаут",
    "интернет", "страш", "истори", "мульт", "анимац", "подвал", "подъезд", "холод", "пропал",
    "исчез", "what if", "surviv", "animat", "rule", "horror", "story", "bunker", "mystery", "scary", "creepy"
]
TT_BAD_WORDS = ["макияж", "рецепт", "футбол", "неймар", "роналду", "танец", "wildberries", "ozon", "анекдот", "тренировк", "похуде", "роблокс"]
TT_CACHE = {"ts": 0, "items": []}
TT_LOCK = threading.Lock()


def _fetch_tt_video(u):
    try:
        r = requests.get(u, proxies=PROXIES, headers=UA, timeout=12)
        m = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', r.text, re.S)
        if not m:
            return None
        d = json.loads(m.group(1))
        it = d.get("__DEFAULT_SCOPE__", {}).get("webapp.video-detail", {}).get("itemInfo", {}).get("itemStruct", {})
        if not it:
            return None
        desc = re.sub(r"\s+", " ", it.get("desc", "")).strip()
        low = desc.lower()
        if any(bw in low for bw in TT_BAD_WORDS):
            return None
        if not any(nw in low for nw in TT_NICHE_WORDS):
            return None
        st = it.get("stats", {})
        au = it.get("author", {})
        aus = it.get("authorStats", {})
        views = int(st.get("playCount", 0) or 0)
        fol = max(int(aus.get("followerCount", 0) or 0), 1)
        if views < 1000:
            return None
        likes = int(st.get("diggCount", 0) or 0)
        comments = int(st.get("commentCount", 0) or 0)
        ct = int(it.get("createTime", 0) or 0)
        year = datetime.datetime.fromtimestamp(ct).year if ct else 2026
        if year < 2024:
            return None
        ratio = round(views / fol, 1)
        small_bonus = 2.5 if fol < 5000 else (1.5 if fol < 25000 else 1.0)
        age_days = (time.time() - ct) / 86400 if ct else 90
        recency = 1.8 if age_days <= 45 else (1.2 if age_days <= 120 else 0.7)
        score = round((ratio * small_bonus + (views ** 0.35)) * recency, 1)
        return {
            "url": u,
            "author": au.get("uniqueId", "creator"),
            "nickname": au.get("nickname", ""),
            "followers": fol,
            "views": views,
            "likes": likes,
            "comments": comments,
            "ratio": ratio,
            "score": score,
            "date": datetime.datetime.fromtimestamp(ct).strftime("%Y-%m-%d") if ct else "",
            "desc": desc[:170],
            "theme": detect_theme(desc),
        }
    except Exception:
        return None


def collect_tiktok(limit=6):
    urls = []
    try:
        from ddgs import DDGS
        ddgs = DDGS(proxy=PROXY or None)
        for q, tl in TT_QUERIES:
            try:
                res = ddgs.text(q, timelimit=tl, max_results=15)
                for r in res:
                    href = r.get("href", "")
                    if "tiktok.com/@" in href and "/video/" in href:
                        urls.append(re.sub(r"\?.*$", "", href))
            except Exception as e:
                log("ddgs err", q[:25], str(e)[:60])
    except Exception as e:
        log("ddgs import/init err", str(e)[:80])

    # Дополняем поиск через Bing Video Search
    for q in ("site:tiktok.com что если", "site:tiktok.com what if animation", "site:tiktok.com правила выживания", "site:tiktok.com лифт аномалия"):
        try:
            r = requests.get("https://www.bing.com/videos/search?q=" + quote(q), proxies=PROXIES, headers=UA, timeout=12)
            from urllib.parse import unquote
            dec = unquote(r.text)
            urls.extend(re.findall(r"https?://(?:www\.|m\.)?tiktok\.com/@[\w.\-]+/video/\d+", dec))
        except Exception:
            pass

    urls = list(dict.fromkeys(urls))[:45]
    if not urls:
        return []
    with ThreadPoolExecutor(max_workers=8) as ex:
        rows = [x for x in ex.map(_fetch_tt_video, urls) if x]
    rows.sort(key=lambda x: x["score"], reverse=True)
    # Не повторяем одного и того же автора в топе
    uniq, seen = [], set()
    for x in rows:
        au = (x.get("author") or "").lower()
        if au and au in seen:
            continue
        if au:
            seen.add(au)
        uniq.append(x)
        if len(uniq) >= limit:
            break
    return uniq


def get_tiktok(force=False):
    with TT_LOCK:
        if force or time.time() - TT_CACHE["ts"] > 3600 or not TT_CACHE["items"]:
            items = collect_tiktok()
            if items or force:
                TT_CACHE["items"] = items
                TT_CACHE["ts"] = time.time()
        return TT_CACHE["items"]


def fmt_num(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def tiktok_html(items):
    e = html.escape
    d = now_local().strftime("%d.%m %H:%M")
    if not items:
        return f"🎯 <b>TikTok-радар · {d}</b>\n\nНе удалось получить свежие ролики из TikTok прямо сейчас. Попробуйте обновить чуть позже."
    lines = [f"🎯 <b>TikTok-радар в вашей нише · {d}</b> (реальные данные)\n"]
    for i, x in enumerate(items, 1):
        lines.append(
            f"{i}. 🔥 <b>{x['ratio']}x виральность</b> · <code>{fmt_num(x['views'])}</code> просм. / <code>{fmt_num(x['followers'])}</code> подп.\n"
            f"   👤 @{e(x['author'])} · 📅 {e(x['date'])}\n"
            f"   💬 <i>{e(x['desc'][:120])}</i>\n"
            f"   🔗 <a href=\"{e(x['url'])}\">Открыть видео в TikTok</a>"
        )
    lines.append("\n💡 Нажми кнопку ниже — перепишу ролик в ваш кодовый мультик (без плагиата).")
    return "\n".join(lines)[:4000]


def tiktok_kb(items):
    nums = [(f"🎬 В мультик #{i}", f"tt:{i - 1}") for i in range(1, len(items) + 1)]
    rows = [nums[i:i + 3] for i in range(0, len(nums), 3)]
    rows.append([("🔄 Обновить TikTok", "tt:refresh"), ("📱 Студия", {"web_app": APP_URL})])
    return kb(rows)


# ============================================================
# 4. НОВОСТИ (шокирующие сводки)
# ============================================================
SHOCK = {"отключ": 3, "блокиров": 3, "запрет": 2, "шок": 3, "срочно": 2, "экстренн": 3, "катастроф": 3, "взрыв": 3, "землетряс": 3,
         "авари": 2, "обруш": 2, "рекорд": 2, "впервые": 2, "обнаружил": 2, "аномал": 2, "утечк": 3, "взлом": 3, "кибератак": 3,
         "сбой": 3, "коллапс": 3, "дефицит": 2, "обвал": 3, "паник": 2, "загадоч": 2, "исчез": 2, "пропал": 2, "предупред": 2,
         "опасн": 2, "угроз": 2, "слух": 1, "фейк": 1, "прогноз": 1, "ограничен": 2, "штраф": 1, "блэкаут": 3, "дефолт": 3,
         "shock": 3, "breaking": 2, "outage": 3, "shutdown": 3, "blackout": 3, "leak": 2, "hack": 2, "crash": 2, "collapse": 3,
         "warning": 2, "unprecedented": 3, "discover": 2, "mystery": 2, "emergency": 3, "ban": 2, "record": 1}
BORING = ["сняты ограничения", "снят режим", "сняли ограничения", "шоумен", "певиц", "актер", "актёр", "госпитализир", "гороскоп",
          "курс валют", "отменены ограничения", "аэропорт", "катани", "шок-рейтинг", "джигурд", "погода"]
RUMOR = ["слух", "фейк", "опроверг", "прогноз", "fake", "rumor", "hoax", "миф"]
QUERIES = [
    ("отключение интернета OR блокировка OR сбой связи when:1d", "ru"),
    ("шок OR срочно OR экстренно when:1d", "ru"),
    ("учёные обнаружили OR аномалия OR впервые в истории when:2d", "ru"),
    ("кибератака OR утечка данных OR взлом when:1d", "ru"),
    ("дефицит OR обвал OR блэкаут OR ограничения when:1d", "ru"),
    ("internet shutdown OR outage OR blackout when:1d", "en"),
    ("scientists discover OR unprecedented OR mystery when:2d", "en"),
]
NEWS_CACHE = {"ts": 0, "items": []}
NEWS_LOCK = threading.Lock()


def toks(t):
    return {w[:5] for w in re.findall(r"\w{4,}", t.lower())}


def similar(a, b):
    return (len(a & b) / min(len(a), len(b))) if a and b else 0


def fetch_rss(url):
    r = None
    for attempt in range(3):
        r = requests.get(url, headers=UA, proxies=PROXIES, timeout=15)
        if r.status_code != 429:
            break
        time.sleep(2 + attempt * 2)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    out = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        src = (it.findtext("source") or "").strip()
        if src and title.endswith(" - " + src):
            title = title[: -(len(src) + 3)]
        elif " - " in title and not src:
            title, src = title.rsplit(" - ", 1)
        try:
            dt = parsedate_to_datetime(it.findtext("pubDate"))
        except Exception:
            dt = None
        out.append({"title": title, "source": src, "link": (it.findtext("link") or "").strip(), "dt": dt})
    return out


def collect_news(limit=8):
    raw = []
    urls = ["https://news.google.com/rss?hl=ru&gl=RU&ceid=RU:ru"]
    for q, lang in QUERIES:
        if lang == "ru":
            urls.append(f"https://news.google.com/rss/search?q={quote(q)}&hl=ru&gl=RU&ceid=RU:ru")
        else:
            urls.append(f"https://news.google.com/rss/search?q={quote(q)}&hl=en-US&gl=US&ceid=US:en")

    def safe(u):
        try:
            return fetch_rss(u)
        except Exception as e:
            log("rss error", str(e)[:80])
            return []

    with ThreadPoolExecutor(max_workers=3) as ex:
        for part in ex.map(safe, urls):
            raw += part

    now = datetime.datetime.now(datetime.timezone.utc)
    items = []
    for x in raw:
        if not x["title"] or not x["dt"]:
            continue
        age_h = (now - x["dt"]).total_seconds() / 3600
        if age_h > 40 or age_h < -1:
            continue
        low = x["title"].lower()
        x["age_h"] = max(age_h, 0)
        x["tk"] = toks(x["title"])
        x["shock"] = sum(w for k, w in SHOCK.items() if k in low)
        if any(k in low for k in BORING):
            x["shock"] = max(0, x["shock"] - 4)
        items.append(x)
    for x in items:
        cl = sum(1 for y in items if y is not x and similar(x["tk"], y["tk"]) >= 0.5)
        x["cluster"] = cl
        rec = 3 if x["age_h"] < 6 else 2 if x["age_h"] < 12 else 1 if x["age_h"] < 24 else 0
        x["score"] = min(x["shock"], 8) + min(cl * 2, 6) + rec
    items = [x for x in items if x["shock"] >= 2]
    items.sort(key=lambda x: -x["score"])
    kept = []
    for x in items:
        if any(similar(x["tk"], k["tk"]) >= 0.5 for k in kept):
            continue
        kept.append(x)
        if len(kept) >= limit:
            break
    return [{"title": x["title"], "source": x["source"], "link": x["link"], "age_h": round(x["age_h"], 1),
             "score": x["score"], "sources_count": x["cluster"] + 1,
             "rumor": any(k in x["title"].lower() for k in RUMOR),
             "sensitive": any(k in x["title"].lower() for k in SENSITIVE)} for x in kept]


def get_news(force=False):
    with NEWS_LOCK:
        if force or time.time() - NEWS_CACHE["ts"] > 1800 or not NEWS_CACHE["items"]:
            items = collect_news()
            if items or force:
                NEWS_CACHE["items"] = items
                NEWS_CACHE["ts"] = time.time()
        return NEWS_CACHE["items"]


def age_txt(h):
    return "только что" if h < 1 else f"{int(h)} ч назад"


def digest_html(items):
    e = html.escape
    d = now_local().strftime("%d.%m %H:%M")
    if not items:
        return f"☀️ <b>Сводка новостей · {d}</b>\n\nСегодня громких инфоповодов не нашлось. Спокойный день."
    lines = [f"📰 <b>Сводка жёстких новостей · {d}</b> (UTC+{TZ})\n"]
    for i, x in enumerate(items, 1):
        tag = " 🧪 <i>слух/разбор</i>" if x["rumor"] else ""
        tag += " 🕊️ <i>тяжёлая тема</i>" if x["sensitive"] else ""
        cnt = f" · {x['sources_count']} СМИ" if x["sources_count"] > 1 else ""
        lines.append(f"{i}. 🔥 <a href=\"{e(x['link'])}\">{e(x['title'])}</a>{tag}\n    <i>{e(x['source'])} · {age_txt(x['age_h'])}{cnt}</i>")
    lines.append("\n💡 Нажми номер — сделаю сценарий мультика.")
    return "\n".join(lines)[:4000]


def digest_kb(items):
    nums = [(f"🎬 {i}", f"ns:{i - 1}") for i, x in enumerate(items, 1) if not x["sensitive"]]
    rows = [nums[i:i + 4] for i in range(0, len(nums), 4)]
    rows.append([("🔄 Обновить", "news:refresh"), ("📱 Студия", {"web_app": APP_URL})])
    return kb(rows)


# ============================================================
# 5. TELEGRAM
# ============================================================
def kb(rows):
    out = []
    for row in rows:
        r = []
        for text, data in row:
            if isinstance(data, dict) and "web_app" in data:
                r.append({"text": text, "web_app": {"url": data["web_app"]}})
            else:
                r.append({"text": text, "callback_data": data})
        out.append(r)
    return {"inline_keyboard": out}


def reply_menu():
    return {
        "keyboard": [
            [{"text": "🎬 Новый сюжет"}, {"text": "🔥 TikTok Радар"}],
            [{"text": "📰 Новости"}, {"text": "📱 Студия", "web_app": {"url": APP_URL}}],
            [{"text": "⚙️ Настройки"}, {"text": "✂️ Видео-студия"}],
        ],
        "resize_keyboard": True,
        "is_persistent": True,
    }


def tg(method, **payload):
    try:
        r = requests.post(f"{API}/{method}", json=payload, timeout=30, proxies=PROXIES)
        return r.json()
    except Exception as e:
        log("tg error", method, str(e)[:100])
        return {}


def send(chat, text, markup=None, pre=False):
    chunks, cur = [], ""
    for line in text.split("\n"):
        if len(cur) + len(line) + 1 > 3500:
            chunks.append(cur)
            cur = ""
        cur += line + "\n"
    chunks.append(cur)
    res = None
    for i, c in enumerate(chunks):
        c = c.strip()
        if not c:
            continue
        payload_text = f"<pre>{html.escape(c)}</pre>" if pre else c
        kw = {"reply_markup": markup} if markup and i == len(chunks) - 1 else {}
        res = tg("sendMessage", chat_id=chat, text=payload_text, parse_mode="HTML", disable_web_page_preview=True, **kw)
        if res and not res.get("ok"):
            log("send failed", str(res)[:200])
            res = tg("sendMessage", chat_id=chat, text=re.sub(r"<[^>]+>", "", payload_text), disable_web_page_preview=True, **kw)
    return res


def edit(chat, mid, text, markup=None):
    res = tg("editMessageText", chat_id=chat, message_id=mid, text=text, parse_mode="HTML", disable_web_page_preview=True,
             **({"reply_markup": markup} if markup else {}))
    if res and not res.get("ok"):
        log("edit failed", str(res)[:150])
    return res


STATE, PREFS, BANNER = {}, {}, {}
DEF_BANNER = {"text": "ПОДПИШИСЬ • @riz_videostudio", "pos": "bottom"}


def user_prefs(chat):
    return PREFS.setdefault(chat, {"theme": "random", "char": "random", "length": 60, "style": "code2d", "voice": "calm_m"})


def st_of(chat):
    return STATE.setdefault(chat, {"story": None, "mode": None, "split": []})


def story_html(s):
    e = html.escape
    beats = "\n".join(f"<b>{b['t']}</b>  {e(b['text'])}" for b in s["beats"])
    ep = f" · серия {s['ep']}" if s.get("ep", 1) > 1 else ""
    return (f"🎬 <b>{e(s['title'])}</b>{ep}\n"
            f"{s['theme_icon']} {e(s['theme_name'])} · 👤 {e(s['char_name'])} · ⏱ {s['length']}с · {s['style_icon']} {e(s['style_name'])}\n\n"
            f"⚡ <b>Хук (0:00–0:03)</b>\n<blockquote>{e(s['hook'])}</blockquote>\n"
            f"🎮 <b>HUD</b>\n<code>{e(s['hud'])}</code>\n\n"
            f"📜 <b>Сцены</b>\n{beats}\n\n"
            f"🪝 <b>Клиффхэнгер ({s['cliff_t']})</b>\n<i>{e(s['cliff'])}</i>")


def story_kb():
    return kb([[("🔁 Ещё вариант", "st:new"), ("✏️ Править", "ed:menu")],
               [("🎬 Серия 2", "st:cont"), ("🎨 Промпты", "pr:menu")],
               [("⚙️ Настройки", "set:menu"), ("📱 Студия", {"web_app": APP_URL})]])


def main_kb():
    return kb([[("📱 Открыть Студию", {"web_app": APP_URL})],
               [("🎲 Сюжет", "st:new"), ("🔥 TikTok Радар", "tt:show")],
               [("📰 Новости", "news:show"), ("⚙️ Настройки", "set:menu")],
               [("✂️ Видео (Баннер / Сплиттер)", "vid:menu")]])


def give_story(chat, s):
    st_of(chat)["story"] = s
    send(chat, story_html(s), story_kb())


def new_story(chat):
    p = user_prefs(chat)
    return build_story(None if p["theme"] == "random" else p["theme"], None if p["char"] == "random" else p["char"], p["length"], p["style"], p["voice"])


def settings_kb(chat):
    p = user_prefs(chat)
    th = "Случайно" if p["theme"] == "random" else THEMES[p["theme"]][1]
    ch = "Случайно" if p["char"] == "random" else CHARS[p["char"]][0]
    return kb([[(f"🎭 Тема: {th}", "set:theme")], [(f"👤 Герой: {ch}", "set:char")],
               [(f"🎨 Стиль: {STYLES[p['style']][1]}", "set:style")], [(f"⏱ Длина: {p['length']} с", "set:length")],
               [(f"🎙️ Голос: {VOICES[p['voice']][1]}", "set:voice")], [("🎲 Создать сюжет", "st:new")]])


def picker(kind):
    if kind == "theme":
        rows = [[("🎲 Случайно", "pk:theme:random")]] + [[(f"{v[0]} {v[1]}", f"pk:theme:{k}")] for k, v in THEMES.items()]
    elif kind == "char":
        rows = [[("🎲 Случайно", "pk:char:random")]] + [[(f"{v[0]} — {v[1]}", f"pk:char:{k}")] for k, v in CHARS.items()]
    elif kind == "style":
        items = list(STYLES.items())
        rows = [[(f"{v[0]} {v[1]}", f"pk:style:{k}") for k, v in items[i:i + 2]] for i in range(0, len(items), 2)]
    elif kind == "length":
        rows = [[(f"{L} с", f"pk:length:{L}") for L in LENGTHS]]
    else:
        rows = [[(f"{v[0]} {v[1]}", f"pk:voice:{k}")] for k, v in VOICES.items()]
    rows.append([("⬅️ Назад", "set:menu")])
    return kb(rows)


PICK_TITLE = {"theme": "тему", "char": "героя", "style": "стиль анимации", "length": "длину", "voice": "голос"}


def send_tiktok_report(chat, force=False):
    send(chat, "⏳ Сканирую реальные ролики TikTok в вашей нише…")
    items = get_tiktok(force=force)
    send(chat, tiktok_html(items), tiktok_kb(items))


def send_news_report(chat, force=False):
    send(chat, "⏳ Собираю жёсткие новости за сутки…")
    items = get_news(force=force)
    send(chat, digest_html(items), digest_kb(items))


def on_callback(cb):
    chat = cb["message"]["chat"]["id"]
    mid = cb["message"]["message_id"]
    data = cb.get("data", "")
    tg("answerCallbackQuery", callback_query_id=cb["id"])
    st = st_of(chat)
    p = user_prefs(chat)
    if data == "st:new":
        give_story(chat, new_story(chat))
    elif data == "st:cont":
        if st["story"]:
            give_story(chat, continue_story(st["story"]))
        else:
            send(chat, "Сначала создай сюжет 👇", main_kb())
    elif data == "ed:menu":
        edit(chat, mid, "✏️ <b>Что поменять в сюжете?</b>", kb([
            [("😱 Страшнее", "ed:darker"), ("⚡ Новый хук", "ed:hook")], [("🌀 Поворот", "ed:twist"), ("👤 Другой герой", "ed:hero")],
            [("⏱ Короче", "ed:shorter"), ("⏳ Длиннее", "ed:longer")], [("⬅️ Назад", "ed:back")]]))
    elif data == "ed:back":
        edit(chat, mid, story_html(st["story"]) if st["story"] else "Готово.", story_kb())
    elif data.startswith("ed:") and st["story"]:
        give_story(chat, edit_story(st["story"], data[3:]))
    elif data == "pr:menu":
        edit(chat, mid, "🎨 <b>Какой промпт нужен?</b>\nСтиль можно сменить в ⚙️ Настройках.", kb([
            [("🎥 Для нейросети-видео", "pr:video")], [("💻 Для кодовой анимации", "pr:code")],
            [("🎙️ Для озвучки", "pr:voice"), ("🖼 Обложка", "pr:cover")], [("🎨 Сменить стиль", "set:style"), ("⬅️ Назад", "ed:back")]]))
    elif data.startswith("pr:") and st["story"]:
        send(chat, make_prompts(st["story"], data[3:]), kb([[("🎨 Другой промпт", "pr:menu"), ("📱 Студия", {"web_app": APP_URL})]]), pre=True)
    elif data == "set:menu":
        edit(chat, mid, "⚙️ <b>Настройки генератора</b>\nВыбери параметры — потом жми «Создать».", settings_kb(chat))
    elif data in ("set:theme", "set:char", "set:style", "set:length", "set:voice"):
        kind = data[4:]
        edit(chat, mid, f"Выбери <b>{PICK_TITLE[kind]}</b>:", picker(kind))
    elif data.startswith("pk:"):
        _, kind, val = data.split(":")
        p[kind] = int(val) if kind == "length" else val
        if st["story"] and kind in ("style", "voice", "length"):
            st["story"] = edit_story(st["story"], kind, val)
        edit(chat, mid, "⚙️ <b>Настройки обновлены</b>", settings_kb(chat))
    elif data in ("tt:show", "tt:refresh"):
        send_tiktok_report(chat, force=(data == "tt:refresh"))
    elif data.startswith("tt:"):
        items = TT_CACHE["items"]
        i = int(data[3:])
        if i < len(items):
            give_story(chat, enhance_idea(items[i]["desc"], p["char"] if p["char"] != "random" else None, p["length"], p["style"], p["voice"], src="tiktok", theme=items[i]["theme"]))
    elif data in ("news:show", "news:refresh"):
        send_news_report(chat, force=(data == "news:refresh"))
    elif data.startswith("ns:"):
        items = NEWS_CACHE["items"]
        i = int(data[3:])
        if i < len(items):
            give_story(chat, enhance_idea(items[i]["title"], p["char"] if p["char"] != "random" else None, p["length"], p["style"], p["voice"], src="news"))
    elif data == "vid:menu":
        send(chat, video_help(chat), kb([[("🏷 Баннер", "vid:banner"), ("🪟 Сплиттер", "vid:split")]]))
    elif data == "vid:banner":
        start_banner(chat)
    elif data == "vid:split":
        start_split(chat)


def video_help(chat):
    b = BANNER.get(chat, DEF_BANNER)
    return ("✂️ <b>Видео-студия</b>\n\n🏷 <b>Баннер</b> — пришли видео, подпись = текст баннера. Позицию задай в подписи: "
            "<code>#верх</code> / <code>#центр</code> / <code>#низ</code>. Без подписи возьму сохранённый: "
            f"<i>{html.escape(b['text'])}</i> ({b['pos']}).\n\n🪟 <b>Сплиттер</b> — пришли два видео подряд: первое сверху, второе снизу (9:16).\n\n"
            "⚠️ Telegram позволяет ботам скачивать файлы до 20 МБ.")


def start_banner(chat):
    st_of(chat).update(mode=None, split=[])
    send(chat, "🏷 Пришли видео. В подписи можно написать текст баннера и <code>#верх</code>, <code>#центр</code> или <code>#низ</code>.")


def start_split(chat):
    st_of(chat).update(mode="split", split=[])
    send(chat, "🪟 Пришли <b>первое видео</b> (оно будет сверху). Потом второе — снизу.")


# ---------- видео ----------
def ffmpeg_exe():
    p = shutil.which("ffmpeg")
    if p:
        return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def download(file_id, path):
    info = tg("getFile", file_id=file_id)
    fp = info.get("result", {}).get("file_path")
    if not fp:
        raise RuntimeError("Не удалось получить файл (возможно, больше 20 МБ)")
    r = requests.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{fp}", timeout=120, proxies=PROXIES, stream=True)
    r.raise_for_status()
    with open(path, "wb") as f:
        for ch in r.iter_content(1 << 16):
            f.write(ch)
    return path


def probe_size(ff, src):
    r = subprocess.run([ff, "-i", src], capture_output=True, text=True)
    m = re.search(r"Video:.*?,\s*(\d{2,5})x(\d{2,5})", r.stderr)
    if not m:
        raise RuntimeError("Не удалось прочитать размеры видео")
    return int(m.group(1)), int(m.group(2))


def make_banner_png(text, width, path):
    from PIL import Image, ImageDraw, ImageFont
    height = max(int(width * 0.13), 60)
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = int(height * 0.12)
    d.rounded_rectangle([pad, pad, width - pad, height - pad], radius=int(height * 0.3), fill=(8, 13, 22, 215),
                        outline=(237, 191, 116, 255), width=max(2, height // 40))
    fpath = os.path.join(BASE, "font.ttf")
    size = int(height * 0.42)
    font = None
    while size > 12:
        try:
            font = ImageFont.truetype(fpath, size)
        except Exception:
            font = ImageFont.load_default()
            break
        if d.textlength(text, font=font) <= width * 0.84:
            break
        size -= 2
    d.text((width / 2, height / 2), text, font=font, fill=(255, 255, 255, 255), anchor="mm")
    img.save(path)
    return path


def send_video(chat, path, caption=""):
    with open(path, "rb") as f:
        r = requests.post(f"{API}/sendVideo", data={"chat_id": chat, "supports_streaming": "true", "caption": caption},
                          files={"video": f}, timeout=180, proxies=PROXIES)
    return r.json()


def run_ff(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("FFmpeg: " + r.stderr[-300:])


def render_banner(ff, src, text, pos, out, workdir):
    w, _ = probe_size(ff, src)
    png = make_banner_png(text, w, os.path.join(workdir, "b.png"))
    y = {"top": "H*0.04", "center": "(H-h)/2", "bottom": "H-h-H*0.06"}.get(pos, "H-h-H*0.06")
    run_ff([ff, "-y", "-i", src, "-i", png, "-filter_complex",
            f"[0:v][1:v]overlay=0:{y},scale=trunc(iw/2)*2:trunc(ih/2)*2[v]", "-map", "[v]", "-map", "0:a?",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart", out])


def render_split(ff, a, b, out):
    fc = ("[0:v]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960,setsar=1,fps=30[t];"
          "[1:v]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960,setsar=1,fps=30[b];"
          "[t][b]vstack=inputs=2:shortest=1[v]")
    run_ff([ff, "-y", "-i", a, "-i", b, "-filter_complex", fc, "-map", "[v]", "-map", "0:a?", "-shortest",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart", out])


def job_banner(chat, file_id, text, pos):
    try:
        ff = ffmpeg_exe()
        if not ff:
            raise RuntimeError("FFmpeg не найден на сервере")
        send(chat, "⏳ Накладываю баннер…")
        with tempfile.TemporaryDirectory() as d:
            src = download(file_id, os.path.join(d, "in.mp4"))
            out = os.path.join(d, "out.mp4")
            render_banner(ff, src, text, pos, out, d)
            res = send_video(chat, out, f"🏷 {text}")
            if not res.get("ok"):
                send(chat, "Не получилось отправить результат: " + html.escape(str(res.get("description"))))
    except Exception as e:
        log("banner error", e)
        send(chat, "❌ Ошибка: " + html.escape(str(e)[:300]))


def job_split(chat, ids):
    try:
        ff = ffmpeg_exe()
        if not ff:
            raise RuntimeError("FFmpeg не найден на сервере")
        send(chat, "⏳ Склеиваю сплиттер 1080×1920…")
        with tempfile.TemporaryDirectory() as d:
            a = download(ids[0], os.path.join(d, "a.mp4"))
            b = download(ids[1], os.path.join(d, "b.mp4"))
            out = os.path.join(d, "out.mp4")
            render_split(ff, a, b, out)
            res = send_video(chat, out, "🪟 Сплиттер готов")
            if not res.get("ok"):
                send(chat, "Не получилось отправить результат: " + html.escape(str(res.get("description"))))
    except Exception as e:
        log("split error", e)
        send(chat, "❌ Ошибка: " + html.escape(str(e)[:300]))


def parse_caption(cap, default):
    pos = default["pos"]
    text = cap
    for key, val in (("#верх", "top"), ("#top", "top"), ("#центр", "center"), ("#center", "center"), ("#низ", "bottom"), ("#bottom", "bottom")):
        if key in text.lower():
            pos = val
            text = re.sub(re.escape(key), "", text, flags=re.I)
    text = text.strip() or default["text"]
    return text[:60], pos


def on_video(chat, m, v):
    st = st_of(chat)
    if (v.get("file_size") or 0) > 20 * 1024 * 1024:
        send(chat, "⚠️ Файл больше 20 МБ — Telegram не даёт боту его скачать.")
        return
    if st["mode"] == "split":
        st["split"].append(v["file_id"])
        if len(st["split"]) == 1:
            send(chat, "✅ Верхнее видео принято. Теперь пришли <b>второе</b> (нижнее).")
            return
        ids, st["split"], st["mode"] = st["split"][:2], [], None
        threading.Thread(target=job_split, args=(chat, ids), daemon=True).start()
        return
    text, pos = parse_caption((m.get("caption") or "").strip(), BANNER.get(chat, DEF_BANNER))
    threading.Thread(target=job_banner, args=(chat, v["file_id"], text, pos), daemon=True).start()


WELCOME = ("👋 <b>VideoStudio — студия вирусных мультиков</b>\n\n"
           "🔥 <b>TikTok-радар (08:00):</b> реальные ролики в вашей нише (просмотры, подписчики, x-виральность)\n"
           "📰 <b>Новости (08:00):</b> громкие инфоповоды за сутки\n"
           "🎲 <b>Сюжеты:</b> 8 тем, 8 героев, 12 стилей, 6 голосов, правки и Серия 2\n"
           "🎨 <b>Промпты:</b> нейросеть-видео, кодовая анимация, озвучка, обложка\n"
           "🚀 <b>Улучшатор:</b> напиши любую идею в чат — перепишу без плагиата\n"
           "✂️ <b>Видео:</b> баннер и сплиттер 9:16\n\n"
           "Выбирай действие кнопками ниже 👇")


def send_main_menu(chat):
    send(chat, WELCOME, reply_menu())
    send(chat, "📌 <b>Быстрые действия:</b>", main_kb())


def on_message(m):
    chat = m["chat"]["id"]
    text = (m.get("text") or "").strip()
    v = m.get("video") or m.get("animation")
    doc = m.get("document")
    if doc and str(doc.get("mime_type", "")).startswith("video"):
        v = doc
    if v:
        return on_video(chat, m, v)
    if not text:
        return

    # Быстрые кнопки нижней клавиатуры
    if text == "🎬 Новый сюжет":
        return give_story(chat, new_story(chat))
    if text == "🔥 TikTok Радар":
        return send_tiktok_report(chat, force=True)
    if text == "📰 Новости":
        return send_news_report(chat, force=True)
    if text == "⚙️ Настройки":
        return send(chat, "⚙️ <b>Настройки генератора</b>", settings_kb(chat))
    if text == "✂️ Видео-студия":
        return send(chat, video_help(chat), kb([[("🏷 Баннер", "vid:banner"), ("🪟 Сплиттер", "vid:split")]]))

    if text.startswith("/"):
        cmd, _, arg = text.partition(" ")
        cmd = cmd.split("@")[0].lower()
        if cmd in ("/start", "/help", "/menu"):
            if arg.strip() == "banner":
                return start_banner(chat)
            if arg.strip() == "split":
                return start_split(chat)
            return send_main_menu(chat)
        if cmd in ("/app", "/studio"):
            return send(chat, "📱 Открой студию:", kb([[("📱 Открыть Студию", {"web_app": APP_URL})]]))
        if cmd == "/story":
            return give_story(chat, new_story(chat))
        if cmd == "/tiktok":
            return send_tiktok_report(chat, force=True)
        if cmd in ("/news", "/daily"):
            return send_news_report(chat, force=True)
        if cmd == "/settings":
            return send(chat, "⚙️ <b>Настройки генератора</b>", settings_kb(chat))
        if cmd == "/banner":
            return start_banner(chat)
        if cmd == "/split":
            return start_split(chat)
        if cmd == "/myid":
            return send(chat, f"Твой chat_id: <code>{chat}</code>")
        if cmd == "/idea":
            if not arg.strip():
                return send(chat, "Напиши так: <code>/idea что если исчезнут все пароли</code>")
            text = arg
        else:
            return send_main_menu(chat)

    p = user_prefs(chat)
    s = enhance_idea(text, p["char"] if p["char"] != "random" else None, p["length"], p["style"], p["voice"])
    st_of(chat)["story"] = s
    send(chat, "🚀 <b>Идея улучшена (антиплагиат)</b>\n\n" + story_html(s) + "\n\n<b>Что изменено:</b>\n• " + "\n• ".join(html.escape(c) for c in s["changes"]), story_kb())


def handle(u):
    if "callback_query" in u:
        on_callback(u["callback_query"])
    elif "message" in u:
        on_message(u["message"])


def poll_loop():
    if not BOT_TOKEN:
        log("BOT_TOKEN не задан — бот Telegram выключен (работает только веб-API)")
        return
    tg("deleteWebhook")
    tg("setMyCommands", commands=[
        {"command": "start", "description": "Главное меню"},
        {"command": "tiktok", "description": "Реальные тренды TikTok"},
        {"command": "news", "description": "Жёсткие новости за сутки"},
        {"command": "story", "description": "Новый сюжет мультика"},
        {"command": "settings", "description": "Тема, герой, стиль, голос"},
        {"command": "banner", "description": "Баннер на видео"},
        {"command": "split", "description": "Сплиттер 9:16"},
        {"command": "app", "description": "Открыть мини-приложение"},
    ])
    tg("setChatMenuButton", menu_button={"type": "web_app", "text": "📱 Студия", "web_app": {"url": APP_URL}})
    log("polling started")
    offset = 0
    while True:
        try:
            r = requests.get(f"{API}/getUpdates", params={"offset": offset, "timeout": 25, "allowed_updates": json.dumps(["message", "callback_query"])},
                             timeout=40, proxies=PROXIES)
            j = r.json()
            if not j.get("ok"):
                log("getUpdates", str(j)[:150])
                time.sleep(5)
                continue
            for u in j["result"]:
                offset = u["update_id"] + 1
                try:
                    handle(u)
                except Exception:
                    traceback.print_exc()
        except Exception as e:
            log("poll error", str(e)[:100])
            time.sleep(3)


def send_morning_bundle(chat):
    tt = get_tiktok(force=True)
    send(chat, tiktok_html(tt), tiktok_kb(tt))
    nw = get_news(force=True)
    send(chat, digest_html(nw), digest_kb(nw))
    return len(tt), len(nw)


def scheduler_loop():
    last = ""
    while True:
        try:
            n = now_local()
            today = n.strftime("%Y-%m-%d")
            if BOT_TOKEN and CHAT_ID and n.hour == DIGEST_HOUR and last != today:
                tt_n, nw_n = send_morning_bundle(CHAT_ID)
                last = today
                log(f"morning bundle sent: tt={tt_n}, news={nw_n}")
        except Exception:
            traceback.print_exc()
        time.sleep(30)


def keepalive_loop():
    while True:
        time.sleep(300)
        if SELF_URL:
            try:
                requests.get(SELF_URL + "/api/health", timeout=20)
            except Exception:
                pass


# ============================================================
# 6. WEB API ДЛЯ MINI APP
# ============================================================
def meta():
    return {"themes": [{"id": k, "icon": v[0], "name": v[1], "desc": v[2]} for k, v in THEMES.items()],
            "chars": [{"id": k, "name": v[0], "desc": v[1]} for k, v in CHARS.items()],
            "styles": [{"id": k, "icon": v[0], "name": v[1]} for k, v in STYLES.items()],
            "voices": [{"id": k, "icon": v[0], "name": v[1]} for k, v in VOICES.items()],
            "lengths": LENGTHS}


def verify_init(init_data):
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
        h = pairs.pop("hash", None)
        s = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
        secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calc = hmac.new(secret, s.encode(), hashlib.sha256).hexdigest()
        if h and hmac.compare_digest(calc, h):
            return json.loads(pairs["user"])["id"]
    except Exception:
        pass
    return None


def api_route(path, q, data):
    if path == "/api/health":
        return {"ok": True, "bot_active": bool(BOT_TOKEN), "time": now_local().isoformat(),
                "tiktok_cached": len(TT_CACHE["items"]), "news_cached": len(NEWS_CACHE["items"])}
    if path == "/api/meta":
        return meta()
    if path == "/api/tiktok":
        items = get_tiktok(force=bool(q.get("refresh")))
        return {"items": items, "updated": TT_CACHE["ts"]}
    if path == "/api/news":
        items = get_news(force=bool(q.get("refresh")))
        return {"items": items, "updated": NEWS_CACHE["ts"]}
    if path == "/api/story":
        return build_story(data.get("theme"), data.get("char"), data.get("length", 60), data.get("style", "code2d"), data.get("voice", "calm_m"))
    if path == "/api/enhance":
        return enhance_idea(data.get("text", ""), data.get("char"), data.get("length", 60), data.get("style", "code2d"),
                            data.get("voice", "calm_m"), data.get("src", "idea"), data.get("theme"))
    if path == "/api/edit":
        return edit_story(data["story"], data.get("action"), data.get("value"))
    if path == "/api/continue":
        return continue_story(data["story"])
    if path == "/api/prompts":
        return {"text": make_prompts(data["story"], data.get("kind", "video"))}
    if path == "/api/send":
        uid = verify_init(data.get("initData", ""))
        if not uid:
            return {"ok": False, "error": "Откройте приложение из Telegram"}
        s = data["story"]
        if data.get("kind"):
            send(uid, make_prompts(s, data["kind"]), pre=True)
        else:
            send(uid, story_html(s), story_kb())
        st_of(uid)["story"] = s
        return {"ok": True}
    if path == "/api/banner":
        uid = verify_init(data.get("initData", ""))
        if not uid:
            return {"ok": False, "error": "Откройте приложение из Telegram"}
        pos = data.get("pos") if data.get("pos") in ("top", "center", "bottom") else "bottom"
        BANNER[uid] = {"text": (data.get("text") or "ПОДПИШИСЬ")[:60], "pos": pos}
        return {"ok": True}
    return None


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, HEAD")

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        u = urlparse(self.path)
        if u.path.startswith("/api/"):
            try:
                res = api_route(u.path, {k: v[0] for k, v in parse_qs(u.query).items()}, {})
            except Exception as e:
                traceback.print_exc()
                return self._json(500, {"error": str(e)})
            return self._json(200 if res is not None else 404, res if res is not None else {"error": "not found"})
        for cand in ("index.html", os.path.join("webapp", "index.html")):
            fp = os.path.join(BASE, cand)
            if os.path.exists(fp):
                with open(fp, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(body)
                return
        self._json(200, {"ok": True, "service": "VideoStudio"})

    def do_POST(self):
        u = urlparse(self.path)
        try:
            n = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(n) or b"{}")
            res = api_route(u.path, {}, data)
        except Exception as e:
            traceback.print_exc()
            return self._json(500, {"error": str(e)})
        self._json(200 if res is not None else 404, res if res is not None else {"error": "not found"})

    def log_message(self, *a):
        pass


def main():
    for fn in (poll_loop, scheduler_loop, keepalive_loop):
        threading.Thread(target=fn, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    log(f"web on :{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
