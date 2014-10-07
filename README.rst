flask-admin-openerp
===================

OpenERP Backend for Flask-Admin

.. code-block:: python
    
    from flask_admin_openerp import OpenERPModelView
    
    # You need a ERPPeek client instance in this example is c
    
    admin.add_view(c.ResPartner, name='Partners', endpoint='partners'))
