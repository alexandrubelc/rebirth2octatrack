// ReBirth -> Octatrack in the browser: Pyodide runs py/rbs2ot.py (the same converter as the
// command line), the template folder is kept in IndexedDB, every converted project goes into
// one zip that the page hands back.
"use strict";

const PY_FILES = ["ot_bank.py", "ot_project.py", "rbs2ot.py", "web.py"];
const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/";
const $ = id => document.getElementById(id);
let py = null, web = null, template = null, converted = 0, busy = false;

// ---- IndexedDB: the template, one record --------------------------------------------
function db() {
  return new Promise((res, rej) => {
    const q = indexedDB.open("rebirth2octatrack", 1);
    q.onupgradeneeded = () => q.result.createObjectStore("kv");
    q.onsuccess = () => res(q.result);
    q.onerror = () => rej(q.error);
  });
}
async function kvGet(k) {
  try {
    const d = await db();
    return await new Promise(res => {
      const q = d.transaction("kv").objectStore("kv").get(k);
      q.onsuccess = () => res(q.result || null);
      q.onerror = () => res(null);
    });
  } catch (e) { return null; }
}
async function kvSet(k, v) {
  try {
    const d = await db();
    await new Promise(res => {
      const t = d.transaction("kv", "readwrite");
      t.objectStore("kv").put(v, k);
      t.oncomplete = res; t.onerror = res;
    });
  } catch (e) { /* the template is just not remembered */ }
}

// ---- the template ---------------------------------------------------------------------
// files: [[path inside the project folder, ArrayBuffer]], name: the project's folder name
async function useTemplate(name, files, remember) {
  py.runPython("import shutil; shutil.rmtree('/tpl', ignore_errors=True)");
  const root = `/tpl/${name}`;
  for (const [path, buf] of files) {
    const full = `${root}/${path}`;
    py.FS.mkdirTree(full.slice(0, full.lastIndexOf("/")));
    py.FS.writeFile(full, new Uint8Array(buf));
  }
  const why = web.check_template(root);
  const st = $("tplState");
  if (why) {
    template = null;
    st.className = "state bad";
    st.textContent = `${name}: ${why}`;
  } else {
    template = root;
    st.className = "state ok";
    st.textContent = `${name} (${files.length} fișiere) — OK`;
    if (remember) await kvSet("template", {name, files});
  }
  refresh();
}

async function pickTemplate(fileList) {
  const all = [...fileList];
  if (!all.length) return;
  const top = all[0].webkitRelativePath.split("/")[0];
  const files = [];
  for (const f of all) {
    const rel = f.webkitRelativePath.split("/").slice(1).join("/");
    if (!rel || rel.split("/").some(p => p.startsWith("."))) continue;   // .DS_Store and friends
    files.push([rel, await f.arrayBuffer()]);
  }
  await useTemplate(top, files, true);
}

// ---- converting -----------------------------------------------------------------------
function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}

async function convertFiles(files) {
  files = files.filter(f => /\.rbs$/i.test(f.name));
  if (!files.length || !template || busy) return;
  busy = true; refresh();
  $("results").hidden = false;
  const opts = [+$("bank").value, +$("oct1").value, +$("oct2").value, $("octknob").checked, $("song").checked];
  for (const f of files) {
    const item = el("div", "item"), head = el("div", "head"), st = el("span", "st wait", "…");
    const dest = el("span", "dest");
    head.append(st, el("span", "name", f.name), dest);
    item.append(head);
    $("list").prepend(item);
    await new Promise(r => setTimeout(r, 20));          // let the row draw before the work
    let r;
    try {
      py.FS.mkdirTree("/in");
      py.FS.writeFile("/in/song.rbs", new Uint8Array(await f.arrayBuffer()));
      const res = web.convert(f.name, "/in/song.rbs", template, ...opts);
      r = res.toJs({dict_converter: Object.fromEntries});
      res.destroy();
    } catch (e) {
      r = {ok: false, name: null, log: String(e)};
    }
    st.className = "st " + (r.ok ? "ok" : "bad");
    st.textContent = r.ok ? "OK" : "EROARE";
    if (r.ok) { dest.textContent = `→ ${r.name}`; converted++; }
    const det = el("details");
    det.append(el("summary", null, r.ok ? "detalii" : r.log.split("\n").pop()), el("pre", null, r.log));
    if (!r.ok) det.open = false;
    item.append(det);
    refresh();
  }
  busy = false; refresh();
}

function download() {
  const data = py.FS.readFile("/out/rebirth2octatrack.zip");
  const a = el("a");
  a.href = URL.createObjectURL(new Blob([data], {type: "application/zip"}));
  a.download = "rebirth2octatrack.zip";
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 10000);
}

function clearAll() {
  web.reset();
  converted = 0;
  $("list").replaceChildren();
  $("results").hidden = true;
  refresh();
}

function refresh() {
  const ready = py && template && !busy;
  $("drop").className = ready ? "" : "off";
  $("pickTpl").disabled = !py || busy;
  $("download").disabled = !converted || busy;
  $("count").textContent = converted ? `${converted} proiect${converted === 1 ? "" : "e"} în arhivă` : "";
}

// ---- wiring -----------------------------------------------------------------------------
$("pickTpl").onclick = () => $("tplInput").click();
$("tplInput").onchange = e => pickTemplate(e.target.files);
const drop = $("drop"), pick = $("pick");
drop.onclick = () => { if (!drop.classList.contains("off")) pick.click(); };
pick.onchange = () => { convertFiles([...pick.files]); pick.value = ""; };
drop.ondragover = e => { e.preventDefault(); if (!drop.classList.contains("off")) drop.classList.add("on"); };
drop.ondragleave = () => drop.classList.remove("on");
drop.ondrop = e => { e.preventDefault(); drop.classList.remove("on"); convertFiles([...e.dataTransfer.files]); };
$("download").onclick = download;
$("clear").onclick = clearAll;

(async () => {
  try {
    py = await loadPyodide({indexURL: PYODIDE_URL});
    py.FS.mkdirTree("/app");
    for (const f of PY_FILES) {
      const r = await fetch(`py/${f}`);
      if (!r.ok) throw new Error(`py/${f}: ${r.status}`);
      py.FS.writeFile(`/app/${f}`, await r.text());
    }
    py.runPython("import sys; sys.path.insert(0, '/app')");
    web = py.pyimport("web");
    web.reset();
    $("status").textContent = "Gata. Motorul rulează local, în browser.";
    const saved = await kvGet("template");
    if (saved) await useTemplate(saved.name, saved.files, false);
  } catch (e) {
    $("status").textContent = `Nu s-a putut porni motorul Python: ${e}`;
  }
  refresh();
})();
