# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from werkzeug.exceptions import Forbidden
import logging
import hmac
import hashlib
import json
from odoo.addons.razorpay_custom import const

_logger = logging.getLogger(__name__)

class RazorpayController(http.Controller):
    _webhook_url = '/payment/razorpay/webhook'

    @http.route(_webhook_url, type='json', auth='public', methods=['POST'], csrf=False)
    def razorpay_webhook(self):
        data = request.get_json_data()
        _logger.info("Razorpay Webhook received: %s", json.dumps(data, indent=2))

        event_type = data.get('event')
        if event_type not in const.HANDLED_WEBHOOK_EVENTS:
            _logger.info("Razorpay: Ignoring unhandled event type %s", event_type)
            return {'status': 'ignored'}

        entity = data['payload'].get('payment', {}).get('entity', data['payload'].get('refund', {}).get('entity'))
        if not entity:
            _logger.error("Razorpay: Invalid webhook payload, no entity found")
            return {'status': 'error'}

        received_signature = request.httprequest.headers.get('X-Razorpay-Signature')
        tx = request.env['payment.transaction'].sudo()._get_tx_from_notification_data('razorpay', entity)

        expected_signature = tx.provider_id._razorpay_calculate_signature(request.httprequest.data)
        if not received_signature or not hmac.compare_digest(received_signature.encode('utf-8'), expected_signature.encode('utf-8')):
            _logger.error("Razorpay: Invalid webhook signature for transaction %s", tx.reference)
            raise Forbidden("Invalid webhook signature")

        try:
            tx._handle_notification_data('razorpay', entity)
            return {'status': 'success'}
        except Exception as e:
            _logger.exception("Razorpay: Error processing webhook for transaction %s: %s", tx.reference, str(e))
            return {'status': 'error'}