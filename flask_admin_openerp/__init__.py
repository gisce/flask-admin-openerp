import base64
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from flask import (
    request, abort, redirect, url_for, flash, send_file, current_app
)
from jinja2.loaders import ChoiceLoader, PackageLoader
from flask.ext.admin import expose
from flask.ext.admin.model import BaseModelView
from itsdangerous import Signer, BadSignature
from .form import Form
from .filters import *


class OpenERPModelView(BaseModelView):

    edit_template = 'admin_openerp/model/edit.html'

    def __init__(self, model, **kwargs):
        super(OpenERPModelView, self).__init__(model, **kwargs)
        self.dynamic_choice_fields = {}
        fields = getattr(self, 'fields', [])
        for field, desc in model.fields_get(fields).items():
            if 'relation' in desc and desc['relation']:
                self.dynamic_choice_fields[field] = desc['relation']

    def update_choices(self, form):
        for choice_field, relation in self.dynamic_choice_fields.items():
            relation = self.model.client.model(relation)
            remote_ids = relation.search([])
            field = getattr(form, choice_field)
            field.choices = [(0, '')] + relation.name_get(remote_ids)

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

    def create_blueprint(self, admin):
        res = super(OpenERPModelView, self).create_blueprint(admin)
        loader = ChoiceLoader([
            PackageLoader('flask_admin_openerp'),
            self.blueprint.jinja_loader
        ])
        self.blueprint.jinja_loader = loader
        return res

    def render(self, template, **kwargs):
        attach_obj = self.model.client.model('ir.attachment')
        model = kwargs.get('model')
        if model:
            search_params = [
                ('res_id', '=', model.id),
                ('res_model', '=', self.model._name)
            ]
            attach_ids = attach_obj.search(search_params)
            fields_to_read = ['datas_fname', 'name']
            if attach_ids:
                attachments = attach_obj.read(attach_ids, fields_to_read)
            else:
                attachments = []
            s = Signer(current_app.config.get('SECRET_KEY'), sep='$')
            for att in attachments:
                att['id'] = s.sign(str(att['id']))
            kwargs['attachments'] = attachments
        return super(OpenERPModelView, self).render(template, **kwargs)

    @expose('/attachments', methods=['POST'])
    def attachments(self):
        attach_obj = self.model.client.model('ir.attachment')
        obj_id = request.args.get('id')
        if not obj_id:
            return abort(404)
        if request.method == 'POST':
            if request.args.get('action') == "delete":
                attach_id = request.args.get('attach_id')
                if not attach_id:
                    return abort(404)
                try:
                    s = Signer(current_app.config.get('SECRET_KEY'), sep='$')
                    attach_id = int(s.unsign(attach_id))
                except BadSignature:
                    return abort(404)
                attach_obj.unlink([attach_id])
                flash("Attachment deleted succesfully", "info")
            else:
                created = 0
                for key, value in request.files.items():
                    if key.startswith('attachment_'):
                        content = base64.b64encode(value.read())
                        if not content:
                            continue
                        attach_obj.create({
                            'name': value.filename,
                            'datas': content,
                            'datas_fname': value.filename,
                            'res_model': self.model._name,
                            'res_id': obj_id
                        })
                        created += 1
                flash("%s new attachments created" % created, "info")
            return redirect(url_for('.edit_view', id=obj_id))

    @expose('/attachment/<string:att_id>')
    def attachment(self, att_id):
        s = Signer(current_app.config.get('SECRET_KEY'), sep='$')
        try:
            att_id = int(s.unsign(att_id))
            attach_obj = self.model.client.model('ir.attachment')
            content = attach_obj.read(att_id, ['datas'])['datas']
            image_fp = StringIO(base64.b64decode(content))
            return send_file(image_fp)
        except BadSignature:
            abort(404)

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
                flt += [OpenerpLikeFilter(label, name),
                        OpenerpILikeFilter(label, name)]
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
        if columns is not None:
            return {key: value for key, value in origin_data
                         if key in columns}
        else:
            return dict(origin_data)

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
