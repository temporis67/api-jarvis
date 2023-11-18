#
# Class to bundle all storage operations
from typing import Any

import psycopg2
from definitions.user import User
from definitions.question import Question


class DB:
    conn = None

    def __init__(self):
        self.connect_db()

    # Data functions
    def get_user(self, user=None):

        print("Get User Start: %s / %s / %s / %s" % (user.uuid, user.name, user.email, user.password))

        if user.uuid is not None and user.uuid == 'undefined':
            print("ERROR:: get_user() user_uuid is undefined")

        if user.uuid is not None:
            cur = self.conn.cursor()
            try:
                print("get user by user_uuid: %s" % user.uuid)
                stmt = ("select (uuid, username, email, password) from users where uuid = '%s'" % user.uuid)
                cur.execute(stmt)
                res = cur.fetchone()
                if res is None:
                    cur.close()
                    return None
                user.uuid = res[0]
                user.name = res[1]
                user.email = res[2]
                user.password = res[3]
            except Exception as e:
                print("Error33:: get_user() by user.uuid: %s" % e)
            cur.close()
            return user

        if user.name is not None:
            print("get user by name: %s :: %s" % (user.name, user.password))
            cur = self.conn.cursor()
            stmt = "select * from users where username = '%s'" % user.name
            print("get_user() stmt: %s" % stmt)
            try:
                cur.execute(stmt)
                res = cur.fetchone()
            except Exception as e:
                print("ERROR:: get_user() by name: %s" % e)
                res = None

            if res is None:
                stmt = "insert into users (uuid, username, email, password) values (DEFAULT,'%s','%s','%s') RETURNING uuid" % (user.name, user.email, user.password)
                raise Exception("ERROR:: new user by name: %s" % stmt)
                ## cur.execute(stmt)
                res = cur.fetchone()
                print("INSERT: " + str(res[0]))
                user.uuid = res[0]
                user.name = user.name
                user.email = user.email
                user.password = user.password
                self.conn.commit()
                print("New User in DB: %s" % str(user))
            else:
                user.uuid = res[0]
                user.name = res[1]
                user.email = res[2]
                user.password = res[3]

            cur.close()
            return user

        if user.email is not None:
            print("get user by mail: %s :: %s" % (user.email, user.password))
            cur = self.conn.cursor()
            stmt = "select * from users where email = '%s'" % user.email
            try:
                cur.execute(stmt)
                res = cur.fetchone()
            except Exception as e:
                print("ERROR:: get_user() by mail: %s" % e)
                res = None

            if res is None:
                stmt = "insert into users (uuid, username, email, password) values (DEFAULT,'%s','%s','%s') RETURNING uuid" % (user.name, user.email, user.password)
                try:
                    cur.execute(stmt)
                    res = cur.fetchone()
                except Exception as e:
                    print("ERROR:: new user by mail: %s" % e)
                    res = None
                print("INSERT: %s" % stmt )
                user.uuid = res[0]
                user.name = user.name
                user.email = user.email
                user.password = user.password
                self.conn.commit()
                print("New User in DB: %s" % str(user))

            else:
                user.uuid = res[0]
                user.name = res[1]
                user.email = res[2]
                user.password = res[3]
                print("Loaded User from DB: %s %s" % (user, user.name))

            cur.close()
            print("get_user() Ende: %s" % user)

            return user

    def get_questions(self, user_uuid=None):
        print("*************** Get Questions: %s #" % user_uuid)

        if user_uuid is not None:
            cur = self.conn.cursor()
            # stmt = "select question_uuid from user_question where user_uuid = '%s'" % user_uuid
            stmt = "SELECT qu.question_uuid, q.title, q.content, q.date_created, q.date_updated FROM user_question AS qu JOIN questions AS q ON qu.question_uuid = q.uuid WHERE qu.user_uuid = '%s'" % user_uuid
            print("get_questions() stmt: %s #" % stmt)
            cur.execute(stmt)
            res = cur.fetchall()

            questions = {}
            for qu in res:
                question = dict()
                # print("get_questions %s" % str(qu))
                question['user_uuid'] = qu[0]
                question['title'] = qu[1]
                question['content'] = qu[2]
                question['date_created'] = str(qu[3])
                question['date_updated'] = str(qu[4])
                questions[qu[0]] = question

            cur.close()
            good_question = {
                'name': "Test",
                'title': 'Test Title',
            }
            return questions

    def get_question(self, uuid=None, user_uuid=None, title=None):
        question = Question()
        print("Get Question: %s" % title)

        if uuid is not None:
            cur = self.conn.cursor()
            stmt = "select (uuid, title) from questions where uuid = '%s'" % uuid
            cur.execute(stmt)
            res = cur.fetchone()
            if res is None:
                return None
            question.uuid = res[0]
            question.text = res[1]
            return question

        if title is not None:
            cur = self.conn.cursor()
            stmt = "select * from questions where title = '%s'" % title
            cur.execute(stmt)
            res = cur.fetchone()

            if res is None:
                stmt = "insert into questions (uuid, title) values (DEFAULT,'%s') RETURNING uuid" % title
                cur.execute(stmt)
                res = cur.fetchone()
                # print("INSERT Question: " + str(res[0]))
                question.uuid = res[0]
                question.title = title

                user_stmt = "insert into user_question values('%s','%s')" % (user_uuid, question.uuid)
                cur.execute(user_stmt)

                self.conn.commit()
                print("New Question in DB: %s" % str(question))
            else:
                question.uuid = res[0]
                question.title = res[1]

            cur.close()
            return question

    # Helper
    def make_statement(some_class):
        stmt = ""
        # print("Some Class # %s #" % repr(some_class))
        stmt += "INSERT INTO "
        table_name = some_class.__class__.__name__
        stmt += table_name + " ("
        v_names = ""
        values = ""
        for f in dir(some_class):
            if not f.startswith('_') and f in some_class.__dict__:
                # print("F: %s" % repr(f))
                v_names += f + ', '
                values += repr(some_class.__dict__[f]) + ", "

        stmt += v_names + ") VALUES ("
        stmt += values + ")"

        # print("HERE 2 ### " + getattr(some_class, 'text'))

        return stmt

    # system functions
    def connect_db(self):
        self.conn = psycopg2.connect(
            host="localhost",
            database="ai-chat-db",
            user="ai-chat-pguser",
            password="--jarvis+")

    def show_pg_version(self):
        # create a cursor
        cur = self.conn.cursor()

        # execute a statement
        print('PostgreSQL database version:')
        # display the PostgreSQL database server version
        cur.execute('SELECT version()')
        db_version = cur.fetchone()
        print(db_version)

        # get data
        cur.execute('select * from questions')
        question = cur.fetchone()
        print(question)

        cur.close()
