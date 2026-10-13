"""sitemap.xml üretir: sabit sayfalar + js/products.js ve js/products-premier.js içindeki her ürün.

Kullanım (proje kökünden):  python tools/build_sitemap.py
Ürünler import_vinaldi.py / import_premier.py ile güncellendikten sonra yeniden çalıştırın.
"""
import datetime
import json
import os
from xml.sax.saxutils import escape

BASE = 'https://gimli361.github.io/TullePerde/'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

products = []
for name in ('products.js', 'products-premier.js'):
    src = open(os.path.join(ROOT, 'js', name), encoding='utf-8').read()
    products += json.loads(src[src.index('[\n'):src.rindex(']') + 1])
today = datetime.date.today().isoformat()

urls = [('', '1.0'), ('tul-perde.html', '0.9'), ('fon-perde.html', '0.9')]
urls += [('urun.html?slug=' + p['slug'], '0.7') for p in products]

lines = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for path, prio in urls:
    lines.append('  <url><loc>%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>'
                 % (escape(BASE + path), today, prio))
lines.append('</urlset>')

with open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(lines) + '\n')
print('sitemap.xml: %d adres' % len(urls))
