#
# Jarvis Backend API as proxy to internal and external model & db services
#

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
import json
from dotenv import load_dotenv
import os


# project specific
from db_tool import DB
from definitions.user import User
from definitions.question import Question
from definitions.answer import Answer
from jarvis.jarvis import Jarvis
from tagger import Tagger
from pprint import pprint

# Lade die Umgebungsvariablen aus der .env-Datei
load_dotenv()
JARVIS_PROTOCOL=os.getenv('JARVIS_PROTOCOL') or "http"
JARVIS_HOST=os.getenv('JARVIS_HOST') or "localhost"
JARVIS_PORT=os.getenv('JARVIS_PORT') or "5000"
JARVIS_BASE_URL=os.getenv('JARVIS_BASE_URL') or ""




app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknflasdf123s2#'
app.config['DEBUG'] = 'True'

my_jarvis = Jarvis()
my_db = DB()
my_tagger = Tagger()

CORS(app)


#
# Static Pages
#
@app.route(JARVIS_BASE_URL + '/')
def index():  # put application's code here
    return render_template('index.html')

#
# Handling Queries to LLM
#

is_working = False

@app.route(JARVIS_BASE_URL + '/api/ask', methods=['POST', 'GET'])
@cross_origin()
def ask():
    print("\n app.ask() Start")
    global is_working
    if is_working:
        return jsonify({'title': 'Server is busy'}), 200
    is_working = True

    if request.method != 'POST':
        is_working = False
        return jsonify({'error': 'Only POST method is allowed'}), 405

    model_string = request.form.get('model')
    if not model_string or str(model_string) == 'null':
        print("ERROR:: app.ask(): No model provided")
        is_working = False
        return jsonify({'error': 'No model provided'}), 400
    model = json.loads(model_string)
    # print("app.ask() model: %s" % model)
    # print("app.ask() model prompt: %s" % model['default_prompt'])
    if 'model_label' in model:
        model_name = model['model_label'][:8]
        model_uuid = model['uuid']
    else:
        model_name = "default"
        model_uuid = ""

    user_uuid = request.form.get('user_uuid')
    if not user_uuid or str(user_uuid) == 'null':
        print("ERROR:: app.ask(): No user_uuid provided")
        is_working = False
        return jsonify({'error': 'No user_uuid provided'}), 400

    creator_uuid = request.form.get('creator_uuid')
    if not creator_uuid or str(creator_uuid) == 'null' or str(creator_uuid) == 'undefined':
        print("ERROR:: app.ask(): No creator_uuid provided")
        is_working = False
        return jsonify({'error': 'No creator_uuid provided'}), 400

    question_uuid = request.form.get('question_uuid')
    if not question_uuid or str(question_uuid) == 'null':
        print("ERROR:: app.ask(): No question_uuid provided")
        is_working = False
        return jsonify({'error': 'No question_uuid provided'}), 400

    answer_string = request.form.get('answer')
    if not answer_string or str(answer_string) == 'null':
        print("ERROR:: app.ask(): No answer provided")
        is_working = False
        return jsonify({'error': 'No answer provided'}), 400
    print("app.ask() received answer: %s" % answer_string)

    answer = json.loads(answer_string)

    if 'uuid' in answer and answer['uuid'] != "":
        # updating existing answer
        print("app.ask() answer uuid is full")
    else:
        # creating new answer
        print("app.ask() answer uuid is empty, create new one")
        res = my_db.new_answer(user_uuid=user_uuid, creator_uuid=creator_uuid, question_uuid=question_uuid)
        if 'uuid' in res:
            answer['uuid'] = res['uuid']
        else:
            print("ERROR:: app.ask(): No answer_uuid could be created")
            is_working = False
            return jsonify({'error': 'No answer_uuid could be created'}), 400

    print("app.ask() answer uuid: %s" % answer['uuid'])

    prompt = request.form.get('prompt')
    if not prompt or str(prompt) == 'null':
        print("ERROR:: app.ask(): No prompt provided")
        is_working = False
        return jsonify({'error': 'No prompt provided'}), 400

    question_string = request.form.get('question')
    if not question_string or str(question_string) == 'null':
        print("ERROR:: app.ask(): No question provided")
        is_working = False
        return jsonify({'error': 'No question provided'}), 400
    

    context = request.form.get('context')
    if not context or str(context) == 'null':
        print("Warning:: app.ask(): No context provided")
        # is_working = False
        # return jsonify({'error': 'No context provided'}), 400
        pass
    # remove whitespaces and \n from context
    context = context.replace("  ", " ")
    context = context.replace("\n\n", "")
    
    try:
        # print("app.ask() user_uuid: %s" % user_uuid)
        # print("app.ask() question: %s" % question)
        #
        [answer_text, time_elapsed] = my_jarvis.ask(model=model, prompt=prompt, context=context, question=question_string)
        
        if answer_text is None or answer_text == "null" or answer_text == "":
            print("WARNING:: app.ask(): Model provided no answer")
            answer_text = "Sorry, ich weiß es nicht. (Model hat keine Antwort geliefert.)"
        print("app.ask() Success - answer: #%s#" % answer_text)
        
        
        answer['title'] = answer_text[:100]   # get short title from llm.
        answer['content'] = answer_text
        answer['time_elapsed'] = time_elapsed
        answer['creator'] = model_uuid
        answer['username'] = model_name

        my_db.update_answer(answer_uuid=answer['uuid'], title=answer['title'], content=answer['content'], time_elapsed=time_elapsed)

        print("app.ask() Success:: %s" % answer)
        is_working = False
        return jsonify(answer), 200
    except Exception as e:
        print("ERROR:: app.ask(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        is_working = False
        return jsonify({'error': 'Internal server error'}), 500


#
# handling user
#

# this function verifies the user by email and password
# expects param 'email' and 'password' in the request
@app.route(JARVIS_BASE_URL + '/api/verify_user', methods=['POST', 'GET'])
@cross_origin()
def verify_user():
    # pprint(vars(request))
    user = User()
    given_passsword = None
    if request.method == 'POST' and 'password' in request.form:
        given_passsword = request.form.get('password')

    try:
        if request.method == 'POST':
            # print("verify_user() POST method")
            result = request.form
            for key in user.__dict__:
                if key in result and result[key] is not None and result[key] != '':
                    setattr(user, key, result[key])
                    # print("verify_user() by %s : %s" % (key, result[key]))
                else:
                    # print("verify_user() %s not found" % key)
                    pass
        else:
            print("request not used the POST method")
    except Exception as e:
        print("Error bei app.verify_user(): %s " % e)

    user = my_db.get_user(user=user)

    if user is None:
        print("verify_user() user not found")
        return jsonify({'error': 'User not found'}), 400
    
    if str(given_passsword) != str(user.password):
        print("verify_user() wrong password: %s ### %s" % (str(given_passsword), str(user.password)))
        return jsonify({'error': 'Wrong password'}), 400

    print("verify_user() Success: ")
    if(user):
        pprint(vars(user))

    return user.__dict__, 200



@app.route(JARVIS_BASE_URL + '/api/user', methods=['POST', 'GET'])
@cross_origin()
def get_user():
    # pprint(vars(request))
    user = User()

    try:
        if request.method == 'POST':
            # print("get_user() POST method")
            result = request.form
            for key in user.__dict__:
                if key in result and result[key] is not None and result[key] != '':
                    setattr(user, key, result[key])
                    print("get_user() by %s : %s" % (key, result[key]))
                else:
                    # print("get_user() %s not found" % key)
                    pass
        else:
            print("request not used the POST method")
    except Exception as e:
        print("Error bei app.get_user(): %s " % e)


    user = my_db.get_user(user=user)

    if user is None:
        print("get_user() user not found")
        return jsonify({'error': 'User not found'}), 400
        
    
    print("get_user() Success: ")
    if(user):
        pprint(vars(user))

    return user.__dict__, 200

@app.route(JARVIS_BASE_URL + '/api/new_user', methods=['POST', 'GET'])
@cross_origin()
def new_user():
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405

    user = User()

    try:
        if request.method == 'POST':
            print("new_user() POST method")
            result = request.form
            for key in user.__dict__:
                if key in result and result[key] is not None and result[key] != '':
                    setattr(user, key, result[key])
                    print("new_user() %s : %s" % (key, result[key]))
                else:
                    print("new_user() %s not found" % key)
                    pass
        else:
            print("request not used the POST method")
    except Exception as e:
        print("Error bei app.new_user(): %s " % e)

    user = my_db.new_user(user=user)

    print("new_user() Success: %s" % vars(user))
    # pprint(vars(user))

    return user.__dict__, 200


#
# handling questions
#
@app.route(JARVIS_BASE_URL + '/api/questions', methods=['POST', 'GET'])
@cross_origin()
def get_questions():
    print("app.fetch_questions() Start")
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405

    user_uuid = request.form.get('user_uuid')
    if not user_uuid or str(user_uuid) == 'null':
        print("ERROR:: app.fetch_questions(): No user_uuid provided")
        return jsonify({'error': 'No user_uuid provided'}), 400

    isFilteredParam = request.form.get('filter')
    isFiltered = False
    if isFilteredParam and str(isFilteredParam) == 'true':
        isFiltered = True
    else:
        isFiltered = False

    try:
        print("app.fetch_questions() user_uuid: %s" % user_uuid)
        if isFiltered:
            questions = my_db.get_questions_by_tag(user_uuid=user_uuid)
        else:
            questions = my_db.get_questions(user_uuid=user_uuid)
        print("app.fetch_questions() Success - %s questions found" % len(questions))
        return jsonify(questions), 200
    except Exception as e:
        print("ERROR:: app.fetch_questions(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500


@app.route(JARVIS_BASE_URL + '/api/new_question', methods=['POST', 'GET'])
@cross_origin()
def new_question():
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405

    user_uuid = request.form.get('user_uuid')
    if not user_uuid:
        print("ERROR:: app.new_question(): No user_uuid provided")
        return jsonify({'error': 'No user_uuid provided'}), 400

    title = request.form.get('title')
    if not title:
        title = ""

    content = request.form.get('content')
    if not content:
        content = ""

    try:
        question = my_db.new_question(user_uuid=user_uuid, title=title, content=content)
        print("app.new_question() Success")
        pprint(question)
        return jsonify(question), 200
    except Exception as e:
        print("ERROR:: app.new_question(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500


@app.route(JARVIS_BASE_URL + '/api/update_question_rank', methods=['POST', 'GET'])
@cross_origin()
def update_question_rank():
    print("********** app.update_question_rank() Start")
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405

    user_uuid = request.form.get('user_uuid')
    if not user_uuid:
        print("ERROR:: app.update_question_rank(): No user_uuid provided")
        return jsonify({'error': 'No user_uuid provided'}), 400

    question_uuid = request.form.get('question_uuid')
    if not question_uuid:
        print("ERROR:: app.update_question_rank(): No question_uuid provided")
        return jsonify({'error': 'No question_uuid provided'}), 400

    rank = request.form.get('rank')
    if not rank:
        print("ERROR:: app.update_question_rank(): No rank provided")
        return jsonify({'error': 'No rank provided'}), 400

    try:
        question = my_db.update_question_rank(user_uuid=user_uuid, question_uuid=question_uuid, rank=rank)
        print("app.update_question_rank() Success")
        pprint(question)
        return jsonify(question), 200
    except Exception as e:
        print("ERROR:: app.update_question_rank(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500


@app.route(JARVIS_BASE_URL + '/api/update_question', methods=['POST', 'GET'])
@cross_origin()
def update_question():
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405

    user_uuid = request.form.get('user_uuid')
    if not user_uuid:
        print("ERROR:: app.update_question(): No user_uuid provided")
        return jsonify({'error': 'No user_uuid provided'}), 400

    question_string = request.form.get('question')

    # Prüfen, ob question_string None oder 'null' (als String) ist
    if question_string in (None, 'null'):
        print("ERROR:: app.update_question(): No question provided")
        return jsonify({'error': 'No question provided'}), 400

    try:
        question = json.loads(question_string)
        print("app.update_question() question2: %s" % question['uuid'])
    except json.JSONDecodeError:
        print("ERROR:: app.ask(): Invalid JSON for question")
        return jsonify({'error': 'Invalid JSON format for question'}), 400

    question_uuid = question['uuid']
    if not question_uuid:
        print("ERROR:: app.update_question(): No question_uuid provided")
        return jsonify({'error': 'No question_uuid provided'}), 400

    title = question['title']
    if not title:
        print("ERROR:: app.update_question(): No title provided")
        return jsonify({'error': 'No title provided'}), 400

    content = question['content']
    if not content:
        question['content'] = ""
        # print("ERROR:: app.update_question(): No content provided")
        # return jsonify({'error': 'No content provided'}), 400

    try:
        print("go for DB update")
        question = my_db.update_question(question=question)
        return jsonify(question), 200
    except Exception as e:
        print("ERROR:: app.update_question() end: %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500


@app.route(JARVIS_BASE_URL + '/api/delete_question', methods=['POST', 'GET'])
@cross_origin()
def delete_question():
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405

    user_uuid = request.form.get('user_uuid')
    if not user_uuid:
        print("ERROR:: app.delete_question(): No user_uuid provided")
        return jsonify({'error': 'No user_uuid provided'}), 400

    question_uuid = request.form.get('question_uuid')
    if not question_uuid:
        print("ERROR:: app.delete_question(): No question_uuid provided")
        return jsonify({'error': 'No question_uuid provided'}), 400

    try:
        question = my_db.delete_question(user_uuid=user_uuid, question_uuid=question_uuid)
        print("app.delete_question() Success %s" % question_uuid)
        return jsonify(question), 200
    except Exception as e:
        print("ERROR:: app.delete_question(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500


#
# handling answers
#
@app.route(JARVIS_BASE_URL + '/api/get_answers', methods=['POST', 'GET'])
@cross_origin()
def get_answers():
    print("app.get_answers() Start")
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405

    question_uuid = request.form.get('question_uuid')
    if not question_uuid or str(question_uuid) == 'null':
        print("ERROR:: app.get_answers(): No question_uuid provided")
        return jsonify({'error': 'No question_uuid provided'}), 400
    
    isFilteredParam = request.form.get('filter')
    isFiltered = False
    if isFilteredParam and str(isFilteredParam) == 'true':
        isFiltered = True
    else:
        isFiltered = False
        

    try:
        print("app.get_answers() question_uuid: %s" % question_uuid)
        
        if isFiltered:
            answers = my_db.get_answers_by_tag(question_uuid=question_uuid)
        else:
            answers = my_db.get_answers(question_uuid=question_uuid)
        
        print("app.get_answers() Success - %s answers found" % len(answers))
#        print("TIME ELAPSED: %s" % answers)
        return jsonify(answers), 200
    except Exception as e:
        print("ERROR:: app.get_answers(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500


@app.route(JARVIS_BASE_URL + '/api/new_answer', methods=['POST', 'GET'])
@cross_origin()
def new_answer():
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405

    user_uuid = request.form.get('user_uuid')
    if not user_uuid:
        print("ERROR:: app.new_answer(): No user_uuid provided")
        return jsonify({'error': 'No user_uuid provided'}), 400

    creator_uuid = request.form.get('creator_uuid')
    if not creator_uuid or str(creator_uuid) == 'null' or str(creator_uuid) == 'undefined':
        print("ERROR:: app.new_answer(): No creator_uuid provided")
        return jsonify({'error': 'No creator_uuid provided'}), 400

    question_uuid = request.form.get('question_uuid')
    if not question_uuid:
        print("ERROR:: app.new_answer(): No question_uuid provided")
        return jsonify({'error': 'No question_uuid provided'}), 400

    try:
        answer = my_db.new_answer(user_uuid=user_uuid, creator_uuid=creator_uuid, question_uuid=question_uuid)
        print("app.new_answer() Success")
        pprint(answer)
        return jsonify(answer), 200
    except Exception as e:
        print("ERROR:: app.new_answer(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500

@app.route(JARVIS_BASE_URL + '/api/update_answer_rank', methods=['POST', 'GET'])
@cross_origin()
def update_answer_rank():
    # print("app.update_answer_rank() Start")
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405

    answer_uuid = request.form.get('answer_uuid')
    if not answer_uuid:
        print("ERROR:: app.update_answer_rank(): No answer_uuid provided")
        return jsonify({'error': 'No answer_uuid provided'}), 400
    
    question_uuid = request.form.get('question_uuid')
    if not question_uuid:
        print("ERROR:: app.update_answer_rank(): No question_uuid provided")
        return jsonify({'error': 'No question_uuid provided'}), 400

    rank = request.form.get('rank')
    if not rank:
        print("ERROR:: app.update_answer_rank(): No rank provided")
        return jsonify({'error': 'No rank provided'}), 400

    try:
        answer = my_db.update_answer_rank(answer_uuid=answer_uuid, question_uuid=question_uuid, rank=rank)
        #print("app.update_answer_rank() Success")
        # pprint(answer)
        return jsonify(answer), 200
    except Exception as e:
        print("ERROR:: app.update_answer_rank(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500

@app.route(JARVIS_BASE_URL + '/api/update_answer', methods=['POST', 'GET'])
@cross_origin()
def update_answer():
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405

    answer_uuid = request.form.get('answer_uuid')
    if not answer_uuid:
        print("ERROR:: app.update_answer(): No answer_uuid provided")
        return jsonify({'error': 'No answer_uuid provided'}), 400

    title = request.form.get('title')
    if not title:
        print("ERROR:: app.update_answer(): No title provided")
        return jsonify({'error': 'No title provided'}), 400

    content = request.form.get('content')
    if not content:
        print("Warning:: app.update_answer(): No content provided")
        # return jsonify({'error': 'No content provided'}), 400

    try:
        answer = my_db.update_answer(answer_uuid=answer_uuid, title=title, content=content)        
        return jsonify(answer), 200
    except Exception as e:
        print("ERROR:: app.update_answer(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500

@app.route(JARVIS_BASE_URL + '/api/delete_answer', methods=['POST', 'GET'])
@cross_origin()
def delete_answer():
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405

    answer_uuid = request.form.get('answer_uuid')
    if not answer_uuid:
        print("ERROR:: app.delete_answer(): No answer_uuid provided")
        return jsonify({'error': 'No answer_uuid provided'}), 400

    try:
        answer = my_db.delete_answer(answer_uuid=answer_uuid)
        print("app.delete_answer() Success %s" % answer_uuid)
        return jsonify(answer), 200
    except Exception as e:
        print("ERROR:: app.delete_answer(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500


@app.route(JARVIS_BASE_URL + '/api/get_models', methods=['POST', 'GET'])
@cross_origin()
def get_models():
    print("app.get_models() Start")
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405

    try:
        models = my_db.get_models()
        print("app.get_models() Success - %s models found" % len(models))
        return jsonify(models), 200
    except Exception as e:
        print("ERROR:: app.get_models(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500

@app.route(JARVIS_BASE_URL + '/api/add_model', methods=['POST', 'GET'])
@cross_origin()
def add_model():
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405

    model_string = request.form.get('model')
    if not model_string or str(model_string) == 'null':
        print("ERROR:: app.add_model(): No model provided")
        return jsonify({'error': 'No model provided'}), 400

    try:
        model = json.loads(model_string)
        print("app.add_model() model: %s" % model['uuid'])
    except json.JSONDecodeError:
        print("ERROR:: app.add_model(): Invalid JSON for model")
        return jsonify({'error': 'Invalid JSON format for model'}), 400

    try:
        model = my_db.add_model(model=model)
        print("app.add_model() Success %s" % model['uuid'])
        return jsonify(model), 200
    except Exception as e:
        print("ERROR:: app.add_model(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500

@app.route(JARVIS_BASE_URL + '/api/update_model', methods=['POST', 'GET'])
@cross_origin()
def update_model():
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405

    model_string = request.form.get('model')
    if not model_string or str(model_string) == 'null':
        print("ERROR:: app.update_model(): No model provided")
        return jsonify({'error': 'No model provided'}), 400

    try:
        model = json.loads(model_string)
        print("app.update_model() model: %s" % model['uuid'])
    except json.JSONDecodeError:
        print("ERROR:: app.update_model(): Invalid JSON for model")
        return jsonify({'error': 'Invalid JSON format for model'}), 400

    try:
        model = my_db.update_model(model=model)
        print("app.update_model() Success %s" % model['uuid'])
        return jsonify(model), 200
    except Exception as e:
        print("ERROR:: app.update_model(): %s" % e)
        print("ERROR:: app.update_model(): %s" % model)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500

@app.route(JARVIS_BASE_URL + '/api/delete_model', methods=['POST', 'GET'])
@cross_origin()
def delete_model():
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405

    model_string = request.form.get('model')
    if not model_string or str(model_string) == 'null':
        print("ERROR:: app.delete_model(): No model provided")
        return jsonify({'error': 'No model provided'}), 400
    model = json.loads(model_string)

    
    if not "uuid" in model:
        print("ERROR:: app.delete_model(): No model_uuid provided")
        return jsonify({'error': 'No model_uuid provided'}), 400

    try:
        my_db.delete_model(model_uuid=model["uuid"])
        print("app.delete_model() Success %s" % model["uuid"])
        return jsonify({"message":"Model deleted."}), 200
    except Exception as e:
        print("ERROR:: app.delete_model(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500
    
# expects param 'tag' in the request
@app.route(JARVIS_BASE_URL + '/api/get_tag_by_name', methods=['POST', 'GET'])
@cross_origin()
def get_tag():
    print("app.get_tag() Start")
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405
    
    tag = request.form.get('tag')
    if not tag or str(tag) == 'null':
        print("ERROR:: app.get_tag(): No tag provided")
        return jsonify({'error': 'No tag provided'}), 400

    try:
        found_tag = my_db.get_tag_by_name(tag)
        print("app.get_tag() Success - %s tag found" % found_tag['uuid'])
        
        return jsonify(found_tag), 200
    except Exception as e:
        print("ERROR:: app.get_tag(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500

# this function set one tag to a given object_uuid
# expects param 'object_uuid' and 'tag' in the request
@app.route(JARVIS_BASE_URL + '/api/add_tag_to_object', methods=['POST', 'GET'])
@cross_origin()
def add_tag_to_object():
    print("app.add_tag_to_object() Start")
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405
    
    object_uuid = request.form.get('object_uuid')
    if not object_uuid or str(object_uuid) == 'null':
        print("ERROR:: app.add_tag_to_object(): No object_uuid provided")
        return jsonify({'error': 'No object_uuid provided'}), 400
    
    tag = request.form.get('tag')
    if not tag or str(tag) == 'null':
        print("ERROR:: app.add_tag_to_object(): No tag provided")
        return jsonify({'error': 'No tag provided'}), 400
    tag = json.loads(tag)

    try:
        my_db.add_tag_to_object(object_uuid, tag['uuid'])
        print("app.add_tag_to_object() Success")
        
        return jsonify(tag), 200
    except Exception as e:
        print("ERROR:: app.add_tag_to_object(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500


# this function sets a list of tags for a given answer
# expects param 'answer_uuid' and 'tags' in the request
@app.route(JARVIS_BASE_URL + '/api/set_tags_for_answer', methods=['POST', 'GET'])
@cross_origin()
def set_tags_for_answer():
    print("app.set_tags_for_answer() Start")
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405
    
    answer_uuid = request.form.get('answer_uuid')
    if not answer_uuid or str(answer_uuid) == 'null':
        print("ERROR:: app.set_tags_for_answer(): No answer_uuid provided")
        return jsonify({'error': 'No answer_uuid provided'}), 400
    
    tags = request.form.get('tags')
    if not tags or str(tags) == 'null':
        print("ERROR:: app.set_tags_for_answer(): No tags provided")
        return jsonify({'error': 'No tags provided'}), 400

    try:
        tags = json.loads(tags)
        print("app.set_tags_for_answer() tags: %s" % tags)
    except json.JSONDecodeError:
        print("ERROR:: app.set_tags_for_answer(): Invalid JSON for tags")
        return jsonify({'error': 'Invalid JSON format for tags'}), 400

    try:
        my_db.set_tags_for_object(answer_uuid, tags)
        print("app.set_tags_for_answer() Success")
        
        return jsonify({'success': True}), 200
    except Exception as e:
        print("ERROR:: app.set_tags_for_answer(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500


# this function removes a tag from a given object_uuid
# expects param 'object_uuid' and 'tag' in the request
@app.route(JARVIS_BASE_URL + '/api/remove_tag_from_object', methods=['POST', 'GET'])
@cross_origin()
def remove_tag_from_object():
    print("app.remove_tag_from_object() Start")
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405
    
    object_uuid = request.form.get('object_uuid')
    if not object_uuid or str(object_uuid) == 'null':
        print("ERROR:: app.remove_tag_from_object(): No object_uuid provided")
        return jsonify({'error': 'No object_uuid provided'}), 400
    
    tag_uuid = request.form.get('tag_uuid')
    if not tag_uuid or str(tag_uuid) == 'null':
        print("ERROR:: app.remove_tag_from_object(): No tag provided")
        return jsonify({'error': 'No tag provided'}), 400
    tag_uuid = json.loads(tag_uuid)

    try:
        my_db.remove_tag_from_object(object_uuid, tag_uuid)
        print("app.remove_tag_from_object() Success")
        
        return jsonify(tag_uuid), 200
    except Exception as e:
        print("ERROR:: app.remove_tag_from_object(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500
    
# this function gets all tags for an object_uuid
@app.route(JARVIS_BASE_URL + '/api/get_tags_for_object', methods=['POST', 'GET'])
@cross_origin()
def get_tags_for_object():
    
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405
    
    object_uuid = request.form.get('object_uuid')
    if not object_uuid or str(object_uuid) == 'null':
        print("ERROR:: app.get_tags_for_object(): No object_uuid provided")
        return jsonify({'error': 'No object_uuid provided'}), 400
    
    # print("app.get_tags_for_object() Start %s" % object_uuid)

    try:
        tags = my_db.get_tags_for_object(object_uuid)
        # print("app.get_tags_for_object() Success: %s Tags" % len(tags))
        
        return jsonify(tags), 200
    except Exception as e:
        print("ERROR:: app.get_tags_for_object(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500
    
# this function generates a list of tags with jarvis.tag(content)
# expects param 'context' in the request
@app.route(JARVIS_BASE_URL + '/api/generate_tags', methods=['POST', 'GET'])
@cross_origin()
def generate_tags():
    print("app.generate_tags() Start")
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405
    
    context = request.form.get('context')
    if not context or str(context) == 'null':
        print("ERROR:: app.generate_tags(): No context provided")
        return jsonify({'error': 'No context provided'}), 400

    object_uuid = request.form.get('object_uuid')
    if not object_uuid or str(object_uuid) == 'null':
        print("ERROR:: app.generate_tags(): No object_uuid provided")
        return jsonify({'error': 'No object_uuid provided'}), 400


    try:        
        tags = my_tagger.tag(object_uuid=object_uuid, content=context)
        print("app.generate_tags() Success: %s Tags" % tags)        
        return jsonify(tags), 200
    except Exception as e:
        print("ERROR:: app.generate_tags(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500

#
# Start App
#
if __name__ == '__main__':
    app.run(host=JARVIS_HOST, port=JARVIS_PORT, debug=True)
