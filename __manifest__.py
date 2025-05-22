{
    'name': 'Razorpay Payment custom',
    'version': '1.0',
    'category': 'Accounting/Payment',
    'summary': 'Integrate Razorpay payment gateway with Odoo',
    'description': """
        This module integrates Razorpay as a payment provider in Odoo.""",
    'depends': ['payment'],
    'data': [
        'views/payment_provider_view.xml',
        'data/payment_provider.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'razorpay_custom/static/src/js/payment_form.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'external_dependencies': {
        'python': ['requests'],
    },
}