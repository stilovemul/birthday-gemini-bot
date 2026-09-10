"""
Каталог интерактивных проверочных работ (Street Smart Quizzes):
Тесты на знание реального разговорного языка без занудных правил грамматики.
"""

from typing import List, Dict, Any

QUIZ_CATEGORIES = {
    "blitz": {
        "title": "⚡️ Экспресс-Блиц: Как говорят нейтивы",
        "icon": "⚡️",
        "description": "5 быстрых жизненных вопросов на проверку уличного чутья"
    },
    "food_bar": {
        "title": "🍻 Бар, Рестораны & Еда",
        "icon": "🍻",
        "description": "Заказ еды, напитков, чаевые, счет и просьбы без неловкости"
    },
    "travel_airport": {
        "title": "✈️ Аэропорт, Отель & Дорога",
        "icon": "✈️",
        "description": "Паспортный контроль, багаж, ресепшн, такси и навигация"
    },
    "slang_idioms": {
        "title": "🕶 Уличный сленг & Реакции нейтивов",
        "icon": "🕶",
        "description": "Фразочки, которые делают тебя своим среди иностранцев"
    }
}

QUESTIONS_DATA: List[Dict[str, Any]] = [
    # --- БЛИЦ / ВСЕ ТЕМЫ ---
    {
        "id": "q1",
        "category": "blitz",
        "situation": "Ты в пабе в Дублине или Лондоне. Бармен подходит и с улыбкой спрашивает: «What's your poison?». Что он имеет в виду?",
        "question": "Как перевести «What's your poison?» в баре?",
        "options": [
            "Какое у тебя отравление?",
            "Что будешь пить? (пиво/коктейль)",
            "Какую музыку включить?",
            "Кто тебя обидел?"
        ],
        "correct_idx": 1,
        "native_tip": (
            "🎯 <b>Правильно:</b> «What's your poison?» — культовая фраза барменов, означающая: "
            "<i>«Какой алкоголь будешь пить?»</i> (букв. «Какой твой яд?»).\n"
            "💬 <b>Как ответить красиво:</b> <i>«A pint of Guinness, please!»</i> или <i>«Just a lager, mate»</i>.\n"
            "🗣 <i>Транскрипция: [Уотс ё по́йзн?]</i>"
        )
    },
    {
        "id": "q2",
        "category": "blitz",
        "situation": "Ты поел в ресторане и хочешь попросить счет. Какая фраза звучит максимально естественно для официанта в США?",
        "question": "Как попросить чек без пафоса и книжных штампов?",
        "options": [
            "Give me bill immediately!",
            "Could we get the check, please?",
            "I demand payment documentation!",
            "How many money to pay you?"
        ],
        "correct_idx": 1,
        "native_tip": (
            "🎯 <b>Правильно:</b> В США счет называют <b>«the check»</b> (в Британии чаще «the bill»). "
            "Фраза <i>«Could we get the check, please?»</i> или коротко <i>«Check, please!»</i> — идеальный баланс вежливости и простоты.\n"
            "❌ <i>«Give me bill»</i> звучит грубо, как приказ охранника.\n"
            "🗣 <i>Транскрипция: [Куд уи гет зэ чек, плиз?]</i>"
        )
    },
    {
        "id": "q3",
        "category": "blitz",
        "situation": "Ты покупаешь кофе. Бариста уточняет: «For here or to go?». Ты спешишь и берешь напиток с собой на улицу. Что сказать?",
        "question": "Твой ответ баристе:",
        "options": [
            "I will run away now",
            "To go, please!",
            "Not for here",
            "Outside my friend"
        ],
        "correct_idx": 1,
        "native_tip": (
            "🎯 <b>Правильно:</b> <b>«To go, please!»</b> (в США) или <b>«Takeaway, please»</b> (в Британии/Австралии/Европе). "
            "Если пьешь в кофейне — отвечай <i>«For here, please»</i> или <i>«Having here»</i>.\n"
            "🗣 <i>Транскрипция: [Ту го́у, плиз] / [Тэ́йк-эуэй, плиз]</i>"
        )
    },
    {
        "id": "q4",
        "category": "blitz",
        "situation": "Ты случайно задел прохожего на улице или в метро. Он поворачивается и доброжелательно говорит: «You're all good, don't sweat it!». Что это значит?",
        "question": "Что имел в виду прохожий?",
        "options": [
            "Ты вспотел, отойди от меня",
            "Всё отлично, не парься / забей!",
            "Срочно заплати мне компенсацию",
            "Пойдем быстрее"
        ],
        "correct_idx": 1,
        "native_tip": (
            "🎯 <b>Правильно:</b> <b>«Don't sweat it!»</b> (букв. «не потей из-за этого») — топ-1 сленговое выражение, "
            "означающее <i>«Не парься / Вообще без проблем / Забей»</i>!\n"
            "🗣 <i>Транскрипция: [Донт суэ́т ит!]</i>"
        )
    },
    {
        "id": "q5",
        "category": "blitz",
        "situation": "На рынке в Таиланде или Турции продавец просит за футболку 30$. Ты хочешь сбить цену до 18$. Какая фраза идеальна?",
        "question": "Как сторговаться как профи:",
        "options": [
            "You are scammer, give for 18!",
            "Can you do 18 for it? Cash right now",
            "Decrease payment amount by 12 points",
            "I don't have currency"
        ],
        "correct_idx": 1,
        "native_tip": (
            "🎯 <b>Правильно:</b> Магическая связка торга: <b>«Can you do [сумма]? Cash right now»</b>. "
            "Продавцы обожают наличные и сразу соглашаются на скидку.\n"
            "🗣 <i>Транскрипция: [Кэн ю ду эйти́н фор ит? Кэш райт нау]</i>"
        )
    },

    # --- ЕДА & БАР ---
    {
        "id": "fb1",
        "category": "food_bar",
        "situation": "Официант спрашивает, готов ли ты сделать заказ: «Are you ready to order, or do you need a couple more minutes?». Ты еще не выбрал. Что ответить?",
        "question": "Как сказать «нам нужно еще пару минут посмотреть меню»:",
        "options": [
            "We are not ready, go away",
            "We just need a few more minutes, thanks!",
            "Stop looking at us",
            "Reading menu is hard"
        ],
        "correct_idx": 1,
        "native_tip": (
            "🎯 <b>Правильно:</b> <b>«We just need a couple more minutes, thanks!»</b> — идеальный ответ. "
            "Официант с улыбкой отойдет и вернется чуть позже.\n"
            "🗣 <i>Транскрипция: [Уи джаст нид э ка́пл мор ми́нитс, сэнкс]</i>"
        )
    },
    {
        "id": "fb2",
        "category": "food_bar",
        "situation": "Ты заказал стейк или бургер. Официант уточняет: «How would you like that cooked?». Что он спрашивает?",
        "question": "О чем вопрос официанта?",
        "options": [
            "Какую степень прожарки мяса сделать?",
            "На каком масле жарить?",
            "Сварить или пожарить?",
            "Кто шеф-повар?"
        ],
        "correct_idx": 0,
        "native_tip": (
            "🎯 <b>Правильно:</b> Степень прожарки! Запомни шкалу нейтивов:\n"
            "• <b>Rare</b> [рэ́ар] — с кровью (светло-красный)\n"
            "• <b>Medium-rare</b> [ми́диум-рэ́ар] — сочный с розовой серединкой (золотой стандарт)\n"
            "• <b>Medium</b> [ми́диум] — умеренная прожарка\n"
            "• <b>Well-done</b> [уэл-дан] — полная прожарка"
        )
    },
    {
        "id": "fb3",
        "category": "food_bar",
        "situation": "Ты хочешь повторить тот же коктейль или пиво в баре. Как сказать бармену «повтори то же самое» одной короткой фразой?",
        "question": "Фраза нейтива для повтора напитка:",
        "options": [
            "Make drink duplication please",
            "Same again, please!",
            "Repeat what you did before",
            "One more identical liquid"
        ],
        "correct_idx": 1,
        "native_tip": (
            "🎯 <b>Правильно:</b> <b>«Same again, please!»</b> или <b>«Another round, cheers!»</b>. "
            "Бармен мгновенно нальет бокал без лишних вопросов!\n"
            "🗣 <i>Транскрипция: [Сэйм эгэ́йн, плиз!]</i>"
        )
    },
    {
        "id": "fb4",
        "category": "food_bar",
        "situation": "Тебе принесли блюдо, но в нем лук, на который у тебя аллергия. Как сказать официанту вежливо, но твердо?",
        "question": "Как сказать про аллергию на ингредиент:",
        "options": [
            "Onion is poison for my body",
            "Excuse me, I'm allergic to onions. Could this be remade without it?",
            "Chef is trying to kill me",
            "Take it away, disgusting"
        ],
        "correct_idx": 1,
        "native_tip": (
            "🎯 <b>Правильно:</b> Конструкция <b>«I'm allergic to [ингредиент]»</b> — сигнал тревоги номер один в ресторанах на Западе. "
            "Блюдо мгновенно переделают бесплатно и с извинениями.\n"
            "🗣 <i>Транскрипция: [Икскью́з ми, айм элё́рджик ту а́ньонз]</i>"
        )
    },

    # --- АЭРОПОРТ & ДОРОГА ---
    {
        "id": "ta1",
        "category": "travel_airport",
        "situation": "Офицер на паспортном контроле листает твой паспорт и спрашивает: «How long are you intending to stay?». Что он хочет знать?",
        "question": "О чем спросил офицер?",
        "options": [
            "Сколько длился твой перелет?",
            "На какой срок ты приехал в страну?",
            "Когда у тебя день рождения?",
            "Сколько денег у тебя на карте?"
        ],
        "correct_idx": 1,
        "native_tip": (
            "🎯 <b>Правильно:</b> Срок пребывания! Четкий ответ:\n"
            "<i>«Just for 10 days, here is my return ticket»</i>.\n"
            "🗣 <i>Транскрипция: [Хау лонг ар ю интэ́ндин ту стэй?]</i>"
        )
    },
    {
        "id": "ta2",
        "category": "travel_airport",
        "situation": "В отеле кондиционер издает странные звуки и не дует холодом. Как объяснить это на ресепшн без сложных терминов?",
        "question": "Что сказать на ресепшн отеля:",
        "options": [
            "Cold wind maker is broken",
            "Hey, the AC in my room isn't cooling, could someone take a look?",
            "My room is hot desert, repair it!",
            "I want new air immediately"
        ],
        "correct_idx": 1,
        "native_tip": (
            "🎯 <b>Правильно:</b> Кондиционер на английском всегда сокращают до <b>«AC»</b> [эй-си]. "
            "Фраза <i>«The AC isn't cooling properly»</i> — стопроцентный натуральный разговорный язык.\n"
            "🗣 <i>Транскрипция: [Зи эй-си́ изнт ку́лин про́перли]</i>"
        )
    },
    {
        "id": "ta3",
        "category": "travel_airport",
        "situation": "Ты сел в такси Uber. Тебе нужно выйти прямо у светофора на этом перекрестке. Что сказать водителю?",
        "question": "Фраза для высадки из такси:",
        "options": [
            "Car must stop now!",
            "You can drop me off right here by the lights, thanks!",
            "Emergency exit open door",
            "I am ready to leave vehicle"
        ],
        "correct_idx": 1,
        "native_tip": (
            "🎯 <b>Правильно:</b> Глагол <b>«drop off»</b> — высаживать пассажира. "
            "<i>«Drop me off right here»</i> — эталонный оборот для любого таксиста от Лондона до Нью-Йорка.\n"
            "🗣 <i>Транскрипция: [Дроп ми оф райт хи́ар бай зэ лайтс, сэнкс]</i>"
        )
    },

    # --- СЛЕНГ & РЕАКЦИИ ---
    {
        "id": "si1",
        "category": "slang_idioms",
        "situation": "Твой новый иностранный знакомый предлагает сходить завтра на пляж или в крутой бар и спрашивает: «Are you down for it?». Что значит «down for it»?",
        "question": "Что означает «I'm down»?",
        "options": [
            "Мне грустно и печально",
            "Я в деле! / Я за! / Погнали!",
            "Я упал на пол",
            "Я спускаюсь вниз"
        ],
        "correct_idx": 1,
        "native_tip": (
            "🎯 <b>Правильно:</b> <b>«I'm down!»</b> — легендарный сленг, означает <i>«Я за! Погнали! Я в теме!»</i>. "
            "Синоним: <i>«I'm in!»</i> или <i>«Count me in!»</i>.\n"
            "🗣 <i>Транскрипция: [Айм да́ун!]</i>"
        )
    },
    {
        "id": "si2",
        "category": "slang_idioms",
        "situation": "Иностранец угостил тебя пивом в баре и говорит: «It's on me!». Что это означает?",
        "question": "Что значит «It's on me»?",
        "options": [
            "Пиво пролилось на меня",
            "Я угощаю! / За мой счет!",
            "Ты мне должен",
            "Подержи мой стакан"
        ],
        "correct_idx": 1,
        "native_tip": (
            "🎯 <b>Правильно:</b> <b>«It's on me!»</b> или <b>«My treat!»</b> — <i>«Я угощаю / Это за мой счет»</i>. "
            "Когда ты захочешь угостить друга в ответ, скажи: <i>«Next round is on me!»</i>.\n"
            "🗣 <i>Транскрипция: [Итс он ми!]</i>"
        )
    },
    {
        "id": "si3",
        "category": "slang_idioms",
        "situation": "Ты спросил у бармена или официанта, есть ли у них свободный столик на двоих. Он ответил: «No biggie, we got you covered, right this way!». Что значит «No biggie»?",
        "question": "Что такое «No biggie»?",
        "options": [
            "Здесь нет больших блюд",
            "Вообще без проблем! / Ерунда / Пустяки!",
            "У нас нет больших столов",
            "Ты слишком маленький"
        ],
        "correct_idx": 1,
        "native_tip": (
            "🎯 <b>Правильно:</b> <b>«No biggie»</b> (сокращение от «No big deal») — <i>«Пустяки / Без проблем / Вообще не вопрос»</i>.\n"
            "🗣 <i>Транскрипция: [Но́у би́ги]</i>"
        )
    }
]


def get_quiz_by_id(qid: str) -> Dict[str, Any]:
    for q in QUESTIONS_DATA:
        if q["id"] == qid:
            return q
    return QUESTIONS_DATA[0]


def get_category_questions(category: str) -> List[Dict[str, Any]]:
    if category == "blitz":
        return [q for q in QUESTIONS_DATA if q["category"] == "blitz"]
    return [q for q in QUESTIONS_DATA if q["category"] == category]
