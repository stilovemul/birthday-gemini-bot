# 🤖 AiGemAntigravity — Модульный Telegram AI Супер-Бот (24/7 Cloud)

Многофункциональный, расширяемый и полностью автономный Telegram-бот на **aiogram 3** с интеграцией **Google Gemini AI**, напоминаниями о событиях и модульной системой плагинов.

---

## 🌟 Текущие модули «из коробки»

1. 🤖 **Gemini AI Assistant (`modules/ai_assistant`)**:
   - Живой диалог 24/7 с сохранением контекста беседы
   - Анализ фотографий и изображений (Multimodal Vision)
   - Автоматический fallback между моделями (`gemini-3.7-flash`, `gemini-3.5-flash`, `gemini-3.1-flash-lite`)
   - `/clear` — сбросить контекст диалога

2. 🎂 **Дни рождения и напоминания (`modules/birthdays`)**:
   - Автономный фоновый планировщик на 09:00 MSK (UTC+3)
   - Многоуровневые предупреждения (за 7, 3, 1 день и в праздник)
   - Автоматический расчет возраста и склонений (год, года, лет)
   - `/add`, `/list`, `/upcoming`, `/today`, `/del`, `/check`

3. 📝 **Быстрые заметки и задачи (`modules/notes`)**:
   - `/note <текст>` — мгновенно сохранить мысль или задачу
   - `/notes` — просмотр всех заметок с метками времени
   - `/delnote <id>` — удаление заметки

---

## 🧩 Как легко добавлять новые модули и функции в будущем

Каждая новая функция добавляется за 3 простых шага:

### Шаг 1. Создайте папку в `modules/`
Например: `modules/weather/` или `modules/crypto/`

### Шаг 2. Создайте `handlers.py`
```python
from aiogram import Router, types
from aiogram.filters import Command

router = Router(name="my_new_feature")

@router.message(Command("mycommand"))
async def handle_my_command(message: types.Message):
    await message.answer("Привет! Это новая функция!")
```

### Шаг 3. Подключите роутер в `app.py`
```python
from modules.my_new_feature.handlers import router as my_router
dp.include_router(my_router)
```

При каждом `git push` на GitHub сервис на Render автоматически соберется и применит новые функции!

---

## 📁 Структура проекта

```
.
├── app.py                 # Главная точка входа (FastAPI + Telegram Bot)
├── requirements.txt       # Зависимости
├── Dockerfile             # Сборка контейнера
├── render.yaml            # Blueprint конфигурации для Render.com
├── core/
│   ├── config.py          # Настройки, ключи и пути
│   ├── gemini.py          # Ядро Gemini AI
│   ├── keyboards.py       # Меню и кнопки
│   └── scheduler.py       # Центральный фоновый планировщик
├── modules/
│   ├── ai_assistant/      # Модуль Gemini AI
│   ├── birthdays/         # Модуль дней рождения
│   └── notes/             # Модуль быстрых заметок
└── data/
    ├── birthdays.json     # База дней рождения
    └── notes.json         # База заметок
```
