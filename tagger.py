""" Class to connect to the local tagge model """

import json
from llama_cpp import Llama
import time
from dotenv import load_dotenv
import os
import psycopg2

# LLM settings for GPU
n_gpu_layers = 25  # Change this value based on your model and your GPU VRAM pool.
n_batch = 512  # Should be between 1 and n_ctx, consider the amount of VRAM in your GPU.

# model_name = "spicyboros-13b-2.2.Q5_K_M.gguf"
# model_name = "Llama-2-13b-chat-german-GGUF.q5_K_M.bin"
tagger_model_name = "tinyllama-1.1b-chat-v0.6.Q5_K_M.gguf"

QUALITY_TAGGER_PROMPT = '''
<|system|> 
You are a code generator. Always output your answer in JSON. No pre-amble.</s>
<|user|>Exoplaneten, Planeten außerhalb unseres Sonnensystems, sind seit der ersten Entdeckung 1995 
ein faszinierendes Forschungsfeld. Sie umkreisen fremde Sterne und bieten Einblicke in die Vielfalt 
des Universums. Mit Tausenden entdeckten Exoplaneten, von erdähnlichen bis zu Gasriesen, erweitern 
sie unser Verständnis von Planetenbildung und -entwicklung. Moderne Technologien wie das Weltraumteleskop 
Kepler haben die Suche und Analyse dieser entfernten Welten revolutioniert, wobei einige in der bewohnbaren 
Zone liegen, was Fragen nach möglichem außerirdischem Leben aufwirft.</s> 
<|assistant|>{"max-items": "3", "tags":[{"name":"Exoplaneten", "score":"100"},  {"name":"Forschung", "score":"70"}, {"name":"außerirdisches Leben", "score":"63"}]}</s>
<|user|>Die im Ozean lebenden Seeschlangen, faszinierende Meeresreptilien, sind für ihre Anpassungsfähigkeit 
an das Leben im Ozean bekannt. Sie gehören zur Familie der Elapidae, verwandt mit Kobras und Mambas. 
Diese Schlangen leben überwiegend in tropischen und subtropischen Meeren, vor allem im Indo-Pazifischen Raum.
Mit abgeflachten, paddelförmigen Schwänzen und ventralen Schuppen, die ihre Beweglichkeit im Wasser 
unterstützen, sind sie ausgezeichnete Schwimmer. Seeschlangen ernähren sich hauptsächlich von Fischen und
weichen Tieren. Interessanterweise haben sie spezialisierte Drüsen, um überschüssiges Salz auszuscheiden, 
eine Anpassung an das marine Leben.</s> 
<|assistant|>{"max-items": "3", "tags": [{"name":"Seeschlangen", "score":"95"},  {"name":"Reptilien", "score":"81"}, {"name":"Meere", "score":"55"}]}</s> 
<|user|>{content}</s> 
<|assistant|>
'''

