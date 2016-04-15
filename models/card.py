from openerp.osv import osv, fields
from openerp.tools.translate import _
from magento import API


class MageGiftCard(osv.osv_memory):
    _name = 'mage.gift.card'

    def process_cancellation(self, cr, uid, cardNumber, amount, object, ctype, store_id):
	user = self.pool.get('res.users').browse(cr, uid, uid)
	existing_card_data = self.lookup_card(cr, uid, cardNumber)
        data = {
                'balance': amount,
		'cert_number': cardNumber,
                'store_id': store_id,
                'user_id': 4,
                'user_name': user.name,
        }
	if ctype == 'new_card':
	    data['status'] = 'P'
 	    data['balance'] = 0

	else:
	    existing_balance = round(float(existing_card_data['balance']), 2)
	    current_balance = round(amount, 2) * -1
	    existing_balance += current_balance
	    data['balance'] = existing_balance

	return self.update_card(cr, uid, cardNumber, data)


    def create_card(self, cr, uid, data):
        integrator_obj = self.pool.get('mage.integrator')
        credentials = integrator_obj.get_external_credentials(cr, uid)
        try:
            with API(credentials['url'], credentials['username'], credentials['password']) as card_api:
		cardNumber = card_api.call('ugiftcert.create', [data])
		return cardNumber

        except Exception, e:
            raise osv.except_osv(_('Gift Card Error!'),_(str(e)))
        return True


    def update_card(self, cr, uid, code, data):
        integrator_obj = self.pool.get('mage.integrator')
        credentials = integrator_obj.get_external_credentials(cr, uid)
        try:
            with API(credentials['url'], credentials['username'], credentials['password']) as card_api:
		result = card_api.call('ugiftcert.update', [code, data])
		return result

        except Exception, e:
            raise osv.except_osv(_('Gift Card Error!'),_(str(e)))
        return True


    def lookup_card(self, cr, uid, code):
        integrator_obj = self.pool.get('mage.integrator')
        credentials = integrator_obj.get_external_credentials(cr, uid)

	try:
	    with API(credentials['url'], credentials['username'], credentials['password']) as card_api:
		result = card_api.call('ugiftcert.fetch', [code])
		return result

	except Exception, e:
	    raise osv.except_osv(_('Gift Card Error!'),_(str(e)))
