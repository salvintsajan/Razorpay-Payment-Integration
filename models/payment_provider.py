# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import ValidationError
import requests
import logging
import hmac
import hashlib
import json
from odoo.addons.razorpay_custom import const

_logger = logging.getLogger(__name__)

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('razorpay', "Razorpay")], ondelete={'razorpay': 'set default'})
    razorpay_key_id = fields.Char("Razorpay Key ID", required_if_provider='razorpay', help="Public key provided by Razorpay.")
    razorpay_key_secret = fields.Char("Razorpay Key Secret", required_if_provider='razorpay', groups='base.group_system')
    razorpay_webhook_secret = fields.Char("Webhook Secret", groups='base.group_system')


    def _razorpay_make_request(self, endpoint, payload=None, method='POST'):
        self.ensure_one()
        if not self.razorpay_key_id or not self.razorpay_key_secret:
            raise ValidationError(_("Razorpay credentials are missing. Please configure Key ID and Key Secret."))

        url = f"https://api.razorpay.com/v1/{endpoint}"
        auth = (self.razorpay_key_id, self.razorpay_key_secret)
        headers = {'Content-Type': 'application/json'}

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, auth=auth, params=payload, timeout=10)
            else:
                response = requests.request(method, url, headers=headers, auth=auth, json=payload, timeout=10)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error_data = response.json().get('error', {})
            msg = error_data.get('description', str(e))
            _logger.error("Razorpay API error: %s", msg)
            raise ValidationError(_("Razorpay API error: %s") % msg)
        except requests.exceptions.RequestException as e:
            _logger.error("Razorpay connection error: %s", str(e))
            raise ValidationError(_("Failed to connect to Razorpay: %s") % str(e))

        return response.json()

