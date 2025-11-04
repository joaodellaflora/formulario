function normalizeTransportRaw(s){
  if (!s && s !== '') return '';
  try {
    // normalize diacritics, remove combining marks, convert NBSP to space, collapse whitespace
    let t = String(s || '');
    if (typeof t.normalize === 'function') t = t.normalize('NFKD');
    // remove combining diacritics
    t = t.replace(/[\u0300-\u036f]/g, '');
    // convert non-breaking spaces to regular spaces
    t = t.replace(/\u00A0/g, ' ');
    // remove control characters
    t = t.replace(/[\x00-\x1F\x7F]/g, '');
    // collapse whitespace
    t = t.replace(/\s+/g, '');
    return t.toLowerCase().trim();
  } catch (e) { return String(s || '').toLowerCase().trim(); }
}
const form = document.getElementById('tripForm');
const transport = document.getElementById('transport');
const originRow = document.getElementById('originRow');
const destinationRow = document.getElementById('destinationRow');
const distanceRow = document.getElementById('distanceRow');
const fuelRow = document.getElementById('fuelRow');
const vehicleSubtypeRow = document.getElementById('vehicleSubtypeRow');
const vehicleSubtypeEl = document.getElementById('vehicleSubtype');
const yearRow = document.getElementById('yearRow');
const balsaTypeRow = document.getElementById('balsaTypeRow');
const balsaTypeEl = document.getElementById('balsaType');
const airSection = document.getElementById('airSection');
const trainSection = document.getElementById('trainSection');
const hadConnections = document.getElementById('hadConnections');
const connectionsRow = document.getElementById('connectionsRow');
const connectionsEl = document.getElementById('connections');
const connectionsCountEl = document.getElementById('connectionsCount');
const connectionsListEl = document.getElementById('connectionsList');
const depCountryEl = document.getElementById('dep_country');
const depCityEl = document.getElementById('dep_city');
const depAirportEl = document.getElementById('dep_airport');
const arrCountryEl = document.getElementById('arr_country');
const arrCityEl = document.getElementById('arr_city');
const arrAirportEl = document.getElementById('arr_airport');
const usedAfterFlightEl = document.getElementById('usedAfterFlight');
const postFlightSection = document.getElementById('postFlightSection');
const postTransportEl = document.getElementById('post_transport');
const postFuelRow = document.getElementById('post_fuelRow');
const postFuelEl = document.getElementById('post_fuel');
const postYearRow = document.getElementById('post_yearRow');
const postYearEl = document.getElementById('post_year');
const postDistanceEl = document.getElementById('post_distance');
const usedAfterTrainEl = document.getElementById('usedAfterTrain');
const postTrainSection = document.getElementById('postTrainSection');
const postTransportTrainEl = document.getElementById('post_transport_train');
const postFuelTrainRow = document.getElementById('post_fuelTrainRow');
const postFuelTrainEl = document.getElementById('post_fuel_train');
const postYearTrainRow = document.getElementById('post_yearTrainRow');
const postYearTrainEl = document.getElementById('post_year_train');
const postDistanceTrainEl = document.getElementById('post_distance_train');
const metroSection = document.getElementById('metroSection');
const usedAfterMetroEl = document.getElementById('usedAfterMetro');
const postMetroSection = document.getElementById('postMetroSection');
const postTransportMetroEl = document.getElementById('post_transport_metro');
const postFuelMetroRow = document.getElementById('post_fuelMetroRow');
const postFuelMetroEl = document.getElementById('post_fuel_metro');
const postYearMetroRow = document.getElementById('post_yearMetroRow');
const postYearMetroEl = document.getElementById('post_year_metro');
const postDistanceMetroEl = document.getElementById('post_distance_metro');
const entriesTableBody = document.querySelector('#entriesTable tbody');

// cache for coords fetched from server
const _coordsCache = {};

function toRad(deg){ return deg * Math.PI / 180; }

function haversineKm(lat1, lon1, lat2, lon2){
  const R = 6371; // km
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
            Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}

async function getCoordsForIata(iata){
  if (!iata) return null;
  const key = String(iata).toUpperCase();
  if (_coordsCache[key] !== undefined) return _coordsCache[key];
  try {
    const res = await fetch('/api/coords?iata=' + encodeURIComponent(key));
    if (!res.ok) { _coordsCache[key] = null; return null; }
    const j = await res.json();
    // expected { lat: number, lon: number }
    if (j && typeof j.lat === 'number' && typeof j.lon === 'number') {
      _coordsCache[key] = { lat: j.lat, lon: j.lon };
      return _coordsCache[key];
    }
  } catch (e){ console.debug('Erro ao buscar coords', e); }
  _coordsCache[key] = null;
  return null;
}