QTP2 = '''
<|system|> 
You are a code generator. Always output your answer in JSON. No pre-amble.</s>
<|user|>Exoplaneten, Planeten außerhalb unseres Sonnensystems, sind seit der ersten Entdeckung 1995 
ein faszinierendes Forschungsfeld. Sie umkreisen fremde Sterne und bieten Einblicke in die Vielfalt 
des Universums. Mit Tausenden entdeckten Exoplaneten, von erdähnlichen bis zu Gasriesen, erweitern 
sie unser Verständnis von Planetenbildung und -entwicklung. Moderne Technologien wie das Weltraumteleskop 
Kepler haben die Suche und Analyse dieser entfernten Welten revolutioniert, wobei einige in der bewohnbaren 
Zone liegen, was Fragen nach möglichem außerirdischem Leben aufwirft.</s> 
<|assistant|>{"max-items": "3", "tags":[{"name":"Exoplaneten", "score":"100"},  {"name":"Forschung", "score":"70"}, {"name":"außerirdisches Leben", "score":"63"}]}</s>
<|user|>Es gibt zahlreiche Sehenswürdigkeiten in Brasilien, die Sie besuchen können. Einige der bekanntesten und interessantesten sind:
1. Christusstatue von Rio de Janeiro - Eine 38 Meter hohe Statue des Jesus Christus, die auf einem 710 Meter hohen Hügel thront und eine großartige Aussicht über die Stadt bietet.
2. Iguaçu-Wasserfälle - Ein atemberaubendes Naturschauspiel mit mehr als 275 Wasserfällen, die sich an der Grenze von Brasilien, Argentinien und Paraguay befinden.
3. Copacabana und Ipanema - Zwei berühmte Strände in Rio de Janeiro, die für ihre weißen Sandstrände und lebhaften Nächte bekannt sind.
4. Brasília - Die Hauptstadt von Brasilien, mit ihren modernen und bizarr gestalteten Gebäuden, wie zum Beispiel dem Palácio da Alvorada und dem Cathedral Saint Peter.
5. Amazonas - Der Strom für die Ewigkeit</s> 
<|assistant|>{"max-items": "3", "tags": [{"name":"Brasilien", "score":"95"},  {"name":"Christusstatue", "score":"81"}, {"name":"Iguaçu-Wasserfälle", "score":"75"}]}</s> 
<|user|>{content}</s> 
<|assistant|>
'''

TAGGER_PROMPT = '''<|system|>You are a code generator. Always output your answer in JSON. No pre-amble.</s>
<|user|>Exoplaneten, Planeten außerhalb unseres Sonnensystems, sind seit der ersten Entdeckung 1995 
ein faszinierendes Forschungsfeld. Sie umkreisen fremde Sterne und bieten Einblicke in die Vielfalt 
des Universums. Mit Tausenden entdeckten Exoplaneten, von erdähnlichen bis zu Gasriesen, erweitern 
sie unser Verständnis von Planetenbildung und -entwicklung. Moderne Technologien wie das Weltraumteleskop 
Kepler haben die Suche und Analyse dieser entfernten Welten revolutioniert, wobei einige in der bewohnbaren 
Zone liegen, was Fragen nach möglichem außerirdischem Leben aufwirft.</s> 
<|assistant|>{"tags": [ {"name":"Exoplaneten", "score":100},  {"name":"Forschung", "score":70}, {"name":"außerirdisches Leben", "score":63},]}</s>
<|user|>{content}</s> 
<|assistant|>
'''

