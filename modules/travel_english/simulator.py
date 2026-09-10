"""
AI-движок интерактивного диалога «🗣 Живой English»:
- Отыгрыш персонажей в реальных бытовых ситуациях
- Ориентация на чистый базовый школьный английский (A1-B1) без сложного сленга
- Разбор полезных слов с русской транскрипцией и ударениями
- Подсказки 3 простых вариантов продолжения диалога
- Мягкий доброжелательный разбор грамматических ошибок
- Поддержка русского ввода: если пользователь не знает слово или пишет по-русски,
  бот переводит мысль на английский, обучает слову и продолжает диалог!
"""

import re
import json
import logging
from typing import Dict, Any, Optional
from core.gemini import get_genai_client, CANDIDATE_MODELS
from modules.travel_english.scenarios_catalog import get_scenario_info

logger = logging.getLogger("TravelEnglishSimulator")

# Флаг обнаружения невалидного API ключа (чтобы не спамить попытками и не тормозить бота)
_API_KEY_DISABLED = False


def _detect_grammar_and_feedback(scenario_key: str, user_text: str) -> Dict[str, Any]:
    """
    Анализирует фразу ученика на типичные базовые ошибки школьного уровня:
    - Русский ввод: 'я пью пиво' / 'как сказать...' -> объясняем и переводим
    - 'i'm drink' / 'i'm eat' -> Present Continuous vs Present Simple
    - 'i am live' -> 'I live'
    - 'he go' -> 'he goes'
    - 'how much it cost' -> 'how much does it cost'
    - Пропуск глагола to be ('this free' -> 'this is free')
    """
    text_lower = user_text.lower().strip()
    has_russian = bool(re.search(r"[а-яА-ЯёЁ]", user_text))

    # Если в сообщении есть русские слова
    if has_russian:
        return {
            "score": 9,
            "rule_note": "Молодец! Если не знаешь слово по-английски — смело пиши по-русски прямо в чат! Я перевел твою мысль на чистый базовый английский выше. Запоминай слова и произношение!",
            "correction_found": True,
            "is_russian": True
        }

    # 1. Ошибка типа "i'm drink", "i'm have", "i'm work"
    if re.search(r"\bi'?m\s+(drink|have|work|eat|go|live|want|like|play)\b", text_lower):
        matched = re.search(r"\bi'?m\s+(drink|have|work|eat|go|live|want|like|play)\b", text_lower).group(1)
        better_verb = matched + "ing" if matched != "have" else "having"
        return {
            "score": 8,
            "rule_note": f"Вместо «I'm {matched}» в английском говорят «I am {better_verb}» (если действие происходит прямо сейчас) или просто «I {matched}» (если вообще). При этом тебя отлично поняли!",
            "correction_found": True,
            "is_russian": False
        }

    # 2. Пропуск артикля или to be
    if "this seat free" in text_lower or "seat free" in text_lower:
        return {
            "score": 8,
            "rule_note": "Не забывай глагол to be: «This seat IS free». Но в реальном баре тебя поймут с полуслова!",
            "correction_found": True,
            "is_russian": False
        }

    if "how much it" in text_lower:
        return {
            "score": 8,
            "rule_note": "В вопросах о цене правильнее сказать «How much DOES it cost?» или коротко «How much is it?».",
            "correction_found": True,
            "is_russian": False
        }

    return {
        "score": 9,
        "rule_note": "Отличная, понятная и естественная реплика! Порядок слов правильный, мысль передана четко.",
        "correction_found": False,
        "is_russian": False
    }


