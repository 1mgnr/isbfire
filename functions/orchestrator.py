import config as br
import os
from dotenv import load_dotenv
import openai

load_dotenv()

OPENAI_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_KEY

class OpenAIAssistant:
    def converse(self, system_message, prompt):
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
        )
        
        message = response.choices[0].message.content
        return message

class Orchestrator:
    def __init__(self, assistant):
        self.assistant = assistant


