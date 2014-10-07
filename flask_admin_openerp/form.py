from wtforms import *
from erppeek import mixedcase


MAPPING_TYPES = {
    'boolean': BooleanField,
    'float': FloatField,
    'date': DateField,
    'datetime': DateTimeField,
    'char': StringField,
    'text': TextAreaField,
    'int': IntegerField,
    'selection': SelectField,
}


def create_form(model, relations=True):
    class_name = '%sForm' % mixedcase(model._name)
    attrs = {}
    for k, v in model.fields_get().items():
        type_field = MAPPING_TYPES.get(v.get('type', 'float'))
        if not type_field:
            continue
        kwargs = {}
        if v['type'] == 'selection':
            kwargs['choices'] = v['selection']
        attrs[k] = type_field(label=v['string'], **kwargs)
    return type(class_name, (Form, ), attrs)
