"""Premier Home (premierhometr.com) Fon ve Tül Perde ürünlerini indirir.

Mağaza her rengi ayrı ürün olarak listelediği için ürünler seriye göre
gruplanır (ör. "Osaka Halkalı Fon Perde Gri 140x260" → Osaka Fon Perde / Gri).

Çıktılar:
  images/premier/<slug>/kapak.webp          liste kartı görseli (uzun kenar en fazla 800px)
  images/premier/<slug>/<renk>-<n>.webp     renk galerisi (uzun kenar en fazla 1400px)
  js/products-premier.js                    window.PRODUCTS listesine eklenen veri

images/urunler/ ve js/products.js import_vinaldi.py'ye aittir; bu betik onlara dokunmaz.
Yeniden çalıştırılabilir: var olan görseller atlanır.
Kullanım:  python tools/import_premier.py
"""
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from import_vinaldi import FULL, THUMB, convert, fetch, slugify, text

ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / 'images' / 'premier'
BASE = 'https://premierhometr.com/'
TUL_URL = BASE + 'collections/tul-perdeler/products.json?limit=250'
ALL_URL = BASE + 'products.json?limit=250&page={}'
MAX_IMAGES = 10

SIZE_RE = re.compile(r'\b(\d{2,3})\s*[xX]\s*(\d{2,3})\b(\s*cm\b)?')
TITLE_RE = re.compile(r'^(.*?)\s*\b(Fon|Tül)\b(?:\s+Perde\b)?\s*(.*)$', re.I)


def tr_title(s):
    s = s.replace('I', 'ı').replace('İ', 'i').lower()
    return ' '.join(w[:1].replace('i', 'İ').upper() + w[1:] for w in s.split())


def img_url(src):
    return src.split('?')[0] + '?width=' + str(FULL)


def parse_rest(rest):
    """Başlığın seri adından sonraki kısmı → (renk, ölçüler, tek_kanat)."""
    sizes = [f'{a}x{b}' for a, b, _ in SIZE_RE.findall(rest)]
    single = bool(re.search(r'\bTek\b', rest, re.I))
    color = SIZE_RE.sub(' ', rest)
    color = re.sub(r'\bTek\b.*$', ' ', color, flags=re.I)
    color = re.sub(r'\bV\d\b|\b\d+\b', ' ', color)
    color = re.sub(r'\s+', ' ', color).strip()
    if len(color) < 2:
        color = ''
    return color, sizes, single


def option(p, name):
    for o in p['options']:
        if o['name'].strip().upper() in name:
            return o
    return None


def is_size(v):
    return bool(SIZE_RE.fullmatch(v.strip()))


def variant_info(p, v):
    """Varyantın (renk, ölçüler) bilgisi. Mağazada RENK ve ÖLÇÜ seçenekleri
    zaman zaman karışık girildiği için değer biçimine bakılır."""
    color, sizes = None, []
    for o in p['options']:
        if o['name'].strip().upper() not in ('RENK', 'ÖLÇÜ', 'OLCU'):
            continue
        val = (v.get(f'option{o["position"]}') or '').strip()
        if is_size(val):
            sizes.append(val.lower())
        elif val and val.lower() != 'default title' and not color:
            color = tr_title(val)
    return color, sizes


def split_colors(p, fallback):
    """Ürünü ([(renk, [görsel url'leri])], ölçüler) çiftine çevirir."""
    images = [i for i in p['images'] if i.get('src')]
    info = {v['id']: variant_info(p, v) for v in p['variants']}
    sizes = list(dict.fromkeys(z for _, zs in info.values() for z in zs))
    colors = list(dict.fromkeys(c for c, _ in info.values() if c))
    if len(colors) < 2:
        return [(colors[0] if colors else fallback, [i['src'] for i in images])], sizes
    by_id = {}
    for v in p['variants']:
        if v.get('featured_image') and info[v['id']][0]:
            by_id[v['featured_image']['id']] = info[v['id']][0]
    for i in images:
        for vid in i.get('variant_ids') or []:
            if vid in info and info[vid][0]:
                by_id[i['id']] = info[vid][0]
    if not by_id:
        return [(' / '.join(colors), [i['src'] for i in images])], sizes
    # eşlenen görselden sonraki eşlenmemiş görseller aynı renge aittir
    out, current = {}, colors[0]
    for i in images:
        current = by_id.get(i['id'], current)
        out.setdefault(current, []).append(i['src'])
    return list(out.items()), sizes


def material(body):
    t = text(re.sub(r'<[^>]+>', ' ', body or ''))
    m = re.search(r'%\s*100\s+(PES|Polyester|Pamuk|Keten|Kadife)', t, re.I)
    if m:
        return '%100 ' + ('Polyester' if m.group(1).upper() == 'PES' else tr_title(m.group(1)))
    m = re.search(r'Malzeme/Materyal:\s*([A-Za-zÇĞİÖŞÜçğıöşü]+)', t)
    return tr_title(m.group(1)) if m else ''


def load_products():
    tul = json.loads(fetch(TUL_URL))['products']
    fon = []
    for page in range(1, 20):
        batch = json.loads(fetch(ALL_URL.format(page)))['products']
        if not batch:
            break
        fon += [p for p in batch if re.search(r'fon\s+perde', p['title'], re.I)]
    return [('tul', p) for p in tul] + [('fon', p) for p in fon]


