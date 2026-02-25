#!/usr/bin/env python3
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote

BASE_DIR = os.path.dirname(__file__)
DATA_FILE = os.path.join(BASE_DIR, "tools.json")
TYPES_FILE = os.path.join(BASE_DIR, "types.json")
DEFAULT_TYPES = ["tool", "repo", "doc", "service", "other"]

HTML = """<!doctype html>
<html lang='vi'>
<head>
  <meta charset='utf-8' />
  <meta name='viewport' content='width=device-width, initial-scale=1' />
  <title>Tool Library</title>
  <script src='https://cdn.tailwindcss.com'></script>
  <style>
    :root { color-scheme: dark; }
  </style>
</head>
<body class='bg-slate-950 text-slate-100 antialiased'>
  <div class='min-h-screen'>
    <header class='sticky top-0 z-40 border-b border-slate-800 bg-slate-950/85 backdrop-blur'>
      <div class='mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between'>
        <div>
          <h1 class='text-lg sm:text-xl font-semibold tracking-tight'>Tools Library</h1>
          <p class='hidden sm:block text-xs text-slate-400'>Dashboard style shadcn/ui · responsive</p>
        </div>
        <div class='flex items-center gap-2'>
          <button onclick='openCreate()' class='h-9 px-3 rounded-md bg-white text-slate-900 text-sm font-medium hover:bg-slate-200'>+ Add</button>
          <button onclick='openTypeManager()' class='h-9 px-3 rounded-md border border-slate-700 bg-slate-900 text-sm hover:bg-slate-800'>Types</button>
          <button onclick='exportJson()' class='hidden sm:inline-flex h-9 px-3 rounded-md border border-slate-700 bg-slate-900 text-sm hover:bg-slate-800'>Export</button>
          <label class='hidden sm:inline-flex h-9 px-3 rounded-md border border-slate-700 bg-slate-900 text-sm cursor-pointer hover:bg-slate-800'>Import
            <input type='file' id='importFile' accept='application/json' class='hidden' onchange='importJson(event)'>
          </label>
        </div>
      </div>
    </header>

    <main class='mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6 space-y-4'>
      <section id='kpi' class='grid grid-cols-2 lg:grid-cols-5 gap-3'></section>

      <section class='rounded-xl border border-slate-800 bg-slate-900 p-3 sm:p-4 space-y-3'>
        <div class='grid grid-cols-1 md:grid-cols-4 gap-2'>
          <input id='q' oninput='render()' placeholder='Search name, url, tag, notes...' class='h-10 px-3 rounded-md bg-slate-950 border border-slate-700 outline-none focus:ring-2 focus:ring-slate-600 md:col-span-2' />
          <select id='filterType' onchange='render()' class='h-10 px-3 rounded-md bg-slate-950 border border-slate-700'></select>
          <select id='sortBy' onchange='render()' class='h-10 px-3 rounded-md bg-slate-950 border border-slate-700'>
            <option value='name_asc'>Name A→Z</option>
            <option value='name_desc'>Name Z→A</option>
            <option value='type'>Type</option>
          </select>
        </div>
        <div id='chipBar' class='flex flex-wrap gap-2'></div>
      </section>

      <section class='rounded-xl border border-slate-800 bg-slate-900 overflow-hidden'>
        <div class='px-4 py-3 border-b border-slate-800 text-sm text-slate-400' id='stats'>0 item</div>

        <!-- Desktop table -->
        <div class='hidden md:block overflow-auto'>
          <table class='w-full text-sm min-w-[760px]'>
            <thead class='text-slate-300 bg-slate-900'>
              <tr>
                <th class='text-left px-4 py-3'>Name</th>
                <th class='text-left px-4 py-3'>Type</th>
                <th class='text-left px-4 py-3'>Tags</th>
                <th class='text-left px-4 py-3'>Link</th>
                <th class='text-right px-4 py-3'>Action</th>
              </tr>
            </thead>
            <tbody id='rows'></tbody>
          </table>
        </div>

        <!-- Mobile cards -->
        <div id='mobileRows' class='md:hidden p-3 space-y-2'></div>
      </section>
    </main>
  </div>

  <!-- Item Modal -->
  <div id='modalWrap' class='fixed inset-0 hidden items-center justify-center bg-black/60 p-4 z-50'>
    <div class='w-full max-w-2xl rounded-xl border border-slate-700 bg-slate-900 p-5'>
      <div class='flex items-center justify-between mb-4'>
        <h3 id='modalTitle' class='text-lg font-semibold'>Add item</h3>
        <button onclick='closeModal()' class='h-8 w-8 rounded-md border border-slate-700 hover:bg-slate-800'>✕</button>
      </div>
      <div class='grid sm:grid-cols-2 gap-2 mb-2'>
        <input id='m_name' placeholder='Name' class='h-10 px-3 rounded-md bg-slate-950 border border-slate-700' />
        <select id='m_type' class='h-10 px-3 rounded-md bg-slate-950 border border-slate-700'></select>
      </div>
      <input id='m_url' placeholder='URL' class='h-10 w-full px-3 rounded-md bg-slate-950 border border-slate-700 mb-2' />
      <input id='m_tags' placeholder='tags: ai, github, api' class='h-10 w-full px-3 rounded-md bg-slate-950 border border-slate-700 mb-2' />
      <textarea id='m_notes' rows='4' placeholder='Notes...' class='w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-700 mb-4'></textarea>
      <div class='flex items-center justify-between'>
        <button id='btnDelete' onclick='deleteCurrent()' class='h-9 px-3 rounded-md bg-rose-700 hover:bg-rose-600 hidden'>Delete</button>
        <div class='ml-auto flex gap-2'>
          <button onclick='closeModal()' class='h-9 px-3 rounded-md border border-slate-700 bg-slate-900 hover:bg-slate-800'>Cancel</button>
          <button onclick='saveModal()' class='h-9 px-3 rounded-md bg-white text-slate-900 hover:bg-slate-200'>Save</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Type Modal -->
  <div id='typeWrap' class='fixed inset-0 hidden items-center justify-center bg-black/60 p-4 z-50'>
    <div class='w-full max-w-lg rounded-xl border border-slate-700 bg-slate-900 p-5'>
      <div class='flex items-center justify-between mb-3'>
        <h3 class='text-lg font-semibold'>Manage types</h3>
        <button onclick='closeTypeManager()' class='h-8 w-8 rounded-md border border-slate-700 hover:bg-slate-800'>✕</button>
      </div>
      <div class='flex gap-2 mb-3'>
        <input id='newType' placeholder='New type (e.g. prompt)' class='h-10 flex-1 px-3 rounded-md bg-slate-950 border border-slate-700' />
        <button onclick='addType()' class='h-10 px-3 rounded-md bg-white text-slate-900 hover:bg-slate-200'>Add</button>
      </div>
      <div id='typeList' class='space-y-2 max-h-72 overflow-auto'></div>
    </div>
  </div>

<script>
let items = [];
let types = [];
let editingId = null;
const $ = (id) => document.getElementById(id);
const esc = (s='') => s.replace(/[&<>\"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

function normTags(v){
  if(!v) return [];
  if(Array.isArray(v)) return v.map(x=>String(x).trim()).filter(Boolean);
  return String(v).split(',').map(x=>x.trim()).filter(Boolean);
}

async function loadAll(){
  const [it,tp] = await Promise.all([
    fetch('/api/tools').then(r=>r.json()),
    fetch('/api/types').then(r=>r.json())
  ]);
  items = it; types = tp;
  syncTypeSelects();
  render();
}

function syncTypeSelects(){
  $('filterType').innerHTML = `<option value=''>All types</option>` + types.map(t=>`<option value='${esc(t)}'>${esc(t)}</option>`).join('');
  $('m_type').innerHTML = types.map(t=>`<option value='${esc(t)}'>${esc(t)}</option>`).join('');
}

function badge(type){
  const hue = (type||'').split('').reduce((a,c)=>a+c.charCodeAt(0),0)%360;
  return `<span class='text-xs px-2 py-1 rounded-full' style='background:hsl(${hue} 70% 34%)'>${esc(type||'other')}</span>`;
}

function getFiltered(){
  const q = $('q').value.trim().toLowerCase();
  const ft = $('filterType').value;
  let data = items.filter(i => {
    if (ft && (i.type||'other') !== ft) return false;
    if (!q) return true;
    const hay = [i.name, i.url, i.notes, i.type, (i.tags||[]).join(' ')].join(' ').toLowerCase();
    return hay.includes(q);
  });
  const s = $('sortBy').value;
  if (s === 'name_asc') data.sort((a,b)=>(a.name||'').localeCompare(b.name||''));
  if (s === 'name_desc') data.sort((a,b)=>(b.name||'').localeCompare(a.name||''));
  if (s === 'type') data.sort((a,b)=>(a.type||'').localeCompare(b.type||''));
  return data;
}

function drawKpi(filtered){
  const uniqTags = new Set(items.flatMap(i=>i.tags||[])).size;
  const topTypes = [...types].slice(0,2);
  const typeCounts = Object.fromEntries(types.map(t=>[t, items.filter(i=>i.type===t).length]));
  const cards = [
    {label:'Total', val:items.length},
    {label:topTypes[0]||'type#1', val:typeCounts[topTypes[0]]||0},
    {label:topTypes[1]||'type#2', val:typeCounts[topTypes[1]]||0},
    {label:'Tags', val:uniqTags},
    {label:'Visible', val:filtered.length},
  ];
  $('kpi').innerHTML = cards.map(c=>`
    <div class='rounded-xl border border-slate-800 bg-slate-900 p-4'>
      <div class='text-xs text-slate-400'>${esc(c.label)}</div>
      <div class='text-2xl font-semibold mt-1'>${c.val}</div>
    </div>
  `).join('');
}

function drawTagChips(){
  const all = [...new Set(items.flatMap(i=>i.tags||[]))].sort();
  $('chipBar').innerHTML = all.slice(0,30).map(t=>`<button onclick="$ ('q').value='${esc(t)}';render()" class='h-7 px-2 rounded-full border border-slate-700 bg-slate-950 hover:bg-slate-800 text-xs'>#${esc(t)}</button>`).join('').replace('$ ','$');
}

function render(){
  const data = getFiltered();
  $('stats').textContent = `${data.length} / ${items.length} item`;
  drawKpi(data);
  drawTagChips();

  $('rows').innerHTML = data.map(i=>`
    <tr class='border-t border-slate-800 hover:bg-slate-900/60'>
      <td class='px-4 py-3'>
        <div class='font-medium'>${esc(i.name||'')}</div>
        <div class='text-xs text-slate-400 max-w-sm truncate'>${esc(i.notes||'')}</div>
      </td>
      <td class='px-4 py-3'>${badge(i.type)}</td>
      <td class='px-4 py-3'>${(i.tags||[]).slice(0,4).map(t=>`<span class='inline-block mr-1 mb-1 text-xs px-2 py-0.5 rounded-full border border-slate-700 bg-slate-950'>#${esc(t)}</span>`).join('')}</td>
      <td class='px-4 py-3'><a href='${esc(i.url||'#')}' target='_blank' class='text-sky-400 hover:underline'>Open</a></td>
      <td class='px-4 py-3 text-right'><button onclick="openEdit('${i.id}')" class='h-8 px-3 rounded-md border border-slate-700 bg-slate-900 hover:bg-slate-800'>Edit</button></td>
    </tr>
  `).join('');

  $('mobileRows').innerHTML = data.map(i=>`
    <div class='rounded-lg border border-slate-800 bg-slate-950 p-3'>
      <div class='flex items-start justify-between gap-2'>
        <div>
          <div class='font-medium'>${esc(i.name||'')}</div>
          <div class='text-xs text-slate-400 mt-1'>${esc(i.notes||'')}</div>
        </div>
        ${badge(i.type)}
      </div>
      <div class='mt-2 flex flex-wrap gap-1'>${(i.tags||[]).slice(0,4).map(t=>`<span class='text-xs px-2 py-0.5 rounded-full border border-slate-700 bg-slate-900'>#${esc(t)}</span>`).join('')}</div>
      <div class='mt-3 flex items-center justify-between'>
        <a href='${esc(i.url||'#')}' target='_blank' class='text-sky-400 text-sm'>Open link</a>
        <button onclick="openEdit('${i.id}')" class='h-8 px-3 rounded-md border border-slate-700 bg-slate-900 hover:bg-slate-800 text-sm'>Edit</button>
      </div>
    </div>
  `).join('');
}

function openModal(){ $('modalWrap').classList.remove('hidden'); $('modalWrap').classList.add('flex'); }
function closeModal(){ $('modalWrap').classList.add('hidden'); $('modalWrap').classList.remove('flex'); }

function openCreate(){
  editingId = null;
  $('modalTitle').textContent = 'Add item';
  $('btnDelete').classList.add('hidden');
  $('m_name').value=''; $('m_type').value=types[0]||'other'; $('m_url').value=''; $('m_tags').value=''; $('m_notes').value='';
  openModal();
}

function openEdit(id){
  const i = items.find(x=>x.id===id); if(!i) return;
  editingId = id;
  $('modalTitle').textContent = 'Edit item';
  $('btnDelete').classList.remove('hidden');
  $('m_name').value=i.name||''; $('m_type').value=i.type||types[0]||'other'; $('m_url').value=i.url||''; $('m_tags').value=(i.tags||[]).join(','); $('m_notes').value=i.notes||'';
  openModal();
}

async function saveModal(){
  const payload = {
    id: editingId,
    name: $('m_name').value.trim(),
    type: $('m_type').value,
    url: $('m_url').value.trim(),
    tags: normTags($('m_tags').value),
    notes: $('m_notes').value.trim(),
  };
  if(!payload.name){ alert('Thiếu tên'); return; }
  await fetch('/api/tools', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
  closeModal();
  await loadAll();
}

async function deleteCurrent(){
  if(!editingId) return;
  if(!confirm('Xóa item này?')) return;
  await fetch('/api/tools/'+editingId, {method:'DELETE'});
  closeModal();
  await loadAll();
}

function openTypeManager(){ renderTypeList(); $('typeWrap').classList.remove('hidden'); $('typeWrap').classList.add('flex'); }
function closeTypeManager(){ $('typeWrap').classList.add('hidden'); $('typeWrap').classList.remove('flex'); }

function renderTypeList(){
  $('typeList').innerHTML = types.map(t=>`
    <div class='h-10 px-3 rounded-md border border-slate-700 bg-slate-950 flex items-center justify-between'>
      <span>${esc(t)}</span>
      <button onclick="removeType('${esc(t)}')" class='text-rose-400 text-sm hover:text-rose-300'>Delete</button>
    </div>
  `).join('');
}

async function addType(){
  const t = $('newType').value.trim().toLowerCase();
  if(!t) return;
  await fetch('/api/types', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({type:t})});
  $('newType').value='';
  await loadAll();
  renderTypeList();
}

async function removeType(t){
  if(!confirm(`Xóa type "${t}"?`)) return;
  await fetch('/api/types/'+encodeURIComponent(t), {method:'DELETE'});
  await loadAll();
  renderTypeList();
}

function exportJson(){
  const blob = new Blob([JSON.stringify(items,null,2)], {type:'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = 'tool-library.json'; a.click();
  URL.revokeObjectURL(a.href);
}

async function importJson(ev){
  const f = ev.target.files?.[0]; if(!f) return;
  try {
    const data = JSON.parse(await f.text());
    if(!Array.isArray(data)) throw new Error('JSON phải là array');
    await fetch('/api/import', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
    await loadAll();
    alert('Import xong');
  } catch(e){ alert('Import lỗi: '+e.message); }
  ev.target.value='';
}

loadAll();
</script>
</body>
</html>
"""


