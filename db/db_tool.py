#
# Class to bundle all storage operations

import psycopg2
from definitions.user import User
from definitions.question import Question


class DB:
    conn = None

    def __init__(self):
        self.connect_db()

    def get_questions(self, user_uuid=None):
        # Überprüfen, ob eine user_uuid vorhanden ist
        if user_uuid is None:
            print("ERROR db_tool.get_questions(user_uuid):: No user_uuid given.")  # Log error oder raise an exception
            return {}
        else:
            print("db_tool.get_questions(user_uuid):: user_uuid: %s" % user_uuid)

        # Parametrisierte Abfrage verwenden
        query = ("SELECT qu.question_uuid, q.title, q.content, q.date_created, q.date_updated "
                 "FROM user_question AS qu "
                 "JOIN questions AS q ON qu.question_uuid = q.uuid "
                 "WHERE qu.user_uuid = %s")
        values = (user_uuid,)

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                res = cur.fetchall()

                questions = {}
                for qu in res:
                    questions[qu[0]] = {
                        'uuid': qu[0],
                        'title': qu[1],
                        'content': qu[2],
                        'date_created': str(qu[3]),
                        'date_updated': str(qu[4])
                    }

                return questions

        except Exception as e:
            print("ERROR db_tool.get_questions(user_uuid):: %s" % e)
            self.conn.rollback()
            return {}

    # Data functions
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
            return self.execute_query(query, values, user)
        else:
            # Log error or raise an exception
            print("get_user() - no query")
            pass

    def execute_query(self, query, values, user):
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                res = cur.fetchone()

                if res:
                    user.uuid, user.name, user.email, user.password = res
                    # Log successful operation
                    return user
                else:
                    # Handle user not found or insert new user
                    pass

        except Exception as e:
            # Log exception
            print("execute_query() - %s" % e)
            pass

    # system functions
    def connect_db(self):
        self.conn = psycopg2.connect(
            host="localhost",
            database="ai-chat-db",
            user="ai-chat-pguser",
            password="--jarvis+")

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

                question = {
                    'uuid': res[0],
                    'title': title,
                    'content': content,
                    'date_created': str(res[1]),
                    'date_updated': str(res[2])
                }

                print("New Question in DB: %s" % str(question))

                update_user_query = ("insert into user_question (user_uuid, question_uuid) values (%s, %s)")
                update_user_values = (user_uuid, question['uuid'])

                cur.execute(update_user_query, update_user_values)

                self.conn.commit()

                return question

        except Exception as e:
            print("ERROR db_tool.new_question(user_uuid):: %s" % e)
            return {}

    def update_question(self, user_uuid, question_uuid, title, content):

        # Überprüfen, ob eine user_uuid vorhanden ist
        if user_uuid is None:
            print("ERROR db_tool.update_question(user_uuid):: No user_uuid given.")
            return {}

        query = ("update questions set title = %s, content = %s, date_updated = DEFAULT where uuid = %s RETURNING "
                 "date_updated")
        values = (title, content, question_uuid)

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                res = cur.fetchone()

                question = {
                    'uuid': question_uuid,
                    'title': title,
                    'content': content,
                    'date_updated': str(res[0])
                }

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
