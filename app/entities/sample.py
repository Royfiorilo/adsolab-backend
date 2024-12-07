class SampleEntity:
    def __init__(
            self,
            ce, qe, investigations=None, sample_id=None, title=None, description=None
    ):
        if investigations is None:
            investigations = []
        self.sample_id = sample_id
        self.ce = ce
        self.qe = qe
        self.investigations = investigations
        self.title = title
        self.description = description

    @property
    def id(self):
        return self.sample_id
