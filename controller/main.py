# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class RazorpayPlusController(http.Controller):
    @http.route('/payment/razorpay_plus/verify_payment', type='json', auth='public')
    def razorpay_verify_payment(self, reference, razorpay_payment_id):
        """This function check the state and verify the state of razorpay"""
        payment = request.env['payment.transaction'].sudo().search(
            [('reference', '=', reference)], limit=1)
        if payment:
            provider = payment.provider_id
            payment_data = provider._razorpay_make_request(f'payments/{razorpay_payment_id}',method='GET')
            if payment_data.get('status') == 'captured':
                payment._set_done()
                _logger.info(f"Payment {razorpay_payment_id} for transaction {reference} successfully processed")
                return {'success': True}
            else:
                _logger.warning(
                    f"Payment {razorpay_payment_id} status is {payment_data.get('status')}, not captured"
                )
                return {'warning': f"Payment status: {payment_data.get('status')}"}
        return {'error': f"No transaction found with reference: {reference}"}