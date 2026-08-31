import re
import json
import logging
from typing import Dict, Any
from core.gemini import ask_gemini

logger = logging.getLogger("DriverRights")


async def get_driver_legal_advice(user_id: int, situation: str) -> Dict[str, Any]:
    """
    Provides concise legal analysis of traffic stop/situation with exact articles of laws.
    """
    prompt = (
        f"Ты опытный авто-юрист. Дай краткий, железобетонный и юридически грамотный разбор ситуации водителя: '{situation}'.\n\n"
        "Определи:\n"
        "1. title: Краткая суть ситуации.\n"
        "2. legal_basis: Статьи ПДД и КоАП РФ (с номерами статей и пунктов).\n"
        "3. what_to_say: Что корректно и вежливо сказать инспектору под запись.\n"
        "4. what_not_to_do: Чего категорически нельзя делать или подписывать.\n"
        "5. fine_or_penalty: Официальное наказание по КоАП (штраф, предупреждение, лишение или отсутствие состава правонарушения).\n\n"
        "Верни ТОЛЬКО валидный JSON в формате:\n"
        "{\n"
        '  "title": "Остановка вне стационарного поста / Проверка документов",\n'
        '  "legal_basis": "Приказ МВД №664 (п. 84.13), ст. 27.1 КоАП РФ, п. 2.1.1 ПДД",\n'
        '  "what_to_say": "Инспектор обязан представиться, назвать причину остановки и цель проверки документов. Вы имеете право оставаться в автомобиле.",\n'
        '  "what_not_to_do": "Не выходите из машины без законного требования (досмотр, отстранение, задержание). Не передавайте документы в обложках с удерживающими устройствами.",\n'
        '  "fine_or_penalty": "При наличии всех документов (СТС, ВУ, ОСАГО) состава нарушения нет."\n'
        "}"
    )

    resp = await ask_gemini(user_id, prompt)
    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing rights JSON: {e}")

    return {
        "title": "Юридическая справка для водителя",
        "legal_basis": "КоАП РФ и ПДД РФ",
        "what_to_say": "Инспектор обязан представиться и назвать причину остановки.",
        "what_not_to_do": "Не подписывайте незаполненные протоколы.",
        "fine_or_penalty": "Действуйте в рамках правового поля."
    }
