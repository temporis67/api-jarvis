from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin

# project specific
from db.db_tool import DB
from definitions.user import User
from definitions.question import Question
from pprint import pprint

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
app.config['DEBUG'] = 'True'

my_db = DB()
CORS(app)

#
# Static Pages
#
@app.route('/')
def index():  # put application's code here
    return render_template('index.html')


def get_param(param):
    if param in request.form and request.form[param] is not None and request.form[param] != '':
        return request.form[param]
    else:
        return None

#
# Hooks for NextJS API
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
                    # print("fetch_user() %s : %s" % (key, result[key]))
                else:
                    # print("fetch_user() %s not found" % key)
                    pass
        else:
            print("request not used the POST method")
    except Exception as e:
        print("Error bei app.fetch_user(): %s " % e)

    user = my_db.get_user(user=user)

    print("fetch_user() Success: ")
    pprint(vars(user))

    return user.__dict__, 200


@app.route('/api/questions', methods=['POST', 'GET'])
@cross_origin()
def fetch_questions():
    print("app.fetch_questions() Start")
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405

    user_uuid = request.form.get('user_uuid')
    if not user_uuid:
        return jsonify({'error': 'No user_uuid provided'}), 400

    try:
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
        print("ERROR:: app.new_question(): No title provided")
        return jsonify({'error': 'No title provided'}), 400

    content = request.form.get('content')
    if not content:
        print("ERROR:: app.new_question(): No content provided")
        return jsonify({'error': 'No content provided'}), 400

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

    question_uuid = request.form.get('question_uuid')
    if not question_uuid:
        print("ERROR:: app.update_question(): No question_uuid provided")
        return jsonify({'error': 'No question_uuid provided'}), 400

    title = request.form.get('title')
    if not title:
        print("ERROR:: app.update_question(): No title provided")
        return jsonify({'error': 'No title provided'}), 400

    content = request.form.get('content')
    if not content:
        print("ERROR:: app.update_question(): No content provided")
        return jsonify({'error': 'No content provided'}), 400

    try:
        question = my_db.update_question(user_uuid=user_uuid, question_uuid=question_uuid, title=title, content=content)
        return jsonify(question), 200
    except Exception as e:
        print("ERROR:: app.update_question(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500

# TODO: Implement delete_question
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
        return jsonify(question), 200
    except Exception as e:
        print("ERROR:: app.delete_question(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500



#
# Start App
#

if __name__ == '__main__':
    app.run()
