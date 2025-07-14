import openai
from config import OPENAI_API_KEY

SYSTEM_PROMPT = (
    "Ти — дружній і професійний AI-менеджер клініки лазерної епіляції. "
    "Відповідай на питання клієнтів, допомагай обрати процедуру, "
    "аргументуй переваги, працюй із запереченнями (дорого, боляче, вік тощо). "
    "Якщо клієнт хоче записатися — уточни деталі і запропонуй вільні слоти."
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