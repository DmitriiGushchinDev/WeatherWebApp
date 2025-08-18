/* static/js/main.js */

/* ------------------ utils ------------------ */
function $(sel, ctx = document) { return ctx.querySelector(sel); }
function $all(sel, ctx = document) { return Array.from(ctx.querySelectorAll(sel)); }

function debounce(fn, wait = 300) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn.apply(null, args), wait);
  };
}

// Django CSRF (cookie -> header)
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return decodeURIComponent(parts.pop().split(';').shift());
}
function csrfHeaders(extra = {}) {
  const token = getCookie('csrftoken');
  return Object.assign({
    'X-CSRFToken': token || '',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }, extra);
}

/* ------------------ geolocation detect ------------------ */
// Hook to a button with id="detectCityBtn" and a status div with id="detectStatus"
(function setupGeoDetect() {
  const btn = $('#detectCityBtn');
  const status = $('#detectStatus');

  if (!btn) return;

  btn.addEventListener('click', async (e) => {
    e.preventDefault();
    if (!('geolocation' in navigator)) {
      status && (status.textContent = 'Geolocation not supported on this device.');
      return;
    }
    status && (status.textContent = 'Requesting location…');

    navigator.geolocation.getCurrentPosition(async (pos) => {
      const { latitude, longitude } = pos.coords;
      status && (status.textContent = 'Detecting city…');

      try {
        const res = await fetch('/cities/geolocation/', {
          method: 'POST',
          headers: csrfHeaders(),
          body: JSON.stringify({ lat: latitude, lon: longitude })
        });
        const data = await res.json();
        if (!res.ok || data.error) throw new Error(data.error || 'Geocode failed');

        // Build and submit a hidden form to add the city
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/cities/geolocation/';
        form.innerHTML = `
          <input type="hidden" name="csrfmiddlewaretoken" value="${getCookie('csrftoken') || ''}">
          <input type="hidden" name="name" value="${data.name || ''}">
          <input type="hidden" name="state" value="${data.state || ''}">
          <input type="hidden" name="country" value="${data.country || ''}">
          <input type="hidden" name="lat" value="${data.lat}">
          <input type="hidden" name="lon" value="${data.lon}">
        `;
        document.body.appendChild(form);
        form.submit();
      } catch (err) {
        status && (status.textContent = 'Could not detect city. Try again or type manually.');
      }
    }, (err) => {
      status && (status.textContent = err.code === 1
        ? 'Permission denied. Type your city or use IP fallback.'
        : 'Location error. Try again or type manually.');
    }, { enableHighAccuracy: false, timeout: 8000, maximumAge: 60000 });
  });
})();

/* ------------------ city search suggestions ------------------ */
// Requires: <input id="city-input"> and <ul id="suggestions"> on the page
(function setupCitySuggest() {
  const input = $('#city-input');
  const list = $('#suggestions');

  if (!input || !list) return;

  const render = (items) => {
    list.innerHTML = items.map(it => `
      <li class="sugg" tabindex="0"
          data-lat="${it.lat}" data-lon="${it.lon}"
          data-name="${it.name}" data-state="${it.state || ''}" data-country="${it.country}">
        ${it.name}${it.state ? ', ' + it.state : ''}, ${it.country}
      </li>
    `).join('');
  };

  const fetchSuggest = debounce(async (q) => {
    if (q.length < 2) { list.innerHTML = ''; return; }
    try {
      const res = await fetch(`/api/cities?q=${encodeURIComponent(q)}&limit=6`, {
        headers: { 'Accept': 'application/json' }
      });
      const data = await res.json();
      render(Array.isArray(data) ? data : []);
    } catch {
      list.innerHTML = '';
    }
  }, 300);

  input.addEventListener('input', (e) => fetchSuggest(e.target.value.trim()));

  list.addEventListener('click', (e) => {
    const li = e.target.closest('.sugg');
    if (!li) return;

    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/cities/geolocation/';
    form.innerHTML = `
      <input type="hidden" name="csrfmiddlewaretoken" value="${getCookie('csrftoken') || ''}">
      <input type="hidden" name="name" value="${li.dataset.name}">
      <input type="hidden" name="state" value="${li.dataset.state}">
      <input type="hidden" name="country" value="${li.dataset.country}">
      <input type="hidden" name="lat" value="${li.dataset.lat}">
      <input type="hidden" name="lon" value="${li.dataset.lon}">
    `;
    document.body.appendChild(form);
    form.submit();
  });

  // Keyboard selection
  list.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      e.target.click();
    }
  });
})();

/* ------------------ theming helpers (optional) ------------------ */
// Map OpenWeather icon code to your body background class
// Call setBackgroundByIcon(code, isNight) after you have data on page render,
// or set `data-owm-icon` on <body> server-side and call this on load.

const ICON_BG_MAP = {
  clear: { day: 'bg-clear-day', night: 'bg-clear-night' },
  clouds: { day: 'bg-clouds', night: 'bg-clouds' },
  rain: { day: 'bg-rain', night: 'bg-rain' },
  snow: { day: 'bg-snow', night: 'bg-snow' },
  thunder: { day: 'bg-thunder', night: 'bg-thunder' },
  mist: { day: 'bg-clouds', night: 'bg-clouds' },
};

function classifyIcon(icon) {
  // owm icons: 01d, 01n, 02d, 09n, 10d, 11n, 13d, 50n, etc.
  if (!icon) return { key: 'clouds', night: false };
  const night = icon.endsWith('n');
  let key = 'clouds';
  if (icon.startsWith('01')) key = 'clear';
  else if (icon.startsWith('02') || icon.startsWith('03') || icon.startsWith('04')) key = 'clouds';
  else if (icon.startsWith('09') || icon.startsWith('10')) key = 'rain';
  else if (icon.startsWith('11')) key = 'thunder';
  else if (icon.startsWith('13')) key = 'snow';
  else if (icon.startsWith('50')) key = 'mist';
  return { key, night };
}

function setBackgroundByIcon(icon) {
  const { key, night } = classifyIcon(icon);
  const cls = ICON_BG_MAP[key][night ? 'night' : 'day'];
  document.body.classList.remove('bg-clear-day','bg-clear-night','bg-clouds','bg-rain','bg-snow','bg-thunder');
  document.body.classList.add(cls);
}

// Auto-apply if server sets <body data-owm-icon="10d">
(function applyBodyIcon() {
  const code = document.body?.dataset?.owmIcon;
  if (code) setBackgroundByIcon(code);
})();

/* ------------------ tiny UX touches ------------------ */
// Smooth scroll for horizontal lists on wheel + shift
$all('.hours, .hours-scroll').forEach(el => {
  el.addEventListener('wheel', (e) => {
    if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
      el.scrollLeft += e.deltaY;
    }
  }, { passive: true });
});