import json

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin

# project specific
from db.db_tool import DB
from definitions.user import User
from definitions.question import Question
from definitions.answer import Answer
from jarvis.jarvis import Jarvis
from pprint import pprint

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
app.config['DEBUG'] = 'True'

my_jarvis = Jarvis()
my_db = DB()

CORS(app)


#
# Static Pages
#
@app.route('/')
def index():  # put application's code here
    return render_template('index.html')

#
# Handling Queries to LLM
#

is_working = False

@app.route('/api/ask', methods=['POST', 'GET'])
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

    user_uuid = request.form.get('user_uuid')
    if not user_uuid or str(user_uuid) == 'null':
        print("ERROR:: app.ask(): No user_uuid provided")
        is_working = False
        return jsonify({'error': 'No user_uuid provided'}), 400

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
        print("app.ask() answer uuid is full")
    else:
        print("app.ask() answer uuid is empty, create new one")
        answer['uuid'] = my_db.new_answer(user_uuid=user_uuid, question_uuid=question_uuid)['uuid']

    print("app.ask() answer uuid: %s" % answer['uuid'])

    prompt = request.form.get('prompt')
    if not prompt or str(prompt) == 'null':
        print("ERROR:: app.ask(): No prompt provided")
        is_working = False
        return jsonify({'error': 'No prompt provided'}), 400

    try:
        # print("app.ask() user_uuid: %s" % user_uuid)
        # print("app.ask() question: %s" % question)
        #
        [answer_text, time_elapsed] = my_jarvis.ask(prompt=prompt)
        print("app.ask() Success - answer: #%s#" % answer_text)
        answer['title'] = answer_text[:100]   # get short title from llm.
        answer['content'] = answer_text
        answer['time_elapsed'] = str(time_elapsed)

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
@app.route('/api/user', methods=['POST', 'GET'])
@cross_origin()
def fetch_user():
    # pprint(vars(request))
    user = User()

    try:
        if request.method == 'POST':
            # print("fetch_user() POST method")
            result = request.form
            for key in user.__dict__:
                if key in result and result[key] is not None and result[key] != '':
                    setattr(user, key, result[key])
                    print("fetch_user() %s : %s" % (key, result[key]))
                else:
                    print("fetch_user() %s not found" % key)
                    pass
        else:
            print("request not used the POST method")
    except Exception as e:
        print("Error bei app.fetch_user(): %s " % e)

    user = my_db.get_user(user=user)

    print("fetch_user() Success: ")
    pprint(vars(user))

    return user.__dict__, 200


#
# handling questions
#
@app.route('/api/questions', methods=['POST', 'GET'])
@cross_origin()
def fetch_questions():
    print("app.fetch_questions() Start")
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405

    user_uuid = request.form.get('user_uuid')
    if not user_uuid or str(user_uuid) == 'null':
        print("ERROR:: app.fetch_questions(): No user_uuid provided")
        return jsonify({'error': 'No user_uuid provided'}), 400

    try:
        print("app.fetch_questions() user_uuid: %s" % user_uuid)

        questions = my_db.get_questions(user_uuid=user_uuid)
        print("app.fetch_questions() Success - %s questions found" % len(questions))
        return jsonify(questions), 200
    except Exception as e:
        print("ERROR:: app.fetch_questions(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/new_question', methods=['POST', 'GET'])
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


@app.route('/api/update_question', methods=['POST', 'GET'])
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
        print("ERROR:: app.update_question(): No content provided")
        return jsonify({'error': 'No content provided'}), 400

    try:
        print("go for DB update")
        question = my_db.update_question(question=question)
        return jsonify(question), 200
    except Exception as e:
        print("ERROR:: app.update_question() end: %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/delete_question', methods=['POST', 'GET'])
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
@app.route('/api/answers', methods=['POST', 'GET'])
@cross_origin()
def get_answers():
    print("app.get_answers() Start")
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405

    question_uuid = request.form.get('question_uuid')
    if not question_uuid or str(question_uuid) == 'null':
        print("ERROR:: app.fetch_answers(): No question_uuid provided")
        return jsonify({'error': 'No question_uuid provided'}), 400

    try:
        print("app.fetch_answers() question_uuid: %s" % question_uuid)
        answers = my_db.get_answers(question_uuid=question_uuid)
        print("app.fetch_answers() Success - %s answers found" % len(answers))
        return jsonify(answers), 200
    except Exception as e:
        print("ERROR:: app.fetch_answers(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/new_answer', methods=['POST', 'GET'])
@cross_origin()
def new_answer():
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405

    user_uuid = request.form.get('user_uuid')
    if not user_uuid:
        print("ERROR:: app.new_answer(): No user_uuid provided")
        return jsonify({'error': 'No user_uuid provided'}), 400

    question_uuid = request.form.get('question_uuid')
    if not question_uuid:
        print("ERROR:: app.new_answer(): No question_uuid provided")
        return jsonify({'error': 'No question_uuid provided'}), 400

    try:
        answer = my_db.new_answer(user_uuid=user_uuid, question_uuid=question_uuid)
        print("app.new_answer() Success")
        pprint(answer)
        return jsonify(answer), 200
    except Exception as e:
        print("ERROR:: app.new_answer(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/update_answer', methods=['POST', 'GET'])
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

@app.route('/api/delete_answer', methods=['POST', 'GET'])
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


#
# Start App
#
if __name__ == '__main__':
    app.run()
