import logging

import openai

from ai.utils import calculate_input_price, calculate_output_price

openai_logger = logging.getLogger("openai")


async def get_jargon(base_prompt, message: str) -> str:
    prompt = f'''{base_prompt}

    {message}
    '''
    messages = [
        {"role": "user", "content": prompt},
    ]
    completion = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0,
    )
    result = completion.choices[0].message.content
    price = calculate_input_price(messages) + calculate_output_price(result)
    openai_logger.info(f'price: ${price:.8f}: {message} -> {result}')
    return result
