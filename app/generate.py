from openai import AsyncOpenAI
from dotenv import load_dotenv

import logging
import os

logger = logging.getLogger(__name__)

load_dotenv()
AI_TOKEN = (os.getenv('AI_TOKEN'))

client = AsyncOpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=AI_TOKEN,
)

async def ai_generate(text: str):
  completion = await client.chat.completions.create(
    model="deepseek/deepseek-r1-0528:free",
    messages=[
      {"role": "developer", "content": "отвечай коротко без приветствия, прощания и подробностей"},
      {"role": "user", "content": text}
    ]
  )
  logger.debug("Ответ модели: %s", completion)
  return completion.choices[0].message.content

