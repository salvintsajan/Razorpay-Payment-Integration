# -*- coding: utf-8 -*-
# Sample constants for Razorpay integration
HANDLED_WEBHOOK_EVENTS = [
    'payment.authorized',
    'payment.captured',
    'payment.failed',
    'payment.refunded',
]

SUPPORTED_CURRENCIES = [
    'INR', 'USD', 'EUR', 'GBP', 'AUD', 'SGD',  # Add other supported currencies as needed
]

DEFAULT_PAYMENT_METHOD_CODES = [
    'card',
    'netbanking',
]

FALLBACK_PAYMENT_METHOD_CODES = []