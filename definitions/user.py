#
# Data Class User
#
class User:
    uuid = None
    name = None
    email = None
    password = None

    def __init__(self, name=None, uuid=None, email=None, password=None):
        self.uuid = uuid
        self.email = email
        self.name = name
        self.password = password
        return
