from flask.ext.admin.form import BaseForm, widgets
from wtforms import (
    BooleanField, FloatField, StringField,
    TextAreaField, IntegerField, SelectField
)
from erppeek import mixedcase


MAPPING_TYPES = {
    'boolean': BooleanField,
    'float': FloatField,
    'date': StringField,
    'datetime': StringField,
    'char': StringField,
    'text': TextAreaField,
    'int': IntegerField,
    'selection': SelectField,
}


class Form(object):

    def __init__(self, view):
        self.view = view
        self.model = view.model

    def _get_form_overrides(self, name):
        form_overrides = getattr(self.view, 'form_overrides', {})
        return form_overrides.get(name, None)

    def create_form(self, relations=True):
        model = self.model
        class_name = '%sForm' % mixedcase(model._name)
        attrs = {}
        for k, v in model.fields_get().items():
            type_field = MAPPING_TYPES.get(v.get('type', 'float'))
            if not type_field:
                continue
            override = self._get_form_overrides(k)
            if override:
                type_field = override
            kwargs = {}
            if v['type'] == 'selection':
                kwargs['choices'] = v['selection']
            elif v['type'] == 'date':
                kwargs['widget'] = widgets.DatePickerWidget()
            elif v['type'] == 'datetime':
                kwargs['widget'] = widgets.DateTimePickerWidget()
            attrs[k] = type_field(label=v['string'], **kwargs)
        return type(class_name, (BaseForm, ), attrs)
