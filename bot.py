# -*- coding: utf-8 -*-
"""
GD Music Helper — Telegram bot
Single-file version: локалізація, анкета, Newgrounds.io API, донати.
"""

import asyncio
import base64
import json
import logging
import os
import re

import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
    ReplyKeyboardMarkup,
)
from dotenv import load_dotenv

# =========================================================
# CONFIG
# =========================================================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
NG_APP_ID = os.getenv("NG_APP_ID", "")
NG_ENCRYPTION_KEY = os.getenv("NG_ENCRYPTION_KEY", "")

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не знайдено у .env")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("gd_bot")

# =========================================================
# LOCALES (13 мов)
# =========================================================
LOCALES = {
    "en": {
        "name": "English", "flag": "🇬🇧",
        "welcome": "🎵 <b>GD Music Helper</b>\n\nFind the perfect track for your Geometry Dash level in seconds.\n\nChoose an action below:",
        "btn_search": "🔍 Find a track", "btn_lang": "🌐 Language",
        "btn_donate": "⭐ Support", "btn_help": "❓ Help",
        "ask_length": "🎧 Step 1/5 — Choose track <b>length</b>:",
        "ask_genre": "🎼 Step 2/5 — Choose <b>genre</b>:",
        "ask_mood": "🎭 Step 3/5 — Choose <b>mood</b>:",
        "ask_bpm": "⚡ Step 4/5 — Choose <b>BPM</b> range:",
        "ask_vocals": "🎤 Step 5/5 — <b>Vocals</b>?",
        "searching": "🔎 Searching Newgrounds...",
        "no_results": "😔 No tracks found. Try different filters.",
        "results_header": "🎵 <b>Found {n} tracks:</b>\n\n",
        "cancelled": "❌ Search cancelled.",
        "help_text": "ℹ️ <b>How to use:</b>\n\n1. Tap <b>Find a track</b>\n2. Fill out the short form\n3. Get matching tracks from Newgrounds\n\n⭐ Support us with Telegram Stars!",
        "donate_text": "⭐ <b>Support GD Music Helper</b>\n\nYour donation helps keep the bot running.\nChoose an amount:",
        "donate_thanks": "💛 Thank you for supporting the project!",
        "lang_changed": "✅ Language changed to English",
        "start_search_again": "🔄 Search again",
        "choose_lang": "🌐 Choose your language:",
        "btn_cancel": "❌ Cancel",
        "length_opt_1": "30s – 1m", "length_opt_2": "1m – 1m 30s",
        "length_opt_3": "1m 30s – 2m", "length_opt_4": "2m – 3m",
        "length_opt_5": "3m+",
        "genre_opt_1": "Electronic / EDM", "genre_opt_2": "Dubstep / Bass",
        "genre_opt_3": "Drum & Bass", "genre_opt_4": "House / Techno",
        "genre_opt_5": "Rock / Metal", "genre_opt_6": "Orchestral",
        "genre_opt_7": "Chiptune", "genre_opt_8": "Other",
        "mood_opt_1": "Energetic", "mood_opt_2": "Dark / Intense",
        "mood_opt_3": "Happy / Chill", "mood_opt_4": "Sad / Emotional",
        "mood_opt_5": "Mysterious",
        "bpm_opt_1": "< 100", "bpm_opt_2": "100–140",
        "bpm_opt_3": "140–180", "bpm_opt_4": "180+",
        "vocals_opt_1": "Yes", "vocals_opt_2": "No", "vocals_opt_3": "Doesn't matter",
    },
    "ru": {
        "name": "Русский", "flag": "🇷🇺",
        "welcome": "🎵 <b>GD Music Helper</b>\n\nНайди идеальный трек для своего уровня в Geometry Dash за секунды.\n\nВыбери действие:",
        "btn_search": "🔍 Найти трек", "btn_lang": "🌐 Язык",
        "btn_donate": "⭐ Поддержать", "btn_help": "❓ Помощь",
        "ask_length": "🎧 Шаг 1/5 — Выбери <b>длительность</b>:",
        "ask_genre": "🎼 Шаг 2/5 — Выбери <b>жанр</b>:",
        "ask_mood": "🎭 Шаг 3/5 — Выбери <b>настроение</b>:",
        "ask_bpm": "⚡ Шаг 4/5 — Выбери диапазон <b>BPM</b>:",
        "ask_vocals": "🎤 Шаг 5/5 — <b>Вокал</b>?",
        "searching": "🔎 Ищу на Newgrounds...",
        "no_results": "😔 Ничего не найдено. Попробуй другие фильтры.",
        "results_header": "🎵 <b>Найдено {n} треков:</b>\n\n",
        "cancelled": "❌ Поиск отменён.",
        "help_text": "ℹ️ <b>Как пользоваться:</b>\n\n1. Нажми <b>Найти трек</b>\n2. Заполни анкету\n3. Получи подборку с Newgrounds\n\n⭐ Поддержи проект звёздами!",
        "donate_text": "⭐ <b>Поддержать GD Music Helper</b>\n\nТвой донат помогает боту работать.\nВыбери сумму:",
        "donate_thanks": "💛 Спасибо за поддержку!",
        "lang_changed": "✅ Язык изменён на Русский",
        "start_search_again": "🔄 Искать снова",
        "choose_lang": "🌐 Выбери язык:",
        "btn_cancel": "❌ Отмена",
        "length_opt_1": "30с – 1м", "length_opt_2": "1м – 1м 30с",
        "length_opt_3": "1м 30с – 2м", "length_opt_4": "2м – 3м",
        "length_opt_5": "3м+",
        "genre_opt_1": "Electronic / EDM", "genre_opt_2": "Dubstep / Bass",
        "genre_opt_3": "Drum & Bass", "genre_opt_4": "House / Techno",
        "genre_opt_5": "Rock / Metal", "genre_opt_6": "Orchestral",
        "genre_opt_7": "Chiptune", "genre_opt_8": "Другое",
        "mood_opt_1": "Энергичное", "mood_opt_2": "Тёмное / Напряжённое",
        "mood_opt_3": "Весёлое / Спокойное", "mood_opt_4": "Грустное / Эмоциональное",
        "mood_opt_5": "Загадочное",
        "bpm_opt_1": "< 100", "bpm_opt_2": "100–140",
        "bpm_opt_3": "140–180", "bpm_opt_4": "180+",
        "vocals_opt_1": "Да", "vocals_opt_2": "Нет", "vocals_opt_3": "Не важно",
    },
    "uk": {
        "name": "Українська", "flag": "🇺🇦",
        "welcome": "🎵 <b>GD Music Helper</b>\n\nЗнайди ідеальний трек для свого рівня в Geometry Dash за секунди.\n\nОбери дію:",
        "btn_search": "🔍 Знайти трек", "btn_lang": "🌐 Мова",
        "btn_donate": "⭐ Підтримати", "btn_help": "❓ Допомога",
        "ask_length": "🎧 Крок 1/5 — Обери <b>довжину</b>:",
        "ask_genre": "🎼 Крок 2/5 — Обери <b>жанр</b>:",
        "ask_mood": "🎭 Крок 3/5 — Обери <b>настрій</b>:",
        "ask_bpm": "⚡ Крок 4/5 — Обери діапазон <b>BPM</b>:",
        "ask_vocals": "🎤 Крок 5/5 — <b>Вокал</b>?",
        "searching": "🔎 Шукаю на Newgrounds...",
        "no_results": "😔 Нічого не знайдено. Спробуй інші фільтри.",
        "results_header": "🎵 <b>Знайдено {n} треків:</b>\n\n",
        "cancelled": "❌ Пошук скасовано.",
        "help_text": "ℹ️ <b>Як користуватись:</b>\n\n1. Натисни <b>Знайти трек</b>\n2. Заповни анкету\n3. Отримай підбірку з Newgrounds\n\n⭐ Підтри проєкт зірками!",
        "donate_text": "⭐ <b>Підтримати GD Music Helper</b>\n\nТвій донат допомагає боту працювати.\nОбери суму:",
        "donate_thanks": "💛 Дякую за підтримку!",
        "lang_changed": "✅ Мову змінено на Українську",
        "start_search_again": "🔄 Шукати знову",
        "choose_lang": "🌐 Обери мову:",
        "btn_cancel": "❌ Скасувати",
        "length_opt_1": "30с – 1хв", "length_opt_2": "1хв – 1хв 30с",
        "length_opt_3": "1хв 30с – 2хв", "length_opt_4": "2хв – 3хв",
        "length_opt_5": "3хв+",
        "genre_opt_1": "Electronic / EDM", "genre_opt_2": "Dubstep / Bass",
        "genre_opt_3": "Drum & Bass", "genre_opt_4": "House / Techno",
        "genre_opt_5": "Rock / Metal", "genre_opt_6": "Orchestral",
        "genre_opt_7": "Chiptune", "genre_opt_8": "Інше",
        "mood_opt_1": "Енергійне", "mood_opt_2": "Темне / Напружене",
        "mood_opt_3": "Веселе / Спокійне", "mood_opt_4": "Сумне / Емоційне",
        "mood_opt_5": "Загадкове",
        "bpm_opt_1": "< 100", "bpm_opt_2": "100–140",
        "bpm_opt_3": "140–180", "bpm_opt_4": "180+",
        "vocals_opt_1": "Так", "vocals_opt_2": "Ні", "vocals_opt_3": "Не важливо",
    },
    "es": {
        "name": "Español", "flag": "🇪🇸",
        "welcome": "🎵 <b>GD Music Helper</b>\n\nEncuentra la pista perfecta para tu nivel de Geometry Dash en segundos.\n\nElige una acción:",
        "btn_search": "🔍 Buscar pista", "btn_lang": "🌐 Idioma",
        "btn_donate": "⭐ Apoyar", "btn_help": "❓ Ayuda",
        "ask_length": "🎧 Paso 1/5 — Elige la <b>duración</b>:",
        "ask_genre": "🎼 Paso 2/5 — Elige el <b>género</b>:",
        "ask_mood": "🎭 Paso 3/5 — Elige el <b>ambiente</b>:",
        "ask_bpm": "⚡ Paso 4/5 — Elige el rango de <b>BPM</b>:",
        "ask_vocals": "🎤 Paso 5/5 — ¿<b>Voz</b>?",
        "searching": "🔎 Buscando en Newgrounds...",
        "no_results": "😔 No se encontraron pistas. Prueba otros filtros.",
        "results_header": "🎵 <b>Encontradas {n} pistas:</b>\n\n",
        "cancelled": "❌ Búsqueda cancelada.",
        "help_text": "ℹ️ <b>Cómo usar:</b>\n\n1. Pulsa <b>Buscar pista</b>\n2. Rellena el formulario\n3. Recibe pistas de Newgrounds\n\n⭐ ¡Apóyanos con Telegram Stars!",
        "donate_text": "⭐ <b>Apoyar GD Music Helper</b>\n\nTu donación ayuda a mantener el bot.\nElige una cantidad:",
        "donate_thanks": "💛 ¡Gracias por apoyar!",
        "lang_changed": "✅ Idioma cambiado a Español",
        "start_search_again": "🔄 Buscar de nuevo",
        "choose_lang": "🌐 Elige tu idioma:",
        "btn_cancel": "❌ Cancelar",
        "length_opt_1": "30s – 1min", "length_opt_2": "1min – 1min 30s",
        "length_opt_3": "1min 30s – 2min", "length_opt_4": "2min – 3min",
        "length_opt_5": "3min+",
        "genre_opt_1": "Electronic / EDM", "genre_opt_2": "Dubstep / Bass",
        "genre_opt_3": "Drum & Bass", "genre_opt_4": "House / Techno",
        "genre_opt_5": "Rock / Metal", "genre_opt_6": "Orquestal",
        "genre_opt_7": "Chiptune", "genre_opt_8": "Otro",
        "mood_opt_1": "Enérgico", "mood_opt_2": "Oscuro / Intenso",
        "mood_opt_3": "Alegre / Relajado", "mood_opt_4": "Triste / Emocional",
        "mood_opt_5": "Misterioso",
        "bpm_opt_1": "< 100", "bpm_opt_2": "100–140",
        "bpm_opt_3": "140–180", "bpm_opt_4": "180+",
        "vocals_opt_1": "Sí", "vocals_opt_2": "No", "vocals_opt_3": "Da igual",
    },
    "pt": {
        "name": "Português", "flag": "🇵🇹",
        "welcome": "🎵 <b>GD Music Helper</b>\n\nEncontre a faixa perfeita para o seu nível de Geometry Dash em segundos.\n\nEscolha uma ação:",
        "btn_search": "🔍 Buscar faixa", "btn_lang": "🌐 Idioma",
        "btn_donate": "⭐ Apoiar", "btn_help": "❓ Ajuda",
        "ask_length": "🎧 Passo 1/5 — Escolha a <b>duração</b>:",
        "ask_genre": "🎼 Passo 2/5 — Escolha o <b>gênero</b>:",
        "ask_mood": "🎭 Passo 3/5 — Escolha o <b>clima</b>:",
        "ask_bpm": "⚡ Passo 4/5 — Escolha o intervalo de <b>BPM</b>:",
        "ask_vocals": "🎤 Passo 5/5 — <b>Voz</b>?",
        "searching": "🔎 Buscando no Newgrounds...",
        "no_results": "😔 Nenhuma faixa encontrada. Tente outros filtros.",
        "results_header": "🎵 <b>Encontradas {n} faixas:</b>\n\n",
        "cancelled": "❌ Busca cancelada.",
        "help_text": "ℹ️ <b>Como usar:</b>\n\n1. Toque em <b>Buscar faixa</b>\n2. Preencha o formulário\n3. Receba faixas do Newgrounds\n\n⭐ Apoie-nos com Telegram Stars!",
        "donate_text": "⭐ <b>Apoiar GD Music Helper</b>\n\nSua doação ajuda a manter o bot.\nEscolha um valor:",
        "donate_thanks": "💛 Obrigado por apoiar!",
        "lang_changed": "✅ Idioma alterado para Português",
        "start_search_again": "🔄 Buscar novamente",
        "choose_lang": "🌐 Escolha seu idioma:",
        "btn_cancel": "❌ Cancelar",
        "length_opt_1": "30s – 1min", "length_opt_2": "1min – 1min 30s",
        "length_opt_3": "1min 30s – 2min", "length_opt_4": "2min – 3min",
        "length_opt_5": "3min+",
        "genre_opt_1": "Electronic / EDM", "genre_opt_2": "Dubstep / Bass",
        "genre_opt_3": "Drum & Bass", "genre_opt_4": "House / Techno",
        "genre_opt_5": "Rock / Metal", "genre_opt_6": "Orquestral",
        "genre_opt_7": "Chiptune", "genre_opt_8": "Outro",
        "mood_opt_1": "Enérgico", "mood_opt_2": "Escuro / Intenso",
        "mood_opt_3": "Alegre / Calmo", "mood_opt_4": "Triste / Emocional",
        "mood_opt_5": "Misterioso",
        "bpm_opt_1": "< 100", "bpm_opt_2": "100–140",
        "bpm_opt_3": "140–180", "bpm_opt_4": "180+",
        "vocals_opt_1": "Sim", "vocals_opt_2": "Não", "vocals_opt_3": "Tanto faz",
    },
    "fr": {
        "name": "Français", "flag": "🇫🇷",
        "welcome": "🎵 <b>GD Music Helper</b>\n\nTrouve la musique parfaite pour ton niveau Geometry Dash en quelques secondes.\n\nChoisis une action :",
        "btn_search": "🔍 Trouver une musique", "btn_lang": "🌐 Langue",
        "btn_donate": "⭐ Soutenir", "btn_help": "❓ Aide",
        "ask_length": "🎧 Étape 1/5 — Choisis la <b>durée</b> :",
        "ask_genre": "🎼 Étape 2/5 — Choisis le <b>genre</b> :",
        "ask_mood": "🎭 Étape 3/5 — Choisis l'<b>ambiance</b> :",
        "ask_bpm": "⚡ Étape 4/5 — Choisis la plage de <b>BPM</b> :",
        "ask_vocals": "🎤 Étape 5/5 — <b>Voix</b> ?",
        "searching": "🔎 Recherche sur Newgrounds...",
        "no_results": "😔 Aucune musique trouvée. Essaie d'autres filtres.",
        "results_header": "🎵 <b>{n} musiques trouvées :</b>\n\n",
        "cancelled": "❌ Recherche annulée.",
        "help_text": "ℹ️ <b>Comment utiliser :</b>\n\n1. Appuie sur <b>Trouver une musique</b>\n2. Remplis le formulaire\n3. Reçois des musiques de Newgrounds\n\n⭐ Soutiens-nous avec Telegram Stars !",
        "donate_text": "⭐ <b>Soutenir GD Music Helper</b>\n\nTon don aide à maintenir le bot.\nChoisis un montant :",
        "donate_thanks": "💛 Merci de soutenir !",
        "lang_changed": "✅ Langue changée en Français",
        "start_search_again": "🔄 Rechercher",
        "choose_lang": "🌐 Choisis ta langue :",
        "btn_cancel": "❌ Annuler",
        "length_opt_1": "30s – 1min", "length_opt_2": "1min – 1min 30s",
        "length_opt_3": "1min 30s – 2min", "length_opt_4": "2min – 3min",
        "length_opt_5": "3min+",
        "genre_opt_1": "Electronic / EDM", "genre_opt_2": "Dubstep / Bass",
        "genre_opt_3": "Drum & Bass", "genre_opt_4": "House / Techno",
        "genre_opt_5": "Rock / Metal", "genre_opt_6": "Orchestral",
        "genre_opt_7": "Chiptune", "genre_opt_8": "Autre",
        "mood_opt_1": "Énergique", "mood_opt_2": "Sombre / Intense",
        "mood_opt_3": "Joyeux / Calme", "mood_opt_4": "Triste / Émotionnel",
        "mood_opt_5": "Mystérieux",
        "bpm_opt_1": "< 100", "bpm_opt_2": "100–140",
        "bpm_opt_3": "140–180", "bpm_opt_4": "180+",
        "vocals_opt_1": "Oui", "vocals_opt_2": "Non", "vocals_opt_3": "Peu importe",
    },
    "de": {
        "name": "Deutsch", "flag": "🇩🇪",
        "welcome": "🎵 <b>GD Music Helper</b>\n\nFinde in Sekunden den perfekten Track für dein Geometry Dash-Level.\n\nWähle eine Aktion:",
        "btn_search": "🔍 Track finden", "btn_lang": "🌐 Sprache",
        "btn_donate": "⭐ Unterstützen", "btn_help": "❓ Hilfe",
        "ask_length": "🎧 Schritt 1/5 — Wähle die <b>Länge</b>:",
        "ask_genre": "🎼 Schritt 2/5 — Wähle das <b>Genre</b>:",
        "ask_mood": "🎭 Schritt 3/5 — Wähle die <b>Stimmung</b>:",
        "ask_bpm": "⚡ Schritt 4/5 — Wähle den <b>BPM</b>-Bereich:",
        "ask_vocals": "🎤 Schritt 5/5 — <b>Gesang</b>?",
        "searching": "🔎 Suche auf Newgrounds...",
        "no_results": "😔 Keine Tracks gefunden. Versuche andere Filter.",
        "results_header": "🎵 <b>{n} Tracks gefunden:</b>\n\n",
        "cancelled": "❌ Suche abgebrochen.",
        "help_text": "ℹ️ <b>Bedienung:</b>\n\n1. Tippe auf <b>Track finden</b>\n2. Fülle das Formular aus\n3. Erhalte Tracks von Newgrounds\n\n⭐ Unterstütze uns mit Telegram Stars!",
        "donate_text": "⭐ <b>GD Music Helper unterstützen</b>\n\nDeine Spende hilft, den Bot am Laufen zu halten.\nWähle einen Betrag:",
        "donate_thanks": "💛 Danke für deine Unterstützung!",
        "lang_changed": "✅ Sprache auf Deutsch geändert",
        "start_search_again": "🔄 Erneut suchen",
        "choose_lang": "🌐 Wähle deine Sprache:",
        "btn_cancel": "❌ Abbrechen",
        "length_opt_1": "30s – 1min", "length_opt_2": "1min – 1min 30s",
        "length_opt_3": "1min 30s – 2min", "length_opt_4": "2min – 3min",
        "length_opt_5": "3min+",
        "genre_opt_1": "Electronic / EDM", "genre_opt_2": "Dubstep / Bass",
        "genre_opt_3": "Drum & Bass", "genre_opt_4": "House / Techno",
        "genre_opt_5": "Rock / Metal", "genre_opt_6": "Orchestral",
        "genre_opt_7": "Chiptune", "genre_opt_8": "Andere",
        "mood_opt_1": "Energiegeladen", "mood_opt_2": "Dunkel / Intensiv",
        "mood_opt_3": "Fröhlich / Entspannt", "mood_opt_4": "Traurig / Emotional",
        "mood_opt_5": "Mysteriös",
        "bpm_opt_1": "< 100", "bpm_opt_2": "100–140",
        "bpm_opt_3": "140–180", "bpm_opt_4": "180+",
        "vocals_opt_1": "Ja", "vocals_opt_2": "Nein", "vocals_opt_3": "Egal",
    },
    "it": {
        "name": "Italiano", "flag": "🇮🇹",
        "welcome": "🎵 <b>GD Music Helper</b>\n\nTrova la traccia perfetta per il tuo livello di Geometry Dash in pochi secondi.\n\nScegli un'azione:",
        "btn_search": "🔍 Trova traccia", "btn_lang": "🌐 Lingua",
        "btn_donate": "⭐ Sostieni", "btn_help": "❓ Aiuto",
        "ask_length": "🎧 Passo 1/5 — Scegli la <b>durata</b>:",
        "ask_genre": "🎼 Passo 2/5 — Scegli il <b>genere</b>:",
        "ask_mood": "🎭 Passo 3/5 — Scegli l'<b>atmosfera</b>:",
        "ask_bpm": "⚡ Passo 4/5 — Scegli il range di <b>BPM</b>:",
        "ask_vocals": "🎤 Passo 5/5 — <b>Voce</b>?",
        "searching": "🔎 Cerco su Newgrounds...",
        "no_results": "😔 Nessuna traccia trovata. Prova altri filtri.",
        "results_header": "🎵 <b>Trovate {n} tracce:</b>\n\n",
        "cancelled": "❌ Ricerca annullata.",
        "help_text": "ℹ️ <b>Come usare:</b>\n\n1. Tocca <b>Trova traccia</b>\n2. Compila il modulo\n3. Ricevi tracce da Newgrounds\n\n⭐ Sostienici con Telegram Stars!",
        "donate_text": "⭐ <b>Sostieni GD Music Helper</b>\n\nLa tua donazione aiuta a mantenere il bot.\nScegli un importo:",
        "donate_thanks": "💛 Grazie per aver sostenuto!",
        "lang_changed": "✅ Lingua cambiata in Italiano",
        "start_search_again": "🔄 Cerca di nuovo",
        "choose_lang": "🌐 Scegli la tua lingua:",
        "btn_cancel": "❌ Annulla",
        "length_opt_1": "30s – 1min", "length_opt_2": "1min – 1min 30s",
        "length_opt_3": "1min 30s – 2min", "length_opt_4": "2min – 3min",
        "length_opt_5": "3min+",
        "genre_opt_1": "Electronic / EDM", "genre_opt_2": "Dubstep / Bass",
        "genre_opt_3": "Drum & Bass", "genre_opt_4": "House / Techno",
        "genre_opt_5": "Rock / Metal", "genre_opt_6": "Orchestral",
        "genre_opt_7": "Chiptune", "genre_opt_8": "Altro",
        "mood_opt_1": "Energico", "mood_opt_2": "Scuro / Intenso",
        "mood_opt_3": "Felice / Rilassato", "mood_opt_4": "Triste / Emozionale",
        "mood_opt_5": "Misterioso",
        "bpm_opt_1": "< 100", "bpm_opt_2": "100–140",
        "bpm_opt_3": "140–180", "bpm_opt_4": "180+",
        "vocals_opt_1": "Sì", "vocals_opt_2": "No", "vocals_opt_3": "Indifferente",
    },
    "pl": {
        "name": "Polski", "flag": "🇵🇱",
        "welcome": "🎵 <b>GD Music Helper</b>\n\nZnajdź idealny utwór do swojego poziomu w Geometry Dash w kilka sekund.\n\nWybierz akcję:",
        "btn_search": "🔍 Znajdź utwór", "btn_lang": "🌐 Język",
        "btn_donate": "⭐ Wesprzyj", "btn_help": "❓ Pomoc",
        "ask_length": "🎧 Krok 1/5 — Wybierz <b>długość</b>:",
        "ask_genre": "🎼 Krok 2/5 — Wybierz <b>gatunek</b>:",
        "ask_mood": "🎭 Krok 3/5 — Wybierz <b>nastrój</b>:",
        "ask_bpm": "⚡ Krok 4/5 — Wybierz zakres <b>BPM</b>:",
        "ask_vocals": "🎤 Krok 5/5 — <b>Wokal</b>?",
        "searching": "🔎 Szukam na Newgrounds...",
        "no_results": "😔 Nie znaleziono utworów. Spróbuj innych filtrów.",
        "results_header": "🎵 <b>Znaleziono {n} utworów:</b>\n\n",
        "cancelled": "❌ Wyszukiwanie anulowane.",
        "help_text": "ℹ️ <b>Jak używać:</b>\n\n1. Kliknij <b>Znajdź utwór</b>\n2. Wypełnij formularz\n3. Otrzymaj utwory z Newgrounds\n\n⭐ Wesprzyj nas Telegram Stars!",
        "donate_text": "⭐ <b>Wesprzyj GD Music Helper</b>\n\nTwoja darowizna pomaga utrzymać bota.\nWybierz kwotę:",
        "donate_thanks": "💛 Dziękuję za wsparcie!",
        "lang_changed": "✅ Język zmieniony na Polski",
        "start_search_again": "🔄 Szukaj ponownie",
        "choose_lang": "🌐 Wybierz język:",
        "btn_cancel": "❌ Anuluj",
        "length_opt_1": "30s – 1min", "length_opt_2": "1min – 1min 30s",
        "length_opt_3": "1min 30s – 2min", "length_opt_4": "2min – 3min",
        "length_opt_5": "3min+",
        "genre_opt_1": "Electronic / EDM", "genre_opt_2": "Dubstep / Bass",
        "genre_opt_3": "Drum & Bass", "genre_opt_4": "House / Techno",
        "genre_opt_5": "Rock / Metal", "genre_opt_6": "Orkiestra",
        "genre_opt_7": "Chiptune", "genre_opt_8": "Inne",
        "mood_opt_1": "Energiczny", "mood_opt_2": "Mroczny / Intensywny",
        "mood_opt_3": "Wesoły / Spokojny", "mood_opt_4": "Smutny / Emocjonalny",
        "mood_opt_5": "Tajemniczy",
        "bpm_opt_1": "< 100", "bpm_opt_2": "100–140",
        "bpm_opt_3": "140–180", "bpm_opt_4": "180+",
        "vocals_opt_1": "Tak", "vocals_opt_2": "Nie", "vocals_opt_3": "Obojętne",
    },
    "tr": {
        "name": "Türkçe", "flag": "🇹🇷",
        "welcome": "🎵 <b>GD Music Helper</b>\n\nGeometry Dash seviyen için mükemmel parçayı saniyeler içinde bul.\n\nBir işlem seç:",
        "btn_search": "🔍 Parça bul", "btn_lang": "🌐 Dil",
        "btn_donate": "⭐ Destekle", "btn_help": "❓ Yardım",
        "ask_length": "🎧 Adım 1/5 — <b>Süreyi</b> seç:",
        "ask_genre": "🎼 Adım 2/5 — <b>Türü</b> seç:",
        "ask_mood": "🎭 Adım 3/5 — <b>Atmosferi</b> seç:",
        "ask_bpm": "⚡ Adım 4/5 — <b>BPM</b> aralığını seç:",
        "ask_vocals": "🎤 Adım 5/5 — <b>Vokal</b>?",
        "searching": "🔎 Newgrounds'ta aranıyor...",
        "no_results": "😔 Parça bulunamadı. Başka filtre dene.",
        "results_header": "🎵 <b>{n} parça bulundu:</b>\n\n",
        "cancelled": "❌ Arama iptal edildi.",
        "help_text": "ℹ️ <b>Nasıl kullanılır:</b>\n\n1. <b>Parça bul</b>'a dokun\n2. Formu doldur\n3. Newgrounds'tan parçalar al\n\n⭐ Bizi Telegram Stars ile destekle!",
        "donate_text": "⭐ <b>GD Music Helper'ı destekle</b>\n\nBağışın botu ayakta tutar.\nBir miktar seç:",
        "donate_thanks": "💛 Destek için teşekkürler!",
        "lang_changed": "✅ Dil Türkçe olarak değiştirildi",
        "start_search_again": "🔄 Tekrar ara",
        "choose_lang": "🌐 Dilini seç:",
        "btn_cancel": "❌ İptal",
        "length_opt_1": "30sn – 1dk", "length_opt_2": "1dk – 1dk 30sn",
        "length_opt_3": "1dk 30sn – 2dk", "length_opt_4": "2dk – 3dk",
        "length_opt_5": "3dk+",
        "genre_opt_1": "Electronic / EDM", "genre_opt_2": "Dubstep / Bass",
        "genre_opt_3": "Drum & Bass", "genre_opt_4": "House / Techno",
        "genre_opt_5": "Rock / Metal", "genre_opt_6": "Orkestral",
        "genre_opt_7": "Chiptune", "genre_opt_8": "Diğer",
        "mood_opt_1": "Enerjik", "mood_opt_2": "Karanlık / Yoğun",
        "mood_opt_3": "Neşeli / Sakin", "mood_opt_4": "Hüzünlü / Duygusal",
        "mood_opt_5": "Gizemli",
        "bpm_opt_1": "< 100", "bpm_opt_2": "100–140",
        "bpm_opt_3": "140–180", "bpm_opt_4": "180+",
        "vocals_opt_1": "Evet", "vocals_opt_2": "Hayır", "vocals_opt_3": "Fark etmez",
    },
    "ja": {
        "name": "日本語", "flag": "🇯🇵",
        "welcome": "🎵 <b>GD Music Helper</b>\n\nGeometry Dashのレベルにぴったりの曲を数秒で見つけよう。\n\nアクションを選択:",
        "btn_search": "🔍 曲を探す", "btn_lang": "🌐 言語",
        "btn_donate": "⭐ 支援", "btn_help": "❓ ヘルプ",
        "ask_length": "🎧 ステップ1/5 — <b>長さ</b>を選択:",
        "ask_genre": "🎼 ステップ2/5 — <b>ジャンル</b>を選択:",
        "ask_mood": "🎭 ステップ3/5 — <b>雰囲気</b>を選択:",
        "ask_bpm": "⚡ ステップ4/5 — <b>BPM</b>範囲を選択:",
        "ask_vocals": "🎤 ステップ5/5 — <b>ボーカル</b>?",
        "searching": "🔎 Newgroundsで検索中...",
        "no_results": "😔 曲が見つかりません。フィルターを変えてみて。",
        "results_header": "🎵 <b>{n}曲見つかりました:</b>\n\n",
        "cancelled": "❌ 検索をキャンセルしました。",
        "help_text": "ℹ️ <b>使い方:</b>\n\n1. <b>曲を探す</b>をタップ\n2. フォームを入力\n3. Newgroundsから曲を取得\n\n⭐ Telegram Starsで支援!",
        "donate_text": "⭐ <b>GD Music Helperを支援</b>\n\n寄付はボットの運営を支えます。\n金額を選択:",
        "donate_thanks": "💛 支援ありがとうございます!",
        "lang_changed": "✅ 言語を日本語に変更しました",
        "start_search_again": "🔄 もう一度検索",
        "choose_lang": "🌐 言語を選択:",
        "btn_cancel": "❌ キャンセル",
        "length_opt_1": "30秒 – 1分", "length_opt_2": "1分 – 1分30秒",
        "length_opt_3": "1分30秒 – 2分", "length_opt_4": "2分 – 3分",
        "length_opt_5": "3分+",
        "genre_opt_1": "Electronic / EDM", "genre_opt_2": "Dubstep / Bass",
        "genre_opt_3": "Drum & Bass", "genre_opt_4": "House / Techno",
        "genre_opt_5": "Rock / Metal", "genre_opt_6": "オーケストラ",
        "genre_opt_7": "Chiptune", "genre_opt_8": "その他",
        "mood_opt_1": "エネルギッシュ", "mood_opt_2": "ダーク / 激しい",
        "mood_opt_3": "明るい / チル", "mood_opt_4": "悲しい / エモ",
        "mood_opt_5": "神秘的",
        "bpm_opt_1": "< 100", "bpm_opt_2": "100–140",
        "bpm_opt_3": "140–180", "bpm_opt_4": "180+",
        "vocals_opt_1": "あり", "vocals_opt_2": "なし", "vocals_opt_3": "どちらでも",
    },
    "ko": {
        "name": "한국어", "flag": "🇰🇷",
        "welcome": "🎵 <b>GD Music Helper</b>\n\nGeometry Dash 레벨에 딱 맞는 곡을 몇 초 만에 찾아보세요.\n\n작업 선택:",
        "btn_search": "🔍 곡 찾기", "btn_lang": "🌐 언어",
        "btn_donate": "⭐ 후원", "btn_help": "❓ 도움말",
        "ask_length": "🎧 1/5 단계 — <b>길이</b> 선택:",
        "ask_genre": "🎼 2/5 단계 — <b>장르</b> 선택:",
        "ask_mood": "🎭 3/5 단계 — <b>분위기</b> 선택:",
        "ask_bpm": "⚡ 4/5 단계 — <b>BPM</b> 범위 선택:",
        "ask_vocals": "🎤 5/5 단계 — <b>보컬</b>?",
        "searching": "🔎 Newgrounds 검색 중...",
        "no_results": "😔 곡을 찾을 수 없습니다. 다른 필터를 시도하세요.",
        "results_header": "🎵 <b>{n}곡 발견:</b>\n\n",
        "cancelled": "❌ 검색이 취소되었습니다.",
        "help_text": "ℹ️ <b>사용 방법:</b>\n\n1. <b>곡 찾기</b> 탭\n2. 양식 작성\n3. Newgrounds에서 곡 받기\n\n⭐ Telegram Stars로 후원!",
        "donate_text": "⭐ <b>GD Music Helper 후원</b>\n\n후원은 봇 운영에 도움이 됩니다.\n금액 선택:",
        "donate_thanks": "💛 후원해 주셔서 감사합니다!",
        "lang_changed": "✅ 언어가 한국어로 변경되었습니다",
        "start_search_again": "🔄 다시 검색",
        "choose_lang": "🌐 언어 선택:",
        "btn_cancel": "❌ 취소",
        "length_opt_1": "30초 – 1분", "length_opt_2": "1분 – 1분 30초",
        "length_opt_3": "1분 30초 – 2분", "length_opt_4": "2분 – 3분",
        "length_opt_5": "3분+",
        "genre_opt_1": "Electronic / EDM", "genre_opt_2": "Dubstep / Bass",
        "genre_opt_3": "Drum & Bass", "genre_opt_4": "House / Techno",
        "genre_opt_5": "Rock / Metal", "genre_opt_6": "오케스트라",
        "genre_opt_7": "Chiptune", "genre_opt_8": "기타",
        "mood_opt_1": "활기찬", "mood_opt_2": "어두운 / 강렬한",
        "mood_opt_3": "밝은 / 차분한", "mood_opt_4": "슬픈 / 감성적",
        "mood_opt_5": "신비로운",
        "bpm_opt_1": "< 100", "bpm_opt_2": "100–140",
        "bpm_opt_3": "140–180", "bpm_opt_4": "180+",
        "vocals_opt_1": "있음", "vocals_opt_2": "없음", "vocals_opt_3": "상관없음",
    },
    "zh": {
        "name": "中文", "flag": "🇨🇳",
        "welcome": "🎵 <b>GD Music Helper</b>\n\n几秒内为你的 Geometry Dash 关卡找到完美音乐。\n\n选择一个操作：",
        "btn_search": "🔍 找音乐", "btn_lang": "🌐 语言",
        "btn_donate": "⭐ 支持", "btn_help": "❓ 帮助",
        "ask_length": "🎧 第 1/5 步 — 选择<b>时长</b>：",
        "ask_genre": "🎼 第 2/5 步 — 选择<b>曲风</b>：",
        "ask_mood": "🎭 第 3/5 步 — 选择<b>氛围</b>：",
        "ask_bpm": "⚡ 第 4/5 步 — 选择 <b>BPM</b> 范围：",
        "ask_vocals": "🎤 第 5/5 步 — <b>人声</b>？",
        "searching": "🔎 正在 Newgrounds 搜索...",
        "no_results": "😔 未找到音乐。请尝试其他筛选条件。",
        "results_header": "🎵 <b>找到 {n} 首音乐：</b>\n\n",
        "cancelled": "❌ 搜索已取消。",
        "help_text": "ℹ️ <b>使用方法：</b>\n\n1. 点击<b>找音乐</b>\n2. 填写表单\n3. 获取 Newgrounds 音乐\n\n⭐ 用 Telegram Stars 支持我们！",
        "donate_text": "⭐ <b>支持 GD Music Helper</b>\n\n你的捐赠帮助维持机器人运行。\n选择金额：",
        "donate_thanks": "💛 感谢你的支持！",
        "lang_changed": "✅ 语言已切换为中文",
        "start_search_again": "🔄 重新搜索",
        "choose_lang": "🌐 选择语言：",
        "btn_cancel": "❌ 取消",
        "length_opt_1": "30秒 – 1分", "length_opt_2": "1分 – 1分30秒",
        "length_opt_3": "1分30秒 – 2分", "length_opt_4": "2分 – 3分",
        "length_opt_5": "3分+",
        "genre_opt_1": "Electronic / EDM", "genre_opt_2": "Dubstep / Bass",
        "genre_opt_3": "Drum & Bass", "genre_opt_4": "House / Techno",
        "genre_opt_5": "Rock / Metal", "genre_opt_6": "管弦乐",
        "genre_opt_7": "Chiptune", "genre_opt_8": "其他",
        "mood_opt_1": "充满活力", "mood_opt_2": "黑暗 / 激烈",
        "mood_opt_3": "欢快 / 放松", "mood_opt_4": "悲伤 / 感性",
        "mood_opt_5": "神秘",
        "bpm_opt_1": "< 100", "bpm_opt_2": "100–140",
        "bpm_opt_3": "140–180", "bpm_opt_4": "180+",
        "vocals_opt_1": "有", "vocals_opt_2": "无", "vocals_opt_3": "无所谓",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    """Повертає локалізований рядок з fallback на англійську."""
    data = LOCALES.get(lang) or LOCALES["en"]
    text = data.get(key) or LOCALES["en"].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


# =========================================================
# FSM STATES
# =========================================================
class SearchForm(StatesGroup):
    length = State()
    genre = State()
    mood = State()
    bpm = State()
    vocals = State()


# =========================================================
# BOT INIT
# =========================================================
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

user_lang: dict = {}


def get_lang(user_id: int) -> str:
    return user_lang.get(user_id, "en")


def detect_lang_from_telegram(language_code) -> str:
    """Auto-detect bot language from Telegram language_code."""
    if not language_code:
        return "en"
    code = language_code.lower().split("-")[0]
    return code if code in LOCALES else "en"


# =========================================================
# KEYBOARDS
# =========================================================
def main_menu(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "btn_search"))],
            [KeyboardButton(text=t(lang, "btn_lang")), KeyboardButton(text=t(lang, "btn_donate"))],
            [KeyboardButton(text=t(lang, "btn_help"))],
        ],
        resize_keyboard=True,
    )


