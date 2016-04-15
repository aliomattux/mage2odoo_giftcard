from openerp.osv import osv, fields
from openerp.tools.translate import _

class SaleOrderLine(osv.osv):
    _inherit = 'sale.order.line'

    _columns = {
        'linked_certificate': fields.boolean('Linked To Magento'),
        'certificate_number': fields.char('Certificate Number'),
    }

    def cancel_certificate(self, cr, uid, ids, context=None):
        card_obj = self.pool.get('mage.gift.card')
        line = self.browse(cr, uid, ids[0])
        sale = line.order_id
        if not sale.mage_store:
            raise osv.except_osv(_('Missing Link!'),_("Could not find a Magento store for this order!"))
        mage_store = sale.mage_store.external_id
        cardNumber = line.certificate_number
        amount = line.price_unit

        if amount < 0:
            ctype = 'refund'
        else:
            ctype = 'new_card'

        card_obj.process_cancellation(cr, uid, cardNumber, amount, 'sale', ctype, mage_store)
        self.pool.get('sale.order').message_post(cr, uid, [sale.id], body=_("Gift Certificate Line Cancelled for Amount: %s"%amount))
	self.write(cr, uid, line.id, {'price_unit': 0.00,
				'name': "CANCELED: %s" % cardNumber,
				'product_id': False,
				'linked_certificate': False,
	})
#        return self.unlink(cr, uid, ids)
