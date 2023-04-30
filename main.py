import os
import asyncio
import hashlib
import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.types import InlineQuery, InputTextMessageContent, InlineQueryResultArticle

from ai.competions import get_jargon
from ai.utils import init_openai
from tg.throttling import ThrottlingDispatcher
from utils.persistent_dict import PersistentDict

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
BASE_PROMPT = os.getenv('BASE_PROMPT')

MIN_INPUT_LENGTH = 3
MAX_INPUT_LENGTH = 200
TELEGRAM_CACHE_TIME = 1

logging.basicConfig(level=logging.INFO)
bot_logger = logging.getLogger("bot")

jargon_cache = PersistentDict('jargon_cache.llv')


router = Router()
dp = Dispatcher()
dp.include_router(router)
bot = Bot(TELEGRAM_TOKEN, parse_mode="HTML")
throttling_dispatcher = ThrottlingDispatcher()


async def get_jargon_for_query(user_id, user_query):
    text = user_query
    if not text or len(text) <= MIN_INPUT_LENGTH:
        return

    if len(text) > MAX_INPUT_LENGTH:
        return 'Слишком длинный текст'

    jargon = jargon_cache.get(user_query)
    if jargon:
        return jargon_cache[user_query]

    is_last = await throttling_dispatcher.wait_for_last_request(user_id)
    if not is_last:
        return

    jargon = await get_jargon(BASE_PROMPT, text)
    jargon_cache[user_query] = jargon
    return jargon


@router.inline_query()
async def inline_handler(inline_query: InlineQuery):
    user_query = inline_query.query.strip().lower()
    jargon_text = await get_jargon_for_query(inline_query.from_user.id, user_query)
    if not jargon_text:
        await bot.answer_inline_query(inline_query.id, results=[], cache_time=TELEGRAM_CACHE_TIME)
        return

    input_content = InputTextMessageContent(message_text=jargon_text)
    result_id: str = hashlib.md5(jargon_text.encode()).hexdigest()
    item = InlineQueryResultArticle(
        id=result_id,
        title=f'{jargon_text}',
        input_message_content=input_content,
    )
    bot_logger.info(f'user_id: {inline_query.from_user.id} = {inline_query.query} -> {jargon_text}')
    await bot.answer_inline_query(inline_query.id, results=[item], cache_time=TELEGRAM_CACHE_TIME)


async def main():
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    init_openai(OPENAI_API_KEY)
    asyncio.run(main())
