(function () {
  var body = document.body;
  var hdr = document.getElementById('hdr');
  var mob = document.getElementById('mob');
  var sr = document.getElementById('sr');
  var srInput = document.getElementById('srInput');
  var srResults = document.getElementById('srResults');
  var state = { scrolled: false, menu: false };

  // ===== Açılış animasyonu =====
  setTimeout(function () { body.classList.add('is-drawn'); }, 80);
  setTimeout(function () { body.classList.add('is-loaded'); }, 1800);

  // ===== Görseller: images/<slot>.jpg|.webp|.png varsa yükle, yoksa yer tutucu kalır =====
  var exts = ['webp', 'jpg', 'png'];
  document.querySelectorAll('.slot[data-slot]').forEach(function (slot) {
    var name = slot.getAttribute('data-slot');
    var i = 0;
    var img = new Image();
    img.alt = slot.getAttribute('data-ph') || '';
    img.decoding = 'async';
    img.onload = function () { slot.appendChild(img); slot.classList.add('has-img'); };
    img.onerror = function () { i++; if (i < exts.length) img.src = 'images/' + name + '.' + exts[i]; };
    img.src = 'images/' + name + '.' + exts[0];
  });

  // ===== Header durumu =====
  var solidPage = body.classList.contains('page-solid');
  function syncHeader() { hdr.classList.toggle('is-solid', solidPage || state.scrolled || state.menu); hdr.classList.toggle('is-menu', state.menu); }
  function onScroll() {
    var s = window.scrollY > 18;
    if (s !== state.scrolled) { state.scrolled = s; syncHeader(); }
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  syncHeader();

  function setMenu(v) { if (state.menu !== v) { state.menu = v; syncHeader(); } }
  hdr.querySelectorAll('[data-menu]').forEach(function (a) {
    a.addEventListener('mouseenter', function () { setMenu(a.getAttribute('data-menu') === 'open'); });
  });
  hdr.addEventListener('mouseleave', function () { setMenu(false); });
  hdr.querySelectorAll('.mega__item').forEach(function (a) { a.addEventListener('click', function () { setMenu(false); }); });

  // ===== Mobil menü =====
  function setMobile(v) {
    mob.classList.toggle('is-open', v);
    mob.setAttribute('aria-hidden', String(!v));
    body.classList.toggle('is-locked', v);
  }
  document.getElementById('openMobile').addEventListener('click', function () { setMobile(true); });
  mob.querySelectorAll('[data-close-mobile]').forEach(function (el) { el.addEventListener('click', function () { setMobile(false); }); });
  window.addEventListener('resize', function () { if (window.innerWidth >= 1100) setMobile(false); });

  // ===== Arama =====
  var products = window.PRODUCTS ? window.PRODUCTS.map(function (p) {
    return { name: p.name, code: p.category + ' · ' + p.sub, href: 'urun.html?slug=' + encodeURIComponent(p.slug) };
  }) : Array.prototype.map.call(document.querySelectorAll('#productGrid .card'), function (c) {
    return { name: c.getAttribute('data-name'), code: c.getAttribute('data-code'), href: '#urunler' };
  });
  function setSearch(v) {
    sr.classList.toggle('is-open', v);
    sr.setAttribute('aria-hidden', String(!v));
    if (v) { setMenu(false); setTimeout(function () { srInput.focus(); }, 60); }
  }
  function renderResults() {
    var q = srInput.value.trim().toLocaleLowerCase('tr');
    srResults.innerHTML = '';
    if (!q) return;
    var found = products.filter(function (p) { return (p.name + ' ' + p.code).toLocaleLowerCase('tr').indexOf(q) !== -1; });
    if (!found.length) {
      var e = document.createElement('span');
      e.className = 'sr__empty';
      e.textContent = 'Sonuç bulunamadı.';
      srResults.appendChild(e);
      return;
    }
    found.forEach(function (p) {
      var a = document.createElement('a');
      a.href = p.href;
      var n = document.createElement('span'); n.textContent = p.name;
      var c = document.createElement('span'); c.textContent = p.code;
      a.appendChild(n); a.appendChild(c);
      a.addEventListener('click', function () { setSearch(false); });
      srResults.appendChild(a);
    });
  }
  document.getElementById('openSearch').addEventListener('click', function () { setSearch(true); });
  sr.querySelectorAll('[data-close-search]').forEach(function (el) { el.addEventListener('click', function () { setSearch(false); }); });
  srInput.addEventListener('input', renderResults);

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { setSearch(false); setMobile(false); setMenu(false); }
  });

  // ===== Ürün sekmeleri =====
  var tabs = document.querySelectorAll('.tab');
  var cards = document.querySelectorAll('#productGrid .card');
  tabs.forEach(function (t) {
    t.addEventListener('click', function () {
      var k = t.getAttribute('data-tab');
      tabs.forEach(function (o) {
        var a = o === t;
        o.classList.toggle('is-active', a);
        o.setAttribute('aria-selected', String(a));
      });
      cards.forEach(function (c) { c.hidden = !(k === 'all' || c.getAttribute('data-type') === k); });
    });
  });

  // ===== Kaydırınca belirme =====
  var reveals = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window)) {
    reveals.forEach(function (el) { el.classList.add('is-in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px' });
    reveals.forEach(function (el) { io.observe(el); });
  }
})();
