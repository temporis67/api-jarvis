'''
USERS TABLE
'''

CREATE TABLE users(
    uuid uuid NOT NULL DEFAULT uuid_generate_v1() PRIMARY KEY,
    username text,
    email text,
    password text
);
ALTER TABLE users OWNER TO "ai-chat-pguser";

'''
QUESTION TABLE
'''

CREATE TABLE questions(
    uuid uuid NOT NULL DEFAULT uuid_generate_v1() PRIMARY KEY,
    creator_uuid uuid NOT NULL,
    title text,
    content text,
    date_created timestamp without time zone NOT NULL DEFAULT now(),
    date_updated timestamp without time zone NOT NULL DEFAULT now(),
    source_type varchar(256) NOT NULL DEFAULT 'model'::character varying,
    user_uuid uuid
);
COMMENT ON COLUMN questions.title IS 'short version of question';
COMMENT ON COLUMN questions.content IS 'long version of question';
COMMENT ON COLUMN questions.source_type IS 'human, model, external';
ALTER TABLE questions OWNER TO "ai-chat-pguser";


