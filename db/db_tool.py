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
            print("ERROR db_tool.get_questions(user_uuid):: No user_uuid given.")# Log error oder raise an exception
            return {}

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
                        'user_uuid': qu[0],
                        'title': qu[1],
                        'content': qu[2],
                        'date_created': str(qu[3]),
                        'date_updated': str(qu[4])
                    }

                return questions

        except Exception as e:
            print("ERROR db_tool.get_questions(user_uuid):: %s" % e)
            return {}

    # Data functions
    def get_user(self, user=None):
        # Nutze eine parametrisierte Abfrage, um SQL-Injection zu verhindern
        query = None
        values = None

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