class Tagger:
    
    tagger = None
    conn = None
    
    def __init__(self):
        
        if self.tagger is None:
            print("LOADING tagger: %s" % tagger_model_name)
            time_start = time.time()
            self.tagger = Llama(model_path="models/" + tagger_model_name,
                             n_ctx=4096,
                             n_gpu_layers=n_gpu_layers,
                             n_batch=n_batch,
                             verbose=True)
            time_to_load = time.time() - time_start
            ptime = "%.1f" % time_to_load
            print("loaded tagger %s in %s seconds" % (tagger_model_name, ptime))
        if self.conn is None:
            self.connect_db()

    def tag_content(self, content):
        tag_string = None
        
        prompt = QTP2.replace("{content}", content)
        # print ("** Tagger Start: ", repr(prompt))                
        time_start = time.time()
        output = self.tagger(prompt,
                              max_tokens=256,
                              stop=["</s>", ],
                              echo=False,
                              temperature=0.2,
                              top_p=0.5,
                              top_k=3,
                              )
        # print("** Tagger ready: ", repr(output))
        time_to_load = time.time() - time_start
        ptime = "%.1f" % time_to_load
        print("** TIME %s seconds" % ptime)
        tag_string = output["choices"][0]["text"]
                
        return tag_string
    
            
    def tag(self, object_uuid, content):
        if content is None or content == "":
            print("ERROR:: Tagger.tag() No content specified.")
            raise Exception("ERROR:: Tagger.tag() No content specified.")
        # this gets an answer from the model
        tag_string = self.tag_content(content)
        # this tries to format the model answer to a tag dictionary
        tags = self.format_tags(tag_string)
        
        for tag in tags[0:3]:
            print("TAG: ", tag)
            self.add_tag_to_object(object_uuid=object_uuid, tag_uuid=tag["uuid"])
            
        return tags
    
    def format_tags(self, tag_string):
        tags = []
        jtags = []
        if (tag_string is None or tag_string == ""):
            return tags
        try:
            
            if '"tags":' not in tag_string:
                print("Warning:: ReDo: No tags found in: %s" % tag_string)
                # the answer does not contain the "tags": marker. Mostly the model talks too much. So lets tag that answer for it should be same topic but shorter
                tag_string2 = self.tag_content(tag_string)
                if tag_string2.find("tags") == -1:
                    print("ERROR:: Tagger.format_tags() No tags found in: %s" % tag_string2)
                    return tags
                else:
                    tag_string = tag_string2
            
            # tag_string = {"max-items": "3", "tags": [ {"name":"Ameisen", "score":90}, {"name":"Kommunikation", "score":75}, {"name":"Pheromone", "score":62},]}
            try:
                print("TAGSTRING: ", tag_string)
                jtags = json.loads(tag_string)
            except Exception as e:
                print("ERROR:: Tagger.format_tags() Could not parse JSON: %s" % tag_string)
                print("ERROR:: Exception: %s" % e)
                return tags
            
            if not "tags" in jtags:
                print("ERROR:: Tagger.format_tags() No tags found in: %s" % tag_string)
                return tags
            mtags = jtags["tags"]
            if not isinstance(mtags, list):
                print("ERROR:: Tagger.format_tags() No tags found in: %s" % tag_string)
                return tags
            print(len(mtags), " TAGS generated: ", mtags)
            for tag in mtags:
                # get the uuid of the tag by name from db
                tag2 = self.get_tag_by_name(tag["name"])
                tags.append({"uuid": tag2["uuid"], "name": tag2["name"]})
            print(len(tags), " TAGS generated: ", tags)
            return tags
        except Exception as e:
            print("ERROR:: Tagger.format_tags() for: %s" % tag_string)
            print("ERROR:: Exception: %s" % e)
            return tags
           
    def get_tag_by_name(self, tag_name=None):
        # Nutze eine parametrisierte Abfrage, um SQL-Injection zu verhindern
        query = None
        values = None    
        
        print("get_tag_by_name() - tag_name: %s" % tag_name)
        
        

        if tag_name is None or tag_name == "":
            # Log error or raise an exception
            print("ERROR: get_tag() - no name")
            return None

        
        query = "SELECT uuid, name FROM tags WHERE name = %s"
        values = (tag_name,)

        if query:
            print("get_tag() - query: %s, %s" % (query, values))
            tags = self.execute_query_tags(query, values)
            print("get_tag() - tags: %s" % tags)
            if tags:
                return tags[0]
            else:
                tag = self.insert_tag(tag_name)
                return tag
        else:
            # Log error or raise an exception
            print("get_tag() - no query")
            return None
        
    # this function inserts a new tag into table tags
    def insert_tag(self, name=None):
        if name is None:
            # Log error or raise an exception
            print("ERROR: insert_tag() - no name")
            return None
        
        query = "INSERT INTO tags (uuid, name) VALUES (DEFAULT, %s) RETURNING uuid, name"
        values = (name,)
        print("insert_tag() - query: %s, values: %s" % (query, values))
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                res = cur.fetchone()
                
                if res:
                    # Log successful operation
                    print("insert_tag() - tag inserted %s" % res[0])
                    tag = {'uuid': res[0], 'name': res[1]}
                    self.conn.commit()
                    return tag
                else:
                    # Log error or raise an exception
                    print("insert_tag() - no res returned")
                    return None
                
        except Exception as e:
            # Log exception
            print("insert_tag() - %s" % e)
            return None

    def execute_query_tags(self, query, values):
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                res = cur.fetchall()
                
                tags = []
                for tag in res:
                    tags.append({'uuid': tag[0], 'name': tag[1]})                    
                
                return tags
            
        except Exception as e:
            # Log exception
            print("Error:: execute_query_tags() - %s" % e)
            return None

    
    def connect_db(self):
        host = os.environ.get('POSTGRES_HOST')
        database = os.environ.get('POSTGRES_DB')
        user = os.environ.get('POSTGRES_USER')
        password = os.environ.get('POSTGRES_PASSWORD')
        
        self.conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password)
   
   
       # this function adds a tag to an object via table object_table
    def add_tag_to_object(self, object_uuid=None, tag_uuid=None):
        if object_uuid is None or tag_uuid is None:
            # Log error or raise an exception
            print("ERROR: add_tag_to_object() - no object_uuid or tag_uuid")
            return None
        
        query = "INSERT INTO object_tag (object_uuid, tag_uuid) VALUES (%s, %s)"
        values = (object_uuid, tag_uuid)
        return self.execute_query(query, values)
   
   
    def execute_query(self, query, values):
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                self.conn.commit()
                return True
            
        except Exception as e:
            # Log exception
            print("Error:: execute_query() - %s" % e)
            return False

   
   
   ## main & demo 
    
    def demo(self, content):
        # print("\nText: ", content)
        print("\n")
        print("Result: ", self.tag(content))
        return True
    
