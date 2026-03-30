from ollama import AsyncClient
from config import *
import asyncio
import pandas as pd
import logging

from bot.config import OLLAMA_KEY

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

index_lock = asyncio.Lock()



async def get_ai_response(user_id):
    df = pd.read_csv(f"user_data/{user_id}/report.csv")
    data_preview = df.to_string(index=False)


    messages = [
        {
            'role': 'system',
            'content': (
                "Ты - эксперт по анализу продаж и бизнес-аналитике"
                "Твоя задача - помогать пользователю интерпретировать данные о продажах, "
                "объяснять отклонения плана от факта, выявлять тенденции и давать практические рекомендации\n\n"

                "📌 Правила ответа:\n"
                "Отвечай кратко, ясно и по делу\n"
                "Используй маркированные списки для структурирования\n"
                "Разделяй текст на короткие абзацы\n"
                "Не используй сложные термины без пояснений\n"
                "Ориентируйся на малый и средний бизнес (магазины, кафе, онлайн-продажи)\n\n"

                "📊 Примеры задач:\n"
                "Проанализируй, почему план не выполнен за неделю\n"
                "Что можно улучшить в продажах?\n"
                "Какие дни были самыми успешными и почему?\n"
                "Дай рекомендации для мотивации персонала\n\n"

                "❗ ВАЖНО:\n"
                "- Максимум 500 символов"
                "- НЕ используй парсинг (markdown) при ответе"
                "- Текст кнопки - короткий, понятный\n"
                "- Разделяй на абзацы"
            )
        },
        {
            'role': 'user',
            'content': (
                "Проанализируй следующие данные о продажах:\n\n"
                f"{data_preview}\n\n"
                "Ответь по структуре:\n"
                "Краткий вывод\n"
                "Основные проблемы\n"
                "Что можно улучшить\n"
                "Конкретные рекомендации"
            )
        }
    ]


    for attempt in range(3):
        try:
            client = AsyncClient(
                host="https://ollama.com",
                headers={'Authorization': f'Bearer {OLLAMA_KEY}'}
            )

            response = ''
            async for part in await client.chat(model=AI_MODEL, messages=messages, stream=True):
                content = part['message']['content']
                response += content
                yield content.replace('—', '–')
            return

        except Exception as e:
            yield "Извините, сейчас я не могу ответить – временные неполадки. Попробуйте чуть позже! 🙏"
            return