def group(products):
    series = {}
    for type_, p in products:
        if not p['images']:
            continue
        title = re.sub(r'^Premier Home\s+', '', p['title'].strip(), flags=re.I)
        m = TITLE_RE.match(title)
        if not m:
            print('  atlandı (başlık çözülemedi):', p['title'])
            continue
        base = re.sub(r'\s*\bHalkalı\b', '', m.group(1), flags=re.I).strip() or 'Premier Home'
        kind = 'Fon' if type_ == 'fon' else 'Tül'
        name = f'{base} {kind} Perde'
        s = series.setdefault((type_, name.lower()), {
            'type': type_, 'name': name, 'colors': {}, 'sizes': [], 'tags': set(), 'content': '',
        })
        color, sizes, single = parse_rest(m.group(3))
        parts, vsizes = split_colors(p, tr_title(color) if color else 'Standart')
        s['sizes'] += [z for z in sizes + vsizes if z not in s['sizes']]
        if re.search(r'Halkalı', p['title'], re.I):
            s['tags'].add('Halkalı')
        if single:
            s['tags'].add('Tek kanat')
        if option(p, ('PERDE ENI', 'PERDE ENİ')):
            s['tags'].add('Özel ölçü')
        s['content'] = s['content'] or material(p['body_html'])
        for cname, srcs in parts:
            prev = s['colors'].get(cname)
            # aynı rengin kopya ürünlerinden en çok görseli olanı kalsın
            if prev is None or len(srcs) > len(prev):
                s['colors'][cname] = srcs
    # kırpılmış renk adlarını (Pudr, Antrasi) tam adla düzelt; aynı seride
    # tam adı varsa birleştir
    counts = {}
    for s in series.values():
        for n in s['colors']:
            counts[n] = counts.get(n, 0) + 1
    for s in series.values():
        for n in list(s['colors']):
            if counts[n] > 1:
                continue
            full = next((o for o in sorted(counts, key=len)
                         if len(o) > len(n) and o.startswith(n) and o[len(n)] != ' '), None)
            if not full:
                continue
            srcs = s['colors'].pop(n)
            if len(srcs) > len(s['colors'].get(full, [])):
                s['colors'][full] = srcs
        if len(s['colors']) > 1:
            s['colors'].pop('Standart', None)
    return list(series.values())


def main():
    vinaldi = {p.name for p in (ROOT / 'images' / 'urunler').iterdir() if p.is_dir()}
    out, jobs, used = [], [], set(vinaldi)
    for s in sorted(group(load_products()), key=lambda s: (s['type'], s['name'])):
        slug = slugify(s['name'])
        if slug in used:
            slug += '-premier'
        used.add(slug)
        folder = IMG_DIR / slug
        rel = 'images/premier/' + slug + '/'
        colors, cused = [], set()
        for cname, srcs in s['colors'].items():
            cs = slugify(cname)
            while cs in cused:
                cs += '-2'
            cused.add(cs)
            files = []
            for n, src in enumerate(list(dict.fromkeys(srcs))[:MAX_IMAGES], 1):
                fn = f'{cs}-{n}.webp'
                jobs.append((img_url(src), folder / fn, FULL))
                files.append(rel + fn)
            colors.append({'name': cname, 'images': files})
        first = next(iter(s['colors'].values()))[0]
        jobs.append((img_url(first), folder / 'kapak.webp', THUMB))
        tags = [t for t in ('Özel ölçü', 'Halkalı', 'Tek kanat') if t in s['tags']]
        sub = ' · '.join(tags + ([] if 'Özel ölçü' in tags else s['sizes'][:3])) or s['name']
        out.append({
            'slug': slug, 'name': s['name'], 'sub': sub, 'content': s['content'] or sub,
            'type': s['type'], 'category': 'Fon Perde' if s['type'] == 'fon' else 'Tül Perde',
            'brand': 'Premier Home', 'cover': rel + 'kapak.webp', 'colors': colors,
        })
        print(f'{out[-1]["category"]}: {s["name"]} — {sub} ({", ".join(c["name"] for c in colors)})', flush=True)

    print(f'\n{len(out)} ürün, {sum(len(p["colors"]) for p in out)} renk, {len(jobs)} görsel işleniyor...', flush=True)
    errors = []
    with ThreadPoolExecutor(8) as ex:
        for i, err in enumerate(ex.map(convert, jobs), 1):
            if err:
                errors.append(err)
            if i % 100 == 0:
                print(f'  {i}/{len(jobs)}', flush=True)

    missing = {str(d.relative_to(ROOT)).replace('\\', '/') for _, d, _ in jobs if not d.exists()}
    for p in out:
        for c in p['colors']:
            c['images'] = [f for f in c['images'] if f not in missing]
        p['colors'] = [c for c in p['colors'] if c['images']]
    out = [p for p in out if p['colors'] and p['cover'] not in missing]

    # artık kullanılmayan eski dosyaları sil (yalnızca images/premier/)
    expected = {d.resolve() for _, d, _ in jobs}
    for f in IMG_DIR.rglob('*'):
        if f.is_file() and f.resolve() not in expected:
            f.unlink()

    dest = ROOT / 'js' / 'products-premier.js'
    dest.write_text('// tools/import_premier.py tarafından üretildi — elle düzenlemeyin.\n'
                    'window.PRODUCTS = (window.PRODUCTS || []).concat('
                    + json.dumps(out, ensure_ascii=False, indent=1) + ');\n', encoding='utf-8')

    total = sum(f.stat().st_size for f in IMG_DIR.rglob('*') if f.is_file())
    print(f'\nBitti. {len(out)} ürün. Toplam görsel boyutu: {total / 1e6:.1f} MB')
    if errors:
        print(f'{len(errors)} hata:')
        print('\n'.join(errors))
        sys.exit(1)


if __name__ == '__main__':
    main()
