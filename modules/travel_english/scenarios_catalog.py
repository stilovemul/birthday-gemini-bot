"""
Каталог аутентичных разговорных сценариев для модуля «🗣 Живой English»:
100% реальные бытовые ситуации путешественника без книжной грамматики.
"""

from typing import Dict, Any

SCENARIOS: Dict[str, Dict[str, Any]] = {
    "bar_dating": {
        "title": "🍸 Знакомство с девушкой в баре",
        "icon": "🍸",
        "character": "Джессика (Jessica)",
        "character_role": "Симпатичная, приветливая и открытая девушка за барной стойкой",
        "situation": "Вечер пятницы в уютном баре с приятной музыкой. Ты сидишь за стойкой. Рядом присаживается симпатичная девушка, улыбается и обращается к тебе.",
        "opening_line": "Hi! Is this seat free? What a nice place! What are you drinking? (Привет! Это место свободно? Какое приятное место! Что ты пьешь?)",
        "starter_tip": (
            "📚 <b>Полезные базовые слова раунда:</b>\n"
            "• <b>seat</b> [сит] — место, стул\n"
            "• <b>free</b> [фри] — свободный\n"
            "• <b>drink / drinking</b> [дринк / дри́нкин] — пить / напиток\n\n"
            "🗣 <b>Как просто ответить (выбери любой вариант или скажи голосом 🎙):</b>\n"
            "1. <i>«Hello! Yes, the seat is free, please sit down.»</i>\n"
            "   [Хелло́у! Йес, зэ сит из фри, плиз сит да́ун]\n"
            "   — Привет! Да, место свободно, присаживайся, пожалуйста.\n\n"
            "2. <i>«Hi! Yes, it is free. I am drinking juice. My name is Oleg, and you?»</i>\n"
            "   [Хай! Йес, ит из фри. Ай эм дри́нкин джус. Май нэйм из Оле́г, энд ю?]\n"
            "   — Привет! Да, свободно. Я пью сок. Меня зовут Олег, а тебя?\n\n"
            "3. <i>«Hello! Please take it. It is my first time here, do you like this bar?»</i>\n"
            "   [Хелло́у! Плиз тэйк ит. Ит из май фёрст тайм хи́ар, ду ю лайк зис бар?]\n"
            "   — Привет! Занимай. Я тут впервые, тебе нравится этот бар?"
        ),
        "suggested_replies": [
            "Hello! Yes, the seat is free, please sit down. My name is Oleg.",
            "Hi! I am drinking a cocktail with ice. What would you like to drink?",
            "Yes, it is free. Are you here alone or with friends?"
        ]
    },
    "coffee_shop": {
        "title": "☕️ Кофейня & Стритфуд",
        "icon": "☕️",
        "character": "Бариста Майк (Нью-Йорк)",
        "character_role": "Дружелюбный быстрый бариста в спешелти-кофейне в Бруклине",
        "situation": "Утро, ты зашел в стильную кофейню в Бруклине. За стойкой бариста в кепке приветливо протирает холдер и улыбается тебе.",
        "opening_line": "Hey there! How's it going today? What can I get started for you? (Привет! Как дела? Что для тебя приготовить?)",
        "starter_tip": (
            "💡 <b>Фишка нейтива:</b> Забудь школьное <i>«I would like to order a cup of coffee»</i>. "
            "Живой американец скажет: <b>«Can I grab an iced latte to go, please?»</b> "
            "или <b>«Just a double espresso, thanks!»</b>.\n"
            "🗣 <i>Транскрипция: [Кэн ай грэб эн айст ла́тэ ту го́у, плиз?]</i>"
        ),
        "suggested_replies": [
            "Can I get a flat white with oat milk to go, please?",
            "Just a black coffee and an almond croissant, thanks!",
            "What do you recommend that's not too sweet?"
        ]
    },
    "airport_customs": {
        "title": "✈️ Аэропорт & Паспортный контроль",
        "icon": "✈️",
        "character": "Офицер погранслужбы Джон (Лондон Хитроу)",
        "character_role": "Строгий, но вежливый пограничный офицер на паспортном контроле",
        "situation": "Ты только что прилетел. Подходишь к стойке пограничника в аэропорту Хитроу, отдаешь паспорт.",
        "opening_line": "Good afternoon. Passport and landing card, please. What is the purpose of your visit to the UK? (Добрый день. Паспорт и карту прибытия, пожалуйста. Какова цель вашего визита в Великобританию?)",
        "starter_tip": (
            "💡 <b>Фишка нейтива:</b> Отвечай коротко и уверенно. Никаких длинных сочинений. "
            "Служба безопасности любит конкретику: <b>«Just tourism and sightseeing, about 10 days»</b>.\n"
            "🗣 <i>Транскрипция: [Джаст ту́ризм энд са́йтсиин, эба́ут тэн дэйз]</i>"
        ),
        "suggested_replies": [
            "Just vacation and sightseeing for two weeks.",
            "I'm here for a holiday. Staying at the Hilton central.",
            "Tourism. Here is my return ticket and hotel booking."
        ]
    },
    "hotel_reception": {
        "title": "🏨 Отель, Заезд & Проблемы в номере",
        "icon": "🏨",
        "character": "Портье Дэвид (Сингапур / Барселона)",
        "character_role": "Администратор на ресепшн отеля 4-5 звезд",
        "situation": "Ты зашел в отель после долгой дороги с чемоданом. На часах 11:30, а стандартный заезд только в 14:00.",
        "opening_line": "Welcome to Grand Plaza! Are you checking in? How can I help you today? (Добро пожаловать в Гранд Плаза! Вы заселяетесь? Чем могу помочь?)",
        "starter_tip": (
            "💡 <b>Фишка нейтива:</b> Как спросить про ранний заезд без стеснения: "
            "<b>«Hi! I know I'm a bit early, any chance I could check in now, or at least leave my bags?»</b>.\n"
            "🗣 <i>Транскрипция: [Хай! Ай но́у айм э бит ё́рли, э́ни чэнс ай куд чек ин нау, о эт лист лив май бэгз?]</i>"
        ),
        "suggested_replies": [
            "Hi, I have a reservation under Oleg. Is early check-in available?",
            "The AC in room 402 isn't cooling properly, could someone check it?",
            "Could we get two extra bath towels and the Wi-Fi password?"
        ]
    },
    "taxi_street": {
        "title": "🚕 Такси & Ориентация в городе",
        "icon": "🚕",
        "character": "Водитель Алекс / Местный житель",
        "character_role": "Общительный водитель Uber или отзывчивый прохожий на улице",
        "situation": "Ты сел в такси в незнакомом городе, либо подошел к местному на улице спросить дорогу к метро.",
        "opening_line": "Hey mate! Where are we headed today? Jump in! (Привет, друг! Куда направляемся сегодня? Запрыгивай!)",
        "starter_tip": (
            "💡 <b>Фишка нейтива:</b> Чтобы попросить притормозить у светофора или угла, скажи: "
            "<b>«Could you pull over right by the corner, please?»</b> (не «stop car please»).\n"
            "🗣 <i>Транскрипция: [Куд ю пул о́увер райт бай зэ ко́рнер, плиз?]</i>"
        ),
        "suggested_replies": [
            "Could you drop me off right across the street, please?",
            "Excuse me, I'm a bit lost. Which way is the nearest subway station?",
            "Keep the change, appreciate the smooth ride!"
        ]
    },
    "market_bargain": {
        "title": "🛍 Рынок, Сувениры & Торг",
        "icon": "🛍",
        "character": "Торговец Сэм (Стамбул / Бангкок / Маркет)",
        "character_role": "Харизматичный продавец кожаных курток, часов и сувениров",
        "situation": "Ты разглядываешь стильную кожаную куртку или сувенир на колоритном рынке. Продавец сразу начинает нахваливать товар: цена 90$, но ты хочешь забрать за 50$.",
        "opening_line": "Hello my friend! Top quality genuine leather, look at this finish! Normally 90 bucks, but for you special discount! What do you think? (Привет, мой друг! Чистая кожа высшего качества! Обычно 90 баксов, но для тебя спец-скидка! Что скажешь?)",
        "starter_tip": (
            "💡 <b>Фишка нейтива:</b> Не говори агрессивно. Торгуйся с улыбкой, показывая наличные: "
            "<b>«It's really nice, but 90 is over my budget. Can you do 50 cash right now?»</b>.\n"
            "🗣 <i>Транскрипция: [Итс ри́ли найс, бат на́йнти из о́увер май ба́джет. Кэн ю ду фи́фти кэш райт нау?]</i>"
        ),
        "suggested_replies": [
            "It looks cool, but honestly 90 is too steep. Can you do 50?",
            "What's your absolute best price if I buy two right now?",
            "I'll pass for now, thanks! (прием «я ухожу», чтобы скинули цену)"
        ]
    },
    "bar_smalltalk": {
        "title": "🍻 Бар, Паб, Вечеринка & Знакомства",
        "icon": "🍻",
        "character": "Попутчица Эмили (Лондон / Мельбурн)",
        "character_role": "Открытая девушка за барной стойкой в оживленном пабе",
        "situation": "Вечер пятницы в атмосферном пабе. Рядом за стойкой садится общительная иностранка, пока бармен наливает пиво.",
        "opening_line": "Packed in here tonight! Hey, is this seat taken? What drink is that, looks delicious! (Здесь сегодня битком! Привет, это место свободно? Что это за напиток, выглядит вкусно!)",
        "starter_tip": (
            "💡 <b>Фишка нейтива:</b> Забудь заученное «My name is Oleg, I am from Russia». "
            "Начни легко: <b>«No, please, take it! It's a local craft IPA. I'm Oleg, by the way»</b>.\n"
            "🗣 <i>Транскрипция: [Но́у, плиз, тэйк ит! Итс э ло́укал крафт ай-пи-эй. Айм Оле́г, бай зэ уэ́й]</i>"
        ),
        "suggested_replies": [
            "No, go ahead and sit! It's a smoky whiskey sour, highly recommend!",
            "First time in the city? What brings you here?",
            "Cheers! Let me get the next round."
        ]
    },
    "pharmacy_emergency": {
        "title": "🚨 Аптека & Экстренная помощь",
        "icon": "🚨",
        "character": "Фармацевт Сара",
        "character_role": "Внимательный аптекарь за стойкой дежурной аптеки",
        "situation": "В поездке разболелась голова, продуло кондиционером или скрутило живот. Ты заходишь в городскую аптеку.",
        "opening_line": "Hi! How can I help you? Are you looking for anything specific? (Здравствуйте! Чем помочь? Ищете что-то конкретное?)",
        "starter_tip": (
            "💡 <b>Фишка нейтива:</b> В аптеке не нужно знать сложные медицинские термины латыни. "
            "Просто опиши симптом: <b>«I have a splitting headache and an upset stomach, do you have something over-the-counter?»</b>.\n"
            "🗣 <i>Транскрипция: [Ай хэв э спли́тин хэ́дэйк энд эн апсе́т ста́мак, ду ю хэв са́мсин о́увер-зэ-ка́унтер?]</i>"
        ),
        "suggested_replies": [
            "Do you have painkillers for a bad headache?",
            "I ate something bad and have food poisoning. What can I take?",
            "I'm allergic to penicillin. Is this safe for me?"
        ]
    },
    "custom": {
        "title": "✍️ Своя ситуация или свободный вопрос",
        "icon": "✍️",
        "character": "Street English Coach",
        "character_role": "Персональный тренер живого разговорного английского",
        "situation": "Опиши любую свою ситуацию из жизни, поездки, отеля, аэропорта или переписки.",
        "opening_line": "I'm ready! What situation do you want to practice, or what phrase do you need to say like a native? (Я готов! Какую ситуацию хочешь разыграть, или какую фразу перевести на живой сленг?)",
        "starter_tip": "💡 Напиши текстом или <b>надиктуй голосовым 🎙</b> свой вопрос или фразу на русском!",
        "suggested_replies": [
            "Как вежливо отказать назойливому зазывале?",
            "Как сказать бармену «повтори то же самое»?",
            "Как спросить пароль от вайфая?"
        ]
    }
}

