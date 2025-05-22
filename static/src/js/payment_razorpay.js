/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { rpc, RPCError } from "@web/core/network/rpc";

export default {

    /**
     * Simulate a feedback from a payment provider and redirect the customer to the status page.
     *
     * @private
     * @param {object} processingValues - The processing values of the transaction.
     * @return {void}
     */
    async processDemoPayment(processingValues) {
        const customerInput = document.getElementById('customer_input').value;
        const simulatedPaymentState = document.getElementById('simulated_payment_state').value;

        rpc('/payment/razorpay/webhook', {
            'reference': processingValues.reference,
            'payment_details': customerInput,
            'simulated_state': simulatedPaymentState,
        }).then(() => {
            window.location = '/payment/status';
        }).catch(error => {
            if (error instanceof RPCError) {
                this._displayErrorDialog(_t("Payment processing failed"), error.data.message);
                this._enableButton?.(); // This method doesn't exists in Express Checkout form.
            } else {
                return Promise.reject(error);
            }
        });
    },

};



/** @odoo-module **/
import paymentForm from '@payment/js/payment_form'
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { loadJS } from '@web/core/assets';

paymentForm.include({
    async _prepareInlineForm(providerId, providerCode, paymentOptionId, paymentMethodCode, flow) {
        if (providerCode !== 'razorpay_plus') {
            return this._super(...arguments);
        }
        if (flow === 'token') {
            return;
        }
        this._setPaymentFlow('direct');
    },

    async _processDirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        if (providerCode !== 'razorpay_plus') {
            return this._super(...arguments);
        }
        const razorpayOptions = this._prepareRazorpayOptions( providerCode, processingValues);
        await loadJS('https://checkout.razorpay.com/v1/checkout.js');
        const RazorpayJS = Razorpay(razorpayOptions);
        RazorpayJS.open();
        RazorpayJS.on('payment.failed', response => {
            this._displayErrorDialog(_t("Payment processing failed"), response.error.description);
        });
    },

    _prepareRazorpayOptions(providerCode, processingValues) {
        if (providerCode !== 'razorpay_plus') {
                this._super(...arguments);
                return;
        }
        console.log("2")
        return Object.assign({}, processingValues, {
            'key': processingValues['razorpay_public_token'] || processingValues['razorpay_key_id'],
            'customer_id': processingValues['razorpay_customer_id'],
            'order_id': processingValues['razorpay_order_id'],
            'description': processingValues['reference'],
            'recurring': processingValues['is_tokenize_request'] ? '1': '0',
            'handler': async response => {
                if (
                    response['razorpay_payment_id']
                    && response['razorpay_order_id']
                    && response['razorpay_signature']
                ) {
                    await rpc('/payment/razorpay_plus/verify_payment', {
                        reference: processingValues.reference,
                        razorpay_payment_id: response.razorpay_payment_id,
                    });
                    window.location = '/payment/status';
                }
            },
            'modal': {
                'ondismiss': () => {
                    window.location.reload();
                }
            },
        });
    },
});