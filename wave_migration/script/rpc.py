
import xmlrpc.client

url_11 = ""
url_13 = ""

db_11 = ""
db_13 = ""


username = 'admin'
password = 'admin'

common11 = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url_11), allow_none=True)
uid_11 = common11.authenticate(db_11, username, password, {})
models11 = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url_11), allow_none=True)


common13 = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url_13), allow_none=True)
uid_13 = common13.authenticate(db_13, username, password, {})
models13 = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url_13), allow_none=True)



rev_11 = models11.execute_kw(db_11, uid_11, password, 'sale.revision', 'search', [[]], {})
rev_13 = models13.execute_kw(db_13, uid_13, password, 'sale.revision', 'search', [[]], {})

missing_rev = [
    1357, 1358, 1359, 1360,
    1361, 1362, 1363, 1364,
    1365, 1366, 1367, 1368,
    1369, 1370, 1371, 1372,
    1373, 1374, 1375, 1376,
    1378, 1379, 1380, 1381,
    1382, 1383, 1384, 1385
]


for i in missing_rev:
    if i in rev_13:
        print('PASS - RE- ODOO 13')
    if i in rev_11:
        print('PASS - RE- ODOO 11')