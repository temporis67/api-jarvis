#
# Class to bundle all storage operations
import datetime

import psycopg2
from definitions.user import User
from definitions.question import Question
from definitions.answer import Answer


class DB:
    conn = None

    # system functions
    def __init__(self):
        self.connect_db()

    def connect_db(self):
        self.conn = psycopg2.connect(
            host="localhost",
            database="ai-chat-db",
            user="ai-chat-pguser",
            password="--jarvis+")

    #
    # user functions
    #
    def get_user(self, user=None):
        # Nutze eine parametrisierte Abfrage, um SQL-Injection zu verhindern
        query = None
        values = None

        if user is None:
            # Log error or raise an exception
            print("ERROR: get_user() - no user")
            return None

        if user.uuid:
            query = "SELECT uuid, username, email, password FROM users WHERE uuid = %s"
            values = (user.uuid,)
        elif user.name:
            query = "SELECT uuid, username, email, password FROM users WHERE username = %s"
            values = (user.name,)
        elif user.email:
            query = "SELECT uuid, username, email, password FROM users WHERE email = %s"
            values = (user.email,)

        if query:
            print("get_user() - query: %s, %s" % (query, values))
            return self.execute_query_user(query, values, user)
        else:
            # Log error or raise an exception
            print("get_user() - no query")
            pass

    def execute_query_user(self, query, values, user):
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                res = cur.fetchone()

                if res:
                    user.uuid, user.name, user.email, user.password = res
                    # Log successful operation
                    print("execute_query() - user found %s" % user.uuid)
                    return user
                else:
                    # Handle insert new user
                    return self.insert_user(user)

        except Exception as e:
            # Log exception
            print("execute_query() - %s" % e)
            pass

    def insert_user(self, user):

        print("insert_user() - user: %s" % user)
        query = "INSERT INTO users (uuid, username, email, password) VALUES (DEFAULT, %s, %s, %s) RETURNING uuid"
        values = (user.name, user.email, user.password)

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                res = cur.fetchone()

                if res:
                    user.uuid = res[0]
                    # Log successful operation
                    return user
                else:
                    # Log error or raise an exception
                    print("insert_user() - no res returned")
                    pass

        except Exception as e:
            # Log exception
            print("insert_user() - %s" % e)
            pass

    #
    # questions functions
    #
    def get_questions(self, user_uuid=None):
        # Überprüfen, ob eine user_uuid vorhanden ist
        if user_uuid is None:
            print("ERROR db_tool.get_questions(user_uuid):: No user_uuid given.")  # Log error oder raise an exception
            return {}
        else:
            print("db_tool.get_questions(user_uuid):: user_uuid: %s" % user_uuid)

        # Parametrisierte Abfrage verwenden
        query = (
            "SELECT qu.question_uuid, q.title, q.content, q.date_created, q.date_updated, u.username "
            "FROM user_question AS qu "
            "JOIN questions AS q ON qu.question_uuid = q.uuid "
            "JOIN users AS u ON qu.user_uuid = u.uuid "
            "WHERE qu.user_uuid = %s ORDER BY q.date_updated DESC"
        )
        values = (user_uuid,)

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                res = cur.fetchall()

                questions = {}
                for qu in res:
                    # print("db_tool.get_questions(user_uuid):: qu: %s" % qu[4])

                    date_created = qu[3]
                    date_updated = qu[4]

                    questions[qu[0]] = {
                        'uuid': qu[0],
                        'title': qu[1],
                        'content': qu[2],

                        'date_created': date_created,
                        'date_updated': date_updated,
                        'user_uuid': user_uuid,
                        'user_name': qu[5],
                    }

                return questions

        except Exception as e:
            print("ERROR db_tool.get_questions(user_uuid):: %s" % e)
            self.conn.rollback()
            return {}

    def new_question(self, user_uuid, title, content):

        # Überprüfen, ob eine user_uuid vorhanden ist
        if user_uuid is None:
            print("ERROR db_tool.new_question(user_uuid):: No user_uuid given.")
            return {}

        query = ("insert into questions (uuid, title,content) values (DEFAULT,%s,%s) RETURNING uuid, date_created, "
                 "date_updated")
        values = (title, content)

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                res = cur.fetchone()
                print("Insert OK")
                date_created = res[1]

                date_updated = res[2]

                question = {
                    'uuid': res[0],
                    'title': title,
                    'content': content,
                    'date_created': date_created,
                    'date_updated': date_updated,
                }

                print("New Question in DB: %s" % str(question))

                update_user_query = ("insert into user_question (user_uuid, question_uuid) values (%s, %s)")
                update_user_values = (user_uuid, question['uuid'])

                cur.execute(update_user_query, update_user_values)

                self.conn.commit()

                return question

        except Exception as e:
            print("ERROR db_tool.new_question(user_uuid):: %s" % e)
            self.conn.rollback()
            return {}

    def update_question(self, question=None):

        # Überprüfen, ob eine user_uuid vorhanden ist
        if question is None:
            print("ERROR db_tool.update_question(question):: No question given.")
            return {}
        if question['uuid'] is None or question['uuid'] == "" or question['title'] is None or question['title'] == "":
            print("ERROR db_tool.update_question(question):: No question content given.")
            return {}

        query = "update questions set title = %s, content = %s, date_updated = now() where uuid = %s"
        values = (question['title'], question['content'], question['uuid'])
        print("db_tool.update_question(question):: query: %s, values: %s" % (query, values))

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)

                formatted_time = datetime.datetime.now()
                question["date_updated"] = formatted_time

                print("Updated Question in DB: %s" % str(question))

                self.conn.commit()

                return question

        except Exception as e:
            print("ERROR db_tool.update_question(user_uuid):: %s" % e)
            return {}

    def delete_question(self, user_uuid, question_uuid):

        # Überprüfen, ob eine user_uuid vorhanden ist
        if user_uuid is None:
            print("ERROR db_tool.delete_question(user_uuid):: No user_uuid given.")
            return {}

        query = ("delete from questions where uuid = %s")
        values = (question_uuid,)
        query2 = ("delete from user_question where question_uuid = %s")
        values2 = (question_uuid,)

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                cur.execute(query2, values2)

                print("Deleted Question in DB: %s" % question_uuid)

                self.conn.commit()

                return {}

        except Exception as e:
            print("ERROR db_tool.delete_question(user_uuid):: %s" % e)
            return {}

    #
    # answers functions
    #

    def get_answers(self, question_uuid=None):
        # Überprüfen, ob eine user_uuid vorhanden ist
        if question_uuid is None:
            print("ERROR db_tool.get_answers(question_uuid):: No question_uuid given.")
            return {}
        else:
            print("Start db_tool.get_answers(question_uuid):: question_uuid: %s" % question_uuid)

        # Parametrisierte Abfrage verwenden
        query = ('SELECT '
                 '    answers.*,'
                 ' ROUND('
                 ' EXTRACT(HOUR FROM answers.time_elapsed) * 3600 + ' 
                 ' EXTRACT(MINUTE FROM answers.time_elapsed) * 60 + ' 
                 ' EXTRACT(SECOND FROM answers.time_elapsed),'
                 ' 1) AS seconds, '
                 ' users.username AS user_name, '
                 '    CASE'
                 '        WHEN users.uuid IS NOT NULL THEN users.username '
                 '        WHEN models.uuid IS NOT NULL THEN models.model_label '
                 '    END AS creator_name '
                 'FROM '
                 '    answers '
                 'JOIN '
                 '    question_answer ON answers.uuid = question_answer.answer_uuid '
                 'JOIN '
                 '    user_question ON question_answer.question_uuid = user_question.question_uuid '
                 'LEFT JOIN '
                 '    users ON answers.creator_uuid = users.uuid '
                 'LEFT JOIN '
                 '    models ON answers.creator_uuid = models.uuid '
                 'WHERE '
                 '    question_answer.question_uuid = %s'

                 )
        values = (question_uuid,)

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                res = cur.fetchall()

                # Hole die Spaltennamen
                column_names = [desc[0] for desc in cur.description]

                answers = {}
                for row in res:
                    answer = {column_names[i]: str(row[i]) for i in range(len(column_names))}
                    answers[row[column_names.index('uuid')]] = answer

                return answers

        except Exception as e:
            print("ERROR db_tool.get_answers(question_uuid):: %s" % e)
            self.conn.rollback()
            return {}

    def format_timestamp(self, timestamp):
        """ Wandelt einen Unix-Zeitstempel in das Format 'DD.MM.YY HH:MM' um. """
        return datetime.fromtimestamp(timestamp).strftime("%d.%m.%y %H:%M")

    def new_answer(self, user_uuid, creator_uuid, question_uuid):

        for p in [user_uuid, creator_uuid, question_uuid]:
            if p is None or p == "" or p == "None" or p == "null" or p == "NULL" or p == "undefined":
                print("ERROR:: db_tool.new_answer() Missing Parameter - %s" % p)
                return {}

        query = (
            "insert into answers (uuid, creator_uuid, user_uuid, question) values (DEFAULT, %s, %s, %s) "
            "RETURNING uuid, date_created, "
            "date_updated")
        values = (creator_uuid, user_uuid, question_uuid)
        print(" query: %s" % query)
        print(" values: %s" % str(values))

        try:
            with self.conn.cursor() as cur:

                try:
                    cur.execute(query, values)
                    res = cur.fetchone()
                except Exception as e:
                    print(f"Exception Type: {type(e)}")
                    print(f"Error Message: {e}")
                    self.conn.rollback()
                    return {}

                print("Insert OK")

                date_created = res[1]

                date_updated = res[2]

                answer = {
                    'uuid': res[0],
                    'creator_uuid': creator_uuid,
                    'user_uuid': user_uuid,
                    'question': question_uuid,
                    'date_created': date_created,
                    'date_updated': date_updated,
                }

                print("New Answer in DB: %s" % str(answer))

                update_question_query = "insert into question_answer (question_uuid, answer_uuid) values (%s, %s)"
                update_question_values = (question_uuid, answer['uuid'])

                cur.execute(update_question_query, update_question_values)

                self.conn.commit()

                return answer

        except Exception as e:
            print("ERROR db_tool.new_answer(user_uuid, creator_id, question_uuid):: %s" % e)
            print(f"Exception Type: {type(e)}")
            self.conn.rollback()
            return {}

    def update_answer(self, answer_uuid, title, content, time_elapsed=None):

        # Überprüfen, ob eine answer_uuid vorhanden ist
        if answer_uuid is None:
            print("ERROR db_tool.update_answer(answer_uuid):: No answer_uuid given.")
            return {}

        if title is None:
            title = ""
        if content is None:
            content = ""

        if time_elapsed is None:
            query = ("update answers set title = %s, content = %s, date_updated = DEFAULT where uuid = %s RETURNING "
                     "date_updated")
            values = (title, content, answer_uuid)
        else:
            query = (
                "update answers set title = %s, content = %s, date_updated = DEFAULT,"
                " time_elapsed = %s where uuid = %s RETURNING "
                "date_updated")

            # Umwandlung der Sekunden in Stunden, Minuten, Sekunden und Mikrosekunden
            hours, remainder = divmod(time_elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)
            seconds, microseconds = divmod(seconds, 1)

            # Konvertierung in ein time-Objekt
            time_value = datetime.time(int(hours), int(minutes), int(seconds), int(microseconds * 1_000_000))

            values = (title, content, time_value, answer_uuid)

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                res = cur.fetchone()

                answer = {
                    'uuid': answer_uuid,
                    'title': title,
                    'content': content,
                    'date_updated': str(res[0]),
                    'time_elapsed': time_elapsed,
                }

                print("Updated Answer in DB: %s" % str(answer))

                self.conn.commit()

                return answer

        except Exception as e:
            print("ERROR db_tool.update_answer(answer_uuid):: %s" % e)
            return {}

    def delete_answer(self, answer_uuid):

        # Überprüfen, ob eine answer_uuid vorhanden ist
        if answer_uuid is None:
            print("ERROR db_tool.delete_answer(answer_uuid):: No answer_uuid given.")
            return {}

        query = ("delete from answers where uuid = %s")
        values = (answer_uuid,)
        query2 = ("delete from question_answer where answer_uuid = %s")
        values2 = (answer_uuid,)

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                cur.execute(query2, values2)

                print("Deleted Answer in DB: %s" % answer_uuid)

                self.conn.commit()

                return {}

        except Exception as e:
            print("ERROR db_tool.delete_answer(answer_uuid):: %s" % e)
            return {}

    # Let's write get_models, add_model, update_model, delete_model
    def get_models(self):
        query = ("SELECT * FROM models ORDER BY model_label ASC")
        values = ()

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                res = cur.fetchall()

                models = {}
                for row in res:
                    model = {
                        'uuid': row[0],
                        'model_filename': row[1],
                        'model_label': row[2],
                        'model_type': row[3],
                        'default_prompt': row[4],
                        'default_max_length': row[5],
                    }
                    models[row[0]] = model

                return models

        except Exception as e:
            print("ERROR db_tool.get_models():: %s" % e)
            self.conn.rollback()
            return {}

    # def add_model(self, model):
    #     query = ("INSERT INTO models (uuid, model_filename, model_label, model_type, default_prompt, default_max_length) VALUES (DEFAULT, %s, %s, %s, %s, %s) RETURNING uuid")
    #     values = (model.model_filename, model.model_label, model.model_type, model.default_prompt, model.default_max_length)
    #
    #     try:
    #         with self.conn.cursor() as cur:
    #             cur.execute(query, values)
    #             res = cur.fetchone()
    #
    #             if res:
    #                 model.uuid = res[0]
    #                 # Log successful operation
    #                 return model
    #             else:
    #                 # Log error or raise an exception
    #                 print("add_model() - no res returned")
    #                 pass
    #
    #     except Exception as e:
    #         # Log exception
    #         print("add_model() - %s" % e)
    #         pass

    def update_model(self, model):
        query = "UPDATE models SET model_filename = %s, model_label = %s,"\
                " model_type = %s, default_prompt = %s, default_max_length = %s WHERE uuid = %s"
        values = (model['model_filename'], model['model_label'], model['model_type'],
                  model['default_prompt'],
                  model['default_max_length'], model['uuid'])

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)

                print("Updated Model in DB: %s" % str(model))

                self.conn.commit()

                return model

        except Exception as e:
            print("ERROR db_tool.update_model(model):: %s" % e)
            return {}

    def delete_model(self, model_uuid):
        query = ("DELETE FROM models WHERE uuid = %s")
        values = (model_uuid,)

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)

                print("Deleted Model in DB: %s" % model_uuid)

                self.conn.commit()

                return {}

        except Exception as e:
            print("ERROR db_tool.delete_model(model_uuid):: %s" % e)
            return {}