// compute distance for currently selected flight (including connections)
async function computeTotalFlightDistance(){
  if (!form || form.transport.value !== 'Aéreo') return;
  // gather IATA codes in trip order
  const codes = [];
  try {
    const dep = depAirportEl && depAirportEl.value ? JSON.parse(depAirportEl.value) : null;
    const arr = arrAirportEl && arrAirportEl.value ? JSON.parse(arrAirportEl.value) : null;
    if (dep && dep.airport) codes.push(String(dep.airport).toUpperCase());
    if (hadConnections && hadConnections.checked && connectionsListEl){
      const rows = Array.from(connectionsListEl.querySelectorAll('.connections-list-row'));
      for (const r of rows){
        const sel = r.querySelector('.conn-airport');
        if (sel && sel.value){
          try { const obj = JSON.parse(sel.value); if (obj && obj.airport) codes.push(String(obj.airport).toUpperCase()); } catch(e){}
        }
      }
    }
    if (arr && arr.airport) codes.push(String(arr.airport).toUpperCase());
  } catch(e){ console.debug('Erro ao montar rota', e); }

  if (codes.length < 2){
    // nothing to compute
    if (form.distance) form.distance.value = '';
    return;
  }

  let total = 0;
  for (let i=0;i<codes.length-1;i++){
    const a = codes[i], b = codes[i+1];
    const ca = await getCoordsForIata(a);
    const cb = await getCoordsForIata(b);
    if (!ca || !cb){
      // if any leg missing coords, we can't compute full distance
      console.debug('Coords faltando para', a, b);
      if (form.distance) form.distance.value = '';
      return;
    }
    const d = haversineKm(ca.lat, ca.lon, cb.lat, cb.lon);
    total += d;
  }
  // format with 3 decimal places
  if (form.distance) form.distance.value = total.toFixed(3).toString();
}


const STORAGE_KEY = 'trip_entries_v1';

function shouldShowFuel(value) {
  const showFor = ['Automovel', 'Carro de aplicativo/taxi', 'Motocicleta'];
  return showFor.includes(value);
}

transport.addEventListener('change', () => {
  const v = transport.value;
  try {
    // mostrar seção de voo quando 'Aéreo' selecionado
    if (airSection) {
      if (v === 'Aéreo') airSection.style.display = '';
      else airSection.style.display = 'none';
    }
    // mostrar seção de trem quando 'Trem' selecionado
    if (trainSection) {
      if (v === 'Trem') trainSection.style.display = '';
      else trainSection.style.display = 'none';
    }
    // mostrar seção de metro quando 'Metro' selecionado
    if (metroSection) {
      if (v === 'Metro') metroSection.style.display = '';
      else metroSection.style.display = 'none';
    }
    // when hiding train section, reset its controls
    if (v !== 'Trem') {
      try {
        if (usedAfterTrainEl) usedAfterTrainEl.checked = false;
        if (postTrainSection) postTrainSection.style.display = 'none';
        if (postTransportTrainEl) postTransportTrainEl.value = '';
        if (postFuelTrainEl) postFuelTrainEl.value = '';
        if (postYearTrainEl) postYearTrainEl.value = '';
        if (postDistanceTrainEl) postDistanceTrainEl.value = '';
      } catch(e){}
    }
    // when hiding metro section, reset its controls
    if (v !== 'Metro') {
      try {
        if (usedAfterMetroEl) usedAfterMetroEl.checked = false;
        if (postMetroSection) postMetroSection.style.display = 'none';
        if (postTransportMetroEl) postTransportMetroEl.value = '';
        if (postFuelMetroEl) postFuelMetroEl.value = '';
        if (postYearMetroEl) postYearMetroEl.value = '';
        if (postDistanceMetroEl) postDistanceMetroEl.value = '';
      } catch(e){}
    }

  // control visibility/requirements for special transport types
    if (v === 'Aéreo') {
      // For flights we hide free-text origin/destination/distance (we use airport selectors)
      if (originRow) originRow.style.display = 'none';
      if (destinationRow) destinationRow.style.display = 'none';
      if (distanceRow) distanceRow.style.display = 'none';
      // remove required attributes so HTML5 validation won't block
      const o = document.getElementById('origin'); if (o) o.removeAttribute('required');
      const d = document.getElementById('destination'); if (d) d.removeAttribute('required');
      const dist = document.getElementById('distance'); if (dist) dist.removeAttribute('required');
    } else if (v === 'Trem' || v === 'Metro') {
      // For train: hide origin/destination (not needed), but keep distance visible and required
      if (originRow) originRow.style.display = 'none';
      if (destinationRow) destinationRow.style.display = 'none';
      if (distanceRow) distanceRow.style.display = '';
      const o = document.getElementById('origin'); if (o) o.removeAttribute('required');
      const d = document.getElementById('destination'); if (d) d.removeAttribute('required');
      const dist = document.getElementById('distance'); if (dist) dist.setAttribute('required','');
    } else {
      // default: show origin/destination/distance and make them required
      if (originRow) originRow.style.display = '';
      if (destinationRow) destinationRow.style.display = '';
      if (distanceRow) distanceRow.style.display = '';
      const o = document.getElementById('origin'); if (o) o.setAttribute('required','');
      const d = document.getElementById('destination'); if (d) d.setAttribute('required','');
      const dist = document.getElementById('distance'); if (dist) dist.setAttribute('required','');
    }

  if (shouldShowFuel(v)) {
  if (fuelRow) fuelRow.style.display = '';
  if (yearRow) yearRow.style.display = '';
      // mostrar e popular subtipo conforme transporte (se existir o elemento)
      if (vehicleSubtypeRow && vehicleSubtypeEl) {
        vehicleSubtypeRow.style.display = '';
        populateVehicleSubtype(v);
      }
    } else {
  if (fuelRow) fuelRow.style.display = 'none';
  if (yearRow) yearRow.style.display = 'none';
  if (balsaTypeRow) balsaTypeRow.style.display = 'none';
  const f = document.getElementById('fuel'); if (f) f.value = '';
  const y = document.getElementById('year'); if (y) y.value = '';
      if (vehicleSubtypeRow) vehicleSubtypeRow.style.display = 'none';
      if (vehicleSubtypeEl) vehicleSubtypeEl.value = '';
    }
  } catch (err){
    console.debug('Erro ao manejar mudança de transporte', err);
  }
});

