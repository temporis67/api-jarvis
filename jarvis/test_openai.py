from dotenv import load_dotenv
import os
from openai import OpenAI

# Lade die Umgebungsvariablen aus der .env-Datei
load_dotenv()
openai_key = os.getenv('OPENAI_API_KEY')
openai_host = os.getenv('OPENAI_API_HOST')
openai_org = os.getenv('OPENAI_API_ORG')

prompt = """
Ich habe eine Frage: Welche drei Sehenswürdigkeiten stehen in Berlin auf dem Alexanderplatz
"""


client = OpenAI(
    organization=openai_org,
    api_key=openai_key,
)

completion = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": "Du bist ein poetischer Assistent, geschickt darin, komplexe Programmierkonzepte mit kreativem Flair zu erklären."},
    {"role": "user", "content": "Verfasse ein Gedicht, das das Konzept der Rekursion in der Programmierung erklärt."}
  ]
)

print(completion.choices[0].message)