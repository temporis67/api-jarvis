from llama_cpp import Llama
import time
from dotenv import load_dotenv
import os
from openai import OpenAI

# Lade die Umgebungsvariablen aus der .env-Datei
load_dotenv()

# LLM settings for GPU
n_gpu_layers = 43  # Change this value based on your model and your GPU VRAM pool.
n_batch = 512  # Should be between 1 and n_ctx, consider the amount of VRAM in your GPU.

model_name = "spicyboros-13b-2.2.Q5_K_M.gguf"
# model_name = "Llama-2-13b-chat-german-GGUF.q5_K_M.bin"

# "ON" or "OFF
LOAD_LLM = "OFF"

class Jarvis:
    llm = None
    openai_client = None

    def ask(self, model=None, prompt=None, context=None, question=None):
        if model is None:
            print("ERROR:: Jarvis.ask() No model specified.")
            raise Exception("ERROR:: Jarvis.ask() No model specified.")

        if 'model_type' not in model:
            print("ERROR:: Jarvis.ask() No model_type specified.")
            raise Exception("ERROR:: Jarvis.ask() No model_type specified.")

        if model['model_type'] == "local":
            return self.ask_local_model(prompt)
        elif model['model_type'] == "remote":
            return self.ask_remote_model(model=model, prompt=prompt, context=context, question=question)

    def ask_openai_model(self, model=None, prompt=None, context=None, question=None):

        time_start = time.time()
        print("ask_openai_model() model: %s" % (model['model_filename']))

        completion = self.openai_client.chat.completions.create(
            model=model['model_filename'],
            messages=[
                {"role": "system",
                 "content": prompt},
                {"role": "user",
                 "content": "Berücksichtige folgende Informationen, um die Frage des Benutzers zu beantworten: %s" % context},
                {"role": "assistant", "content": "Danke, ich werde diese Informationen bei meiner Antwort berücksichtigen."},
                {"role": "user",
                 "content": "Beantworte folgende Frage: %s" % question},
            ]
        )

        answer = completion.choices[0].message.content
        time_query = time.time() - time_start

        print("ask_openai_model() answer: %s" % answer)
        print("Query executed in %s seconds" % time_query)

        return [answer, time_query]

    def ask_remote_model(self, model=None, prompt=None, context=None, question=None):
        # if model.model_type contains "*gpt*" ignore uppercase then use OpenAI API
        if "gpt" in model['model_filename'].lower():
            return self.ask_openai_model(model=model, prompt=prompt, context=context, question=question)
        else:
            print("ERROR:: Jarvis.ask_remote_model() No valid model specified. %s" % model)
            raise Exception("ERROR:: Jarvis.ask_remote_model() No valid model specified %s." % model)

    def ask_local_model(self, prompt):
        time_start = time.time()

        if not prompt or prompt == "":
            return ["Kein Prompt übergeben.", None]

        # prompt = """
        # <s>[INST] <<SYS>>You are a helpful, honest assistant.
        #  Use the following pieces of information to answer the user's question: {context} <</SYS>>
        #  {question}[/INST] This is a answer </s>
        # """

        print("start jarvis.ask(): %s" % prompt)

        if LOAD_LLM != "OFF":
            output = self.llm(prompt,
                              max_tokens=256,
                              # stop=["Q:", "\n"],
                              echo=False,
                              temperature=0.2,
                              top_p=0.5,
                              top_k=3,
                              )
            # print("** Answer ready ask(): ", repr(output))

        else:
            # print('Warning: LOAD_LLM == "OFF"')
            time.sleep(2)
            # print('Ende jarvis.ask()')
            time_query = time.time() - time_start
            return ["Das LLama Modell ist deaktiviert.", time_query]

        time_query = time.time() - time_start
        print("Query executed in %s seconds" % time_query)

        answer = output["choices"][0]["text"]

        return [answer, time_query]

    def __init__(self):
        time_start = time.time()
        print("Loading model: %s" % model_name)
        # load the large language model file
        if (LOAD_LLM != "OFF"):
            self.llm = Llama(model_path="models/" + model_name,
                             n_ctx=2048,
                             n_gpu_layers=n_gpu_layers,
                             n_batch=n_batch,
                             verbose=True)
        else:
            self.llm = None

        # load the OpenAI API
        openai_key = os.getenv('OPENAI_API_KEY')
        openai_org = os.getenv('OPENAI_API_ORG')

        self.openai_client = OpenAI(
            organization=openai_org,
            api_key=openai_key,
        )

        time_to_load = time.time() - time_start
        print("loaded model %s in %s seconds" % (model_name, time_to_load))