function populateVehicleSubtype(transportValue){
  if (!vehicleSubtypeEl) return;
  // limpar
  vehicleSubtypeEl.innerHTML = '<option value="">-- selecione --</option>';
  if (transportValue === 'Automovel'){
    const opts = ['Motor flex','Motor híbrido','Motor híbrido plug-in','Não se aplica'];
    opts.forEach(o => {
      const opt = document.createElement('option'); opt.textContent = o; vehicleSubtypeEl.appendChild(opt);
    });
    // foco para facilitar o uso
    setTimeout(() => { try { vehicleSubtypeEl.focus(); } catch(e){} }, 0);
    console.debug('vehicleSubtype options:', Array.from(vehicleSubtypeEl.options).map(o=>o.text));
  } else if (transportValue === 'Motocicleta'){
    const opt = document.createElement('option'); opt.textContent = 'Não se aplica'; vehicleSubtypeEl.appendChild(opt);
    setTimeout(() => { try { vehicleSubtypeEl.focus(); } catch(e){} }, 0);
    console.debug('vehicleSubtype options:', Array.from(vehicleSubtypeEl.options).map(o=>o.text));
  } else {
    // outros meios: deixar como não aplicável
    const opt = document.createElement('option'); opt.textContent = 'Não se aplica'; vehicleSubtypeEl.appendChild(opt);
    setTimeout(() => { try { vehicleSubtypeEl.focus(); } catch(e){} }, 0);
    console.debug('vehicleSubtype options:', Array.from(vehicleSubtypeEl.options).map(o=>o.text));
  }
}

// show balsa type when transport is Balsa
transport.addEventListener('change', () => {
  try {
    if (transport.value === 'Balsa') {
      if (balsaTypeRow) balsaTypeRow.style.display = '';
    } else {
      if (balsaTypeRow) balsaTypeRow.style.display = 'none';
      if (balsaTypeEl) balsaTypeEl.value = '';
    }
  } catch (e) {
    console.debug('Erro ao controlar tipo de balsa', e);
  }
});

// conexões: mostrar textarea quando marcado
if (hadConnections) {
  hadConnections.addEventListener('change', () => {
    if (connectionsRow) connectionsRow.style.display = hadConnections.checked ? '' : 'none';
    // reset count and inputs when unchecked
    if (!hadConnections.checked) {
      if (connectionsCountEl) connectionsCountEl.value = '';
      if (connectionsListEl) connectionsListEl.innerHTML = '';
    }
    computeTotalFlightDistance().catch(()=>{});
  });
}

