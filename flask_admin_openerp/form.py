from flask.ext.admin.form import BaseForm, widgets
from wtforms import (
    BooleanField, FloatField, StringField,
    TextAreaField, IntegerField, SelectField, SelectMultipleField
)
from wtforms import widgets as wtf_widgets
from erppeek import mixedcase, Record


def coerce_relation(value):
    if isinstance(value, Record):
        try:
            return int(value.id)
        except:
            raise TypeError
    else:
        return int(value)


class ListWidget(wtf_widgets.Select):

    def __call__(self, field, **kwargs):
        # Render the list
        kwargs.setdefault('id', 'list_%s' % field.id)
        html = ['<ul %s>' % wtf_widgets.html_params(**kwargs)]
        for subfield in field:
            if subfield.checked:
                html.append('<li>%s</li>' % subfield.label.text)
        html.append('</ul>')
        kwargs.setdefault('id', field.id)
        kwargs['multiple'] = True
        html += ['<select %s style="display: none;">' %
                 wtf_widgets.html_params(name=field.name, **kwargs)]
        for val, label, selected in field.iter_choices():
            html.append(self.render_option(val, label, selected))
        html.append('</select>')
        return wtf_widgets.HTMLString(''.join(html))



MAPPING_TYPES = {
    'boolean': BooleanField,
    'float': FloatField,
    'date': StringField,
    'datetime': StringField,
    'char': StringField,
    'text': TextAreaField,
    'integer': IntegerField,
    'selection': SelectField,
    'many2one': SelectField,
    'one2many': SelectMultipleField
}


class Form(object):

    def __init__(self, view):
        self.view = view
        self.model = view.model

    def _get_form_overrides(self, name):
        form_overrides = getattr(self.view, 'form_overrides')
        if form_overrides:
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
                if v['selection'] and isinstance(v['selection'][0][0], int):
                    kwargs['coerce'] = int
                kwargs['choices'] = v['selection']
            elif v['type'] == 'date':
                kwargs['widget'] = widgets.DatePickerWidget()
            elif v['type'] == 'datetime':
                kwargs['widget'] = widgets.DateTimePickerWidget()
            elif v['type'] in ('many2one', 'one2many'):
                relation = model.client.model(v['relation'])
                ids = relation.search([])
                kwargs['choices'] = relation.name_get(ids)

                kwargs['coerce'] = coerce_relation
                if v['type'] == 'many2one':
                    kwargs['widget'] = widgets.Select2Widget()
                elif v['type'] == 'one2many':
                    kwargs['widget'] = ListWidget()

            attrs[k] = type_field(label=v['string'], **kwargs)
        return type(class_name, (BaseForm, ), attrs)
