import time

class AiChatAPI:

    questions = []
    current_user = None
    my_db = None

    def __init__(self,  my_db=None):
        time_start = time.time()
        self.my_db = my_db

        print("Initializing Chat: %s" % time_start)

    def login_user(self, msg=None):
        print("aichatapi.login_user() w. %s" % msg)
        # pprint(vars(request))
        if 'name' in msg or 'email' in msg:
            self.current_user = self.my_db.get_user(user_uuid=None, name=msg['name'], password=msg['password'], email=msg['email'])
            # print("Logging in User %s" % repr(self.current_user))
            if self.current_user is None:
                print("User not found")
            good_user = {
                'name': self.current_user.name,
                'uuid': self.current_user.uuid,
                'email': self.current_user.email,
                'password': self.current_user.password
            }
            return good_user
        else:
            return "No user email given"

    def get_questions(self, user_uuid=None):
        print("aichatapi.get_questions() w. %s" % user_uuid)
        user = None
        if self.current_user is not None and self.current_user.uuid == user_uuid:
            print("Questions for Current user")
            user = self.current_user
        else:
            user = self.my_db.get_user(user_uuid=user_uuid)  ## *****

        if user is not None:
            return self.my_db.get_questions(user_uuid=user_uuid)
        else:
            return None