// criar N inputs de conexão quando a contagem muda
if (connectionsCountEl) {
  connectionsCountEl.addEventListener('change', () => {
    const v = Number(connectionsCountEl.value || 0);
    // limpar
    connectionsListEl.innerHTML = '';
    if (v > 0 && v <= 10) {
      for (let i = 1; i <= v; i++) {
        const div = document.createElement('div');
        div.className = 'row connections-list-row';
        const label = document.createElement('label');
        label.textContent = `Conexão ${i}`;
  const container = document.createElement('div');
  container.className = 'air-selects';
  // create selects for country / state / city / airport and wrap each in a row so they stack
  const cCountry = document.createElement('select'); cCountry.className = 'small-input conn-country';
  const cCity = document.createElement('select'); cCity.className = 'small-input conn-city';
  const cAirport = document.createElement('select'); cAirport.className = 'small-input conn-airport';
  const r1 = document.createElement('div'); r1.className='row'; const l1=document.createElement('label'); l1.className='small-label'; l1.textContent='País'; r1.appendChild(l1); r1.appendChild(cCountry);
  const r2 = document.createElement('div'); r2.className='row'; const l3=document.createElement('label'); l3.className='small-label'; l3.textContent='Município'; r2.appendChild(l3); r2.appendChild(cCity);
  const r3 = document.createElement('div'); r3.className='row'; const l4=document.createElement('label'); l4.className='small-label'; l4.textContent='Aeroporto'; r3.appendChild(l4); r3.appendChild(cAirport);
  container.appendChild(r1); container.appendChild(r2); container.appendChild(r3);
        div.appendChild(label);
        div.appendChild(container);
        connectionsListEl.appendChild(div);
  // attach cascading behavior
  attachCascadeToConnection(cCountry, cCity, cAirport);
      }
      // after creating connection selects, attempt to compute distance
      computeTotalFlightDistance().catch(()=>{});
    }
  });
}

// --- Cascade selects for airports: country -> city -> airport ---
async function fetchCountries(){
  const res = await fetch('/api/airports/countries');
  if (!res.ok) return [];
  return await res.json();
}

async function fetchCities(country){
  const url = '/api/airports/cities' + (country ? '?country=' + encodeURIComponent(country) : '');
  const res = await fetch(url);
  if (!res.ok) return [];
  return await res.json();
}

async function fetchAirportsFor(country, city){
  const url = '/api/airports/list?country=' + encodeURIComponent(country || '') + '&city=' + encodeURIComponent(city || '');
  const res = await fetch(url);
  if (!res.ok) return [];
  return await res.json();
}

function populateSelect(sel, items, placeholder){
  sel.innerHTML = '';
  const empty = document.createElement('option'); empty.value = ''; empty.textContent = placeholder || '-- selecione --';
  sel.appendChild(empty);
  items.forEach(it => {
    const o = document.createElement('option'); o.value = it; o.textContent = it; sel.appendChild(o);
  });
}

async function initAirportSelectors(){
  const countries = await fetchCountries();
  populateSelect(depCountryEl, countries, '-- país --');
  populateSelect(arrCountryEl, countries, '-- país --');
}

// attach cascade to a set of selects
function attachCascade(countrySel, citySel, airportSel){
  if (!countrySel || !citySel || !airportSel) return;
  countrySel.addEventListener('change', async () => {
    const country = countrySel.value;
    const cities = await fetchCities(country);
    populateSelect(citySel, cities, '-- município --');
    // clear airport
    airportSel.innerHTML = '';
    const empty = document.createElement('option'); empty.value = ''; empty.textContent = '-- aeroporto --'; airportSel.appendChild(empty);
  });
  citySel.addEventListener('change', async () => {
    const country = countrySel.value;
    const city = citySel.value;
    const airports = await fetchAirportsFor(country, city);
    // airports are objects; populate options with JSON as value
    airportSel.innerHTML = '';
    const empty = document.createElement('option'); empty.value = ''; empty.textContent = '-- aeroporto --'; airportSel.appendChild(empty);
    airports.forEach(a => {
      const o = document.createElement('option');
      o.value = JSON.stringify(a);
      // display: Airport name - City (Country)
      o.textContent = (a.airport || '') + (a.city ? (' - '+a.city) : '') + (a.country ? (' ('+a.country+')') : '');
      airportSel.appendChild(o);
    });
  });
}

function attachCascadeToConnection(cCountry, cCity, cAirport){
  // populate country list
  fetchCountries().then(countries => populateSelect(cCountry, countries, '-- país --'));
  attachCascade(cCountry, cCity, cAirport);
}

// wire main departure/arrival (no state select in current UI)
attachCascade(depCountryEl, depCityEl, depAirportEl);
attachCascade(arrCountryEl, arrCityEl, arrAirportEl);
initAirportSelectors();

// recompute distance when main airport selects change
if (depAirportEl) depAirportEl.addEventListener('change', () => { computeTotalFlightDistance().catch(()=>{}); });
if (arrAirportEl) arrAirportEl.addEventListener('change', () => { computeTotalFlightDistance().catch(()=>{}); });

// delegate connection airport changes
if (connectionsListEl) {
  connectionsListEl.addEventListener('change', (ev) => {
    if (ev.target && ev.target.matches && ev.target.matches('.conn-airport')){
      computeTotalFlightDistance().catch(()=>{});
    }
  });
}

// transporte pós-voo: mostrar seção quando marcado
if (usedAfterFlightEl) {
  usedAfterFlightEl.addEventListener('change', () => {
    if (postFlightSection) postFlightSection.style.display = usedAfterFlightEl.checked ? '' : 'none';
  });
}

