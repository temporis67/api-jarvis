import datetime
import json
import psycopg2
from definitions.user import User
from definitions.question import Question
from definitions.answer import Answer
import os

class DB:
    conn = None

    # system functions
    def __init__(self):
        self.connect_db()


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
        
        
    #
    # tag functions
    #
    # CREATE TABLE tags(
    # uuid uuid NOT NULL,
    # name varchar(255) NOT NULL,
    # PRIMARY KEY(uuid)
    # );
    
    def get_tag_by_name(self, tag=None):
        # Nutze eine parametrisierte Abfrage, um SQL-Injection zu verhindern
        query = None
        values = None    
        
        print("get_tag_by_name() - tag: %s" % tag)
        
        tag = json.loads(tag)

        if tag is None or "name" not in tag or tag["name"] == "":
            # Log error or raise an exception
            print("ERROR: get_tag() - no name")
            return None

        if tag:
            query = "SELECT uuid, name FROM tags WHERE name = %s"
            values = (tag["name"],)

        if query:
            print("get_tag() - query: %s, %s" % (query, values))
            tags = self.execute_query_tags(query, values)
            print("get_tag() - tags: %s" % tags)
            if tags:
                return tags[0]
            else:
                tag = self.insert_tag(tag["name"])
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
                    return tag
                else:
                    # Log error or raise an exception
                    print("insert_tag() - no res returned")
                    return None
                
        except Exception as e:
            # Log exception
            print("insert_tag() - %s" % e)
            return None
        
        
    # this function adds a tag to an object via table object_table
    def add_tag_to_object(self, object_uuid=None, tag_uuid=None):
        if object_uuid is None or tag_uuid is None:
            # Log error or raise an exception
            print("ERROR: add_tag_to_object() - no object_uuid or tag_uuid")
            return None
        
        query = "INSERT INTO object_tag (object_uuid, tag_uuid) VALUES (%s, %s)"
        values = (object_uuid, tag_uuid)
        return self.execute_query(query, values)
    
        
    # tags = [{'uuid':'1234567889','name':'tag1'}, {'uuid':'1234567889','name':'tag2'}]
    def set_tags_for_object(self, object_uuid=None, tags=None):
        if object_uuid is None or tags is None:
            # Log error or raise an exception
            print("ERROR: set_tags_for_object() - no object_uuid or tags")
            return None
        
        # delete all tags for object_uuid
        query = "DELETE FROM object_tag WHERE object_uuid = %s"
        values = (object_uuid,)
        self.execute_query(query, values)
        
        # insert new tags for object_uuid
        for tag in tags:
            query = "INSERT INTO object_tag (object_uuid, tag_uuid) VALUES (%s, %s)"
            values = (object_uuid, tag['uuid'])
            self.execute_query(query, values)
            
        return True
    
    def get_tags_for_object(self, object_uuid=None):
        if object_uuid is None:
            # Log error or raise an exception
            print("ERROR: get_tags_for_object() - no object_uuid")
            return None
        
        query = ("SELECT t.uuid, t.name FROM tags t "
                 "JOIN object_tag ot ON t.uuid = ot.tag_uuid "
                 "WHERE ot.object_uuid = %s")
        values = (object_uuid,)
        # print("get_tags_for_object() uuid: %s" % (values))
        return self.execute_query_tags(query, values)
    
    def remove_tag_from_object(self, object_uuid=None, tag_uuid=None):
        if object_uuid is None or tag_uuid is None:
            # Log error or raise an exception
            print("ERROR: remove_tag_from_object() - no object_uuid or tag_uuid")
            return None
        
        query = "DELETE FROM object_tag WHERE object_uuid = %s AND tag_uuid = %s"
        values = (object_uuid, tag_uuid)
        return self.execute_query(query, values)
    
    # this function returns a top 10 list of tags sorted by their count on table object_tag
    def get_top_tags(self):
        query = ("SELECT t.uuid, t.name, COUNT(*) AS count FROM tags t "
                 "JOIN object_tag ot ON t.uuid = ot.tag_uuid "
                 "GROUP BY t.uuid, t.name "
                 "ORDER BY count DESC "
                 "LIMIT 10")
        values = ()
        return self.execute_query_tags(query, values)
    
    def execute_query_tags(self, query, values):
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                res = cur.fetchall()
                
                tags = []
                for tag in res:
                    tags.append({'uuid': tag[0], 'name': tag[1]})                    
                
                # print("execute_query_tags() - tags found %s" % len(tags))
                return tags
            
        except Exception as e:
            # Log exception
            print("Error:: execute_query_tags() - %s" % e)
            return None
        
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
            return None

    def execute_query_user(self, query, values, user):
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                res = cur.fetchone()

                if res:
                    # User exists
                    user.uuid, user.name, user.email, user.password = res                    
                    print("execute_query() - user found %s" % user.uuid)
                    return user
                else:
                    # User does not exist
                    return None

        except Exception as e:
            # Log exception
            print("execute_query() - %s" % e)
            pass

    def new_user(self, user=None):
        return self.insert_user(user)

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
                    print("insert_user() - user inserted %s" % user.uuid)
                    self.conn.commit()
                    return user
                else:
                    # Log error or raise an exception
                    print("insert_user() - no res returned")
                    return None

        except Exception as e:
            # Log exception
            print("insert_user() - %s" % e)
            pass

    #
    # questions functions
    #
    
    def get_questions_by_tag(self, user_uuid=None):
        # Überprüfen, ob eine user_uuid vorhanden ist
        if user_uuid is None:
            print("ERROR db_tool.get_questions_by_tag(user_uuid):: No user_uuid given.")
            return {}
        else:
            print("************************* Start db_tool.get_questions_by_tag(user_uuid):: user_uuid: %s" % user_uuid)
            
        # get the tags for user_uuid
        tags = self.get_tags_for_object(user_uuid)
        # print("db_tool.get_questions_by_tag(user_uuid):: tags: %s" % tags)
        
        # get all questions for user_uuid
        questions = self.get_questions(user_uuid)
        # print("db_tool.get_questions_by_tag(user_uuid):: questions: %s" % questions)
        
        # get all questions for user_uuid
        questions_by_tag = {}
        for question_uuid in questions:
            question = questions[question_uuid]
            # print("db_tool.get_questions_by_tag(user_uuid):: check question: %s" % question['title'])
            question_tags = self.get_tags_for_object(question['uuid'])
            # print("db_tool.get_questions_by_tag(user_uuid):: question_tags: %s" % question_tags)
            for tag in question_tags:                
                if tag in tags:
                    print("db_tool.get_questions_by_tag(user_uuid):: FOUND tag: %s" % tag)
                    questions_by_tag[question_uuid] = question
                    break
        return questions_by_tag
    
    
    
    def get_questions(self, user_uuid=None):
        # Überprüfen, ob eine user_uuid vorhanden ist
        if user_uuid is None:
            print("ERROR db_tool.get_questions(user_uuid):: No user_uuid given.")  # Log error oder raise an exception
            return {}
        else:
            print("db_tool.get_questions(user_uuid):: user_uuid: %s" % user_uuid)

        # Parametrisierte Abfrage verwenden
        query = (
            "SELECT qu.question_uuid, q.title, q.content, q.date_created, q.date_updated, u.username, qu.rank "
            "FROM user_question AS qu "
            "JOIN questions AS q ON qu.question_uuid = q.uuid "
            "JOIN users AS u ON qu.user_uuid = u.uuid "
            "WHERE qu.user_uuid = %s ORDER BY qu.rank DESC"
        )
        values = (user_uuid,)

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                res = cur.fetchall()

                questions = {}
                for qu in res:
                    print("db_tool.get_questions(user_uuid):: qu: %s" % qu[4])

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
                        'rank': qu[6],
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
        
    def update_question_rank(self, user_uuid=None, question_uuid=None, rank=None):
        
        # Überprüfen, ob eine user_uuid vorhanden ist
        if user_uuid is None or question_uuid is None or rank is None:
            print("ERROR db_tool.update_question_rank(user_uuid):: No user_uuid given.")
            return {}
        
        query = ("update user_question set rank = %s where user_uuid = %s and question_uuid = %s")
        values = (rank, user_uuid, question_uuid)
        print("db_tool.update_question_rank(user_uuid):: query: %s, values: %s" % (query, values))
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                
                print("Updated Question Rank in DB: %s" % str(question_uuid))
                
                self.conn.commit()
                
                return {}
            
        except Exception as e:
            print("ERROR db_tool.update_question_rank(user_uuid):: %s" % e)
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
        
        query3 = ("delete from answers where uuid in (select answer_uuid from question_answer where question_uuid = %s)")
        values3 = (question_uuid,)
        
        query4 = ("delete from question_answer where question_uuid = %s")
        values4 = (question_uuid,)

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                cur.execute(query2, values2)
                cur.execute(query3, values3)
                cur.execute(query4, values4)

                print("Deleted Question in DB: %s" % question_uuid)

                self.conn.commit()

                return {}

        except Exception as e:
            print("ERROR db_tool.delete_question(user_uuid):: %s" % e)
            return {}

    #
    # answers functions
    #
    
    # this function  get those answers to the question_uuid, which have the same tag as the question in the tabel object_tag
    def get_answers_by_tag(self, question_uuid=None):
        # Überprüfen, ob eine user_uuid vorhanden ist
        if question_uuid is None:
            print("ERROR db_tool.get_answers_by_tag(question_uuid):: No question_uuid given.")
            return {}
        else:
            print("************************* Start db_tool.get_answers_by_tag(question_uuid):: question_uuid: %s" % question_uuid)
            
        # get the tags for question_uuid
        tags = self.get_tags_for_object(question_uuid)
        print("db_tool.get_answers_by_tag(question_uuid):: tags: %s" % tags)
        
        # get all answers for question_uuid
        answers = self.get_answers(question_uuid)
        # print("db_tool.get_answers_by_tag(question_uuid):: answers: %s" % answers)
        
        # get all answers for question_uuid
        answers_by_tag = {}
        for answer_uuid in answers:
            answer = answers[answer_uuid]
            print("db_tool.get_answers_by_tag(question_uuid):: check answer: %s" % answer['title'])
            answer_tags = answer['tags']
            # print("db_tool.get_answers_by_tag(question_uuid):: answer_tags: %s" % answer_tags)
            for tag in answer_tags:                
                if tag in tags:
                    print("db_tool.get_answers_by_tag(question_uuid):: FOUND tag: %s" % tag)
                    answers_by_tag[answer_uuid] = answer
                    break
                
        return answers_by_tag
    
    

    # this function gets all answers for a question_uuid
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
                 ' question_answer.rank AS rank, '
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
                 '    question_answer.question_uuid = %s '
                 'ORDER BY '
                 '    question_answer.rank DESC '

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
                    
                    # get the tags for answer['uuid'] and add them to answer
                    tags = self.get_tags_for_object(answer['uuid'])
                    answer['tags'] = tags

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
                    'rank': 1000
                }

                print("New Answer in DB: %s" % str(answer))

                insert_question_query = "insert into question_answer (question_uuid, answer_uuid) values (%s, %s)"
                insert_question_values = (question_uuid, answer['uuid'])

                cur.execute(insert_question_query, insert_question_values)

                self.conn.commit()

                return answer

        except Exception as e:
            print("ERROR db_tool.new_answer(user_uuid, creator_id, question_uuid):: %s" % e)
            print(f"Exception Type: {type(e)}")
            self.conn.rollback()
            return {}

    def update_answer_rank(self, question_uuid=None, answer_uuid=None, rank=None):
        
        query = ("update question_answer set rank = %s where question_uuid = %s and answer_uuid = %s")
        values = (rank, question_uuid, answer_uuid)
        # print("db_tool.update_answer_rank(question_uuid):: query: %s, values: %s" % (query, values))
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)                
                # print("Updated Answer Rank in DB: %s" % str(answer_uuid))
                self.conn.commit()                
                return {}
            
        except Exception as e:
            print("ERROR db_tool.update_answer_rank(question_uuid):: %s" % e)
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

    def add_model(self, model):
        query = "INSERT INTO models (uuid, model_filename, model_label, model_type, default_prompt, default_max_length)" \
                " VALUES (DEFAULT, %s, %s, %s, %s, %s) RETURNING uuid"
        values = (model['model_filename'], model['model_label'], model['model_type'],
                  model['default_prompt'],
                  model['default_max_length'])

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                res = cur.fetchone()

                if res:
                    model['uuid'] = res[0]
                    # Log successful operation
                    print("insert_model() - model inserted %s" % model['uuid'])
                    self.conn.commit()
                    return model
                else:
                    # Log error or raise an exception
                    print("insert_model() - no res returned")
                    return None

        except Exception as e:
            # Log exception
            print("insert_model() - %s" % e)
            return None

    def update_model(self, model):
        query = "UPDATE models SET model_label = %s,"\
                " model_type = %s, default_prompt = %s, default_max_length = %s WHERE uuid = %s"
        values = (model['model_label'], model['model_type'],
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