CUSTOM_SCENARIOS_CACHE: Dict[str, Dict[str, Any]] = {}


def register_custom_scenario(key: str, data: Dict[str, Any]):
    """Регистрирует сгенерированный сценарий в оперативной памяти."""
    CUSTOM_SCENARIOS_CACHE[key] = data


def get_scenario_info(key: str, user_id: int = None, custom_info: Dict[str, Any] = None) -> Dict[str, Any]:
    """Возвращает информацию о сценарии (включая пользовательские темы)."""
    if custom_info:
        return custom_info
    if key in CUSTOM_SCENARIOS_CACHE:
        return CUSTOM_SCENARIOS_CACHE[key]
    if user_id:
        try:
            from modules.travel_english.storage import get_saved_dialog
            saved = get_saved_dialog(user_id, key)
            if saved and "scenario_info" in saved:
                return saved["scenario_info"]
        except Exception:
            pass
    if key in SCENARIOS:
        return SCENARIOS[key]
    return SCENARIOS.get("custom", SCENARIOS["coffee_shop"])


def build_custom_scenario_offline(topic: str) -> Dict[str, Any]:
    """
    Быстрый оффлайн-конструктор сценариев на базовом школьном английском (A1-B1)
    для популярных бытовых ситуаций: магазин, аренда авто, врач, спортзал и др.
    """
    t_lower = topic.lower()

    # 1. Магазин / Супермаркет / Продавец-консультант / Одежда
    if any(w in t_lower for w in ["магазин", "продав", "кассир", "покупк", "одежд", "вещ", "супермаркет", "размер", "store", "shop", "market", "clothes"]):
        return {
            "title": "🛒 Общение в магазине с продавцом",
            "icon": "🛒",
            "character": "Продавец Крис (Chris / Store Clerk)",
            "character_role": "Приветливый консультант в магазине одежды и товаров",
            "situation": "Ты зашел в магазин. К тебе подходит дружелюбный продавец-консультант.",
            "opening_line": "Hello! Welcome to our store. How can I help you today? Are you looking for anything specific? (Здравствуйте! Добро пожаловать в наш магазин. Чем могу помочь? Ищете что-то конкретное?)",
            "starter_tip": (
                "📚 <b>Полезные базовые слова раунда:</b>\n"
                "• <b>looking for</b> [лу́кин фор] — ищу / подыскиваю\n"
                "• <b>size</b> [сайз] — размер (S, M, L, XL)\n"
                "• <b>how much is it?</b> [хау мач из ит?] — сколько это стоит?\n"
                "• <b>fitting room</b> [фи́тин рум] — примерочная\n\n"
                "🗣 <b>Как просто ответить (выбери любой вариант или скажи голосом 🎙):</b>\n"
                "1. <i>«Hello! I am just looking around, thank you.»</i>\n"
                "   [Хелло́у! Ай эм джаст лу́кин эра́унд, сэнк ю]\n"
                "   — Здравствуйте! Я просто осматриваюсь, спасибо.\n\n"
                "2. <i>«Hi! Do you have this in size M or L?»</i>\n"
                "   [Хай! Ду ю хэв зис ин сайз эм ор эл?]\n"
                "   — Привет! У вас есть это в размере M или L?\n\n"
                "3. <i>«Hello! How much does this cost? Can I pay by card?»</i>\n"
                "   [Хелло́у! Хау мач даз зис кост? Кэн ай пэй бай кард?]\n"
                "   — Здравствуйте! Сколько это стоит? Могу я оплатить картой?"
            ),
            "suggested_replies": [
                "Hello! I am just looking around, thank you.",
                "Hi! Do you have this in size M or L?",
                "Hello! How much does this cost? Can I pay by card?"
            ]
        }

    # 2. Аренда авто / Такси / Прокат
    elif any(w in t_lower for w in ["машин", "авто", "аренд", "прокат", "каршеринг", "такси", "car", "rent"]):
        return {
            "title": "🚗 Аренда автомобиля",
            "icon": "🚗",
            "character": "Менеджер Марк (Mark / Rental Agent)",
            "character_role": "Сотрудник стойки проката автомобилей",
            "situation": "Ты подошел к стойке проката авто в аэропорту, чтобы взять машину на время поездки.",
            "opening_line": "Hello! Welcome to Car Rental. Do you have a reservation, or are you looking to rent a car today? (Здравствуйте! Добро пожаловать. У вас есть бронь или хотите арендовать автомобиль сегодня?)",
            "starter_tip": (
                "📚 <b>Полезные базовые слова раунда:</b>\n"
                "• <b>reservation</b> [рэзэрвэ́йшн] — бронь\n"
                "• <b>driver's license</b> [дра́йвэрз ла́йсэнс] — водительские права\n"
                "• <b>insurance</b> [иншу́рэнс] — страховка\n\n"
                "🗣 <b>Как просто ответить:</b>\n"
                "1. <i>«Hi! I want to rent an economy car for three days.»</i>\n"
                "   [Хай! Ай уонт ту рэнт эн ико́номи кар фор зри дэйз]\n"
                "   — Привет! Я хочу арендовать эконом-авто на 3 дня.\n\n"
                "2. <i>«Hello! I have a reservation under Oleg. Here are my documents.»</i>\n"
                "   [Хелло́у! Ай хэв э рэзэрвэ́йшн а́ндэр Оле́г. Хир ар май до́кьюмэнтс]\n"
                "   — Здравствуйте! У меня бронь на Олега. Вот мои документы.\n\n"
                "3. <i>«How much is full insurance per day?»</i>\n"
                "   [Хау мач из фул иншу́рэнс пёр дэй?]\n"
                "   — Сколько стоит полная страховка в сутки?"
            ),
            "suggested_replies": [
                "Hi! I want to rent an economy car for three days.",
                "Hello! I have a reservation under Oleg. Here are my documents.",
                "How much is full insurance per day?"
            ]
        }

    # 3. Врач / Больница / Клиника / Аптека
    elif any(w in t_lower for w in ["врач", "доктор", "больниц", "клиник", "болит", "живот", "голов", "doctor", "clinic", "hospital"]):
        return {
            "title": "🏥 Разговор с врачом в клинике",
            "icon": "🏥",
            "character": "Доктор Смит (Dr. Smith)",
            "character_role": "Внимательный дежурный врач",
            "situation": "Ты на приеме у врача за границей из-за недомогания.",
            "opening_line": "Good morning. Please take a seat. What seems to be the problem today? Where does it hurt? (Доброе утро. Присаживайтесь, пожалуйста. На что жалуетесь? Где болит?)",
            "starter_tip": (
                "📚 <b>Полезные базовые слова раунда:</b>\n"
                "• <b>hurt / pain</b> [хёрт / пэйн] — болит / боль\n"
                "• <b>headache</b> [хэ́дэйк] — головная боль\n"
                "• <b>fever</b> [фи́вэр] — температура / жар\n\n"
                "🗣 <b>Как просто ответить:</b>\n"
                "1. <i>«Hello, doctor. I have a bad headache and fever since yesterday.»</i>\n"
                "   [Хелло́у, до́ктор. Ай хэв э бэд хэ́дэйк энд фи́вэр синс йе́стэрдэй]\n"
                "   — Здравствуйте, доктор. У меня сильная головная боль и жар со вчерашнего дня.\n\n"
                "2. <i>«My stomach hurts after food poisoning. What medicine can I take?»</i>\n"
                "   [Май ста́мак хёртс а́фтэр фуд по́йзонинг. Уот мэ́дисин кэн ай тэйк?]\n"
                "   — У меня болит живот после отравления. Какое лекарство мне принять?\n\n"
                "3. <i>«I feel weak and dizzy. Do you have a prescription for me?»</i>\n"
                "   [Ай фил уик энд ди́зи. Ду ю хэв э прискри́пшн фор ми?]\n"
                "   — Я чувствую слабость и головокружение. Выпишете мне рецепт?"
            ),
            "suggested_replies": [
                "Hello, doctor. I have a bad headache and fever since yesterday.",
                "My stomach hurts after food poisoning. What medicine can I take?",
                "I feel weak and dizzy. Do you have a prescription for me?"
            ]
        }

    # 4. Спортзал / Тренер / Фитнес
    elif any(w in t_lower for w in ["зал", "спортзал", "тренер", "фитнес", "тренировк", "gym", "workout"]):
        return {
            "title": "🏋️‍♂️ В спортзале с тренером",
            "icon": "🏋️‍♂️",
            "character": "Тренер Дэн (Coach Dan)",
            "character_role": "Фитнес-инструктор в тренажерном зале",
            "situation": "Ты зашел в спортзал на тренировку за границей.",
            "opening_line": "Hey! Welcome to the gym. First time working out here? Looking for a day pass or a workout session? (Привет! Добро пожаловать в зал. Впервые здесь? Нужен разовый пропуск или тренировка?)",
            "starter_tip": (
                "📚 <b>Полезные базовые слова раунда:</b>\n"
                "• <b>day pass</b> [дэй пас] — разовый абонемент\n"
                "• <b>locker room</b> [ло́кэр рум] — раздевалка\n"
                "• <b>weights</b> [уэйтс] — гантели / тренажеры\n\n"
                "🗣 <b>Как просто ответить:</b>\n"
                "1. <i>«Hi! I would like a day pass, please. How much is it?»</i>\n"
                "   [Хай! Ай вуд лайк э дэй пас, плиз. Хау мач из ит?]\n"
                "   — Привет! Я бы хотел разовый пропуск, пожалуйста. Сколько он стоит?\n\n"
                "2. <i>«Where is the locker room and water cooler?»</i>\n"
                "   [Уэр из зэ ло́кэр рум энд уо́тэр ку́лэр?]\n"
                "   — Где находится раздевалка и кулер с водой?\n\n"
                "3. <i>«Can you show me where the free weights are?»</i>\n"
                "   [Кэн ю шо́у ми уэр зэ фри уэйтс ар?]\n"
                "   — Можете показать, где зона свободных весов?"
            ),
            "suggested_replies": [
                "Hi! I would like a day pass, please. How much is it?",
                "Where is the locker room and water cooler?",
                "Can you show me where the free weights are?"
            ]
        }

    # 5. Универсальный сценарий для любой произвольной ситуации
    cleaned_title = topic.strip().capitalize()
    if len(cleaned_title) > 40:
        cleaned_title = cleaned_title[:37] + "..."

    return {
        "title": f"✍️ {cleaned_title}",
        "icon": "💬",
        "character": "Собеседник Алекс (Alex)",
        "character_role": f"Твой англоязычный собеседник в ситуации «{topic}»",
        "situation": f"Ты за границей. Ситуация: {topic}.",
        "opening_line": f"Hello! Nice to meet you. We are in this situation: {topic}. How can I help you today? (Здравствуйте! Приятно познакомиться. Наша ситуация: {topic}. Чем я могу помочь вам сегодня?)",
        "starter_tip": (
            "📚 <b>Полезные базовые слова раунда:</b>\n"
            "• <b>nice to meet you</b> [найс ту мит ю] — приятно познакомиться\n"
            "• <b>help</b> [хэлп] — помогать / помощь\n"
            "• <b>I would like</b> [ай вуд лайк] — я бы хотел\n\n"
            "🗣 <b>Как просто ответить (пиши по-английски или по-русски):</b>\n"
            "1. <i>«Hello! I want to practice this situation with you.»</i>\n"
            "   [Хелло́у! Ай уонт ту прэ́ктис зис ситьюэ́йшн уиз ю]\n"
            "   — Здравствуйте! Я хочу потренировать эту ситуацию с вами.\n\n"
            "2. <i>«Hi! Can you explain how this works, please?»</i>\n"
            "   [Хай! Кэн ю эксплэ́йн хау зис уоркс, плиз?]\n"
            "   — Привет! Можете объяснить, как это устроено, пожалуйста?\n\n"
            "3. <i>«Hello! Let's start, I am ready!»</i>\n"
            "   [Хелло́у! Лэтс старт, ай эм рэ́ди!]\n"
            "   — Здравствуйте! Давайте начнем, я готов!"
        ),
        "suggested_replies": [
            "Hello! I want to practice this situation with you.",
            "Hi! Can you explain how this works, please?",
            "Hello! Let's start, I am ready!"
        ]
    }


