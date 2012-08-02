from django.http import HttpResponse


class HttpJSONResponse(HttpResponse):
    def __init__(self, **kwargs):
        kwargs['content_type'] = 'application/json'
        super(HttpJSONResponse, self).__init__(**kwargs)
