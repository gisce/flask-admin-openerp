from flask.ext.admin.model import BaseModelView
from .form import Form
from .filters import *


class OpenERPModelView(BaseModelView):

    def __init__(self, model, **kwargs):
        super(OpenERPModelView, self).__init__(model, **kwargs)
        self.dynamic_choice_fields = {}
        for field, desc in model.fields_get().items():
            if 'relation' in desc and desc['relation']:
                self.dynamic_choice_fields[field] = desc['relation']

    def update_choices(self, form):
        for choice_field, relation in self.dynamic_choice_fields.items():
            relation = self.model.client.model(relation)
            remote_ids = relation.search([])
            field = getattr(form, choice_field)
            field.choices = relation.name_get(remote_ids)

    def edit_form(self, obj):
        """Updates the choices for dynamic fields.
        """
        form = super(OpenERPModelView, self).edit_form(obj)
        self.update_choices(form)
        return form

    def create_form(self):
        """Updates the choices for dynamic fields.
        """
        form = super(OpenERPModelView, self).create_form()
        self.update_choices(form)
        return form

    def get_pk_value(self, model):
        return model.id

    def scaffold_list_columns(self):
        return self.model.fields_get().keys()

    def scaffold_sortable_columns(self):
        return None

    def scaffold_form(self):
        oo_form = Form(self)
        return oo_form.create_form()

    def scaffold_filters(self, name):
        field = self.model.fields_get([name])[name]
        field_type = field.get('type', 'float')
        label = field.get('string', name)
        flt = []
        if field_type == 'boolean':
            flt += [OpenerpBooleanFilter(name)]
        else:
            flt += [OpenerpEqualFilter(label, name)]
            if field_type in ('char', 'text'):
                flt += [OpenerpLikeFilter(label, name)]
            else:
                flt += [
                    OpenerpGreaterFilter(label, name),
                    OpenerpLesserFilter(label, name)
                ]
        return flt

    def init_search(self):
        return False

    def get_one(self, object_id):
        object_id = int(object_id)
        return self.model.browse(object_id)

    def get_list(self, page, sort_field, sort_desc, search, flts):
        limit = self.page_size
        offset = page * limit
        query = []
        if not flts:
            flts = []
        for flt, value in flts:
            query = self._filters[flt].apply(query, value)
        n_items = self.model.search_count(query)
        ids = self.model.search(query, offset=offset, limit=limit)
        if not ids:
            res = []
        else:
            res = self.model.browse(ids)
        return n_items, res

    def write_data(self, origin_data, columns):
        if origin_data != None:
            return {key: value for key, value in origin_data.items()
                         if key in columns}
        else:
            return origin_data

    def create_model(self, form):
        data_to_write = self.write_data(form.data.items(),
                                            self.form_create_rules)
        return self.model.create(data_to_write)

    def update_model(self, form, model):
        data_to_write = self.write_data(form.data.items(),
                                        self.form_edit_rules)
        return model.write(data_to_write)

    def delete_model(self, model):
        return model.unlink()
