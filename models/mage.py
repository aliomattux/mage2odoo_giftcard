from openerp.osv import osv, fields


class MageSetup(osv.osv):
    _inherit = 'mage.setup'
    _columns = {
	'gift_product': fields.many2one('product.product', 'Gift Product'),
    }