// transporte pós-trem: mostrar seção quando marcado
if (usedAfterTrainEl) {
  usedAfterTrainEl.addEventListener('change', () => {
    if (postTrainSection) postTrainSection.style.display = usedAfterTrainEl.checked ? '' : 'none';
  });
}

// transporte pós-metro: mostrar seção quando marcado
if (usedAfterMetroEl) {
  usedAfterMetroEl.addEventListener('change', () => {
    if (postMetroSection) postMetroSection.style.display = usedAfterMetroEl.checked ? '' : 'none';
  });
}

// mostrar fuel/ year para o transporte pós-trem conforme seleção
if (postTransportTrainEl) {
  postTransportTrainEl.addEventListener('change', () => {
    const v = postTransportTrainEl.value;
    if (postFuelTrainRow) postFuelTrainRow.style.display = shouldShowFuel(v) ? '' : 'none';
    if (postYearTrainRow) postYearTrainRow.style.display = shouldShowFuel(v) ? '' : 'none';
    if (postFuelTrainEl && !shouldShowFuel(v)) postFuelTrainEl.value = '';
    if (postYearTrainEl && !shouldShowFuel(v)) postYearTrainEl.value = '';
  });
}

// mostrar fuel/ year para o transporte pós-metro conforme seleção
if (postTransportMetroEl) {
  postTransportMetroEl.addEventListener('change', () => {
    const v = postTransportMetroEl.value;
    if (postFuelMetroRow) postFuelMetroRow.style.display = shouldShowFuel(v) ? '' : 'none';
    if (postYearMetroRow) postYearMetroRow.style.display = shouldShowFuel(v) ? '' : 'none';
    if (postFuelMetroEl && !shouldShowFuel(v)) postFuelMetroEl.value = '';
    if (postYearMetroEl && !shouldShowFuel(v)) postYearMetroEl.value = '';
  });
}

// mostrar fuel/ year para o transporte pós-voo conforme seleção
if (postTransportEl) {
  postTransportEl.addEventListener('change', () => {
    const v = postTransportEl.value;
    if (postFuelRow) postFuelRow.style.display = shouldShowFuel(v) ? '' : 'none';
    if (postYearRow) postYearRow.style.display = shouldShowFuel(v) ? '' : 'none';
    if (postFuelEl && !shouldShowFuel(v)) postFuelEl.value = '';
    if (postYearEl && !shouldShowFuel(v)) postYearEl.value = '';
  });
}

// API-backed storage
async function loadEntries() {
  try {
    const res = await fetch('/api/entries');
    if (!res.ok) return [];
    return await res.json();
  } catch (e) {
    console.error('Erro ao carregar entradas do servidor', e);
    return [];
  }
}

async function saveEntry(entry) {
  try {
    const res = await fetch('/api/entries', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(entry)
    });
    if (!res.ok) {
      let txt = '';
      try { txt = await res.text(); } catch(e){}
      console.error('Erro ao salvar no servidor:', res.status, txt);
      alert('Erro ao salvar no servidor: ' + res.status + '\n' + txt);
      return null;
    }
    return await res.json();
  } catch (e) {
    console.error('Erro ao salvar no servidor', e);
    return null;
  }
}

// Note: cálculo foi removido do backend — o formulário apenas salva entradas.

async function renderTable() {
  const entries = await loadEntries();
  entriesTableBody.innerHTML = '';
  entries.forEach((e, idx) => {
    const tr = document.createElement('tr');
  const flightDepFull = e.flight && e.flight.departureAirport ? String(e.flight.departureAirport) : '';
  const flightArrFull = e.flight && e.flight.arrivalAirport ? String(e.flight.arrivalAirport) : '';
  const flightConFull = e.flight && e.flight.connections ? String(e.flight.connections) : '';
  // support postFlight or postTrain
  const postTransport = e.postFlight && e.postFlight.transport ? String(e.postFlight.transport) : (e.postTrain && e.postTrain.transport ? String(e.postTrain.transport) : (e.postMetro && e.postMetro.transport ? String(e.postMetro.transport) : ''));
  const postDistance = (e.postFlight && (e.postFlight.distance !== undefined) ? String(e.postFlight.distance) : (e.postTrain && (e.postTrain.distance !== undefined) ? String(e.postTrain.distance) : (e.postMetro && (e.postMetro.distance !== undefined) ? String(e.postMetro.distance) : '')));
  const truncate = (s, n=40) => s && s.length > n ? s.slice(0,n-1) + '…' : s;
  const flightDep = escapeHtml(truncate(flightDepFull,40));
  const flightArr = escapeHtml(truncate(flightArrFull,40));
  const flightCon = escapeHtml(truncate(flightConFull,40));
  const flightDepTitle = flightDepFull ? ` title="${escapeHtml(flightDepFull)}"` : '';
  const flightArrTitle = flightArrFull ? ` title="${escapeHtml(flightArrFull)}"` : '';
  const flightConTitle = flightConFull ? ` title="${escapeHtml(flightConFull)}"` : '';
    tr.innerHTML = `
      <td>${escapeHtml(e.origin)}</td>
      <td>${escapeHtml(e.destination)}</td>
      <td>${escapeHtml(e.distance)}</td>
        <td>${escapeHtml(e.tipo_frota_de_veiculos || '')}</td>
        <td>${escapeHtml(e.vehicleSubtype || '')}</td>
      <td>${escapeHtml(e.balsaType || '')}</td>
  <td>${escapeHtml(e.transport)}</td>
  <td>${escapeHtml(e.fuel || '')}</td>
  <td>${escapeHtml(e.year || '')}</td>
  <td${flightDepTitle}>${flightDep}</td>
  <td${flightArrTitle}>${flightArr}</td>
  <td${flightConTitle}>${flightCon}</td>
  <td>${escapeHtml(postTransport)}</td>
  <td>${escapeHtml(postDistance)}</td>
      <td><button data-idx="${idx}" class="delete">Excluir</button></td>
    `;
    entriesTableBody.appendChild(tr);
  });
}

