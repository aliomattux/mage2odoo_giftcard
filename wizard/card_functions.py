from openerp.osv import osv, fields
from openerp.tools.translate import _
from pprint import pprint as pp

class SaleAuthorizeGiftCard(osv.osv_memory):
    _name = 'sale.authorize.giftcard'
    _columns = {
	'sale': fields.many2one('sale.order', 'Sale'),
	'invoice': fields.many2one('account.invoice', 'Invoice'),
	'crm_claim': fields.many2one('crm.claim'),
	'add_sale_charge': fields.boolean('Add a Sale Charge', help="This will add a line item to charge the customer on the sale order"),
	'add_invoice_charge': fields.boolean('Add Invoice Charge', help="This will add a line item to charge the customer on the Invoice"),
	'code': fields.char('Card Code'),
	'status': fields.selection ([('P', 'Pending'), ('A', 'Approved')]),
	'action': fields.selection([
		('check_balance', 'Check Balance'),
		('create_balance', 'Create Balance'),
		('redeem_balance', 'Redeem Balance')
	], 'Action', required=True),
	'balance': fields.float('Balance'),
	'store_id': fields.many2one('mage.store.view', 'Storeview', required=True),
	'expire_date': fields.date('Expires On'),
	'sender_name': fields.char('Sender Name'),
	'recipient_name': fields.char('Recipient Name'),
	'recipient_email': fields.char('Recipient Email'),
	'recipient_message': fields.text('Recipient Message'),
	'comments': fields.char('Comments'),
	'qty': fields.integer('Quantity'),
    }

    _defaults = {
	'qty': 1,
    }


    def check_card_balance(self, cr, uid, ids, context=None):
	wizard = self.browse(cr, uid, ids[0])
	sale = wizard.sale
	card = wizard.code
	card_obj = self.pool.get('mage.gift.card')
	res = card_obj.lookup_card(cr, uid, card)
	pp(res)
	message = "Card Balance: %s\n" % res['balance']
	message += "Certificate Number: %s\n" % res['cert_number']
	message += "Pin: %s\n" % res['pin']
	message += "Recipient Email: %s\n" % res['recipient_email']
	message += "Recipient Message: %s\n" % res['recipient_message']
	message += "Status: %s\n" % res['status']

	raise osv.except_osv(_('Here is the Certificate Info'),_(message))
	return True


    def get_card_product(self, cr, uid):
	mage_obj = self.pool.get('mage.setup')
	mage_ids = mage_obj.search(cr, uid, [])
	if not mage_ids:
	    raise osv.except_osv(_('Magento Setup Issue'),_('Could not find suitable Magento setup'))
	mage = mage_obj.browse(cr, uid, mage_ids[0])
	if not mage.gift_product:
	    raise osv.except_osv(_('Magento Selection Issue'),_('Could not find Gift Card Product'))
	return mage.gift_product.id


    def add_charge_to_order(self, cr, uid, cardNumber, balance, object, object_type):
	product = self.get_card_product(cr, uid,)
	if object_type == 'sale':
	    vals = {
		'name': 'Gift Certificate: %s' % cardNumber,
		'product_id': product,
		'price_unit': balance,
		'product_uom': 1,
		'linked_certificate': True,
		'certificate_number': cardNumber,
		'order_id': object.id,
		'product_uom_qty': 1,
	    }
	    line = self.pool.get('sale.order.line').create(cr, uid, vals)
	    self.pool.get('sale.order').message_post(cr, uid, [object.id], body=_("Gift Certificate Action for Amount: %s"%balance))

	elif object_type == 'invoice':
	    vals = {
		'product_id': product,
		'linked_certificate': True,
		'certificate_number': cardNumber,
                'name': 'Gift Certificate: %s' % cardNumber,
		'price_unit': balance,
		'invoice_id': object.id,
		'quantity': 1,
	    }
	    line = self.pool.get('account.invoice.line').create(cr, uid, vals)
	    self.pool.get('account.invoice').message_post(cr, uid, [object.id], body=_("Gift Certificate Action for Amount: %s"%balance))

	return True


    def process_request(self, cr, uid, ids, context=None):
	wizard = self.browse(cr, uid, ids[0])
	card_obj = self.pool.get('mage.gift.card')
	action = wizard.action

	data = self.prepare_card_data(cr, uid, action, wizard)

	if action == 'create_balance':
	    cardNumber = card_obj.create_card(cr, uid, data)
	    print 'CARD NUMBER', cardNumber

	    if wizard.sale and wizard.add_sale_charge:
		self.add_charge_to_order(cr, uid, cardNumber, data['balance'], wizard.sale, 'sale')
		return True
	    elif wizard.invoice and wizard.add_invoice_charge:
		self.add_charge_to_order(cr, uid, cardNumber, data['balance'], wizard.invoice, 'invoice')
		return True
	else:
#	    self.update_card(cr, uid, data)
#	    return True
	    cardNumber = data['cert_number']
	    balance_data = card_obj.lookup_card(cr, uid, cardNumber)
	    card_status = balance_data['status']
	    if card_status != 'A':
		raise osv.except_osv(_('Not Approved'),_('The Card is not approved. The status is: %s')%card_status)

	    balance = round(float(balance_data['balance']), 2)
	    redeem_amount = round(data['balance'], 2)
	    new_balance = balance - redeem_amount
	    if new_balance < 0:
		raise osv.except_osv(_('Insufficient Funds'),_('The balance on the card is %s')%balance)

            if wizard.sale:
                self.add_charge_to_order(cr, uid, cardNumber, -redeem_amount, wizard.sale, 'sale')
            elif wizard.invoice:
                self.add_charge_to_order(cr, uid, cardNumber, -redeem_amount, wizard.invoice, 'invoice')

 	    data['balance'] = new_balance
	    card_obj.update_card(cr, uid, cardNumber, data)
	    return True


    def prepare_card_data(self, cr, uid, action, wizard):
	user_obj = self.pool.get('res.users')
	user = user_obj.browse(cr, uid, uid)
	if not wizard.sale and not wizard.invoice and not wizard.crm_claim:
	    if wizard.action == 'redeem_balance':
		raise osv.except_osv(_('User Error'),_('You cannot redeem a card balance from this menu'))

	data = {
		'balance': wizard.balance,
		'store_id': wizard.store_id.external_id,
		'user_id': 4,
		'user_name': user.name,
		'qty': 1,
	}

	if action == 'create_balance':
	    data['cert_number'] = 'BOL-[AN*4]-[N*2][A*1][N*1]'
	else:
	    data['cert_number'] = wizard.code

	if not data['cert_number']:
	    raise osv.except_osv(_('User Error'),_('You Cannot update a certificate with no Number!'))

	if data['balance'] <= 0:
		raise osv.except_osv(_('User Error'),_('You Cannot do anything with a 0 balance!'))

	if wizard.expire_date:
            data['expire_at'] = '04/7/2016'
	if wizard.sender_name:
            data['sender_name'] = wizard.sender_name
	if wizard.recipient_name:
            data['recipient_name'] = wizard.recipient_name
	if wizard.recipient_email:
            data['recipient_email'] = wizard.recipient_email
	if wizard.recipient_message:
            data['recipient_message'] = wizard.recipient_message
	if wizard.comments:
            data['comments'] = wizard.comments

	return data


    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
	active_model = context.get('active_model')
	if not active_model:
	    return {}

	if active_model == 'sale.order':
            sale_ids = context.get('active_ids', [])
	    if not sale_ids:
		return {}

            sale = self.pool.get('sale.order').browse(cr, uid, sale_ids[0])
	    res = {'sale': sale.id,
		'store_id': sale.mage_store.id or False,
		'add_sale_charge': True
	    }
	elif active_model == 'account.invoice':
	    invoice_ids = context.get('active_ids', [])
	    if not invoice_ids:
		return {}

	    invoice = self.pool.get('account.invoice').browse(cr, uid, invoice_ids[0])
	    if invoice.sale_order:
		store_id = invoice.sale_order.mage_store.id
	    else:
		store_id = False

	    res = {'invoice': invoice.id,
		'store_id': store_id,
		'add_invoice_charge': True,
	    }


	elif active_model == 'crm.claim':
	    claim_ids = context.get('active_ids', [])
	    if not claim_ids:
		return {}
	    claim = self.pool.get('crm.claim').browse(cr, uid, claim_ids[0])
	    if claim.sale:
		store_id = claim.sale.mage_store.id
	    else:
		store_id = False
	    res = {'crm_claim': claim.id, 'store_id': store_id}
	else:
	    res = {}

        return res