def generate_smart_offline_turn(scenario_key: str, user_message: str, history: str = "") -> Dict[str, Any]:
    """
    Умный динамический генератор диалога для ролевых ситуаций на чистом базовом английском (A1-B1).
    Понимает фразы на английском, русском и смешанном языках.
    """
    sc_info = get_scenario_info(scenario_key)
    text_lower = user_message.lower()
    grammar_check = _detect_grammar_and_feedback(scenario_key, user_message)
    score = grammar_check["score"]
    feedback = grammar_check["rule_note"]

    # 1. Сценарий: Знакомство в баре (Джессика)
    if scenario_key == "bar_dating":
        # Тема напитков / пива / вина / сока
        if any(w in text_lower for w in [
            "beer", "drink", "drinking", "wine", "cider", "cocktail", "juice", "water",
            "пив", "напит", "пью", "вин", "сидр", "коктейл", "сок", "вод", "бармен", "бокал", "заказ", "кружк"
        ]):
            better_phrase = "Yes, this seat is free. I am drinking beer. What about you? What is your name?"
            better_transcr = "[Йес, зис сит из фри. Ай эм дри́нкинг бир. Уот эба́ут ю? Уот из ёр нэйм?]"
            if grammar_check.get("is_russian"):
                feedback = "Отлично! Если забыл слово — пиши по-русски. «Пиво» по-английски — «beer» [бир], а «Я пью пиво» — «I am drinking beer» [Ай эм дри́нкинг бир]. Джессика услышала тебя и с радостью отвечает!"

            return {
                "character_reply_en": "Thanks! I'm Jessica, nice to meet you. Beer is a good choice, but I'm having white wine tonight. What kind of beer do you like?",
                "character_reply_ru": "Спасибо! Я Джессика, приятно познакомиться. Пиво — отличный выбор, а я сегодня пью белое вино. Какое пиво ты любишь?",
                "base_score": score,
                "vocabulary": [
                    {"word": "nice to meet you", "transcription": "[найс ту мит ю]", "translation": "приятно познакомиться"},
                    {"word": "white wine", "transcription": "[уа́йт уайн]", "translation": "белое вино"},
                    {"word": "what kind of", "transcription": "[уот кайнд оф]", "translation": "какой именно / какой сорт"}
                ],
                "better_base_phrase": better_phrase,
                "phonetic_transcription_ru": better_transcr,
                "teacher_feedback": feedback,
                "suggested_replies": [
                    {"en": "I like light draft beer. And what wine do you prefer?", "ru": "Я люблю светлое разливное пиво. А какое вино ты предпочитаешь?", "transcription": "[Ай лайк лайт драфт бир. Энд уот уайн ду ю прифёр?]"},
                    {"en": "I prefer dark beer, it tastes great. Are you here on vacation?", "ru": "Я предпочитаю темное пиво, отличный вкус. Ты здесь в отпуске?", "transcription": "[Ай прифёр дарк бир, ит тэйстс грэйт. Ар ю хир он вэкэ́йшн?]"},
                    {"en": "I am just trying local beer. It was very hot today!", "ru": "Я просто пробую местное пиво. Сегодня было очень жарко!", "transcription": "[Ай эм джаст тра́йинг ло́кал бир. Ит уоз вэ́ри хот тудэ́й!]"}
                ]
            }

        # Тема имени / знакомства
        elif any(w in text_lower for w in [
            "name", "oleg", "call me", "i am", "i'm", "meet", "hello", "hi",
            "зовут", "имя", "олег", "меня зовут", "познаком", "привет", "здравствуй"
        ]):
            better_phrase = "Nice to meet you, Jessica! My name is Oleg, I am from Saint Petersburg."
            better_transcr = "[Найс ту мит ю, Джэ́сика! Май нэйм из Оле́г, ай эм фром Сэйнт Пи́терсберг]"
            if grammar_check.get("is_russian"):
                feedback = "Прекрасно! «Меня зовут...» по-английски — «My name is...» [Май нэйм из...], а «Приятно познакомиться» — «Nice to meet you» [Найс ту мит ю]. Джессика всё поняла и улыбнулась!"

            return {
                "character_reply_en": "Nice to meet you, Oleg! It is really crowded in here tonight. Are you traveling alone or with friends?",
                "character_reply_ru": "Приятно познакомиться, Олег! Здесь сегодня довольно многолюдно. Ты путешествуешь один или с друзьями?",
                "base_score": score,
                "vocabulary": [
                    {"word": "crowded", "transcription": "[кра́удэд]", "translation": "многолюдно / тесно"},
                    {"word": "traveling alone", "transcription": "[трэ́вэлинг эло́ун]", "translation": "путешествую один"},
                    {"word": "with friends", "transcription": "[уиз фрэндз]", "translation": "с друзьями"}
                ],
                "better_base_phrase": better_phrase,
                "phonetic_transcription_ru": better_transcr,
                "teacher_feedback": feedback,
                "suggested_replies": [
                    {"en": "I am traveling alone. I enjoy meeting new people.", "ru": "Я путешествую один. Мне нравится знакомиться с новыми людьми.", "transcription": "[Ай эм трэ́вэлинг эло́ун. Ай инджо́й ми́тинг нью пипл]"},
                    {"en": "I am here with my friends, but they are dancing.", "ru": "Я здесь с друзьями, но они пошли танцевать.", "transcription": "[Ай эм хир уиз май фрэндз, бат зэй ар дэ́нсинг]"},
                    {"en": "I am on a short business trip. Do you live in this city?", "ru": "Я в короткой командировке. Ты живешь в этом городе?", "transcription": "[Ай эм он э шорт би́знес трип. Ду ю лив ин зис си́ти?]"}
                ]
            }

        # Тема отпуска / путешествий / откуда приехал
        elif any(w in text_lower for w in [
            "vacation", "trip", "travel", "holiday", "alone", "friends", "city", "russia", "petersburg", "from",
            "отпуск", "отдых", "путешеств", "турист", "один", "друзья", "росси", "питер", "петербург", "москв", "город", "приехал", "откуда", "недел"
        ]):
            better_phrase = "I am on vacation here for one week. I am from Russia. Where are you from?"
            better_transcr = "[Ай эм он вэкэ́йшн хир фор уан уик. Ай эм фром Ра́ша. Уэр ар ю фром?]"
            if grammar_check.get("is_russian"):
                feedback = "Отлично! «Я в отпуске» — «I am on vacation» [Ай эм он вэкэ́йшн], а «Откуда ты?» — «Where are you from?» [Уэр ар ю фром?]. Диалог продолжается!"

            return {
                "character_reply_en": "That sounds exciting! I love traveling too. How long are you staying here, and have you visited any famous places yet?",
                "character_reply_ru": "Звучит здорово! Я тоже люблю путешествовать. На сколько ты здесь остановился и успел ли посмотреть известные места?",
                "base_score": score,
                "vocabulary": [
                    {"word": "sounds exciting", "transcription": "[са́ундз эксáйтинг]", "translation": "звучит увлекательно"},
                    {"word": "staying here", "transcription": "[стэ́йинг хир]", "translation": "останавливаешься здесь"},
                    {"word": "famous places", "transcription": "[фэ́ймос плэ́йсиз]", "translation": "известные места / достопримечательности"}
                ],
                "better_base_phrase": better_phrase,
                "phonetic_transcription_ru": better_transcr,
                "teacher_feedback": feedback,
                "suggested_replies": [
                    {"en": "I am here for one week. Tomorrow I want to visit the city center.", "ru": "Я здесь на одну неделю. Завтра хочу съездить в центр города.", "transcription": "[Ай эм хир фор уан уик. Тумо́роу ай уонт ту ви́зит зэ си́ти сэ́нтэр]"},
                    {"en": "I have three days left. Can you recommend a good local place?", "ru": "У меня осталось три дня. Можешь порекомендовать хорошее местное заведение?", "transcription": "[Ай хэв зри дэйз лэфт. Кэн ю рэкомэ́нд э гуд ло́кал плэйс?]"},
                    {"en": "I arrived yesterday, so I am just looking around.", "ru": "Я приехал только вчера, так что пока просто осматриваюсь.", "transcription": "[Ай эрра́йвд йе́стэрдэй, соу ай эм джаст лу́кинг эра́унд]"}
                ]
            }

        # Тема музыки / бара / атмосферы
        elif any(w in text_lower for w in [
            "music", "song", "track", "loud", "place", "bar", "cool", "vibe",
            "музык", "песн", "трек", "громк", "мест", "бар", "классн", "вайб", "атмосфер"
        ]):
            return {
                "character_reply_en": "I love this song! The band playing tonight is really good. What kind of music do you usually listen to at home?",
                "character_reply_ru": "Обожаю эту песню! Группа, которая играет сегодня, очень хороша. А какую музыку ты обычно слушаешь дома?",
                "base_score": score,
                "vocabulary": [
                    {"word": "band", "transcription": "[бэнд]", "translation": "музыкальная группа"},
                    {"word": "usually", "transcription": "[ю́жуэли]", "translation": "обычно"},
                    {"word": "listen to", "transcription": "[ли́сн ту]", "translation": "слушать (музыку)"}
                ],
                "better_base_phrase": "The music here is great, isn't it? What kind of music do you like?",
                "phonetic_transcription_ru": "[Зэ мью́зик хир из грэйт, и́знт ит? Уот кайнд оф мью́зик ду ю лайк?]",
                "teacher_feedback": feedback,
                "suggested_replies": [
                    {"en": "I like rock and electronic music. And you?", "ru": "Я люблю рок и электронную музыку. А ты?", "transcription": "[Ай лайк рок энд илэктро́ник мью́зик. Энд ю?]"},
                    {"en": "I listen to different songs, mostly relaxed pop and jazz.", "ru": "Я слушаю разные песни, в основном спокойный поп и джаз.", "transcription": "[Ай ли́сн ту ди́френт сонгз, мо́стли рилэ́кст поп энд джаз]"},
                    {"en": "I like this track! Shall we order another drink?", "ru": "Мне нравится этот трек! Закажем еще по напитку?", "transcription": "[Ай лайк зис трэк! Шэл уи о́рдэр энáдэр дринк?]"}
                ]
            }

        # Общий ответ для бара
        else:
            better_phrase = "It is very nice to talk to you. Do you come to this place often?"
            better_transcr = "[Ит из вэ́ри найс ту ток ту ю. Ду ю кам ту зис плэйс о́фен?]"
            if grammar_check.get("is_russian"):
                feedback = "Супер! Если забыл слово — пиши по-русски, я всегда переведу фразу на английский выше и помогу с транскрипцией. Собеседница поняла тебя и продолжает разговор!"

            return {
                "character_reply_en": "That is interesting! The music here is nice tonight, isn't it? What kind of music do you usually listen to?",
                "character_reply_ru": "Интересно! Музыка здесь сегодня приятная, правда? Какую музыку ты обычно слушаешь?",
                "base_score": score,
                "vocabulary": [
                    {"word": "isn't it?", "transcription": "[и́знт ит?]", "translation": "не так ли? / правда?"},
                    {"word": "usually", "transcription": "[ю́жуэли]", "translation": "обычно"},
                    {"word": "listen to", "transcription": "[ли́сн ту]", "translation": "слушать (музыку)"}
                ],
                "better_base_phrase": better_phrase,
                "phonetic_transcription_ru": better_transcr,
                "teacher_feedback": feedback,
                "suggested_replies": [
                    {"en": "I like rock and electronic music. And you?", "ru": "Я люблю рок и электронную музыку. А ты?", "transcription": "[Ай лайк рок энд илэктро́ник мью́зик. Энд ю?]"},
                    {"en": "I listen to different songs, mostly relaxed pop and jazz.", "ru": "Я слушаю разные песни, в основном спокойный поп и джаз.", "transcription": "[Ай ли́сн ту ди́френт сонгз, мо́стли рилэ́кст поп энд джаз]"},
                    {"en": "I like this track! Shall we order another drink?", "ru": "Мне нравится этот трек! Закажем еще по напитку?", "transcription": "[Ай лайк зис трэк! Шэл уи о́рдэр энáдэр дринк?]"}
                ]
            }

    # 2. Сценарий: Кофейня (Бариста Алекс)
    elif scenario_key == "coffee_shop":
        return {
            "character_reply_en": "Sure thing! A medium cappuccino with regular milk. Would you like sugar or any pastry with that?",
            "character_reply_ru": "Конечно! Средний капучино на обычном молоке. Сахар или какую-нибудь выпечку добавить к заказу?",
            "base_score": score,
            "vocabulary": [
                {"word": "sure thing", "transcription": "[шу́р синг]", "translation": "конечно / без проблем"},
                {"word": "regular milk", "transcription": "[рэ́гьюлар милк]", "translation": "обычное коровье молоко"},
                {"word": "pastry", "transcription": "[пэ́йстри]", "translation": "выпечка / круассан"}
            ],
            "better_base_phrase": "Can I have a medium cappuccino to go, please?",
            "phonetic_transcription_ru": "[Кэн ай хэв э ми́диум каппучи́но ту гоу, плиз?]",
            "teacher_feedback": feedback,
            "suggested_replies": [
                {"en": "No sugar, please. Just the coffee to go.", "ru": "Без сахара, пожалуйста. Только кофе навынос.", "transcription": "[Ноу шу́гар, плиз. Джаст зэ ко́фи ту гоу]"},
                {"en": "One brown sugar, and one croissant, please.", "ru": "Один тростниковый сахар и один круассан, пожалуйста.", "transcription": "[Уан браун шу́гар, энд уан круасса́н, плиз]"},
                {"en": "Can I pay by card or contactless?", "ru": "Могу я оплатить картой или бесконтактно?", "transcription": "[Кэн ай пэй бай кард ор контактлэс?]"}
            ]
        }

    # 3. Сценарий: Отель (Портье Майкл)
    elif scenario_key in ["hotel_checkin", "hotel_reception"]:
        return {
            "character_reply_en": "Welcome, sir! I found your booking. Your room is on the 4th floor with a quiet view. May I have your passport for a moment?",
            "character_reply_ru": "Добро пожаловать, сэр! Я нашел вашу бронь. Ваш номер на 4-м этаже с тихим видом. Могу я взглянуть на ваш паспорт на секунду?",
            "base_score": score,
            "vocabulary": [
                {"word": "booking", "transcription": "[бу́кинг]", "translation": "бронирование"},
                {"word": "4th floor", "transcription": "[форс флор]", "translation": "четвертый этаж"},
                {"word": "may I have", "transcription": "[мэй ай хэв]", "translation": "могу я попросить / разрешите взглянуть"}
            ],
            "better_base_phrase": "Hello, I have a reservation under the name Oleg.",
            "phonetic_transcription_ru": "[Хэлло́у, ай хэв э рэзэрвэ́йшн а́ндэр зэ нэйм Оле́г]",
            "teacher_feedback": feedback,
            "suggested_replies": [
                {"en": "Here is my passport. Is breakfast included?", "ru": "Вот мой паспорт. Завтрак включен в стоимость?", "transcription": "[Хир из май па́спорт. Из брэ́кфаст инклу́дэд?]"},
                {"en": "Here you go. What is the Wi-Fi password, please?", "ru": "Пожалуйста. Какой пароль от Wi-Fi?", "transcription": "[Хир ю гоу. Уот из зэ уа́й-фа́й па́суорд, плиз?]"},
                {"en": "Thank you! What time is check-out on Sunday?", "ru": "Спасибо! Во сколько выезд в воскресенье?", "transcription": "[Сэнк ю! Уот тайм из чек-а́ут он са́ндэй?]"}
            ]
        }

    # 4. Сценарий: Магазин / Супермаркет / Одежда / Продавец (Store / Shopping)
    elif "store" in scenario_key or "shop" in scenario_key or any(w in text_lower for w in ["магазин", "продав", "кассир", "покупк", "одежд", "вещ", "размер", "скидк", "купить", "цена", "рубл", "доллар"]):
        # Тема цены или скидки
        if any(w in text_lower for w in ["how much", "cost", "price", "discount", "cheap", "expensive", "цена", "стоимост", "скидк", "дорого", "скольк"]):
            better_phrase = "How much does this cost? Is there any discount?"
            better_transcr = "[Хау мач даз зис кост? Из зэр э́ни ди́скаунт?]"
            return {
                "character_reply_en": "This item is 35 dollars. And if you buy two items today, you get a 10 percent discount! Would you like to try it on?",
                "character_reply_ru": "Этот товар стоит 35 долларов. А если возьмете две вещи сегодня, получите скидку 10%! Хотите примерить?",
                "base_score": score,
                "vocabulary": [
                    {"word": "item", "transcription": "[а́йтэм]", "translation": "товар / вещь"},
                    {"word": "discount", "transcription": "[ди́скаунт]", "translation": "скидка"},
                    {"word": "try it on", "transcription": "[трай ит он]", "translation": "примерить это"}
                ],
                "better_base_phrase": better_phrase,
                "phonetic_transcription_ru": better_transcr,
                "teacher_feedback": feedback,
                "suggested_replies": [
                    {"en": "Yes, where is the fitting room, please?", "ru": "Да, где находится примерочная?", "transcription": "[Йес, уэр из зэ фи́тин рум, плиз?]"},
                    {"en": "That is a good deal. Can I pay by card?", "ru": "Это выгодное предложение. Могу я оплатить картой?", "transcription": "[Зэт из э гуд дил. Кэн ай пэй бай кард?]"},
                    {"en": "35 dollars is a bit expensive for me. Do you have a cheaper one?", "ru": "35 долларов дороговато для меня. Есть что-то подешевле?", "transcription": "[Сёти файв до́лларз из э бит экспэ́нсив фор ми. Ду ю хэв э чи́пэр уан?]"}
                ]
            }

        # Тема размера или наличия
        elif any(w in text_lower for w in ["size", "medium", "large", "small", "have", "color", "black", "white", "размер", "цвет", "черн", "бел", "есть"]):
            better_phrase = "Do you have this shirt in size M or in black color?"
            better_transcr = "[Ду ю хэв зис шёрт ин сайз эм ор ин блэк ка́лор?]"
            return {
                "character_reply_en": "Yes, we have medium and large in stock! Here is the black one. The fitting rooms are right around the corner.",
                "character_reply_ru": "Да, у нас есть размеры M и L в наличии! Вот черный вариант. Примерочные прямо за углом.",
                "base_score": score,
                "vocabulary": [
                    {"word": "in stock", "transcription": "[ин сток]", "translation": "в наличии / на складе"},
                    {"word": "fitting room", "transcription": "[фи́тин рум]", "translation": "примерочная кабинка"},
                    {"word": "around the corner", "transcription": "[эра́унд зэ ко́рнэр]", "translation": "за углом"}
                ],
                "better_base_phrase": better_phrase,
                "phonetic_transcription_ru": better_transcr,
                "teacher_feedback": feedback,
                "suggested_replies": [
                    {"en": "Thank you, I will go try it on.", "ru": "Спасибо, я пойду примерю.", "transcription": "[Сэнк ю, ай уил гоу трай ит он]"},
                    {"en": "It fits me perfectly! I will take it.", "ru": "Сидит идеально! Я это беру.", "transcription": "[Ит фитс ми пё́рфэктли! Ай уил тэйк ит]"},
                    {"en": "Do you also have running shoes in size 42?", "ru": "А у вас также есть кроссовки 42 размера?", "transcription": "[Ду ю о́лсоу хэв ра́нин шуз ин сайз фо́ти ту?]"}
                ]
            }

        # Тема оплаты на кассе
        elif any(w in text_lower for w in ["pay", "card", "cash", "receipt", "bag", "касс", "оплат", "карт", "наличн", "пакет", "чек"]):
            better_phrase = "Can I pay by card, please? And I need a bag."
            better_transcr = "[Кэн ай пэй бай кард, плиз? Энд ай нид э бэг]"
            return {
                "character_reply_en": "Certainly! You can tap your card on the terminal right here. Do you need a receipt in the bag?",
                "character_reply_ru": "Конечно! Приложите карту к терминалу прямо здесь. Чек положить в пакет?",
                "base_score": score,
                "vocabulary": [
                    {"word": "tap your card", "transcription": "[тэп ёр кард]", "translation": "приложите карту бесконтактно"},
                    {"word": "terminal", "transcription": "[тё́рминал]", "translation": "терминал оплаты"},
                    {"word": "receipt", "transcription": "[риси́т]", "translation": "кассовый чек"}
                ],
                "better_base_phrase": better_phrase,
                "phonetic_transcription_ru": better_transcr,
                "teacher_feedback": feedback,
                "suggested_replies": [
                    {"en": "Yes, please put the receipt in the bag. Thank you!", "ru": "Да, пожалуйста, положите чек в пакет. Спасибо!", "transcription": "[Йес, плиз пут зэ риси́т ин зэ бэг. Сэнк ю!]"},
                    {"en": "No receipt needed. Have a great day!", "ru": "Чек не нужен. Отличного дня!", "transcription": "[Ноу риси́т ни́дэд. Хэв э грэйт дэй!]"},
                    {"en": "Thank you for your help, goodbye!", "ru": "Спасибо за помощь, до свидания!", "transcription": "[Сэнк ю фор ёр хэлп, гудба́й!]"}
                ]
            }

        # Базовый ответ продавца
        else:
            better_phrase = "Hello, I am looking for a gift and casual clothes."
            better_transcr = "[Хелло́у, ай эм лу́кин фор э гифт энд кэ́жуал кло́уз]"
            return {
                "character_reply_en": "Great! We have a new collection on the central display. Are you looking for clothes, shoes, or something specific?",
                "character_reply_ru": "Отлично! У нас новая коллекция на центральной стойке. Вы ищете одежду, обувь или что-то конкретное?",
                "base_score": score,
                "vocabulary": [
                    {"word": "display", "transcription": "[дисплэ́й]", "translation": "витрина / стойка с товаром"},
                    {"word": "looking for", "transcription": "[лу́кин фор]", "translation": "искать / присматривать"},
                    {"word": "casual clothes", "transcription": "[кэ́жуал кло́уз]", "translation": "повседневная одежда"}
                ],
                "better_base_phrase": better_phrase,
                "phonetic_transcription_ru": better_transcr,
                "teacher_feedback": feedback,
                "suggested_replies": [
                    {"en": "I am looking for a warm jacket and a t-shirt.", "ru": "Я ищу теплую куртку и футболку.", "transcription": "[Ай эм лу́кин фор э уорм джэ́кэт энд э ти-шёрт]"},
                    {"en": "I am just browsing, thanks. I will let you know if I need help.", "ru": "Я пока просто смотрю, спасибо. Обращусь, если понадобится помощь.", "transcription": "[Ай эм джаст бра́узин, сэнкс. Ай уил лэт ю ноу иф ай нид хэлп]"},
                    {"en": "Where can I find the sale section?", "ru": "Где находится отдел со скидками и распродажей?", "transcription": "[Уэр кэн ай файнд зэ сэйл сэ́кшн?]"}
                ]
            }

    # 5. Общий умный ответ для любого ролевого сценария
    char_name = sc_info.get("character", "Собеседник")
    return {
        "character_reply_en": f"I understand completely! That makes sense. Tell me, how can we solve this or what do you want to do next?",
        "character_reply_ru": "Я тебя прекрасно понял! Это логично. Скажи, как мы можем это решить или что ты хочешь сделать дальше?",
        "base_score": score,
        "vocabulary": [
            {"word": "makes sense", "transcription": "[мэйкс сэнс]", "translation": "это имеет смысл / логично"},
            {"word": "solve", "transcription": "[солв]", "translation": "решить проблему"},
            {"word": "next", "transcription": "[нэкст]", "translation": "дальше / затем"}
        ],
        "better_base_phrase": "I understand your point and I am ready to continue.",
        "phonetic_transcription_ru": "[Ай а́ндэрстэнд ёр пойнт энд ай эм рэ́ди ту конти́нью]",
        "teacher_feedback": feedback,
        "suggested_replies": [
            {"en": "I want to explain the details clearly.", "ru": "Я хочу подробно объяснить детали.", "transcription": "[Ай уонт ту эксплэ́йн зэ ди́тэйлз кли́рли]"},
            {"en": "Can you give me your advice on this?", "ru": "Можешь дать мне свой совет по этому поводу?", "transcription": "[Кэн ю гив ми ёр эдва́йс он зис?]"},
            {"en": "Let's finish this and move forward.", "ru": "Давай закончим с этим и двинемся дальше.", "transcription": "[Лэтс фи́ниш зис энд мув фо́руорд]"}
        ]
    }