if __name__ == "__main__":

    content1 = '''Ameisen kommunizieren hauptsächlich durch chemische Signale, sogenannte Pheromone. Diese setzen sie ein, um Informationen über Futterquellen, Alarme oder die Richtung und Identität von Pfaden zu übermitteln. Sie verwenden auch Berührung und ihre Antennen zur Kommunikation. Ihre komplexe Kolonieorganisation basiert auf einer arbeitsteiligen Struktur ohne zentrale Kontrolle, wobei das kollektive Verhalten aus einfachen Interaktionen zwischen Individuen entsteht.'''
    content2 = '''Im 18. Jahrhundert war das Heilige Römische Reich Deutscher Nation, eine lose Vereinigung von Hunderten kleinerer Staaten und Territorien, das vorherrschende politische Gebilde im deutschen Raum. Diese Periode war geprägt von aufklärerischen Ideen, territorialen Konflikten und einer zunehmenden kulturellen Blüte, symbolisiert durch Persönlichkeiten wie Johann Wolfgang von Goethe und Ludwig van Beethoven. Das 19. Jahrhundert brachte tiefgreifende Veränderungen, beginnend mit den Befreiungskriegen gegen Napoleon und mündend in der zunehmenden Nationalbewegung, die schließlich 1871 zur Gründung des Deutschen Kaiserreichs unter preußischer Führung führte. Diese Ära war auch von der Industriellen Revolution geprägt, die Deutschland in eine moderne Industrienation transformierte und soziale sowie politische Veränderungen nach sich zog.'''
    content3 = '''Wolkenkratzer sind hohe, oft beeindruckende Gebäude, die als Wahrzeichen für Städte weltweit dienen. Sie nutzen fortschrittliche Technik und Materialien, um Höhen zu erreichen, die früher undenkbar waren, und sind häufig Zentren für Geschäfte und Wohnen. Ihre Konstruktion erfordert tiefgreifende Kenntnisse in Architektur, Ingenieurwesen und Nachhaltigkeit, um sowohl ästhetisch ansprechend als auch funktional zu sein.'''

        
    load_dotenv()
    my_tagger = Tagger()
    my_tagger.demo(content1)
    # my_tagger.demo(content2)
    # my_tagger.demo(content3)