def _inline_from_options(lang: str, prefix: str, keys) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=t(lang, k), callback_data=f"{prefix}:{k}")] for k in keys]
    rows.append([InlineKeyboardButton(text=t(lang, "btn_cancel"), callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def length_kb(lang): return _inline_from_options(lang, "len", [f"length_opt_{i}" for i in range(1, 6)])
def genre_kb(lang):  return _inline_from_options(lang, "gen", [f"genre_opt_{i}" for i in range(1, 9)])
def mood_kb(lang):   return _inline_from_options(lang, "mood", [f"mood_opt_{i}" for i in range(1, 6)])
def bpm_kb(lang):    return _inline_from_options(lang, "bpm", [f"bpm_opt_{i}" for i in range(1, 5)])
def vocals_kb(lang): return _inline_from_options(lang, "voc", [f"vocals_opt_{i}" for i in range(1, 4)])


def lang_kb() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=f"{d['flag']} {d['name']}", callback_data=f"lang:{c}")]
            for c, d in LOCALES.items()]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def donate_kb() -> InlineKeyboardMarkup:
    amounts = [5, 25, 50, 100]
    rows = [[InlineKeyboardButton(text=f"⭐ {a} Stars", callback_data=f"donate:{a}")] for a in amounts]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def results_kb(lang: str, tracks: list) -> InlineKeyboardMarkup:
    rows = []
    for i, tr in enumerate(tracks, 1):
        title = tr["title"][:40]
        rows.append([InlineKeyboardButton(text=f"🎵 {i}. {title}", url=tr["url"])])
    rows.append([InlineKeyboardButton(text=t(lang, "start_search_again"), callback_data="restart")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# =========================================================
# NEWGROUNDS.IO API (v3) — RC4 + Base64
# =========================================================
NG_API_URL = "https://www.newgrounds.io/gateway_v3.php"

GENRE_MAP = {
    "genre_opt_1": "electronic",
    "genre_opt_2": "dubstep",
    "genre_opt_3": "drum and bass",
    "genre_opt_4": "house",
    "genre_opt_5": "rock",
    "genre_opt_6": "orchestral",
    "genre_opt_7": "chiptune",
    "genre_opt_8": "",
}

MOOD_MAP = {
    "mood_opt_1": "energetic",
    "mood_opt_2": "dark",
    "mood_opt_3": "happy",
    "mood_opt_4": "sad",
    "mood_opt_5": "ambient",
}


def _rc4_encrypt(plaintext: bytes, key_bytes: bytes) -> bytes:
    """Реалізація шифру RC4."""
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key_bytes[i % len(key_bytes)]) % 256
        S[i], S[j] = S[j], S[i]

    i = j = 0
    out = bytearray()
    for byte in plaintext:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        K = S[(S[i] + S[j]) % 256]
        out.append(byte ^ K)
    return bytes(out)


def _encrypt_call(call_obj: dict) -> str:
    """Шифрує об'єкт виклику (JSON) + Base64."""
    plaintext = json.dumps(call_obj, separators=(",", ":")).encode("utf-8")
    key_bytes = NG_ENCRYPTION_KEY.encode("utf-8")
    encrypted = _rc4_encrypt(plaintext, key_bytes)
    return base64.b64encode(encrypted).decode("ascii")


async def _ng_call(component: str, method: str, parameters: dict) -> dict:
    """Робить запит до Newgrounds.io API."""
    if not NG_APP_ID or not NG_ENCRYPTION_KEY:
        log.warning("NG_APP_ID or NG_ENCRYPTION_KEY not set")
        return {}

        call_obj = {
        "app_id": NG_APP_ID,
        "call": {
            "component": component,
            "method": method,
            "parameters": parameters,
        },
    }
    encrypted_data = _encrypt_call(call_obj)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                NG_API_URL,
                data={"data": encrypted_data},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                raw = await resp.text()
                log.info(f"NG RAW RESPONSE: {raw[:500]}")
                if resp.status != 200:
                    log.warning(f"NG returned status {resp.status}")
                    return {}
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    log.error("NG response is not JSON")
                    return {}
    except Exception as e:
        log.error(f"NG request error: {e}")
        return {}


async def search_tracks(length: str, genre: str, mood: str, bpm: str, vocals: str, limit: int = 8) -> list:
    """Реальний пошук треків через Newgrounds.io API."""
    query_parts = []
    if genre in GENRE_MAP and GENRE_MAP[genre]:
        query_parts.append(GENRE_MAP[genre])
    if mood in MOOD_MAP:
        query_parts.append(MOOD_MAP[mood])

    query = " ".join(query_parts) if query_parts else "electronic"

        data = await _ng_call("Audio", "getList", {
        "q": query,
        "limit": limit,
    })
    tracks = []
    result = data.get("result", {})
    if result.get("success"):
        songs = result.get("data", {}).get("songs", [])
        for song in songs[:limit]:
            song_id = song.get("id")
            if not song_id:
                continue
            tracks.append({
                "title": song.get("name", "Unknown")[:60],
                "author": song.get("artist", "Unknown"),
                "url": f"https://www.newgrounds.com/audio/listen/{song_id}",
            })

    if not tracks:
        log.warning("No tracks found via NG API, using fallback")
        return _fallback_tracks(limit)
    return tracks


def _fallback_tracks(limit: int) -> list:
    """Демо-треки, якщо API не спрацював."""
    demo = [
        {"title": "Stereo Madness", "author": "ForeverBound", "url": "https://www.newgrounds.com/audio/listen/398089"},
        {"title": "Back on Track", "author": "DJVI", "url": "https://www.newgrounds.com/audio/listen/398090"},
        {"title": "Polargeist", "author": "Step", "url": "https://www.newgrounds.com/audio/listen/398091"},
        {"title": "Dry Out", "author": "DJVI", "url": "https://www.newgrounds.com/audio/listen/398092"},
        {"title": "Base After Base", "author": "DJVI", "url": "https://www.newgrounds.com/audio/listen/398093"},
        {"title": "Cant Let Go", "author": "DJVI", "url": "https://www.newgrounds.com/audio/listen/398094"},
        {"title": "Jumper", "author": "Waterflame", "url": "https://www.newgrounds.com/audio/listen/398095"},
        {"title": "Time Machine", "author": "Waterflame", "url": "https://www.newgrounds.com/audio/listen/398096"},
    ]
    return demo[:limit]


# =========================================================
# HANDLERS
# =========================================================
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id

    if user_id not in user_lang:
        user_lang[user_id] = detect_lang_from_telegram(message.from_user.language_code)

    lang = get_lang(user_id)
    await message.answer(t(lang, "welcome"), reply_markup=main_menu(lang))


@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(t(get_lang(message.from_user.id), "help_text"))


@dp.message(Command("lang"))
async def cmd_lang(message: Message):
    lang = get_lang(message.from_user.id)
    await message.answer(t(lang, "choose_lang"), reply_markup=lang_kb())


SEARCH_TEXTS = {t(c, "btn_search") for c in LOCALES}
LANG_TEXTS = {t(c, "btn_lang") for c in LOCALES}
DONATE_TEXTS = {t(c, "btn_donate") for c in LOCALES}
HELP_TEXTS = {t(c, "btn_help") for c in LOCALES}


@dp.message(F.text.in_(SEARCH_TEXTS))
async def start_search(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    await state.set_state(SearchForm.length)
    await message.answer(t(lang, "ask_length"), reply_markup=length_kb(lang))


@dp.message(F.text.in_(LANG_TEXTS))
async def open_lang(message: Message):
    lang = get_lang(message.from_user.id)
    await message.answer(t(lang, "choose_lang"), reply_markup=lang_kb())


@dp.message(F.text.in_(DONATE_TEXTS))
async def open_donate(message: Message):
    lang = get_lang(message.from_user.id)
    await message.answer(t(lang, "donate_text"), reply_markup=donate_kb())


@dp.message(F.text.in_(HELP_TEXTS))
async def open_help(message: Message):
    await message.answer(t(get_lang(message.from_user.id), "help_text"))


@dp.callback_query(F.data.startswith("lang:"))
async def set_lang(cb: CallbackQuery, state: FSMContext):
    code = cb.data.split(":")[1]
    if code in LOCALES:
        user_lang[cb.from_user.id] = code
        await cb.message.answer(t(code, "lang_changed"), reply_markup=main_menu(code))
    await cb.answer()


@dp.callback_query(F.data == "cancel")
async def cancel(cb: CallbackQuery, state: FSMContext):
    lang = get_lang(cb.from_user.id)
    await state.clear()
    try:
        await cb.message.edit_text(t(lang, "cancelled"))
    except Exception:
        pass
    await cb.message.answer(t(lang, "welcome"), reply_markup=main_menu(lang))
    await cb.answer()


@dp.callback_query(F.data == "restart")
async def restart(cb: CallbackQuery, state: FSMContext):
    lang = get_lang(cb.from_user.id)
    await state.set_state(SearchForm.length)
    await cb.message.answer(t(lang, "ask_length"), reply_markup=length_kb(lang))
    await cb.answer()


@dp.callback_query(SearchForm.length, F.data.startswith("len:"))
async def pick_length(cb: CallbackQuery, state: FSMContext):
    await state.update_data(length=cb.data.split(":")[1])
    lang = get_lang(cb.from_user.id)
    await state.set_state(SearchForm.genre)
    await cb.message.edit_text(t(lang, "ask_genre"), reply_markup=genre_kb(lang))
    await cb.answer()


@dp.callback_query(SearchForm.genre, F.data.startswith("gen:"))
async def pick_genre(cb: CallbackQuery, state: FSMContext):
    await state.update_data(genre=cb.data.split(":")[1])
    lang = get_lang(cb.from_user.id)
    await state.set_state(SearchForm.mood)
    await cb.message.edit_text(t(lang, "ask_mood"), reply_markup=mood_kb(lang))
    await cb.answer()


@dp.callback_query(SearchForm.mood, F.data.startswith("mood:"))
async def pick_mood(cb: CallbackQuery, state: FSMContext):
    await state.update_data(mood=cb.data.split(":")[1])
    lang = get_lang(cb.from_user.id)
    await state.set_state(SearchForm.bpm)
    await cb.message.edit_text(t(lang, "ask_bpm"), reply_markup=bpm_kb(lang))
    await cb.answer()


@dp.callback_query(SearchForm.bpm, F.data.startswith("bpm:"))
async def pick_bpm(cb: CallbackQuery, state: FSMContext):
    await state.update_data(bpm=cb.data.split(":")[1])
    lang = get_lang(cb.from_user.id)
    await state.set_state(SearchForm.vocals)
    await cb.message.edit_text(t(lang, "ask_vocals"), reply_markup=vocals_kb(lang))
    await cb.answer()


@dp.callback_query(SearchForm.vocals, F.data.startswith("voc:"))
async def pick_vocals(cb: CallbackQuery, state: FSMContext):
    await state.update_data(vocals=cb.data.split(":")[1])
    data = await state.get_data()
    lang = get_lang(cb.from_user.id)

    await cb.message.edit_text(t(lang, "searching"))
    await cb.answer()

    tracks = await search_tracks(
        length=data.get("length", ""),
        genre=data.get("genre", ""),
        mood=data.get("mood", ""),
        bpm=data.get("bpm", ""),
        vocals=data.get("vocals", ""),
        limit=8,
    )

    if not tracks:
        await cb.message.edit_text(t(lang, "no_results"))
        await cb.message.answer(t(lang, "welcome"), reply_markup=main_menu(lang))
        await state.clear()
        return

    text = t(lang, "results_header", n=len(tracks))
    for i, tr in enumerate(tracks, 1):
        text += f"<b>{i}. {tr['title']}</b>\n👤 {tr['author']}\n\n"

    await cb.message.edit_text(text, reply_markup=results_kb(lang, tracks))
    await state.clear()


@dp.callback_query(F.data.startswith("donate:"))
async def donate_cb(cb: CallbackQuery):
    amount = int(cb.data.split(":")[1])
    await bot.send_invoice(
        chat_id=cb.from_user.id,
        title="Support GD Music Helper",
        description="Thank you for supporting the project! ⭐",
        payload=f"donate_{amount}",
        currency="XTR",
        prices=[LabeledPrice(label="Donate", amount=amount)],
        provider_token="",
    )
    await cb.answer()


@dp.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
    await q.answer(ok=True)


@dp.message(F.successful_payment)
async def on_paid(message: Message):
    await message.answer(t(get_lang(message.from_user.id), "donate_thanks"))


@dp.message()
async def fallback(message: Message):
    lang = get_lang(message.from_user.id)
    await message.answer(t(lang, "welcome"), reply_markup=main_menu(lang))


# =========================================================
# MAIN
# =========================================================
async def _health(request):
    from aiohttp import web as _web
    return _web.Response(text="OK")


async def _start_health_server():
    """Фіктивний HTTP-сервер, щоб Render бачив відкритий порт."""
    from aiohttp import web as _web
    port = int(os.getenv("PORT", "10000"))
    app = _web.Application()
    app.router.add_get("/", _health)
    runner = _web.AppRunner(app)
    await runner.setup()
    site = _web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log.info(f"🌐 Health server on port {port}")


async def main():
    log.info("🚀 Бот запущено")
    asyncio.create_task(_start_health_server())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
