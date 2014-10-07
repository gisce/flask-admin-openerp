from flask.ext.admin.model import filters


class OpenERPBaseFilter(filters.BaseFilter):

    def __init__(self, name, field, options=None, data_type=None):
        super(OpenERPBaseFilter, self).__init__(name, options, data_type)
        self.field = field

    def apply(self, query, value):
        query += [(self.field, self.op, value)]
        return query

    def operation(self):
        return self.op


class OpenerpLikeFilter(OpenERPBaseFilter):
    op = 'ilike'


class OpenerpEqualFilter(OpenERPBaseFilter):
    op = '='


class OpenerpGreaterFilter(OpenERPBaseFilter):
    op = '>='


class OpenerpLesserFilter(OpenERPBaseFilter):
    op = '<='


class OpenerpBooleanFilter(filters.BaseBooleanFilter):
    def apply(self, query, value):
        query += [(self.name, '=', value)]
        return query

    def operation(self):
        return '='

    def clean(self, value):
        return int(value)