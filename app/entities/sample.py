class SampleEntity:
    def __init__(
            self,
            ce, qe, sample_id=None, title=None, description=None
    ):
        self.sample_id = sample_id
        self.ce = ce
        self.qe = qe
        self.title = title
        self.description = description

    @property
    def id(self):
        return self.sample_id

    def remove(self, indexes):
        if not indexes:
            return
        self.ce = [x for i, x in enumerate(self.ce) if i not in indexes]
        self.qe = [x for i, x in enumerate(self.qe) if i not in indexes]

    def len(self):
        return len(self.ce)