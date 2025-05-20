# -*- coding: utf-8 -*-
SUPPORTED_CURRENCIES = ['INR', 'USD', 'EUR', 'GBP', 'AUD', 'SGD']
DEFAULT_PAYMENT_METHOD_CODES = ['card', 'netbanking', 'wallet', 'upi']
HANDLED_WEBHOOK_EVENTS = [
    'payment.authorized',
    'payment.captured',
    'payment.failed',
    'refund.failed',
    'refund.processed',
]

FALLBACK_PAYMENT_METHOD_CODES = [
    'wallets_india',
    'paylater_india',
    'emi_india',
]