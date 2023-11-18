from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin

# project specific
from db.db_tool import DB
from definitions.user import User
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
@cross_origin()
def fetch_questions():
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405

    user_uuid = request.form.get('user_uuid')
    if not user_uuid:
        return jsonify({'error': 'No user_uuid provided'}), 400

    try:
        questions = my_db.get_questions(user_uuid=user_uuid)
        return jsonify(questions), 200
    except Exception as e:
        print("ERROR:: app.fetch_questions(): %s" % e)
        # Hier ein geeignetes Logging-Framework verwenden
        return jsonify({'error': 'Internal server error'}), 500



#
# Start App
#

if __name__ == '__main__':
    app.run()
