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

  var main = document.getElementById('pdGallery').querySelector('.pd__main');
  var track = document.getElementById('pdTrack');
  var thumbs = document.getElementById('pdThumbs');
  var strip = document.getElementById('pdStrip');
  var swatches = document.getElementById('pdSwatches');
  var counter = document.getElementById('pdCounter');
  var badgeName = document.getElementById('pdBadgeName');
  var selectedLabel = document.getElementById('pdSelected');
  var barColor = document.getElementById('pdBarColor');
  var pickerName = document.getElementById('pdPickerName');
  var reduceMq = window.matchMedia('(prefers-reduced-motion: reduce)');
  var current = 0;   // seçili renk
  var slide = 0;     // seçili görsel

  function behavior() { return reduceMq.matches ? 'auto' : 'smooth'; }

  // Görsel şeridi: aktif görseli sayaç ve küçük resimlerle eşitle
  function setSlide(n) {
    var c = p.colors[current];
    slide = Math.max(0, Math.min(n, c.images.length - 1));
    counter.textContent = c.images.length > 1 ? (slide + 1) + ' / ' + c.images.length : '';
    thumbs.querySelectorAll('.pd__thumb').forEach(function (t, i) {
      t.classList.toggle('is-active', i === slide);
      t.setAttribute('aria-current', String(i === slide));
    });
  }
  function goTo(n, smooth) {
    track.scrollTo({ left: n * track.clientWidth, behavior: smooth ? behavior() : 'auto' });
    setSlide(n);
  }
  var scrollTick = null;
  track.addEventListener('scroll', function () {
    if (scrollTick) return;
    scrollTick = requestAnimationFrame(function () {
      scrollTick = null;
      if (track.clientWidth) setSlide(Math.round(track.scrollLeft / track.clientWidth));
    });
  }, { passive: true });
  window.addEventListener('resize', function () { goTo(slide, false); });

  function openZoom() {
    if (!window.tpLightbox) return;
    window.tpLightbox(p.colors[current].images, slide, function (i) { goTo(i, false); });
  }
  track.addEventListener('click', openZoom);
  document.getElementById('pdZoom').addEventListener('click', openZoom);

  function selectColor(idx, fromUser) {
    var c = p.colors[idx];
    if (!c) return;
    current = idx;
    var label = p.name + ' — ' + c.name;
    selectedLabel.textContent = c.name;
    badgeName.textContent = c.name;
    barColor.textContent = c.name;
    pickerName.textContent = c.name;

    track.classList.add('is-swapping');
    track.innerHTML = '';
    thumbs.innerHTML = '';
    c.images.forEach(function (src, n) {
      var s = el('div', 'pd__slide');
      var im = img(src, n === 0 ? label : label + ' ' + (n + 1), n > 0);
      if (n === 0) {
        var done = function () { track.classList.remove('is-swapping'); };
        if (im.complete) done(); else { im.onload = done; im.onerror = done; }
      }
      s.appendChild(im);
      track.appendChild(s);

      var b = el('button', 'pd__thumb');
      b.type = 'button';
      b.setAttribute('aria-label', c.name + ' görsel ' + (n + 1));
      b.appendChild(img(src, '', true));
      b.addEventListener('click', function () { goTo(n, true); });
      thumbs.appendChild(b);
    });
    thumbs.hidden = c.images.length < 2;
    main.classList.toggle('is-single', c.images.length < 2);
    goTo(0, false);

    [swatches, strip].forEach(function (box) {
      box.querySelectorAll('.swatch, .pd__chip').forEach(function (s, i) { s.setAttribute('aria-pressed', String(i === idx)); });
    });
    var chip = strip.children[idx];
    if (chip) strip.scrollTo({ left: chip.offsetLeft - (strip.clientWidth - chip.offsetWidth) / 2, behavior: fromUser ? behavior() : 'auto' });

    if (fromUser) {
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

    // Mobil renk şeridi
    var chip = el('button', 'pd__chip');
    chip.type = 'button';
    chip.title = c.name;
    chip.setAttribute('aria-label', c.name);
    chip.setAttribute('aria-pressed', 'false');
    chip.appendChild(img(c.images[0], '', true));
    chip.addEventListener('click', function () { selectColor(i, true); });
    strip.appendChild(chip);
  });
  document.getElementById('pdPickerCount').textContent = p.colors.length + ' renk';
  document.getElementById('pdPicker').hidden = p.colors.length < 2;

  var start = parseInt(params.get('renk'), 10) - 1;
  selectColor(start >= 0 && start < p.colors.length ? start : 0, false);

  // Mobil alt çubuk: sayfa içi butonlar ekranın altında kaldığı sürece görünür
  var bar = document.getElementById('pdBar');
  var actions = document.getElementById('pdActions');
  if (bar && actions && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      var e = entries[0];
      var show = !e.isIntersecting && e.boundingClientRect.top > 0;
      bar.classList.toggle('is-on', show);
      bar.setAttribute('aria-hidden', String(!show));
      bar.querySelector('a').tabIndex = show ? 0 : -1;
    }).observe(actions);
  }
})();
