(function () {
  var products = window.PRODUCTS || [];
  var cat = document.body.getAttribute('data-cat');
  var CAT_PAGE = { fon: 'fon-perde.html', tul: 'tul-perde.html' };

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function img(src, alt, lazy) {
    var i = new Image();
    i.src = src;
    i.alt = alt || '';
    i.decoding = 'async';
    if (lazy) i.loading = 'lazy';
    return i;
  }

  // ===== Liste sayfası =====
  var grid = document.getElementById('catalogGrid');
  if (grid && cat) {
    var list = products.filter(function (p) { return p.type === cat; });
    var count = document.getElementById('catalogCount');
    if (count) count.textContent = list.length + ' ürün';
    if (!list.length) grid.appendChild(el('p', 'catalog__empty', 'Ürün bulunamadı.'));
    list.forEach(function (p, i) {
      var a = el('a', 'card reveal');
      a.href = 'urun.html?slug=' + encodeURIComponent(p.slug);
      a.style.setProperty('--d', (i % 4) * 0.08 + 's');
      var media = el('div', 'card__media');
      var zoom = el('div', 'card__zoom');
      zoom.appendChild(img(p.cover, p.name, true));
      media.appendChild(zoom);
      media.appendChild(el('span', 'card__tag', p.brand));
      var body = el('div', 'card__body');
      var txt = el('div');
      txt.appendChild(el('span', 'card__name', p.name));
      txt.appendChild(el('span', 'card__code', p.sub + ' · ' + p.colors.length + ' renk'));
      body.appendChild(txt);
      body.appendChild(el('span', 'card__arrow', '→'));
      a.appendChild(media);
      a.appendChild(body);
      grid.appendChild(a);
    });
  }

  // ===== Ürün detay sayfası =====
  var pd = document.getElementById('productDetail');
  if (!pd) return;
  var params = new URLSearchParams(location.search);
  var slug = params.get('slug');
  var p = products.filter(function (x) { return x.slug === slug; })[0];
  if (!p) {
    pd.innerHTML = '';
    var empty = el('div', 'catalog__empty');
    empty.appendChild(el('p', null, 'Ürün bulunamadı.'));
    var back = el('a', 'arrow-link', 'Koleksiyona dön ');
    back.href = 'fon-perde.html';
    back.appendChild(el('span', null, '→'));
    empty.appendChild(back);
    pd.appendChild(empty);
    return;
  }

  document.title = p.name + ' — ' + p.category + ' · Tulle Perde';
  var catLink = document.getElementById('crumbCat');
  catLink.textContent = p.category;
  catLink.href = CAT_PAGE[p.type];
  document.getElementById('crumbName').textContent = p.name;
  document.getElementById('pdKicker').textContent = p.brand + ' · ' + p.category;
  document.getElementById('pdName').textContent = p.name;
  document.getElementById('pdLede').textContent = p.sub;
  document.getElementById('pdCategory').textContent = p.category;
  document.getElementById('pdContent').textContent = p.content || p.sub;
  document.getElementById('pdBrand').textContent = p.brand;
  document.getElementById('pdColorCount').textContent = p.colors.length + ' renk';

  var mainImg = document.getElementById('pdMainImg');
  var thumbs = document.getElementById('pdThumbs');
  var swatches = document.getElementById('pdSwatches');
  var selectedLabel = document.getElementById('pdSelected');

  function showImage(src, btn) {
    mainImg.src = src;
    thumbs.querySelectorAll('.pd__thumb').forEach(function (t) { t.classList.toggle('is-active', t === btn); });
  }

  function selectColor(idx, updateUrl) {
    var c = p.colors[idx];
    if (!c) return;
    mainImg.alt = p.name + ' — ' + c.name;
    selectedLabel.textContent = c.name;
    thumbs.innerHTML = '';
    c.images.forEach(function (src, n) {
      var b = el('button', 'pd__thumb');
      b.type = 'button';
      b.setAttribute('aria-label', c.name + ' görsel ' + (n + 1));
      b.appendChild(img(src, '', true));
      b.addEventListener('click', function () { showImage(src, b); });
      thumbs.appendChild(b);
    });
    thumbs.hidden = c.images.length < 2;
    showImage(c.images[0], thumbs.firstChild);
    swatches.querySelectorAll('.swatch').forEach(function (s, i) { s.setAttribute('aria-pressed', String(i === idx)); });
    if (updateUrl) {
      params.set('renk', String(idx + 1));
      history.replaceState(null, '', '?' + params.toString());
    }
  }

  p.colors.forEach(function (c, i) {
    var s = el('button', 'swatch');
    s.type = 'button';
    s.setAttribute('aria-pressed', 'false');
    var box = el('span', 'swatch__img');
    box.appendChild(img(c.images[0], '', true));
    s.appendChild(box);
    s.appendChild(el('span', null, c.name));
    s.addEventListener('click', function () { selectColor(i, true); });
    swatches.appendChild(s);
  });

  var start = parseInt(params.get('renk'), 10) - 1;
  selectColor(start >= 0 && start < p.colors.length ? start : 0, false);
})();