function escapeHtml(s){
  if (!s && s !== 0) return '';
  return String(s)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

form.addEventListener('submit', async (ev) => {
  ev.preventDefault();
  const data = {
    origin: form.origin.value.trim(),
    destination: form.destination.value.trim(),
    distance: form.distance.value.trim(),
    transport: form.transport.value,
    fuel: form.fuel ? form.fuel.value : '',
    vehicleSubtype: form.vehicleSubtype ? form.vehicleSubtype.value : '',
    year: form.year ? form.year.value.trim() : '',
    balsaType: form.balsaType ? form.balsaType.value : ''
  };

  // se transporte for aéreo, incluir campos de voo
  if (data.transport === 'Aéreo') {
    // build flight object from cascading selects
  const depSelVal = depAirportEl && depAirportEl.value ? JSON.parse(depAirportEl.value) : null;
  const arrSelVal = arrAirportEl && arrAirportEl.value ? JSON.parse(arrAirportEl.value) : null;
  const depDisplay = depSelVal ? `${depSelVal.airport || ''} - ${depSelVal.city || ''} (${depSelVal.country || ''})` : '';
  const arrDisplay = arrSelVal ? `${arrSelVal.airport || ''} - ${arrSelVal.city || ''} (${arrSelVal.country || ''})` : '';
    data.flight = {
      departureAirport: depDisplay,
      arrivalAirport: arrDisplay,
      hadConnections: hadConnections ? Boolean(hadConnections.checked) : false,
      connections: ''
    };
    // se utilizou transporte após o voo, incluir objeto postFlight
    if (usedAfterFlightEl && usedAfterFlightEl.checked) {
      data.postFlight = {
        transport: postTransportEl ? postTransportEl.value : '',
        fuel: postFuelEl ? postFuelEl.value : '',
        year: postYearEl ? postYearEl.value : '',
        distance: postDistanceEl ? postDistanceEl.value : ''
      };
    }
    // build connections string from dynamic inputs if present
    if (data.flight.hadConnections && connectionsListEl) {
      const rows = Array.from(connectionsListEl.querySelectorAll('.connections-list-row'));
      const vals = [];
      for (const r of rows) {
        const aSel = r.querySelector('.conn-airport');
        if (aSel && aSel.value) {
          try { const obj = JSON.parse(aSel.value); vals.push(`${obj.airport || ''} - ${obj.city || ''} (${obj.country || ''})`); } catch(e){}
        }
      }
      data.flight.connections = vals.join(', ');
    }
  }

  // se transporte for trem, permitir pós-transporte similar ao aéreo
  if (data.transport === 'Trem') {
    if (usedAfterTrainEl && usedAfterTrainEl.checked) {
      data.postTrain = {
        transport: postTransportTrainEl ? postTransportTrainEl.value : '',
        fuel: postFuelTrainEl ? postFuelTrainEl.value : '',
        year: postYearTrainEl ? postYearTrainEl.value : '',
        distance: postDistanceTrainEl ? postDistanceTrainEl.value : ''
      };
    }
  }
  // se transporte for metro, permitir pós-transporte similar ao trem
  if (data.transport === 'Metro') {
    if (usedAfterMetroEl && usedAfterMetroEl.checked) {
      data.postMetro = {
        transport: postTransportMetroEl ? postTransportMetroEl.value : '',
        fuel: postFuelMetroEl ? postFuelMetroEl.value : '',
        year: postYearMetroEl ? postYearMetroEl.value : '',
        distance: postDistanceMetroEl ? postDistanceMetroEl.value : ''
      };
    }
  }

  // Fallback: se transporte for Trem/Metro e distância principal estiver vazia,
  // tentar preencher a partir do campo de pós-transporte (postTrain/postMetro/postFlight).
  // Isso corrige casos em que o usuário preencheu apenas o Km no bloco pós-transporte.
  try {
    const rawTransport = (data.transport || '').toString();
    const hasNormalize = typeof rawTransport.normalize === 'function';
    const tnorm = hasNormalize ? rawTransport.normalize('NFKD').replace(/[ -\u036f]/g, '').replace(/\s+/g,'').toLowerCase() : rawTransport.toLowerCase();
    if ((tnorm === 'trem' || tnorm === 'metro') && (!data.distance || data.distance === '')) {
      data.distance = (data.postTrain && data.postTrain.distance) || (data.postMetro && data.postMetro.distance) || (data.postFlight && data.postFlight.distance) || '';
      // trim string if any
      if (data.distance && typeof data.distance === 'string') data.distance = data.distance.trim();
    }
  } catch (e) {
    // ignore fallback errors
  }

  // marcação especial: Tipo da frota de Veiculos
  data.tipo_frota_de_veiculos = '';
  if (data.transport === 'Automovel' && data.vehicleSubtype === 'Flex'){
    if (data.fuel === 'Gasolina Automotiva (comercial)') data.tipo_frota_de_veiculos = 'Automóvel flex a gasolina';
    if (data.fuel === 'Etanol Hidratado') data.tipo_frota_de_veiculos = 'Automóvel flex a etanol';
  }
  // regra adicional: quando subtipo é 'Não se aplica' e transporte é Automovel,
  // considerar como 'Automóvel a gasolina' ou 'Automóvel a etanol' conforme combustível
  if (data.transport === 'Automovel' && data.vehicleSubtype === 'Não se aplica'){
    if (data.fuel === 'Gasolina Automotiva (comercial)') data.tipo_frota_de_veiculos = 'Automóvel a gasolina';
    if (data.fuel === 'Etanol Hidratado') data.tipo_frota_de_veiculos = 'Automóvel a etanol';
    if (data.fuel === 'Óleo Diesel (comercial)') data.tipo_frota_de_veiculos = 'Veículo comercial leve a Diesel';
  }
  // regra para motocicleta com subtipo 'Não se aplica' e combustível gasolina
  if (data.transport === 'Motocicleta' && data.vehicleSubtype === 'Não se aplica' && data.fuel === 'Gasolina Automotiva (comercial)'){
    data.tipo_frota_de_veiculos = 'Motocicleta flex a gasolina';
  }
  // regras para ônibus
  if (data.transport === 'Ônibus Municipal'){
    data.tipo_frota_de_veiculos = 'Ônibus municipal';
  }
  if (data.transport === 'Ônibus Intermunicipal'){
    data.tipo_frota_de_veiculos = 'Ônibus de viagem';
  }

  // regras para balsa (mapear tipo de balsa para tipo_frota_de_veiculos)
  if (data.transport === 'Balsa') {
    if (data.balsaType === 'Balsa de passageiros') data.tipo_frota_de_veiculos = 'Balsa de passageiros';
    if (data.balsaType === 'Balsa de veículos') data.tipo_frota_de_veiculos = 'Balsa de veículos';
    if (data.balsaType === 'Balsa híbrida veículos e passageiros') data.tipo_frota_de_veiculos = 'Balsa híbrida veículos e passageiros';
    // default if balsaType empty
    if (!data.tipo_frota_de_veiculos) data.tipo_frota_de_veiculos = 'Balsa';
  }

  // validation: different rules for Aéreo, Trem/Metro, and others
  try {
    const rawTransport = (data.transport || '').toString();
    const tnorm = normalizeTransportRaw(rawTransport);
    // flight: no free-text origin/destination/distance required
    if (tnorm === 'aereo' || rawTransport === 'Aéreo') {
      // ok
    } else if (tnorm === 'trem' || tnorm === 'metro') {
      if (data.distance === '') {
        // give more debugging info to help trace what the client is about to send
        console.error('Validação falhou: Trem/Metro sem distância', { transport: rawTransport, transport_norm: tnorm, distance: data.distance, postTrain: data.postTrain, postMetro: data.postMetro });
        alert(`Preencha a distância. (debug: transport='${rawTransport}', transport_norm='${tnorm}', distance='${data.distance}')`);
        return;
      }
    } else {
      if (!data.origin || !data.destination || data.distance === '') {
        console.error('Validação falhou: campos obrigatórios ausentes', { transport: rawTransport, transport_norm: tnorm, origin: data.origin, destination: data.destination, distance: data.distance });
        alert(`Preencha origem, destino e distância. (debug: transport='${rawTransport}', transport_norm='${tnorm}', origin='${data.origin}', destination='${data.destination}', distance='${data.distance}')`);
        return;
      }
    }
  } catch (err) {
    // fallback to previous strict checks
    if (data.transport === 'Aéreo') {
      // ok
    } else if (data.transport === 'Trem' || data.transport === 'Metro') {
      if (data.distance === '') { alert('Preencha a distância.'); return; }
    } else {
      if (!data.origin || !data.destination || data.distance === '') { alert('Preencha origem, destino e distância.'); return; }
    }
  }

  if (shouldShowFuel(data.transport) && !data.fuel) {
    alert('Por favor selecione o tipo de combustível.');
    return;
  }

  // validar subtipo quando aplicável
  const needSubtype = data.transport === 'Automovel' || data.transport === 'Motocicleta';
  if (needSubtype && !data.vehicleSubtype) {
    alert('Por favor selecione o Subtipo do veículo.');
    return;
  }

  // debug: log payload to browser console so we can inspect what is being sent
  // normalize key fields as a last-resort guard (helps if DOM values changed)
  try {
    data.transport = (data.transport || (document.getElementById('transport') && document.getElementById('transport').value) || '').trim();
    data.distance = (data.distance || (document.getElementById('distance') && document.getElementById('distance').value) || '').toString().trim();
  } catch(e){}
  try { console.debug('Submitting entry to /api/entries', data); console.debug('Submitting JSON body:', JSON.stringify(data)); } catch(e){}

  const saved = await saveEntry(data);
  if (!saved) { alert('Erro ao salvar no servidor'); return; }
  await renderTable();
  form.reset();
  transport.dispatchEvent(new Event('change'));
});

// cálculo removido — nenhum resultado exibido aqui

document.getElementById('clearForm').addEventListener('click', () => {
  form.reset();
  transport.dispatchEvent(new Event('change'));
});

document.getElementById('clearStorage').addEventListener('click', async () => {
  if (!confirm('Excluir todos os dados salvos?')) return;
  const res = await fetch('/api/entries', { method: 'DELETE' });
  if (!res.ok) { alert('Erro ao limpar dados'); return; }
  await renderTable();
});

entriesTableBody.addEventListener('click', async (ev) => {
  if (ev.target.matches('button.delete')) {
    const idx = Number(ev.target.dataset.idx);
    const res = await fetch(`/api/entries/${idx}`, { method: 'DELETE' });
    if (!res.ok) { alert('Erro ao excluir'); return; }
    await renderTable();
  }
});

document.getElementById('exportCsv').addEventListener('click', async () => {
  const entries = await loadEntries();
  if (!entries.length) { alert('Nenhuma entrada para exportar.'); return; }
  // separator ';' is often required for Excel in pt-BR locales
  const sep = ';';
  // base headers
  const headers = ['origin','destination','distance','tipo_frota_de_veiculos','vehicleSubtype','balsaType','transport','fuel','year','createdAt'];
  // include flight-related fields if any entry has flight/postFlight
  const hasFlight = entries.some(e => e.flight);
  const hasPostFlight = entries.some(e => e.postFlight);
  const hasPostTrain = entries.some(e => e.postTrain);
  const hasPostMetro = entries.some(e => e.postMetro);
  if (hasFlight) {
    headers.push('flight_departure','flight_arrival','flight_connections');
  }
  if (hasPostFlight || hasPostTrain || hasPostMetro) {
    headers.push('post_transport','post_distance');
  }

  function csvSafe(v){
    if (v === null || v === undefined) return '';
    const s = String(v);
    const esc = s.replace(/"/g, '""');
    return `"${esc}"`;
  }

  const rows = entries.map(e => {
    const r = [];
    for (const h of headers) {
      if (h === 'flight_departure') r.push(csvSafe(e.flight ? (e.flight.departureAirport||'') : ''));
      else if (h === 'flight_arrival') r.push(csvSafe(e.flight ? (e.flight.arrivalAirport||'') : ''));
      else if (h === 'flight_connections') r.push(csvSafe(e.flight ? (e.flight.connections||'') : ''));
  else if (h === 'post_transport') r.push(csvSafe(e.postFlight ? (e.postFlight.transport||'') : (e.postTrain ? (e.postTrain.transport||'') : (e.postMetro ? (e.postMetro.transport||'') : ''))));
  else if (h === 'post_distance') r.push(csvSafe(e.postFlight ? (e.postFlight.distance||'') : (e.postTrain ? (e.postTrain.distance||'') : (e.postMetro ? (e.postMetro.distance||'') : ''))));
      else r.push(csvSafe(e[h] ?? ''));
    }
    return r.join(sep);
  });
  // add UTF-8 BOM so Excel recognizes encoding
  const csv = '\uFEFF' + headers.join(sep) + '\n' + rows.join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `deslocamentos_${new Date().toISOString().slice(0,10)}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
});

// initial render
renderTable();
