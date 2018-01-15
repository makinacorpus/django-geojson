import warnings
from django.http import HttpResponse


class HttpGeoJSONResponse(HttpResponse):
    def __init__(self, **kwargs):
        kwargs['content_type'] = 'application/geo+json'
        super(HttpGeoJSONResponse, self).__init__(**kwargs)


class HttpJSONResponse(HttpGeoJSONResponse):
    def __init__(self, **kwargs):
        warnings.warn("The 'HttpJSONResponse' class was renamed to 'HttpGeoJSONResponse'",
                      DeprecationWarning)
        super(HttpJSONResponse, self).__init__(**kwargs)
