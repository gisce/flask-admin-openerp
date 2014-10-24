from setuptools import setup


setup(
    name='flask-admin-openerp',
    version='0.3.3',
    packages=['flask_admin_openerp'],
    url='http://www.gisce.net',
    license='MIT',
    author='GISCE-TI, S.L.',
    author_email='ti@gisce.net',
    install_requires=['flask-admin', 'erppeek'],
    description='OpenERP Backend for Flask-Admin'
)
