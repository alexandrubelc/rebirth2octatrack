"""The page's side of rbs2ot, run by Pyodide: the template lives at /tpl/<name>, each song
converts into /out/work/<project>, goes into one zip (/out/rebirth2octatrack.zip) and is
deleted, so the in-browser file system never holds more than one project at a time."""
import contextlib
import io
import pathlib
import shutil
import zipfile

import rbs2ot as r

OUT = pathlib.Path("/out")
WORK = OUT / "work"
ZIP = OUT / "rebirth2octatrack.zip"
_names = set()


def reset():
    """A new batch: no zip, no names taken."""
    shutil.rmtree(OUT, ignore_errors=True)
    WORK.mkdir(parents=True)
    _names.clear()


def _name(filename):
    base = r.project_name(filename, WORK)
    name, n = base, 2
    while name in _names:
        tag = f" {n}"
        name, n = base[:16 - len(tag)] + tag, n + 1
    _names.add(name)
    return name


def convert(filename, rbs_path, template, bank=1, oct1=0, oct2=0, octknob=True, song=True):
    """-> {'ok', 'name', 'log'}; a converted project is added to the zip under its name."""
    if not WORK.is_dir():
        reset()
    o = r.Options(bank=int(bank), oct1=int(oct1), oct2=int(oct2), oct_knob=bool(octknob), song=bool(song))
    buf = io.StringIO()
    name = _name(filename)
    dest = WORK / name
    rbs = pathlib.Path(rbs_path)
    ok = False
    with contextlib.redirect_stdout(buf):
        try:
            if not 1 <= o.bank <= 15:
                raise ValueError("bank: 1..15")
            r.convert(rbs, pathlib.Path(template), dest, o)
            ok = True
        except SystemExit as e:
            print(e.code if isinstance(e.code, str) else f"stopped ({e.code})")
        except ValueError as e:
            print(f"rbs2ot: {e}")
        except Exception as e:                    # noqa: BLE001 -- one bad file must not stop the batch
            print(f"{type(e).__name__}: {e}")
    if ok:
        with zipfile.ZipFile(ZIP, "a", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for f in sorted(dest.rglob("*")):
                if f.is_file():
                    z.write(f, f"{name}/{f.relative_to(dest)}")
    else:
        _names.discard(name)
    shutil.rmtree(dest, ignore_errors=True)
    rbs.unlink(missing_ok=True)
    log = "\n".join(l for l in buf.getvalue().splitlines() if not l.startswith("0 .strd file"))
    return {"ok": ok, "name": name if ok else None, "log": log.strip()}


def check_template(template):
    """-> '' when the folder is an Octatrack project with the GARDEN layout in bank A, else why not."""
    t = pathlib.Path(template)
    if not (t / "project.work").is_file() or not (t / "bank01.work").is_file():
        return "nu e un proiect Octatrack (lipsesc project.work / bank01.work)"
    data = (t / "bank01.work").read_bytes()
    errs = r.mapping_errors(t, 1, {r.pattern_part(data, p) for p in range(16)})
    return "\n".join(errs)
