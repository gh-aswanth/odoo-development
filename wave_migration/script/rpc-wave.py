import json
import xmlrpc.client
from collections import deque
from itertools import groupby


url_13 = ""
db_13 = ""

username = 'root'
password = 'Confianz321#'

def get_connection():
    print('V13 -> Server Initialized !!')
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url_13), allow_none=True)
    uid = common.authenticate(db_13, username, password, {})
    print('Login Successfully Completed : V13 [USER] -->', uid)
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url_13), allow_none=True)
    return models, uid


def revision_restore():
    data = {}
    import_data = []
    count = 0
    # migration query from v11 for sale_orderLine_revision
    """
        select  ct.name as section,
        n.name,n.revision_id, 
        n.order_line,
        n.product_id, 
        l.product_uom, 
        n.product_uom_qty,
        l.product_uom_qty as original_qty,
        l.discount as discount,
        l.route_id, 
        l.price_unit, 
        l.purchase_price as purchase_price,
        n.price_subtotal, 
        n.margin, 
        n.currency_id,
        l.order_partner_id,
        n.state
        from sale_order_line_revision n 
        LEFT JOIN sale_order_line l on l.id = n.order_line 
        LEFT JOIN sale_layout_category ct on ct.id = l.layout_category_id;
    """

    with open('../json/wave_us_order_line_revision.json', encoding='utf-8') as jp:
        dp = json.load(jp)
        import_data.extend(list(dp.values())[0])

    # migration query from v11 for sale_revision_new_line
    """
        select  c.name as section ,
        n.name,revision_id, 
        product_id, 
        product_uom, 
        product_uom_qty,
        product_uom_qty as original_qty,
        route_id, 
        salesman_id, 
        price_unit, 
        price_subtotal, 
        discount, 
        margin, 
        purchase_price, 
        currency_id, 
        company_id, 
        order_partner_id, n.state
        from sale_revision_new_line n 
        LEFT JOIN sale_layout_category c on c.id = layout_category_id;
    """

    with open('../json/wave_us_order_line_new_revision.json', encoding='utf-8') as jp:
        dp = json.load(jp)
        import_data.extend(list(dp.values())[0])
        import_data = sorted(import_data, key=lambda r: r['revision_id'])

    section_past = []

    for revision, lines in groupby(import_data, key=lambda r: r['revision_id']):
        section_category = {}
        for rvl in lines:
            section_category.setdefault(rvl['section'], []).append(rvl)

        lines = sum(list(section_category.values()), [])

        for section, rvl in groupby(lines, key=lambda k: k['section']):
            converted_data = list(rvl)
            count += len(converted_data)
            if section:
                if section not in section_past:
                    section_past.append(section)
                    data.setdefault(
                        revision, deque()).extend([{
                            'name': section,
                            'section': section,
                            'display_type': 'line_section',
                            'revision_id': revision,
                            'order_line': converted_data[0].get('order_line', False),
                            'flag': False if converted_data[0].get('order_line', False) else True
                        }])

                for cv in converted_data:
                    cv['flag'] = False if cv.get('order_line', False) else True

                data.setdefault(revision, deque()).extend(converted_data)
                count += 1
            else:
                for cv in converted_data:
                    cv['flag'] = False if cv.get('order_line', False) else True

                data.setdefault(revision, deque()).extendleft(converted_data)

        section_past = []

    r_data = sum(list(map(lambda t: list(t), data.values())), [])

    model, uid_13 = get_connection()

    new_data = []

    for patch in r_data:
        if patch.get('order_line') and not patch.get('display_type'):
            t = patch['product_uom_qty']
            if patch['state'] == 'done':
                patch['original_qty'] = patch['original_qty'] - t
                patch['product_uom_qty'] = patch['original_qty'] + t
            else:
                patch['product_uom_qty'] = patch['original_qty'] + t

            patch.pop('state')
            new_data.append(patch)
            continue
        if not patch.get('display_type'):
            patch.pop('state')
        new_data.append(patch)
   
    model.execute_kw(db_13, uid_13, password, 'sale.revision', 'cit_rpc_patch', [[]], {'patch_data': new_data})

# used to re-sequence the existing so lines.
def update_sale_lines():
    model, uid = get_connection()
    model.execute_kw(db_13, uid, password, 'sale.order', 'cit_rpc_section_restore', [[]])


if __name__ == '__main__':
    # always run this method first if you were to start the migration for the first time.
    # update_sale_lines()
    revision_restore()
