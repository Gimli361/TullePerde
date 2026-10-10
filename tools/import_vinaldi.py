"""Vinaldi Fon ve Tül Perde ürünlerini indirir.

Çıktılar:
  images/urunler/<slug>/kapak.<ext>         liste kartı görseli (uzun kenar en fazla 800px)
  images/urunler/<slug>/<renk>-<n>.<ext>    renk galerisi (uzun kenar en fazla 1400px)

JPEG kaynaklar ikinci kez sıkıştırılmasın diye boyutu uygunsa olduğu gibi
saklanır (.jpg); büyük PNG kaynaklar WebP'ye çevrilir.
  js/products.js                            window.PRODUCTS verisi

Yeniden çalıştırılabilir: var olan görseller atlanır.
Kullanım:  python tools/import_vinaldi.py
"""
import html
import io
import json
import re
import sys
import unicodedata
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / 'images' / 'urunler'
BASE = 'https://www.vinaldi.com/public/'
CATEGORIES = [
    ('fon', 'Fon Perde', BASE + 'kategori.php?slug=perde&sub=fon-perde'),
    ('tul', 'Tül Perde', BASE + 'kategori.php?slug=perde&sub=tul-perde'),
]
FULL = 1400
THUMB = 800
QUALITY = 85


def fetch(url, binary=False):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            return data if binary else data.decode('utf-8', 'replace')
        except Exception:
            if attempt == 2:
                raise


def slugify(s):
    s = unicodedata.normalize('NFKD', s.replace('ı', 'i').replace('İ', 'i'))
    s = s.encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-') or 'renk'


def text(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', s))).strip()


def parse_category(page):
    items = []
    for block in re.findall(r'<article class="category-product-card.*?</article>', page, re.S):
        slug = re.search(r'urun-detay\.php\?slug=([^"&]+)', block).group(1)
        name = text(re.search(r'<h3 class="product-title">(.*?)</h3>', block, re.S).group(1))
        sub = re.search(r'<span class="product-code">(.*?)</span>', block, re.S)
        items.append({'slug': slug, 'name': name, 'sub': text(sub.group(1)) if sub else ''})
    return items


def attr(tag, name):
    m = re.search(name + r'="([^"]*)"', tag)
    return html.unescape(m.group(1)) if m else ''


def parse_detail(page):
    content = re.search(r'<dt>İçerik</dt>\s*<dd[^>]*>(.*?)</dd>', page, re.S)
    colors = []
    for tag in re.findall(r'<button\s+class="product-variant-card".*?>', page, re.S):
        imgs = json.loads(attr(tag, 'data-images') or '[]') or [attr(tag, 'data-cover')]
        imgs = list(dict.fromkeys(i for i in imgs if i))
        if imgs:
            colors.append({'name': attr(tag, 'data-name'), 'src': imgs})
    if not colors:
        m = re.search(r'data-default-images="([^"]*)"', page)
        imgs = json.loads(html.unescape(m.group(1))) if m else []
        if imgs:
            colors.append({'name': 'Standart', 'src': imgs})
    cover = re.search(r'<meta property="og:image" content="([^"]+)"', page)
    return {
        'content': text(content.group(1)) if content else '',
        'cover': cover.group(1) if cover else (colors[0]['src'][0] if colors else ''),
        'colors': colors,
    }


def convert(job):
    url, dest, size = job
    if dest.exists():
        return None
    try:
        data = fetch(url, binary=True)
        im = Image.open(io.BytesIO(data))
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix('.tmp')
        if dest.suffix == '.jpg' and im.format == 'JPEG' and max(im.size) <= size:
            tmp.write_bytes(data)
            tmp.replace(dest)
            return None
        im = im.convert('RGBA' if im.mode in ('RGBA', 'LA', 'P') else 'RGB')
        if im.mode == 'RGBA':
            bg = Image.new('RGB', im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[3])
            im = bg
        im.thumbnail((size, size), Image.LANCZOS)
        if dest.suffix == '.jpg':
            im.save(tmp, 'JPEG', quality=92, optimize=True)
        else:
            im.save(tmp, 'WEBP', quality=QUALITY, method=5)
        tmp.replace(dest)
        return None
    except Exception as e:
        return f'{url} -> {e}'


def ext(url):
    return '.jpg' if re.search(r'\.jpe?g$', url, re.I) else '.webp'


def main():
    products, jobs = [], []
    for type_, label, url in CATEGORIES:
        seen = set()
        for item in parse_category(fetch(url)):
            if item['slug'] in seen:
                continue
            seen.add(item['slug'])
            detail = parse_detail(fetch(BASE + 'urun-detay.php?slug=' + item['slug']))
            slug = item['slug']
            folder = IMG_DIR / slug
            rel = 'images/urunler/' + slug + '/'
            cover = 'kapak' + ext(detail['cover'])
            jobs.append((detail['cover'], folder / cover, THUMB))
            colors, used = [], set()
            for c in detail['colors']:
                cs = slugify(c['name'])
                base, k = cs, 2
                while cs in used:
                    cs, k = f'{base}-{k}', k + 1
                used.add(cs)
                files = []
                for n, src in enumerate(c['src'], 1):
                    fn = f'{cs}-{n}' + ext(src)
                    jobs.append((src, folder / fn, FULL))
                    files.append(rel + fn)
                colors.append({'name': c['name'], 'images': files})
            products.append({
                'slug': slug, 'name': item['name'], 'sub': item['sub'] or detail['content'],
                'content': detail['content'], 'type': type_, 'category': label,
                'brand': 'Vinaldi', 'cover': rel + cover, 'colors': colors,
            })
            print(f'{label}: {item["name"]} ({len(colors)} renk)', flush=True)

    print(f'\n{len(products)} ürün, {sum(len(p["colors"]) for p in products)} renk, {len(jobs)} görsel işleniyor...', flush=True)
    errors = []
    with ThreadPoolExecutor(8) as ex:
        for i, err in enumerate(ex.map(convert, jobs), 1):
            if err:
                errors.append(err)
            if i % 100 == 0:
                print(f'  {i}/{len(jobs)}', flush=True)

    missing = {str(d.relative_to(ROOT)).replace('\\', '/') for _, d, _ in jobs if not d.exists()}
    for p in products:
        for c in p['colors']:
            c['images'] = [f for f in c['images'] if f not in missing]
        p['colors'] = [c for c in p['colors'] if c['images']]

    # artık kullanılmayan eski dosyaları sil
    expected = {d.resolve() for _, d, _ in jobs}
    for f in IMG_DIR.rglob('*'):
        if f.is_file() and f.resolve() not in expected:
            f.unlink()

    out = ROOT / 'js' / 'products.js'
    out.write_text('// tools/import_vinaldi.py tarafından üretildi — elle düzenlemeyin.\nwindow.PRODUCTS = '
                   + json.dumps(products, ensure_ascii=False, indent=1) + ';\n', encoding='utf-8')

    total = sum(f.stat().st_size for f in IMG_DIR.rglob('*') if f.is_file())
    print(f'\nBitti. Toplam görsel boyutu: {total / 1e6:.1f} MB')
    if errors:
        print(f'{len(errors)} hata:')
        print('\n'.join(errors))
        sys.exit(1)


if __name__ == '__main__':
    main()
