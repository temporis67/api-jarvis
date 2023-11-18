from flask import Flask, render_template, request, url_for, flash, redirect
from flask_cors import CORS, cross_origin

# project specific
from aichatapi import AiChatAPI
from db.db_tool import DB
from definitions.user import User
from pprint import pprint



app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
app.config['DEBUG'] = 'True'

my_db = DB()
my_api = AiChatAPI(my_db=my_db)  ## todo add Jarvis
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
            print("fetch_user() POST method")
            result = request.form
            for key in user.__dict__:
                if key in result and result[key] is not None and result[key] != '':
                    setattr(user, key, result[key])
                    print("fetch_user() %s : %s" % (key, result[key]))
                else:
                    print("fetch_user() %s not found" % key)
        else:
            print("request not used the POST method")
    except Exception as e:
        print("Error bei app.fetch_user(): %s " % e)

    # msg = {'name': name, 'password': password, 'email': email}
    # user = my_api.login_user(msg=msg)
    user3 = my_db.get_user(user=user)

    print("HERE USER3 fetch_user() Ende:")
    pprint(vars(user3))
    user2 = {'name': 'Peter', 'uuid': 'c382bc64-7817-11ee-b70f-047c16bbac51', 'email': 'ahem00@gmail.com', 'password': '123456'}
    return user2


#
@app.route('/api/questions', methods=['POST', 'GET'])
def fetch_questions():
    # pprint(vars(request))
    # print("fetch_questions() for user Start")
    user_uuid = None
    # for key in request.form:
    #    print("fetch_questions() %s : %s" % (key, request.form[key]))

    try:
        if request.method == 'POST':
            result = request.form
            if 'user_uuid' in result and result['user_uuid'] is not None and result['user_uuid'] != '':
                user_uuid = result['user_uuid']
                # print("fetch_questions() user_uuid ok: %s" % user_uuid)
            else:
                print("ERROR:: No user_uuid given to fetch_questions()")
        else:
            print("ERROR:: request not used the POST method")
    except Exception as e:
        print("ERROR:: Error bei app.questions(): %s " % e)

    # print("app.fetch_questions() UUID: %s :: %s" % (type(user_uuid), str(user_uuid)))
    questions = my_api.get_questions(user_uuid=user_uuid)

    # print("/api/questions sending: %s" % (questions,))

    # dummy_question_full = {
    #     "id": "WXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    #     "creator": "pAUL",
    #     "creatorUuid": "",
    #     "title": "Eine neue Frage",
    #     "content": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed non risus. Suspendisse ...",
    #     "dateCreated": "",
    #     "dateUpdated": "",
    #     "tags": []
    # }
    # dummy_array = [dummy_question_full]

    return questions


#
# Start App
#

if __name__ == '__main__':
    app.run()