async def generate_custom_scenario(topic: str) -> Dict[str, Any]:
    """
    Генерирует уникальный ролевой сценарий по любой теме пользователя.
    Использует Gemini API, если доступен, либо мгновенно отдает умный оффлайн-шаблон.
    """
    import re
    import json
    import logging
    from core.gemini import get_genai_client, CANDIDATE_MODELS

    logger = logging.getLogger("CustomScenarioGenerator")
    offline_fallback = build_custom_scenario_offline(topic)

    system_prompt = """Ты — опытный методист разговорного английского языка.
Пользователь хочет потренировать диалог в конкретной жизненной ситуации.
ПРАВИЛО: ЧИСТЫЙ ШКОЛЬНЫЙ БАЗОВЫЙ АНГЛИЙСКИЙ (A1-B1)! Никакого заумного сленга и сложной грамматики.

Сгенерируй JSON-карточку нового сценария:
1. "title": краткое название с эмодзи (например: "🛒 Покупка кроссовок в магазине").
2. "icon": подходящий эмодзи.
3. "character": имя и роль персонажа (например: "Продавец Крис (Chris)").
4. "character_role": краткое описание его роли.
5. "situation": описание обстановки (1-2 предложения на русском).
6. "opening_line": первая реплика персонажа на простом школьном английском с русским переводом в скобках.
7. "starter_tip": HTML-подсказка со словариком полезных слов (3-4 слова с русской транскрипцией и переводом) и 3 простыми вариантами ответа с транскрипцией и переводом.
8. "suggested_replies": массив из 3 простых фраз ответа на английском.

СТРОГО верни JSON:
{
  "title": "...",
  "icon": "...",
  "character": "...",
  "character_role": "...",
  "situation": "...",
  "opening_line": "...",
  "starter_tip": "...",
  "suggested_replies": ["...", "...", "..."]
}
"""

    try:
        client = get_genai_client()
        for model_name in CANDIDATE_MODELS:
            try:
                resp = await client.aio.models.generate_content(
                    model=model_name,
                    contents=f"Создай сценарий для тренировки ситуации: «{topic}»",
                    config={
                        "system_instruction": system_prompt,
                        "temperature": 0.4,
                        "response_mime_type": "application/json"
                    }
                )
                if resp and resp.text:
                    cleaned = resp.text.strip()
                    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
                    if m:
                        data = json.loads(m.group(0))
                        if "title" in data and "opening_line" in data:
                            return data
            except Exception as e:
                err_str = str(e)
                if "401" in err_str or "UNAUTHENTICATED" in err_str or "ACCOUNT_STATE_INVALID" in err_str:
                    break
                logger.warning(f"Model {model_name} failed to generate custom scenario: {e}")
    except Exception as e:
        logger.warning(f"Gemini custom scenario generation failed: {e}")

    return offline_fallback
