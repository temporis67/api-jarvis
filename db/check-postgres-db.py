import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="ai-chat-db",
    user="ai-chat-pguser",
    password="--jarvis+")


def show_pg_version():
    # create a cursor
    cur = conn.cursor()

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

show_pg_version()