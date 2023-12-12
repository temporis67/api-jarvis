CREATE TABLE tags (
    uuid uuid NOT NULL DEFAULT uuid_generate_v1(),
    name varchar(255) NOT NULL,
    PRIMARY KEY (uuid)
);
ALTER TABLE tags OWNER TO "ai-chat-pguser";

CREATE TABLE object_tag (
    object_uuid uuid NOT NULL,
    tag_uuid uuid NOT NULL,
    PRIMARY KEY (object_uuid, tag_uuid),    
    FOREIGN KEY (tag_uuid) REFERENCES tags(uuid) ON DELETE CASCADE
);
ALTER TABLE object_tag OWNER TO "ai-chat-pguser";

CREATE OR REPLACE FUNCTION delete_tags_by_object_id(object_uuid uuid)
RETURNS void AS $$
BEGIN
    DELETE FROM object_tag WHERE object_uuid = object_uuid;
END;
$$ LANGUAGE plpgsql;
ALTER FUNCTION delete_tags_by_object_id(object_uuid uuid) OWNER TO "ai-chat-pguser";

CREATE OR REPLACE FUNCTION delete_tags_on_object_delete() RETURNS TRIGGER AS $$
BEGIN
    PERFORM delete_tags_by_object_id(OLD.uuid);
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;
ALTER FUNCTION delete_tags_on_object_delete() OWNER TO "ai-chat-pguser";

CREATE TRIGGER delete_tags_after_answer_delete
AFTER DELETE ON answers
FOR EACH ROW EXECUTE PROCEDURE delete_tags_on_object_delete();

CREATE TRIGGER delete_tags_after_question_delete
AFTER DELETE ON questions
FOR EACH ROW EXECUTE PROCEDURE delete_tags_on_object_delete();
CREATE TRIGGER delete_tags_after_users_delete
AFTER DELETE ON users
FOR EACH ROW EXECUTE PROCEDURE delete_tags_on_object_delete();

DROP TRIGGER IF EXISTS delete_tags_after_answer_delete ON answers;
DROP TRIGGER IF EXISTS delete_tags_after_question_delete ON questions;
DROP TRIGGER IF EXISTS delete_tags_after_users_delete ON users;