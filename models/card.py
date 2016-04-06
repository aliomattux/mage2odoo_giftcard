from openerp.osv import osv, fields
from openerp.tools.translate import _



class MageGiftCard(osv.osv_memory):
    _name = 'mage.gift.card'

    def create_card(self, data):
        integrator_obj = self.pool.get('mage.integrator')
        credentials = integrator_obj.get_external_credentials(cr, uid)
        try:
            with API(credentials['url'], credentials['username'], credentials['password']) as card_api:
		result = card_api.call('ugiftcert.create', [data])
		return result
        except Exception, e:
            raise osv.except_osv(_('Gift Card Error!'),_(str(e)))
        return True


    def update_card(self, code, data):
        integrator_obj = self.pool.get('mage.integrator')
        credentials = integrator_obj.get_external_credentials(cr, uid)
        try:
            with API(credentials['url'], credentials['username'], credentials['password']) as card_api:
		result = card_api.call('ugiftcert.update', [code, data])
		return result

        except Exception, e:
            raise osv.except_osv(_('Gift Card Error!'),_(str(e)))
        return True


    def lookup_card(self, code):
        integrator_obj = self.pool.get('mage.integrator')
        credentials = integrator_obj.get_external_credentials(cr, uid)

	try:
	    with API(credentials['url'], credentials['username'], credentials['password']) as card_api:
		result = card_api.call('ugiftcert.fetch', [code])
		return result

	except Exception, e:
	    raise osv.except_osv(_('Gift Card Error!'),_(str(e)))
