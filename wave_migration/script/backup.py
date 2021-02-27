import json
from itertools import groupby
import xmlrpc.client

import_data = []

url_13 = ""
db_13 = ""

username = ''
password = ''

common13 = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url_13), allow_none=True)
uid_13 = common13.authenticate(db_13, username, password, {})
models13 = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url_13), allow_none=True)

with open('../json/prd_line.json', encoding='utf-8') as jp:
        dp = json.load(jp)
        import_data.extend(list(dp.values())[0])

for j in import_data:
    j.pop('id')

re = models13.execute_kw(db_13, uid_13, password, 'product.related.line', 'create', [import_data])
print(re)

import_data = []

with open('m2m_prd_line.json', encoding='utf-8') as jp:
        dp = json.load(jp)
        import_data.extend(list(dp.values())[0])

for s, l in groupby(import_data, key=lambda r: r.get('product_template_id')):
    ids = list(map(lambda p: p.get('product_related_line_id'), l))
    print(ids)
    models13.execute_kw(db_13, uid_13, password, 'product.template', 'write', [[s], {'product_related_line_ids': [[6, 0, ids]]}])