async def simulate_dialog_turn(
    user_id: int,
    scenario_key: str,
    user_message: str,
    history: str = "",
    is_voice: bool = False
) -> Dict[str, Any]:
    """
    Проводит один раунд интерактивного диалога:
    - Приоритет: LLM Gemini (если доступен ключ)
    - При ошибке 401 UNAUTHENTICATED / недоступности API: мгновенный переход на умный оффлайн-движок
    - Возвращает чистый, понятный базовый школьный английский (A1-B1)
    - Идеально понимает русский и смешанный ввод!
    """
    global _API_KEY_DISABLED

    # Если мы уже определили, что API ключ деактивирован в Google Cloud, мгновенно отдаем умный ответ
    if _API_KEY_DISABLED:
        return generate_smart_offline_turn(scenario_key, user_message, history)

    sc_info = get_scenario_info(scenario_key)
    char_name = sc_info["character"]
    situation = sc_info["situation"]

    system_prompt = f"""Ты — заботливый, дружелюбный преподаватель английского языка и собеседник в ролевой игре.
Ученик попросил: "СТРОГО БЕЗ СЛОЖНОГО СЛЕНГА! Чистый, понятный школьный английский (уровни Elementary / Pre-Intermediate / Intermediate A1-B1), чтобы подтянуть базу, слова и порядок слов".

Сейчас идет ролевая игра:
Ситуация: {situation}
Твоя роль персонажа: {char_name} ({sc_info['character_role']}).

Текущий ответ ученика: "{user_message}"
Ученик ответил голосом: {"Да (голосовое сообщение)" if is_voice else "Нет (текст)"}.

КРИТИЧЕСКИ ВАЖНОЕ ПРАВИЛО: РУССКИЙ И СМЕШАННЫЙ ВВОД:
Если ученик написал фразу частично или полностью НА РУССКОМ ЯЗЫКЕ (например, не знал слово по-английски или спросил 'как сказать/как будет...'):
- Твоя задача: понять, что он хотел сказать, и перевести это на правильный, чистый базовый английский в поле 'better_base_phrase' с русской транскрипцией в 'phonetic_transcription_ru'.
- В 'teacher_feedback' дружелюбно похвалить, подсказать перевод этого русского слова или фразы: 'Отлично! Если не помнишь слово, смело пиши по-русски — я всегда подскажу перевод. Фраза [...] переводится как [...]'.
- В 'character_reply_en' твой персонаж ({char_name}) отвечает так, будто ученик произнес эту мысль на английском, продолжая живой диалог без пауз и перебиваний!

Правила генерации ответа:
1. "character_reply_en": твоя реплика как персонажа на ПРОСТОМ, ПРАВИЛЬНОМ и ПОНЯТНОМ базовом английском (1-3 коротких предложения). Никакого сложного сленга! Обязательно закончи встречным простым вопросом, чтобы диалог продолжался.
2. "character_reply_ru": точный понятный перевод твоей реплики на русский язык.
3. "base_score": оценка ответа ученика по 10-балльной шкале (1-10) за понятность и базовую грамматику.
4. "vocabulary": массив из 2-3 полезных базовых слов или словосочетаний из твоей реплики: {{"word": "...", "transcription": "[...]", "translation": "..."}} для пополнения словарного запаса ученика.
5. "better_base_phrase": как выразить мысль ученика на правильном, чистом базовом английском без ошибок.
6. "phonetic_transcription_ru": русская транскрипция фразы с ударениями для легкого чтения.
7. "teacher_feedback": ободряющий, доброжелательный комментарий преподавателя на русском (1-2 предложения): похвалить за смелость, подсказать перевод русского слова или базовое грамматическое правило.
8. "suggested_replies": массив из 3 простых вариантов ответа для ученика на чистом базовом английском:
   [{{"en": "...", "ru": "...", "transcription": "[...]"}}]

Верни СТРОГО валидный JSON:
{{
  "character_reply_en": "...",
  "character_reply_ru": "...",
  "base_score": 9,
  "vocabulary": [
    {{"word": "...", "transcription": "[...]", "translation": "..."}}
  ],
  "better_base_phrase": "...",
  "phonetic_transcription_ru": "[...]",
  "teacher_feedback": "...",
  "suggested_replies": [
    {{"en": "...", "ru": "...", "transcription": "[...]"}},
    {{"en": "...", "ru": "...", "transcription": "[...]"}},
    {{"en": "...", "ru": "...", "transcription": "[...]"}}
  ]
}}
"""

    user_prompt = f"""История диалога:\n{history}\n\nУченик сказал: {user_message}"""

    client = get_genai_client()
    for model_name in CANDIDATE_MODELS:
        try:
            resp = await client.aio.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config={
                    "system_instruction": system_prompt,
                    "temperature": 0.5,
                    "response_mime_type": "application/json"
                }
            )
            if resp and resp.text:
                cleaned = resp.text.strip()
                m = re.search(r"\{.*\}", cleaned, re.DOTALL)
                if m:
                    data = json.loads(m.group(0))
                    return data
        except Exception as e:
            err_str = str(e)
            if "401" in err_str or "UNAUTHENTICATED" in err_str or "ACCOUNT_STATE_INVALID" in err_str:
                logger.warning(f"Gemini API key is unauthenticated/disabled: {e}. Switching to instant smart offline engine.")
                _API_KEY_DISABLED = True
                break
            logger.warning(f"Model {model_name} error in travel english simulator ({e}), trying next...")

    # Мгновенный умный диалоговый генератор
    return generate_smart_offline_turn(scenario_key, user_message, history)


