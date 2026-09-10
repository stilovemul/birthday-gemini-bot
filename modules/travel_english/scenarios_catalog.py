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


def get_scenario_info(key: str) -> Dict[str, Any]:
    return SCENARIOS.get(key, SCENARIOS["coffee_shop"])
