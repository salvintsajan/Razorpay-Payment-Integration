# -*- coding: utf-8 -*-
from odoo import _, api, models
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import logging
from odoo.addons.payment import utils as payment_utils
from odoo.addons.razorpay_custom import const

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_processing_values(self, processing_values):
        res = super()._get_specific_processing_values(processing_values)
        if self.provider_code != 'razorpay' or self.operation in ('online_token', 'offline'):
            return res or {}

        customer = self._razorpay_create_customer()
        order = self._razorpay_create_order(customer.get('id'))

        return {
            'razorpay_key_id': self.provider_id.razorpay_key_id,
            'razorpay_order_id': order['id'],
            'razorpay_customer_id': customer['id'],
            'is_tokenize_request': self.tokenize,
        }

    def _razorpay_create_customer(self):
        payload = {
            'name': self.partner_name,
            'email': self.partner_email or '',
            'contact': self.partner_phone or '',
            'fail_existing': '0',
        }
        return self.provider_id._razorpay_make_request('customers', payload)

    def _razorpay_create_order(self, customer_id=None):
        payload = self._razorpay_prepare_order_payload(customer_id)
        return self.provider_id._razorpay_make_request('orders', payload)

    def _razorpay_prepare_order_payload(self, customer_id=None):
        converted_amount = payment_utils.to_minor_currency_units(self.amount, self.currency_id)
        pm_code = (self.payment_method_id.primary_payment_method_id or self.payment_method_id).code
        payload = {
            'amount': converted_amount,
            'currency': self.currency_id.name,
            **({'method': pm_code} if pm_code not in const.FALLBACK_PAYMENT_METHOD_CODES else {}),
        }

        if self.operation in ['online_direct', 'validation']:
            payload['customer_id'] = customer_id
            if self.tokenize:
                payload['token'] = {
                    'max_amount': payment_utils.to_minor_currency_units(
                        self._razorpay_get_mandate_max_amount(), self.currency_id
                    ),
                    'expire_at': int((datetime.now() + relativedelta(years=10)).timestamp()),
                    'frequency': 'as_presented',
                }

        if self.provider_id.capture_manually:
            payload['payment'] = {
                'capture': 'manual',
                'capture_options': {
                    'manual_expiry_period': 7200,
                    'refund_speed': 'normal',
                }
            }
        return payload

    def _razorpay_get_mandate_max_amount(self):
        return self.amount * 10  # Allow mandate for up to 10 times the transaction amount

    @api.model
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        if provider_code != 'razorpay':
            return super()._get_tx_from_notification_data(provider_code, notification_data)

        reference = notification_data.get('notes', {}).get('odoo_reference', notification_data.get('order_id'))
        if not reference:
            _logger.error("Razorpay: No reference found in notification data")
            raise ValidationError(_("Razorpay: Missing transaction reference"))

        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'razorpay')])
        if not tx:
            _logger.error("Razorpay: No transaction found for reference %s", reference)
            raise ValidationError(_("Razorpay: No transaction found for reference %s") % reference)
        return tx

    def _handle_notification_data(self, provider_code, notification_data):
        if provider_code != 'razorpay':
            return super()._handle_notification_data(provider_code, notification_data)

        status = notification_data.get('status')
        payment_id = notification_data.get('id')

        if status == 'success':
            self._set_done()
            self.provider_reference = payment_id
        elif status == 'authorized' and self.provider_id.capture_manually:
            self._set_authorized()
            self.provider_reference = payment_id
        elif status == 'failed':
            self._set_error(_("Payment failed: %s") % notification_data.get('error_description', 'Unknown error'))
        elif status == 'refunded':
            self._set_refunded()
        else:
            _logger.warning("Razorpay: Unhandled payment status %s for transaction %s", status, self.reference)
            self._set_pending()

        return True