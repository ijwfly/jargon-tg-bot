import openai
import tiktoken


PRICE_PER_TOKEN = 0.002 / 1000


def calculate_input_price(messages):
    encoding = tiktoken.encoding_for_model('gpt-3.5-turbo-0301')
    tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
    tokens_per_name = -1  # if there's a name, the role is omitted
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens * PRICE_PER_TOKEN


def calculate_output_price(output_message):
    encoding = tiktoken.encoding_for_model('gpt-3.5-turbo-0301')
    return len(encoding.encode(output_message)) * PRICE_PER_TOKEN


def init_openai(openai_api_key):
    openai.api_key = openai_api_key