def read_json(path, fallback):
    if not os.path.exists(path):
        return fallback
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fallback


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_types():
    arr = read_json(TYPES_FILE, DEFAULT_TYPES)
    if not isinstance(arr, list) or not arr:
        arr = DEFAULT_TYPES
    arr = sorted(list(dict.fromkeys([str(x).strip().lower() for x in arr if str(x).strip()])))
    return arr or DEFAULT_TYPES


def save_types(arr):
    arr = sorted(list(dict.fromkeys([str(x).strip().lower() for x in arr if str(x).strip()])))
    write_json(TYPES_FILE, arr or DEFAULT_TYPES)


def normalize(item, types):
    tags = item.get("tags", [])
    if isinstance(tags, str):
        tags = [x.strip() for x in tags.split(',') if x.strip()]
    if not isinstance(tags, list):
        tags = []

    t = str(item.get("type", item.get("kind", ""))).strip().lower() or (types[0] if types else "other")
    if t not in types:
        t = types[0] if types else "other"

    return {
        "id": item.get("id"),
        "name": item.get("name", ""),
        "type": t,
        "url": item.get("url", ""),
        "tags": tags,
        "notes": item.get("notes", "")
    }


def load_data():
    return read_json(DATA_FILE, [])


def save_data(data):
    write_json(DATA_FILE, data)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code=200, ctype="text/html; charset=utf-8", body=""):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.wfile.write(body)

    def do_GET(self):
        p = urlparse(self.path)
        if p.path == "/":
            return self._send(200, body=HTML)
        if p.path == "/api/tools":
            return self._send(200, "application/json; charset=utf-8", json.dumps(load_data(), ensure_ascii=False))
        if p.path == "/api/types":
            return self._send(200, "application/json; charset=utf-8", json.dumps(load_types(), ensure_ascii=False))
        return self._send(404, body="Not found")

    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0"))
        payload = json.loads((self.rfile.read(n).decode("utf-8") if n else "{}"))

        if self.path == "/api/types":
            t = str(payload.get("type", "")).strip().lower()
            if not t:
                return self._send(400, "application/json", '{"ok":false}')
            arr = load_types()
            if t not in arr:
                arr.append(t)
                save_types(arr)
            return self._send(200, "application/json", '{"ok":true}')

        if self.path == "/api/import":
            if not isinstance(payload, list):
                return self._send(400, "application/json", '{"ok":false}')
            types = load_types()
            import uuid
            data = []
            for it in payload:
                x = normalize(it, types)
                if not x.get("id"):
                    x["id"] = str(uuid.uuid4())[:8]
                data.append(x)
            save_data(data)
            return self._send(200, "application/json", '{"ok":true}')

        if self.path != "/api/tools":
            return self._send(404, body="Not found")

        types = load_types()
        data = load_data()
        tid = payload.get("id")
        if tid:
            for i, it in enumerate(data):
                if it.get("id") == tid:
                    merged = it.copy()
                    merged.update(payload)
                    data[i] = normalize(merged, types)
                    save_data(data)
                    return self._send(200, "application/json", '{"ok":true}')

        import uuid
        item = normalize(payload, types)
        item["id"] = str(uuid.uuid4())[:8]
        data.append(item)
        save_data(data)
        return self._send(200, "application/json", '{"ok":true}')

    def do_DELETE(self):
        p = urlparse(self.path)
        if p.path.startswith('/api/tools/'):
            tid = unquote(p.path.split('/')[-1])
            data = [x for x in load_data() if x.get('id') != tid]
            save_data(data)
            return self._send(200, "application/json", '{"ok":true}')

        if p.path.startswith('/api/types/'):
            t = unquote(p.path.split('/')[-1]).strip().lower()
            arr = load_types()
            if t in arr and len(arr) > 1:
                arr = [x for x in arr if x != t]
                save_types(arr)
                data = load_data()
                fallback = arr[0]
                changed = False
                for it in data:
                    if it.get('type') not in arr:
                        it['type'] = fallback
                        changed = True
                if changed:
                    save_data(data)
            return self._send(200, "application/json", '{"ok":true}')

        return self._send(404, body='Not found')


if __name__ == "__main__":
    os.makedirs(BASE_DIR, exist_ok=True)
    if not os.path.exists(TYPES_FILE):
        save_types(DEFAULT_TYPES)

    types = load_types()
    data = load_data()
    migrated = []
    changed = False
    for it in data:
        if 'kind' in it or 'category' in it or 'type' not in it:
            changed = True
        migrated.append(normalize(it, types))
    if changed:
        save_data(migrated)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8888)
    args = parser.parse_args()

    print(f"Tool Library running at http://{args.host}:{args.port}")
    HTTPServer((args.host, args.port), Handler).serve_forever()
