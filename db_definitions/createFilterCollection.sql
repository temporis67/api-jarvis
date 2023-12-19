
DROP TABLE IF EXISTS filter CASCADE;
CREATE TABLE filter (
    uuid uuid NOT NULL DEFAULT uuid_generate_v1(),
    name varchar(255),
    PRIMARY KEY (uuid)
);
ALTER TABLE filter OWNER TO "ai-chat-pguser";

ALTER TABLE questions ADD COLUMN filter_uuid uuid, ADD FOREIGN KEY (filter_uuid) REFERENCES filter(uuid) ON DELETE CASCADE;
ALTER TABLE answers ADD COLUMN filter_uuid uuid, ADD FOREIGN KEY (filter_uuid) REFERENCES filter(uuid) ON DELETE CASCADE;


CREATE OR REPLACE FUNCTION delete_filter_by_object_id(object_uuid uuid)
RETURNS void AS $$
BEGIN
    DELETE FROM filter WHERE object_uuid = object_uuid;
END;
$$ LANGUAGE plpgsql;
ALTER FUNCTION delete_filter_by_object_id(object_uuid uuid) OWNER TO "ai-chat-pguser";

CREATE OR REPLACE FUNCTION delete_filter_on_object_delete() RETURNS TRIGGER AS $$
BEGIN
    PERFORM delete_filter_by_object_id(OLD.uuid);
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

ALTER Function delete_filter_on_object_delete() OWNER TO "ai-chat-pguser";

ALTER TABLE questions DROP CONSTRAINT IF EXISTS questions_filter_uuid_fkey;
ALTER TABLE answers DROP CONSTRAINT IF EXISTS answers_filter_uuid_fkey;

CREATE TRIGGER delete_filter_after_answer_delete
AFTER DELETE ON answers
FOR EACH ROW EXECUTE PROCEDURE delete_filter_on_object_delete();

CREATE TRIGGER delete_filter_after_question_delete
AFTER DELETE ON questions
FOR EACH ROW EXECUTE PROCEDURE delete_filter_on_object_delete();


ALTER TABLE users
ADD PRIMARY KEY (uuid);

CREATE TABLE user_filter (
    user_uuid uuid NOT NULL,
    filter_uuid uuid NOT NULL,
    PRIMARY KEY (user_uuid, filter_uuid),
    FOREIGN KEY (user_uuid) REFERENCES users(uuid) ON DELETE CASCADE,
    FOREIGN KEY (filter_uuid) REFERENCES filter(uuid) ON DELETE CASCADE
);
ALTER TABLE user_filter OWNER TO "ai-chat-pguser";
