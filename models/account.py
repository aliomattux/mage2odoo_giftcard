from openerp.osv import osv, fields
from openerp.tools.translate import _

class AccountInvoiceLine(osv.osv):
    _inherit = 'account.invoice.line'

    _columns = {
	'linked_certificate': fields.boolean('Linked To Magento'),
	'certificate_number': fields.char('Certificate Number'),
    }

    def cancel_certificate(self, cr, uid, ids, context=None):
	card_obj = self.pool.get('mage.gift.card')
	line = self.browse(cr, uid, ids[0])
	invoice = line.invoice_id
	if not invoice.sale_order or not invoice.sale_order.mage_store:
	    raise osv.except_osv(_('Missing Link!'),_("Could not find either the sale or Magento store for this order!"))
	mage_store = invoice.sale_order.mage_store.external_id
	cardNumber = line.certificate_number
	amount = line.price_unit
	if amount < 0:
	    ctype = 'refund'
	else:
	    ctype = 'new_card'
	card_obj.process_cancellation(cr, uid, cardNumber, amount, 'invoice', ctype, mage_store)
	self.pool.get('account.invoice').message_post(cr, uid, [invoice.id], body=_("Gift Certificate Line Cancelled for Amount: %s"%amount))
	self.write(cr, uid, line.id, {'price_unit': 0.00,
                                'name': "CANCELED: %s" % cardNumber,
                                'product_id': False,
				'linked_certificate': False,
	})
	return True
#	return self.unlink(cr, uid, ids)
