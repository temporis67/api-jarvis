#
# Data Class Answer
#
class Answer:
    uuid = None
    creator = None
    source = None
    question = None

    title = None
    content = None

    time_elapsed = None
    date_created = None
    date_updated = None

    quality = 0
    trust = 0

    def __init__(self, uuid, creator, source, question, title, content, time_elapsed, date_created, date_updated, quality, trust):
        self.uuid = uuid
        self.creator = creator
        self.source = source
        self.question = question

        self.title = title
        self.content = content

        self.time_elapsed = time_elapsed
        self.date_created = date_created
        self.date_updated = date_updated

        self.quality = quality
        self.trust = trust

