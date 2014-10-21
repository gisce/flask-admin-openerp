from flask.ext.admin.form import BaseForm, widgets
from wtforms import (
    BooleanField, FloatField, StringField,
    TextAreaField, IntegerField, SelectField, SelectMultipleField, FileField,
    PasswordField
)
from wtforms import widgets as wtf_widgets
from erppeek import mixedcase, Record
import base64


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
                html.append('<li>%s <a class="icon-trash" href="#" onclick="delete_item(this, %s)"> </a></li>' % (subfield.label.text.strip(), subfield.data))
        html.append('</ul>')
        kwargs.setdefault('id', field.id)
        kwargs['multiple'] = True
        html += ['<select %s style="display: none;">' %
                 wtf_widgets.html_params(name=field.name, **kwargs)]
        for val, label, selected in field.iter_choices():
            html.append(self.render_option(val, label, selected))
        html.append('</select>')
        html += ['''
            <script type="text/javascript">
               function delete_item(elem, val) {
                    $(elem).parent().css("text-decoration", "line-through");
                    $("option[value="+val+"]").removeAttr("selected");
               }
            </script>
        ''']
        return wtf_widgets.HTMLString(''.join(html))

class BinaryField(FileField):

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = base64.b64encode(valuelist[0].stream.read())
        else:
            self.data = ''

    def _value(self):
        return base64.b64decode(self.data) if self.data is not None else ''

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
    'one2many': SelectMultipleField,
    'many2many': SelectMultipleField,
    'binary': BinaryField
}


class Form(object):

    def __init__(self, view):
        self.view = view
        self.model = view.model
        self.fields = []
        self.fields = getattr(view, 'fields', [])

    def _get_form_overrides(self, name):
        form_overrides = getattr(self.view, 'form_overrides')
        if form_overrides:
            return form_overrides.get(name, None)

    def create_form(self, relations=True):
        model = self.model
        class_name = '%sForm' % mixedcase(model._name)
        attrs = {}
        fields = model.fields_get(self.fields)
        defaults = model.default_get(fields.keys())
        for k, v in fields.items():
            type_field = MAPPING_TYPES.get(v.get('type', 'float'))
            if not type_field:
                continue
            override = self._get_form_overrides(k)
            if override:
                type_field = override
            kwargs = {}
            if k in defaults and defaults[k] is not False:
                kwargs['default'] = defaults[k]
            if v['type'] == 'selection':
                if v['selection'] and isinstance(v['selection'][0][0], int):
                    kwargs['coerce'] = int
                kwargs['choices'] = v['selection']
            elif v['type'] == 'char' and 'invisible' in v and v['invisible']:
                type_field = PasswordField
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
                elif v['type'] == 'many2many':
                    kwargs['widget'] = widgets.Select2Widget(multiple=True)

            attrs[k] = type_field(label=v['string'], **kwargs)
        return type(class_name, (BaseForm, ), attrs)
