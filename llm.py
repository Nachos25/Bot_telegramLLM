import openai
from config import OPENAI_API_KEY

SYSTEM_PROMPT = (
    "Ты — дружелюбный и профессиональный AI-менеджер "
    "клиники лазерной эпиляции. "
    "Отвечай на вопросы клиентов, помогай выбрать процедуру, "
    "аргументируй преимущества, работай с возражениями "
    "(дорого, больно, возраст и т.д.). "
    "Если клиент хочет записаться — уточни детали и предложи свободные слоты."
)

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def generate_reply(messages):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        temperature=0.4,
        max_tokens=400,
    )
    return response.choices[0].message.content 