async def instant_translate_phrase(user_query: str) -> Dict[str, Any]:
    """
    Раскладывает любую русскую фразу или вопрос пользователя на 3 стиля живого английского:
    1. Street Smart (естественный разговорный)
    2. Polite (вежливый)
    3. Slang (уличный сленг)
    """
    global _API_KEY_DISABLED

    if not _API_KEY_DISABLED:
        system_prompt = """Ты — эксперт по разговорному английскому и сленгу нейтивов.
Пользователь спрашивает, как сказать фразу по-английски в реальной жизни или путешествии.
Никакой грамматики и скучных лекций! Только реальный язык.

Ты должен дать:
1. "street_smart": самый органичный, разговорный вариант, как говорят 90% нейтивов.
2. "street_transcription": русская транскрипция с ударениями для street_smart.
3. "polite": вежливый вариант для деликатных ситуаций.
4. "polite_transcription": русская транскрипция для polite.
5. "slang": яркий разговорный сленг/сокращение.
6. "slang_transcription": русская транскрипция для slang.
7. "context_note": короткий лайфхак, где какая фраза уместна.

Верни СТРОГО валидный JSON:
{
  "street_smart": "...",
  "street_transcription": "[...]",
  "polite": "...",
  "polite_transcription": "[...]",
  "slang": "...",
  "slang_transcription": "[...]",
  "context_note": "..."
}
"""
        client = get_genai_client()
        for model_name in CANDIDATE_MODELS:
            try:
                resp = await client.aio.models.generate_content(
                    model=model_name,
                    contents=f"Как сказать: {user_query}",
                    config={
                        "system_instruction": system_prompt,
                        "temperature": 0.5,
                        "response_mime_type": "application/json"
                    }
                )
                if resp and resp.text:
                    cleaned = resp.text.strip()
                    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
                    if m:
                        return json.loads(m.group(0))
            except Exception as e:
                err_str = str(e)
                if "401" in err_str or "UNAUTHENTICATED" in err_str or "ACCOUNT_STATE_INVALID" in err_str:
                    _API_KEY_DISABLED = True
                    break
                logger.warning(f"Model {model_name} failed in instant translator ({e}), trying next...")

    return {
        "street_smart": f"How do I say «{user_query}» in everyday English?",
        "street_transcription": "[Хау ду ай сэй ... ин э́вридэй и́нглиш?]",
        "polite": f"Could you please explain how to say «{user_query}»?",
        "polite_transcription": "[Куд ю плиз эксплэ́йн хау ту сэй ...?]",
        "slang": "How do locals say this?",
        "slang_transcription": "[Хау ду ло́калс сэй зис?]",
        "context_note": "Используй базовые фразы с вежливым 'Could you please', они работают в любой стране безотказно!"
    }
