#!/usr/bin/env python3
"""rbs2ot -- a ReBirth RB-338 2.0 song (.rbs) into an Octatrack GARDEN project.

    python3 tools/hw/rbs2ot.py show SONG.rbs [--pattern A1]
    python3 tools/hw/rbs2ot.py convert SONG.rbs TEMPLATE_DIR DEST_DIR [--bank N]
            [--oct1 K] [--oct2 K] [--bass-vol V] [--keep-knobs] [--no-oct] [--no-song] [--arr N] [--no-check]
    python3 tools/hw/rbs2ot.py check DEST_DIR SONG.rbs [same options]
    python3 tools/hw/rbs2ot.py serve [--template DIR] [--out DIR] [--port 8338] [--no-browser]
    python3 tools/hw/rbs2ot.py selftest

serve: a page on 127.0.0.1 -- drop .rbs files in, each becomes a project named after
it in --out (default: the template's folder, so ../AUDIO resolves), with the options
above; the template defaults to ~/Desktop/Octatrack/ReBirth.

The song's patterns land in the GARDEN engines (Alex, 28 Oct 2026):

    T1  ACID     (FLEX, sample ACID*)   the first TB-303
    T2  BASS 101 (FLEX, sample BASS*)   the second TB-303
    T5  Rhythm 9 BD (FLEX, BD.wav)      909 bass drum
    T6  Rhythm 9 SD (FLEX, SD.wav)      909 snare
    T7  Rhythm 9 OH (FLEX, OH.wav)      909 CLOSED hat -- GARDEN has no closed hat:
                                        keep T7's DEC low in the template
    T8  Rhythm 9 OH (FLEX, OH.wav)      909 open hat
    T3, T4                              never touched

ReBirth's 32 patterns a machine (A1..D8) go to two Octatrack banks: A1..B8 to
patterns 1..16 of --bank (default 1 = bank A), C1..D8 to patterns 1..16 of the
next bank. OT pattern i plays 303#1 i + 303#2 i + 909 i. Every pattern of the
six tracks is rewritten (an empty ReBirth pattern clears the track).

STEPS (M1). The 303 step is written as ACID GEN writes it (Re:Phase
octatrick-acid/OCTATRICK-ACID-GEN-PLAN.md): a trig with a PTCH lock (flat 5,
raw 40 + 12*oct + note + TUNE's semitones, raw 64 = C4: Re:Phase's MIDI 36 +
12*oct + note); a slide on step s makes step s+1 a trigless lock carrying its
PTCH lock (the GARDEN gate holds a note into a trigless lock on the next step,
GARDEN29+); an accent is an ACC lock = the song's ACCENT knob (flat 8) on
ACID, and an AMP VOL lock = the Part's VOL + 16 * ACCENT / 127 (flat 15) on
BASS, which has no accent of its own. A 909 hit is a trig, its accent an ACC
lock 127 (flat 8, Rhythm 9's LFO slot 2). A pattern with a track shorter than
16 steps is put in SCALE MODE PER TRACK (master 16 / 1X; the mode byte is
inferred from PARAM_PAGES.md's RAM offsets -- check it on the unit).

KNOBS (M2). The 303 knobs (TUNE CUTOFF RESO ENVMOD DECAY ACCENT, the "303 "
chunk's bytes 2..7) go into the Part's PLAYBACK page, each through Re:Phase's
own law into a physical value and back through the GARDEN engine's law:
  ACID: CUT = Re:Phase's cutoff (80 + 5920 b/127 Hz) on 20 * 1000^(i/127) Hz;
        ENV = the peak (cutoff + 7000 b/127 Hz, max 18 kHz) on the same table,
        less CUT; DEC = the sweep's time constant (decay / 3, decay = 0.02 +
        1.78 b/127 s) on 5 ms * 400^(i/127); RES = the byte (both 1 + 27 r/127).
  BASS: Re:Phase's .sh101 path: cutoff max(800, hz) * 1.5 (<= 10 kHz) on 120 *
        100^(i/127) Hz; the peak + 0.9 env (<= 16 kHz); DEC decay / 2; RES =
        127 q / 28 (q = 1 + 27 b/127).
  TUNE: the nearest semitone of Re:Phase's measured law (66 = in tune, +-1
        octave at the ends): its whole octaves, and --octN, go to GARDEN36's OCT
        knob (LFO slot 1, -3..+3, raw 32 = 0), the other semitones onto every
        PTCH lock, the cents onto FINE (ACID: LFO slot 5; BASS: GARDEN36's LFO
        slot 4). --no-oct (GARDEN35 and older): all semitones onto the locks,
        and BASS's cents are lost (its LFO slot 4 is LFO 2's depth there).
  PTCH: the Part's PTCH (PLAYBACK slot 5) := 64 = 0 on T1 / T2 (stock RTIM 79
        read +15 semitones there).
  FINE: ACID's LFO slot 5 (cents, 64 = 0) takes the cents left over -- and is
        always written: the Part's stock DEP3 byte 0 there reads -64 cents.
The Part's ACC (LFO slot 2) is set to 0 on T1 and T5..T8 so an unaccented
step is unaccented (the stock LFO default 32 sat there). WAVE / SUB, BASS's
LFO and the drums' sound are the template's. --keep-knobs leaves the Part as
it is. Every Part a written pattern plays is written with its saved copy.

Dropped, and counted in the summary: a slide from the last step into step 1
(across the loop -- ACID GEN never writes one either), an accent on a slide
target (it has no note start, ACC is read at the start), every 909 voice but
BD SD CH OH, the 909's accent lane and knobs, shuffle, the song's mutes and automation.

SONG (M3). The song's chains (TRKL: 303#1, 303#2, 909) become arrangement --arr (default
1): a row a run of bars on one OT pattern (REP <= 64), then LOOP 000/inf. A bar whose three
machines play one slot plays that slot's pattern in banks --bank / --bank+1; every other
combination gets a pattern of its own (the three machines' patterns) from bank --bank+2 on,
with bank --bank's parts. --no-song writes no arrangement. Turn the arranger on on the unit
(MKI: FUNC + PATTERN).

The TEMPLATE is a project saved on the unit, running GARDEN, with the
markers in FLEX slots and T1/T2/T5..T8 of bank --bank's parts on them (the
table above). convert copies it to DEST (never in place), copies bank N's
eight part records into bank N+1 when N+1's tracks do not match, writes the
patterns, knobs and tempo, and refuses if any byte outside what it writes
changed. Checksums as ot_project._bank_write; .work and .strd both.

Set on the unit for a faithful line: PROJECT > CONTROL > SEQUENCER SCALE OFF
and ACID GEN's ROOT C (ACID and BASS snap and transpose every PTCH), and
SEQUENCER GLIDE > 0 with the track's LEG on for the slides to glide.

Format sources: Re:Phase RephaseCore/IO/RBSImport.swift (the RB40 layout, the
knob laws) and Voices/TB303Voice.swift (the filter envelope),
octatrick-acid/poly.s (ac_cutoff_tab, bs_cut_tab, ac_decay_tab, the RES
laws), tools/hw/ot_bank.py (the TRAC record), ot_project.py (parts,
checksum), docs/firmware/PARAM_PAGES.md section 5 (the Part's page arrays:
the file holds them 9 bytes after the RAM offsets, as the machine byte).
"""
import math
import pathlib
import re
import shutil
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass, field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ot_bank as ob  # noqa: E402
import ot_project as op  # noqa: E402

# ---- the .rbs (ReBirth 2.0, a "CAT " container of "RB40") ------------------
RB_SLOTS = [f"{'ABCD'[p // 8]}{p % 8 + 1}" for p in range(32)]
CHUNK303 = 1097                      # a "303 " chunk's length
PAT303 = 34                          # shuffle, length, 16 x (note, flags)
DRUM_HEAD, PAT909 = 33, 194          # "909 ": steps of pattern p at 33 + 194p
STEP909 = 12                         # col 0 the accent lane, 1..11 the voices
V909 = {"BD": 1, "SD": 2, "LT": 3, "MT": 4, "HT": 5, "RS": 6, "CP": 7, "CH": 8, "OH": 9, "CC": 10, "RC": 11}
F_SLD, F_ACC, F_UP, F_DOWN, F_REST = 1, 2, 4, 8, 16
TUNE_CENTER, TUNE_SPAN = 66, 1200    # RBSImport.tuneCents: 65 / 130 / 260 Hz at min / centre / max


@dataclass
class Step303:
    ni: int                          # 0..12 (12 = the next C, real files carry it)
    oct: int                         # 0 down, 1 normal, 2 up
    acc: bool
    sld: bool
    rest: bool


@dataclass
class Pattern303:
    shuffle: int
    length: int
    steps: list


@dataclass
class Pattern909:
    shuffle: int
    length: int
    steps: list                      # 16 x 12 raw bytes: 0 off, 1 on, 2 accent


@dataclass
class Knobs303:
    tune: int
    cut: int
    res: int
    env: int
    dec: int
    acc: int


@dataclass
class Song:
    synth: list                      # one list of 32 Pattern303 per "303 " chunk
    knobs: list                      # one Knobs303 per "303 " chunk
    drums: list | None               # 32 Pattern909, or None without a "909 " chunk
    tempo: float | None
    bars: list | None = None         # the song: (303#1, 303#2, 909) pattern a bar, or None (no chain)


def _length(b):
    return b if 1 <= b <= 16 else 16


def parse_rbs(data: bytes) -> Song:
    if data[:4] == b"MThd":
        raise ValueError("a ReBirth 1.5 song (or a MIDI file): only ReBirth 2.0 (RB40) is decoded")
    if data[:4] != b"CAT " or data[8:12] != b"RB40":
        raise ValueError("not a ReBirth 2.0 song (no CAT/RB40 header)")
    synth, knobs = [], []
    i = data.find(b"303 ")
    while i >= 0:
        if int.from_bytes(data[i + 4:i + 8], "big") == CHUNK303 and i + 8 + CHUNK303 <= len(data):
            knobs.append(Knobs303(*data[i + 10:i + 16]))
            pay = data[i + 17:i + 8 + CHUNK303]
            bank = []
            for p in range(32):
                b = p * PAT303
                steps = []
                for s in range(16):
                    ni, fl = pay[b + 2 + 2 * s], pay[b + 3 + 2 * s]
                    oct_ = 0 if fl & F_DOWN else (2 if fl & F_UP else 1)
                    steps.append(Step303(ni, oct_, bool(fl & F_ACC), bool(fl & F_SLD), bool(fl & F_REST)))
                bank.append(Pattern303(pay[b], _length(pay[b + 1]), steps))
            synth.append(bank)
        i = data.find(b"303 ", i + 1)
    drums = None
    i = data.find(b"909 ")
    if i >= 0:
        ch = data[i + 8:]
        drums = []
        for p in range(32):
            b = DRUM_HEAD + p * PAT909
            if b + 16 * STEP909 > len(ch):
                break
            drums.append(Pattern909(ch[b - 2], _length(ch[b - 1]),
                                    [list(ch[b + s * STEP909:b + (s + 1) * STEP909]) for s in range(16)]))
    tempo = None
    i = data.find(b"GLOB")
    if i >= 0 and i + 14 <= len(data):
        bpm = int.from_bytes(data[i + 11:i + 14], "big") / 1000
        tempo = bpm if 20 <= bpm <= 1000 else None
    return Song(synth, knobs, drums, tempo, parse_song(data))


# ---- the song (TRKL / TRAK): Re:Phase RBSImport.parseSongArrangement ---------------
# TRKL (no length of its own) holds 9 TRAK chunks; TRAK2 / TRAK3 / TRAK5 are the chains of
# 303#1 / 303#2 / the 909 (TRAK4 the 808's). A chain is a u32 record count, then records
# [VLQ duration][subtag][value], the first `base` of them the track's current values; a
# subtag 0x01 record selects pattern `value` (0..31) and its VLQ is 32 x the bars the
# pattern BEFORE it played. Records run oldest first; the last loops back to bar 0, so it
# names the first pattern (decoded from Alex's controlled ReBirth saves, Sep 2026).
TRAK_BASE = {1: 9, 2: 9, 4: 30}      # TRAK index -> its current-value preamble records


def trak_chunks(data: bytes):
    i = data.find(b"TRKL")
    if i < 0:
        return None
    pos, out = i + 4, []
    while len(out) < 9 and data[pos:pos + 4] == b"TRAK":
        n = int.from_bytes(data[pos + 4:pos + 8], "big")
        if pos + 8 + n > len(data):
            break
        out.append(data[pos + 8:pos + 8 + n])
        pos += 8 + n + (n & 1)
    return out if len(out) == 9 else None


def chain(content: bytes, base: int):
    """-> the per-bar pattern list of one TRAK (index = bar)."""
    if len(content) < 4:
        return []
    total, i, k, recs = int.from_bytes(content[:4], "big"), 4, 0, []
    while i < len(content) and k < total:
        value = n = 0
        while i + n < len(content):
            byte = content[i + n]
            value = value << 7 | byte & 0x7F
            n += 1
            if not byte & 0x80 or n >= 4:
                break
        if i + n + 2 > len(content):
            break
        if k >= base and content[i + n] == 0x01:
            recs.append((min(31, content[i + n + 1]), max(1, value // 32)))
        i += n + 2
        k += 1
    if not recs:
        return []
    bars = [recs[-1][0]] * recs[0][1]
    for j in range(len(recs) - 1):
        bars += [recs[j][0]] * recs[j + 1][1]
    return bars


def parse_song(data: bytes):
    traks = trak_chunks(data)
    if not traks:
        return None
    a, b, d = (chain(traks[t], TRAK_BASE[t]) for t in (1, 2, 4))
    n = max(len(a), len(b), len(d))
    if not n:
        return None

    def at(x, i):
        return x[min(i, len(x) - 1)] if x else 0
    return [(at(a, i), at(b, i), at(d, i)) for i in range(n)]


def has_content(p):
    if isinstance(p, Pattern303):
        return any(not s.rest for s in p.steps[:p.length])
    return any(st[v] for st in p.steps[:p.length] for v in (V909["BD"], V909["SD"], V909["CH"], V909["OH"]))


# ---- the knob laws -------------------------------------------------------------
def tune_cents(b):
    if b <= TUNE_CENTER:
        return (b - TUNE_CENTER) / TUNE_CENTER * TUNE_SPAN
    return (b - TUNE_CENTER) / (127 - TUNE_CENTER) * TUNE_SPAN


def tune_semitones(b):
    return round(tune_cents(b) / 100)


OCT_RAW0 = 32                        # GARDEN36's OCT (LFO slot 1): raw 29..35 = -3..+3 octaves


def octave_split(tune_byte, opt_oct, knobs=True, oct_knob=True):
    """-> (OCT knob octaves, semitones on the PTCH locks). TUNE's whole octaves and
    --octN go to the OCT knob (-3..+3, the rest spills into the locks); TUNE's other
    semitones stay on the locks. Without the knob: everything on the locks."""
    semis = tune_semitones(tune_byte) if knobs else 0
    if not (knobs and oct_knob):
        return 0, semis + 12 * opt_oct
    whole = int(semis / 12)
    want = whole + opt_oct
    k = max(-3, min(3, want))
    return k, semis - 12 * whole + 12 * (want - k)


def fine_raw(b):
    """ACID's FINE (LFO slot 5, cents, raw 64 = 0): what the semitones leave over."""
    return _clamp(64 + tune_cents(b) - 100 * tune_semitones(b))


def _clamp(v):
    return max(0, min(127, int(round(v))))


def _index(hz, base, ratio):
    """The index i of a table hz = base * ratio^(i/127)."""
    return _clamp(127 * math.log(max(hz, 1e-6) / base) / math.log(ratio))


def _dec(tau):
    return _index(tau, 0.005, 400)                 # ac_decay_tab: time constant 5 ms * 400^(i/127)


def _rephase(k: Knobs303):
    """Re:Phase's RBSImport.mapKnob ranges: cutoff, env (Hz), decay (s), reso (q)."""
    return (80 + k.cut / 127 * 5920, k.env / 127 * 7000, 0.02 + k.dec / 127 * 1.78, 1 + 27 * k.res / 127)


def acid_page(k: Knobs303):
    cut, env, decay, _ = _rephase(k)
    c = _index(cut, 20, 1000)                      # ac_cutoff_tab: 20 * 1000^(i/127)
    peak = _index(min(18000, cut + env), 20, 1000)
    return {0: c, 1: k.res, 3: _clamp(peak - c), 4: _dec(decay / 3)}


def bass_page(k: Knobs303):
    cut, env, decay, q = _rephase(k)
    sc = min(10000, max(800, cut) * 1.5)           # TB303Voice.sh101CutoffHz(max(800, cutoff))
    c = _index(sc, 120, 100)                       # bs_cut_tab: 120 * 100^(i/127)
    peak = _index(min(16000, sc + env * 0.9), 120, 100)
    return {0: c, 1: _clamp(127 * q / 28), 3: _clamp(peak - c), 4: _dec(decay / 2)}


# ---- the Octatrack side ------------------------------------------------------
T_ACID, T_BASS, T_BD, T_SD, T_CH, T_OH = 0, 1, 4, 5, 6, 7       # 0-based tracks
DRUM_TRACKS = {T_BD: "BD", T_SD: "SD", T_CH: "CH", T_OH: "OH"}
FLAT_PTCH, FLAT_ACC, FLAT_VOL = 5, 8, 15
DRUM_ACC_LOCK, BASS_ACC_VOL = 127, 16
TRIGW = 0x899                        # the trig words from DATA (the file's, RAM +0x89a)
SCALE_1X, MODE_PER_TRACK = 2, 1
LOCK_BYTES = ob.NSTEPS * ob.LOCK_LEN
FLEX = 1
# the Part's page arrays in the file (PARAM_PAGES.md 5a's RAM offsets + 9)
PB_OFF, LFO_OFF, AMP_OFF = 0x33, 0x123, 0x129   # + t*30 + machine*6 / + t*24
ACC_SLOT, FINE_SLOT, VOL_SLOT = 2, 5, 3   # LFO 2 = ACC (ACID, Rhythm 9), LFO 5 = ACID's FINE; AMP 3 = VOL
OCT_SLOT, PTCH_SLOT = 1, 5           # LFO 1 = OCT (GARDEN36); PLAYBACK 5 = PTCH on ACID / BASS
BFINE_SLOT = 4                       # LFO 4 = BASS 101's FINE (GARDEN36; LFO 2's depth before)
# What a track's FLEX sample must be called (the GARDEN marker rules).
WANT = {T_ACID: ("ACID", "prefix"), T_BASS: ("BASS", "prefix"), T_BD: ("BD", "stem"),
        T_SD: ("SD", "stem"), T_CH: ("OH", "stem"), T_OH: ("OH", "stem")}


def pb_addr(part, t, slot):
    return op.PART_BASE + part * op.PART_STRIDE + PB_OFF + t * 30 + FLEX * 6 + slot


def lfo_addr(part, t, slot):
    return op.PART_BASE + part * op.PART_STRIDE + LFO_OFF + t * 24 + slot


def vol_addr(part, t):
    return op.PART_BASE + part * op.PART_STRIDE + AMP_OFF + t * 24 + VOL_SLOT


@dataclass
class TrackWrite:
    length: int = 16
    trigs: int = 0                   # step mask 0
    tlocks: int = 0                  # step mask 2 (trigless locks: the slide targets)
    locks: dict = field(default_factory=dict)   # step -> {flat: value}


@dataclass
class Options:
    bank: int = 1
    oct1: int = 0
    oct2: int = 0
    bass_vol: int | None = None      # the Part's AMP VOL as stored (64 = panel 0); None = read the Part
    knobs: bool = True
    oct_knob: bool = True            # GARDEN36: OCT takes the octaves, BASS's FINE the cents; False: GARDEN35
    song: bool = True                # the song into arrangement `arr` (M3)
    arr: int = 1


# ---- the arrangement (M3): the song's bars as OT patterns and arranger rows --------
# The arrangement file (arrNN.work / .strd), decoded 29 Oct 2026 from the firmware's own
# save under the port (ot_emu --mkii, ARR > EDIT, ARR > SAVE, PROJECT > SAVE; rows A02 x3,
# B16 x4, A01, C05 LN 8, LOOP 000/inf): a 22-byte header (FORM ... DPS1ARRA, 00 06), two
# copies of the arrangement (0x16 and 0x162a, the live one and the saved one), each a
# 0x14-byte header (+0x12: the row count, u16) then 256 rows of 22 bytes: +0 kind (0 a
# pattern, 1 LOOP / HALT / JUMP), +1 the pattern (bank * 16 + pattern; for kind 1 the
# target row), +2 REP - 1 (kind 1: the count, 0 = inf), +8 ff ff, +10 OF (u16), +12 LN
# (u16), the rest 0. The save sets the second copy's +1 byte and the byte at 0x2c3e; the
# checksum as a bank file's. REP is 1..64 on the panel.
ARR_SIZE, ARR_BLOCKS, ARR_COUNT, ARR_ROW0, ARR_ROW = 0x2C48, (0x16, 0x162A), 0x12, 0x14, 22
ARR_SAVED = (0x162B, 0x2C3E)
ARR_HEADER = b"FORM\0\0\0\0DPS1ARRA\0\0\0\0\0\x06"
REP_MAX, ROWS_MAX = 64, 255          # the panel's REP; rows kept below the 256 slots (END stays)


def build_arr(rows, header=ARR_HEADER):
    """rows: ('pat', global pattern, REP, LN) / ('loop', target row, count) -> the file."""
    d = bytearray(ARR_SIZE)
    d[:0x16] = header[:0x16]
    for b in ARR_BLOCKS:
        d[b + ARR_COUNT:b + ARR_COUNT + 2] = len(rows).to_bytes(2, "big")
        for i, r in enumerate(rows):
            a = b + ARR_ROW0 + ARR_ROW * i
            kind, v1, v2, ln = (0, r[1], r[2] - 1, r[3]) if r[0] == "pat" else (1, r[1], r[2], 16)
            d[a], d[a + 1], d[a + 2] = kind, v1, v2
            d[a + 8:a + 10] = b"\xff\xff"
            d[a + 12:a + 14] = ln.to_bytes(2, "big")
    for f in ARR_SAVED:
        d[f] = 1
    d[-2:] = (sum(d[0x10:-2]) & 0xFFFF).to_bytes(2, "big")
    return bytes(d)


def song_layout(song, o):
    """-> ({(a, b, d): (bank, pattern0)} for every combination the song plays, the arranger
    rows, notes). A bar whose three machines play the same slot i plays OT pattern i of banks
    --bank / --bank+1 (the patterns convert writes anyway); any other combination gets a
    pattern of its own from bank --bank+2 on. Consecutive bars on one pattern are one row
    (REP <= 64), and a LOOP to row 0 ends the song, as ReBirth loops it."""
    notes = Counter()
    if not (o.song and song.bars):
        return {}, [], notes
    slots, nxt, bars = {}, 0, []
    for bar in song.bars:
        a, b, d = bar
        if bar not in slots:
            if a == b == d:
                slots[bar] = (o.bank + a // 16, a % 16)
            else:
                bank = o.bank + 2 + nxt // 16
                if bank > 16:
                    notes[f"song cut at bar {len(bars) + 1} of {len(song.bars)}: its pattern combinations need more than banks {chr(66 + o.bank)}..P"] += 1
                    break
                slots[bar] = (bank, nxt % 16)
                nxt += 1
        bars.append(slots[bar])
    rows = []
    for bank, pat in bars:
        g = (bank - 1) * 16 + pat
        if rows and rows[-1][1] == g and rows[-1][2] < REP_MAX:
            rows[-1] = ("pat", g, rows[-1][2] + 1, 16)
        else:
            rows.append(("pat", g, 1, 16))
    if len(rows) > ROWS_MAX - 1:
        kept = sum(r[2] for r in rows[:ROWS_MAX - 1])
        notes[f"song cut at bar {kept + 1} of {len(bars)}: more than {ROWS_MAX - 1} arranger rows"] += 1
        rows = rows[:ROWS_MAX - 1]
    rows.append(("loop", 0, 0))
    return slots, rows, notes


def encode_303(pat: Pattern303, shift: int, acc_lock: int | None, flat: int, notes: Counter) -> TrackWrite:
    """shift: semitones on top of raw 40 + 12 oct + note; the accent writes acc_lock
    at flat (None: the accent writes nothing)."""
    tw = TrackWrite(length=pat.length)
    L = pat.length
    st = pat.steps
    for s in range(L):
        if st[s].rest:
            continue
        slid_into = s > 0 and not st[s - 1].rest and st[s - 1].sld
        tw.locks[s] = {FLAT_PTCH: max(0, min(127, 40 + 12 * st[s].oct + st[s].ni + shift))}
        if slid_into:
            tw.tlocks |= 1 << s
            if st[s].acc:
                notes["accent on a slide target dropped"] += 1
            continue
        tw.trigs |= 1 << s
        if st[s].acc and acc_lock is not None:
            tw.locks[s][flat] = acc_lock
    if L > 1 and not st[L - 1].rest and st[L - 1].sld and not st[0].rest:
        notes["slide across the loop (last step into step 1) dropped"] += 1
    return tw


def encode_909(pat: Pattern909, voice: str) -> TrackWrite:
    tw = TrackWrite(length=pat.length)
    col = V909[voice]
    for s in range(pat.length):
        raw = pat.steps[s][col]
        if raw:
            tw.trigs |= 1 << s
            if raw == 2:
                tw.locks[s] = {FLAT_ACC: DRUM_ACC_LOCK}
    return tw


def plan(song: Song, o: Options, bass_vol_for):
    """-> ({(bank, pattern0): {track0: TrackWrite}}, notes). bass_vol_for(bank,
    pattern0) = the Part VOL BASS's accent rides on."""
    notes = Counter()
    if len(song.synth) < 2:
        raise ValueError(f"{len(song.synth)} TB-303 bank(s) in the song, two expected")
    if len(song.synth) > 2:
        notes[f"{len(song.synth) - 2} extra 303 chunk(s) ignored"] += 1
    k1, k2 = song.knobs[0], song.knobs[1]
    s1 = octave_split(k1.tune, o.oct1, o.knobs, o.oct_knob)[1]
    s2 = octave_split(k2.tune, o.oct2, o.knobs, o.oct_knob)[1]
    acid_acc = (k1.acc or None) if o.knobs else DRUM_ACC_LOCK
    slots, _, _ = song_layout(song, o)
    todo = [((o.bank + p // 16, p % 16), (p, p, p), notes) for p in range(32)]
    todo += [(slot, combo, Counter()) for combo, slot in slots.items() if not combo[0] == combo[1] == combo[2]]
    out = {}
    for (b, pp), (pa, pb, pd), nt in todo:
        vol = o.bass_vol if o.bass_vol is not None else bass_vol_for(b, pp)
        boost = round(BASS_ACC_VOL * k2.acc / 127) if o.knobs else BASS_ACC_VOL
        tracks = {
            T_ACID: encode_303(song.synth[0][pa], s1, acid_acc, FLAT_ACC, nt),
            T_BASS: encode_303(song.synth[1][pb], s2, min(127, vol + boost) if boost else None, FLAT_VOL, nt),
        }
        d = song.drums[pd] if song.drums and pd < len(song.drums) else None
        for t, v in DRUM_TRACKS.items():
            tracks[t] = encode_909(d, v) if d else TrackWrite()
        if d:
            lost = Counter(name for st in d.steps[:d.length] for name, c in V909.items()
                           if st[c] and name not in DRUM_TRACKS.values())
            for name, n in lost.items():
                nt[f"909 {name} hits dropped (no track)"] += n
        out[(b, pp)] = tracks
    if song.drums is None:
        notes["no 909 chunk: the drum tracks are cleared"] += 1
    return out, notes


def part_writes(song: Song, o: Options):
    """-> {(t, 'pb'|'lfo', slot): value} for every Part a written pattern plays."""
    w = {(T_ACID, "pb", PTCH_SLOT): 64, (T_BASS, "pb", PTCH_SLOT): 64}   # PTCH 0 (stock RTIM 79 = +15)
    if o.oct_knob:
        for t, kn, oo in ((T_ACID, song.knobs[0], o.oct1), (T_BASS, song.knobs[1], o.oct2)):
            w[(t, "lfo", OCT_SLOT)] = OCT_RAW0 + octave_split(kn.tune, oo)[0]
        w[(T_BASS, "lfo", BFINE_SLOT)] = fine_raw(song.knobs[1].tune)
    for slot, v in acid_page(song.knobs[0]).items():
        w[(T_ACID, "pb", slot)] = v
    for slot, v in bass_page(song.knobs[1]).items():
        w[(T_BASS, "pb", slot)] = v
    for t in (T_ACID, *DRUM_TRACKS):
        w[(t, "lfo", ACC_SLOT)] = 0
    w[(T_ACID, "lfo", FINE_SLOT)] = fine_raw(song.knobs[0].tune)
    return w


def part_addr(part, key):
    t, page, slot = key
    return pb_addr(part, t, slot) if page == "pb" else lfo_addr(part, t, slot)


def tail(pattern):
    return ob.PTRN_BASE + pattern * ob.PTRN_STRIDE + ob.PTRN_STRIDE - 11


def pattern_part(data, pattern):
    """The 0-based Part a pattern plays (ot_project.bank_info's byte)."""
    return data[ob.PTRN_BASE + (pattern + 1) * ob.PTRN_STRIDE - 5]


def parts_played(data):
    """Every Part record a bank's patterns play, live (0..3) and saved (4..7) copy."""
    live = {pattern_part(data, p) for p in range(16)}
    return sorted(live | {p + op.NPARTS for p in live})


def write_track(data: bytearray, pattern: int, track: int, tw: TrackWrite):
    base = ob.trac(pattern, track) + ob.DATA
    for which in range(4):            # trig, trigless trig, trigless lock, the fourth (ACID GEN's four)
        ob.set_mask(data, pattern, track, 0, which)
    ob.set_mask(data, pattern, track, tw.trigs, 0)
    ob.set_mask(data, pattern, track, tw.tlocks, ob.LOCK_TRIGS)
    lk = ob.trac(pattern, track) + ob.LOCKS
    data[lk:lk + LOCK_BYTES] = bytes([ob.NOLOCK]) * LOCK_BYTES
    for s, row in tw.locks.items():
        for flat, v in row.items():
            data[lk + s * ob.LOCK_LEN + flat] = v
    for s in range(ob.NSTEPS):        # no trig condition (stock clears it with and #0x80 on a placed trig)
        data[base + TRIGW + 2 * s + 1] &= 0x80
    data[base + ob.TRK_LENGTH] = tw.length
    data[base + ob.TRK_SCALE] = SCALE_1X


def write_pattern_mode(data: bytearray, pattern: int):
    """SCALE MODE PER TRACK, master length 16 (a short, -1 = INF), master scale 1X.
    🟡 From PARAM_PAGES.md: RAM +0x8e50 master length, +0x8e53 length, +0x8e54
    scale, +0x8e55 mode; the file's tail+2/+3 is the measured length/scale pair,
    so tail-1 .. tail+4 = master length (2), master scale, length, scale, mode."""
    t = tail(pattern)
    data[t - 1], data[t] = 0, 16
    data[t + 1] = SCALE_1X
    data[t + 4] = MODE_PER_TRACK


def read_track(data, pattern, track) -> TrackWrite:
    base = ob.trac(pattern, track) + ob.DATA
    lk = ob.trac(pattern, track) + ob.LOCKS
    locks = {}
    for s in range(ob.NSTEPS):
        row = {i: v for i, v in enumerate(data[lk + s * ob.LOCK_LEN:lk + (s + 1) * ob.LOCK_LEN]) if v != ob.NOLOCK}
        if row:
            locks[s] = row
    return TrackWrite(length=data[base + ob.TRK_LENGTH], trigs=ob.mask(data, pattern, track, 0),
                      tlocks=ob.mask(data, pattern, track, ob.LOCK_TRIGS), locks=locks)


def track_ok(path, t):
    name = path.split("/")[-1].upper()
    want, how = WANT[t]
    return name.startswith(want) if how == "prefix" else (name.split(".")[0] == want and "." in name)


def mapping_errors(pdir, bank, parts):
    m = op.track_map(pdir)
    errs = []
    for p in sorted(parts):
        rows = {r[0] - 1: r for r in m[(bank, p + 1)]}
        for t in WANT:
            _, mt, slot, path = rows[t]
            if mt != "FLEX" or not track_ok(path, t):
                errs.append(f"bank {chr(64 + bank)} part {p + 1} T{t + 1}: {mt} slot {slot} "
                            f"'{path.split('/')[-1] or '-'}', want FLEX {WANT[t][0]}"
                            + ("*" if WANT[t][1] == "prefix" else ".wav"))
    return errs


def short(tracks):
    return any(tw.length != 16 for tw in tracks.values())


def allowed(writes, copied_parts, parts, pw):
    """The byte offsets / ranges convert may change in a bank file."""
    r = []
    for pattern, tracks in writes.items():
        for t in tracks:
            r.append((ob.trac(pattern, t) + ob.DATA, ob.trac(pattern, t) + ob.TRAC_STRIDE))
        r.append((tail(pattern) - 1, tail(pattern) + 5))
    if copied_parts:
        r.append((op.PART_BASE, op.PART_BASE + op.NPARTS_ALL * op.PART_STRIDE))
    for part in parts:
        for key in pw:
            a = part_addr(part, key)
            r.append((a, a + 1))
    return r


def set_tempo(pdir, bpm):
    v = round(bpm * 24)
    for suffix in ("work", "strd"):
        f = pdir / f"project.{suffix}"
        if f.is_file():
            raw, n = re.subn(rb"TEMPOx24=\d+", b"TEMPOx24=%d" % v, f.read_bytes())
            if n != 1:
                sys.exit(f"{f.name}: {n} TEMPOx24 lines, one expected")
            f.write_bytes(raw)
    return v


def bass_vol_reader(pdir):
    cache = {}

    def vol(bank, pattern):
        if bank not in cache:
            cache[bank] = (pdir / f"bank{bank:02d}.work").read_bytes()
        d = cache[bank]
        return d[vol_addr(pattern_part(d, pattern), T_BASS)]
    return vol


def convert(rbs, template, dest, o: Options, check_tracks=True):
    song = parse_rbs(pathlib.Path(rbs).read_bytes())
    template, dest = pathlib.Path(template), pathlib.Path(dest)
    slots, rows, _ = song_layout(song, o)
    banks = sorted({o.bank, o.bank + 1} | {b for b, _ in slots.values()})
    if dest.exists():
        sys.exit(f"{dest} exists -- refusing to overwrite")
    for b in banks:
        if not (template / f"bank{b:02d}.work").is_file():
            sys.exit(f"{template}: no bank{b:02d}.work -- not an Octatrack project, or not that bank")
    shutil.copytree(template, dest)
    try:
        copied = set()
        if check_tracks:
            fdata = (dest / f"bank{o.bank:02d}.work").read_bytes()
            errs = mapping_errors(dest, o.bank, {pattern_part(fdata, p) for p in range(16)})
            if errs:
                raise SystemExit("the template's tracks are not the GARDEN layout:\n  " + "\n  ".join(errs))
            for bk in banks[1:]:
                data = (dest / f"bank{bk:02d}.work").read_bytes()
                if mapping_errors(dest, bk, {pattern_part(data, p) for p in range(16)}):
                    blk = fdata[op.PART_BASE:op.PART_BASE + op.NPARTS_ALL * op.PART_STRIDE]

                    def cp(d, blk=blk):
                        d[op.PART_BASE:op.PART_BASE + len(blk)] = blk
                    op._bank_write(dest, bk, cp, guard=False)
                    copied.add(bk)
                    errs = mapping_errors(dest, bk, {pattern_part(data, p) for p in range(16)})
                    if errs:
                        raise SystemExit("after the part copy:\n  " + "\n  ".join(errs))
            if copied:
                print(f"bank(s) {' '.join(chr(64 + b) for b in sorted(copied))}: their parts did not match, "
                      f"bank {chr(64 + o.bank)}'s eight part records copied in")
        writes, notes = plan(song, o, bass_vol_reader(dest))
        pw = part_writes(song, o) if o.knobs else {}
        for b in banks:
            mine = {p: tr for (bb, p), tr in writes.items() if bb == b}
            played = parts_played((dest / f"bank{b:02d}.work").read_bytes())

            def mut(d, mine=mine, played=played):
                ob.check_tags(d)
                for p, tracks in mine.items():
                    for t, tw in tracks.items():
                        write_track(d, p, t, tw)
                    if short(tracks):
                        write_pattern_mode(d, p)
                for part in played:
                    for key, v in pw.items():
                        d[part_addr(part, key)] = v
            op._bank_write(dest, b, mut, guard=False)
            # the guard: nothing outside the written records (and a copied part block) moved
            ok = allowed(mine, b in copied, played, pw)
            for suffix in ("work", "strd"):
                new = dest / f"bank{b:02d}.{suffix}"
                if not new.is_file():
                    continue
                old, nb = (template / new.name).read_bytes(), new.read_bytes()
                if len(nb) != len(old):
                    raise SystemExit(f"{new.name}: length changed")
                okb = ok + [(len(nb) - 2, len(nb))]
                stray = [a for a in range(len(nb)) if nb[a] != old[a] and not any(lo <= a < hi for lo, hi in okb)]
                if stray:
                    raise SystemExit(f"{new.name}: {len(stray)} byte(s) changed outside the written records, "
                                     f"first at {stray[0]:#x} -- refusing")
                if int.from_bytes(nb[-2:], "big") != sum(nb[0x10:-2]) & 0xFFFF:
                    raise SystemExit(f"{new.name}: checksum did not take")
        if rows:
            hdr = (template / f"arr{o.arr:02d}.work").read_bytes()[:0x16] if (template / f"arr{o.arr:02d}.work").is_file() else ARR_HEADER
            if hdr[:4] != b"FORM" or hdr[8:16] != b"DPS1ARRA":
                raise SystemExit(f"arr{o.arr:02d}.work: not an arrangement file")
            for suffix in ("work", "strd"):
                (dest / f"arr{o.arr:02d}.{suffix}").write_bytes(build_arr(rows, hdr))
        if song.tempo:
            v = set_tempo(dest, song.tempo)
            print(f"tempo {song.tempo:g} BPM (TEMPOx24={v})")
        else:
            notes["no tempo in the song: the template's kept"] += 1
        op.write_stored(dest)
    except BaseException:
        shutil.rmtree(dest, ignore_errors=True)
        raise
    bad = check(dest, song, o, quiet=True)
    if bad:
        sys.exit("read-back FAILED:\n  " + "\n  ".join(bad[:20]))
    try:
        summary(song, writes, notes, o)
    except Exception as e:                        # noqa: BLE001 -- the project is written and read back
        print(f"(the summary failed: {type(e).__name__}: {e} -- the project itself is fine)")
    print(f"{dest}: written and read back (.work and .strd)")


def check(dest, song, o: Options, quiet=False):
    """Every written track, pattern mode and Part byte read back from both files = the plan."""
    dest = pathlib.Path(dest)
    writes, _ = plan(song, o, bass_vol_reader(dest))
    pw = part_writes(song, o) if o.knobs else {}
    bad = []
    _, rows, _ = song_layout(song, o)
    if rows:
        for suffix in ("work", "strd"):
            f = dest / f"arr{o.arr:02d}.{suffix}"
            if not f.is_file() or f.read_bytes()[0x16:] != build_arr(rows)[0x16:]:
                bad.append(f"{f.name}: not the planned arrangement")
    for suffix in ("work", "strd"):
        for b in sorted({b for b, _ in writes}):
            f = dest / f"bank{b:02d}.{suffix}"
            if not f.is_file():
                if suffix == "work":
                    bad.append(f"{f.name} missing")
                continue
            data = f.read_bytes()
            if int.from_bytes(data[-2:], "big") != sum(data[0x10:-2]) & 0xFFFF:
                bad.append(f"{f.name}: bad checksum")
            for (bb, p), tracks in writes.items():
                if bb != b:
                    continue
                for t, tw in tracks.items():
                    got = read_track(data, p, t)
                    if got != tw:
                        bad.append(f"{f.name} {chr(64 + b)}{p + 1:02d} T{t + 1}: wrote {tw}, read {got}")
                if short(tracks) and data[tail(p) + 4] != MODE_PER_TRACK:
                    bad.append(f"{f.name} {chr(64 + b)}{p + 1:02d}: not PER TRACK")
            for part in parts_played(data):
                for key, v in pw.items():
                    if data[part_addr(part, key)] != v:
                        bad.append(f"{f.name} part {part + 1} {key}: {data[part_addr(part, key)]}, want {v}")
    if not quiet:
        print("check: " + ("OK" if not bad else f"{len(bad)} mismatch(es)"))
        for line in bad[:20]:
            print("  " + line)
    return bad


def summary(song, writes, notes, o):
    full = sum(1 for p in range(32) for bank in song.synth[:2] if has_content(bank[p]))
    drums = sum(1 for d in (song.drums or []) if has_content(d))
    combo = {v: k for k, v in song_layout(song, o)[0].items()}

    def rb(b, p):                    # the ReBirth slot(s) an OT pattern plays
        if (b, p) in combo and not combo[(b, p)][0] == combo[(b, p)][1] == combo[(b, p)][2]:
            return "/".join(RB_SLOTS[x] for x in combo[(b, p)])
        return RB_SLOTS[(b - o.bank) * 16 + p]
    shorts = [f"{chr(64 + b)}{p + 1:02d} ({rb(b, p)}: " +
              "/".join(f"T{t + 1}={tw.length}" for t, tw in tr.items() if tw.length != 16) + ")"
              for (b, p), tr in sorted(writes.items()) if short(tr)]
    print(f"303 patterns with notes: {full} (of 64); 909 patterns with BD/SD/CH/OH: {drums} (of 32)")
    print(f"banks {chr(64 + o.bank)} (A1..B8) and {chr(65 + o.bank)} (C1..D8), patterns 1..16")
    slots, rows, snotes = song_layout(song, o)
    if rows:
        comp = sorted(v for k, v in slots.items() if not k[0] == k[1] == k[2])
        where = (f", {len(comp)} combination pattern(s) {chr(64 + comp[0][0])}{comp[0][1] + 1:02d}.."
                 f"{chr(64 + comp[-1][0])}{comp[-1][1] + 1:02d}" if comp else "")
        print(f"song: {sum(r[2] for r in rows if r[0] == 'pat')} bars -> ARR {o.arr}, {len(rows) - 1} rows + LOOP{where}")
        notes = notes + snotes
    elif o.song:
        print("song: none in the file (no TRKL chain)")
    if o.knobs:
        for k, (t, name, page) in enumerate(((T_ACID, "ACID", acid_page), (T_BASS, "BASS", bass_page))):
            kn = song.knobs[k]
            pg = page(kn)
            cents = tune_cents(kn.tune)
            semi = tune_semitones(kn.tune)
            left = cents - 100 * semi
            okn, lock = octave_split(kn.tune, (o.oct1, o.oct2)[k], True, o.oct_knob)
            acc = (f"accent lock ACC {kn.acc}" if t == T_ACID
                   else f"accent lock VOL +{round(BASS_ACC_VOL * kn.acc / 127)}")
            fine = (f", FINE {fine_raw(kn.tune)} ({left:+.0f} cents)" if t == T_ACID or o.oct_knob
                    else f" ({left:+.0f} cents not representable: BASS has no FINE before GARDEN36)" if abs(left) >= 1 else "")
            print(f"303#{k + 1} -> T{t + 1} {name}: ReBirth TUNE {kn.tune} CUT {kn.cut} RES {kn.res} "
                  f"ENV {kn.env} DEC {kn.dec} ACC {kn.acc} -> CUT {pg[0]} RES {pg[1]} ENV {pg[3]} DEC {pg[4]}, "
                  f"{acc}, " + (f"OCT {okn:+d}, " if o.oct_knob else "") + f"notes {lock:+d} st" + fine)
    if shorts:
        more = f", ... and {len(shorts) - 12} more" if len(shorts) > 12 else ""
        print(f"SCALE MODE PER TRACK set on {len(shorts)} pattern(s) (check on the unit): " + ", ".join(shorts[:12]) + more)
    for k, n in sorted(notes.items()):
        print(f"  note: {k}: {n}")


# ---- show ----------------------------------------------------------------------
NAMES = "C C# D D# E F F# G G# A A# B".split()


def show(rbs, only=None):
    song = parse_rbs(pathlib.Path(rbs).read_bytes())
    print(f"tempo {song.tempo} BPM, {len(song.synth)} x 303, 909 {'yes' if song.drums else 'no'}")
    for k, kn in enumerate(song.knobs):
        print(f"  303#{k + 1} knobs: TUNE {kn.tune} ({tune_cents(kn.tune):+.0f} cents) CUT {kn.cut} "
              f"RES {kn.res} ENV {kn.env} DEC {kn.dec} ACC {kn.acc}")
    for p in range(32):
        if only and RB_SLOTS[p] != only.upper():
            continue
        rows = []
        for k, bank in enumerate(song.synth[:2]):
            pat = bank[p]
            if has_content(pat) or only:
                cells = []
                for s, st in enumerate(pat.steps[:pat.length]):
                    if st.rest:
                        cells.append("  .  ")
                        continue
                    n = 36 + 12 * st.oct + st.ni
                    cells.append(f"{NAMES[n % 12]}{n // 12 - 1}{'!' if st.acc else ''}{'~' if st.sld else ''}".ljust(5))
                rows.append(f"  303#{k + 1} L{pat.length:2d} " + "".join(cells))
        d = song.drums[p] if song.drums and p < len(song.drums) else None
        if d and (has_content(d) or only):
            for v in ("BD", "SD", "CH", "OH"):
                c = V909[v]
                rows.append(f"  909 {v} L{d.length:2d} " + "".join(
                    ("X" if st[c] == 2 else "x" if st[c] else ".") for st in d.steps[:d.length]))
        if rows:
            print(RB_SLOTS[p])
            print("\n".join(rows))


# ---- selftest: a synthetic song through a synthetic project -----------------
KNOBS1 = (127, 0, 64, 127, 127, 100)   # TUNE +1 octave, CUT 0, RES 64, ENV max, DEC max, ACC 100
KNOBS2 = (66, 127, 0, 0, 0, 0)         # in tune, open, no resonance, no env, ACC 0


def _fake_rbs():
    b = bytearray(b"CAT \0\0\0\0RB40")
    pay = bytearray(CHUNK303 - 9)
    # A1: C2 trig, D2 accent+slide -> E2 (slide target, accented: dropped), rest, ...
    seq = [(0, 1, 0), (2, 1, F_ACC | F_SLD), (4, 1, F_ACC), (0, 0, F_REST), (11, 2, F_SLD)]
    for s in range(16):
        ni, oct_, fl = seq[s] if s < len(seq) else (0, 1, F_REST)
        fl |= F_DOWN if oct_ == 0 else F_UP if oct_ == 2 else 0
        pay[2 + 2 * s], pay[3 + 2 * s] = ni, fl
    pay[1] = 16
    pay[PAT303 * 31 + 1] = 4            # D8: 4 steps, a slide from the last step into step 1
    for s in range(4):
        pay[PAT303 * 31 + 2 + 2 * s] = 0
        pay[PAT303 * 31 + 3 + 2 * s] = F_SLD if s == 3 else 0
    for p in range(32):
        if p not in (0, 31):
            pay[p * PAT303 + 1] = 16
            for s in range(16):
                pay[p * PAT303 + 3 + 2 * s] = F_REST
    for kn in (KNOBS1, KNOBS2):
        b += b"303 " + CHUNK303.to_bytes(4, "big") + bytes(2) + bytes(kn) + bytes(1) + pay
    drum = bytearray(DRUM_HEAD + 32 * PAT909)
    for p in range(32):
        drum[DRUM_HEAD + p * PAT909 - 1] = 16
    a1 = DRUM_HEAD
    for s in range(0, 16, 4):
        drum[a1 + s * STEP909 + V909["BD"]] = 2 if s == 0 else 1
    drum[a1 + 4 * STEP909 + V909["SD"]] = 1
    drum[a1 + 2 * STEP909 + V909["OH"]] = 1
    drum[a1 + 1 * STEP909 + V909["CH"]] = 1
    drum[a1 + 3 * STEP909 + V909["RS"]] = 1
    b += b"909 " + len(drum).to_bytes(4, "big") + drum
    b += b"GLOB" + bytes(7) + (133000).to_bytes(3, "big") + bytes(4)
    # the song: 303#1 A1 A1 A2, 303#2 A1 x3, 909 A1 A1 A2 (chain records [VLQ 32 x bars][01][slot])
    def trak(base, recs):
        body = bytes(3) * base + b"".join(bytes((32 * held, 1, pat)) for pat, held in recs)
        return (base + len(recs)).to_bytes(4, "big") + body
    traks = [bytes(4)] * 9
    traks[1] = trak(9, [(31, 2), (0, 1)])          # 303#1 A1 A1 D8 (D8: 4 steps)
    traks[2] = trak(9, [(0, 3)])
    traks[4] = trak(30, [(1, 2), (0, 1)])
    b += b"TRKL" + b"".join(b"TRAK" + len(t).to_bytes(4, "big") + t + bytes(len(t) & 1) for t in traks)
    return bytes(b)


def _fake_project(pdir, banks=(1, 2, 3), layout=True):
    pdir.mkdir()
    files = {1: "ACID.wav", 2: "BASS_101.wav", 3: "BD.wav", 4: "SD.wav", 5: "OH.wav"}
    slots = "".join(f"[SAMPLE]\r\nTYPE=FLEX\r\nSLOT={n:03d}\r\nPATH=../AUDIO/{f}\r\nGAIN=48\r\n[/SAMPLE]\r\n"
                    for n, f in files.items())
    (pdir / "project.work").write_bytes(f"[PROJECT]\r\nTEMPOx24=2880\r\n[/PROJECT]\r\n{slots}".encode())
    size = op.PART_BASE + op.NPARTS_ALL * op.PART_STRIDE + 4 * 7 + 2
    tmap = {T_ACID: 1, T_BASS: 2, T_BD: 3, T_SD: 4, T_CH: 5, T_OH: 5}
    for b in banks:
        d = bytearray(size)
        d[:4] = b"FORM"
        for p in range(16):
            a = ob.PTRN_BASE + p * ob.PTRN_STRIDE
            d[a:a + 4] = b"PTRN"
            for t in range(8):
                d[ob.trac(p, t):ob.trac(p, t) + 4] = b"TRAC"
                d[ob.trac(p, t) + ob.LOCKS:ob.trac(p, t) + ob.LOCKS + LOCK_BYTES] = bytes([ob.NOLOCK]) * LOCK_BYTES
                d[ob.trac(p, t) + ob.DATA + TRIGW + 1] = 0x14       # a stale trig condition on step 1
            d[tail(p)], d[tail(p) + 1], d[tail(p) + 2], d[tail(p) + 3] = 16, SCALE_1X, 16, SCALE_1X
        d[ob.trac(0, 2) + ob.DATA] = 0xff                           # T3 content the convert must keep
        for p in range(op.NPARTS_ALL):
            for t in range(8):                                     # the stock FLEX / LFO / AMP defaults
                d[pb_addr(p, t, 0):pb_addr(p, t, 0) + 6] = bytes((64, 0, 0, 127, 0, 79))
                d[lfo_addr(p, t, 0):lfo_addr(p, t, 0) + 6] = bytes((32, 32, 32, 0, 0, 0))
                d[vol_addr(p, t)] = 64
            if layout and b == banks[0]:
                base = op.PART_BASE + p * op.PART_STRIDE
                for t, sl in tmap.items():
                    d[base + op.MTYPE_OFF + t] = FLEX
                    d[base + op.SLOT_OFF + t * 5 + op.SLOT_KIND["flex"]] = sl - 1
        d[-2:] = (sum(d[0x10:-2]) & 0xFFFF).to_bytes(2, "big")
        (pdir / f"bank{b:02d}.work").write_bytes(bytes(d))
        (pdir / f"bank{b:02d}.strd").write_bytes(bytes(d))


def selftest():
    # the arrangement writer = the firmware's own save under the port (29 Oct 2026: the whole
    # file compared equal; these are its bytes over an empty arrangement's header)
    fw = bytearray(ARR_SIZE)
    fw[:0x16] = ARR_HEADER
    for at, hx in ((41, "05000102"), (50, "ffff"), (55, "10"), (65, "1f03"), (72, "ffff"), (77, "10"),
                   (94, "ffff"), (99, "10"), (109, "24"), (116, "ffff"), (121, "08"), (130, "01"),
                   (138, "ffff"), (143, "10"), (5693, "05000102"), (5702, "ffff"), (5707, "10"),
                   (5717, "1f03"), (5724, "ffff"), (5729, "10"), (5746, "ffff"), (5751, "10"),
                   (5761, "24"), (5768, "ffff"), (5773, "08"), (5782, "01"), (5790, "ffff"),
                   (5795, "10"), (0x162B, "01"), (0x2C3E, "01"), (11334, "1522")):
        fw[at:at + len(hx) // 2] = bytes.fromhex(hx)
    assert build_arr([("pat", 1, 3, 16), ("pat", 31, 4, 16), ("pat", 0, 1, 16), ("pat", 36, 1, 8),
                      ("loop", 0, 0)]) == bytes(fw)                  # A02 x3, B16 x4, A01, C05 LN 8, LOOP
    # the laws at their anchors
    assert tune_semitones(66) == 0 and tune_semitones(127) == 12 and tune_semitones(0) == -12
    assert tune_semitones(64) == 0 and round(tune_cents(64)) == -36
    assert fine_raw(64) == 28 and fine_raw(66) == 64 and fine_raw(127) == 64   # -36 c; in tune; +1 oct exact
    k = Knobs303(66, 0, 0, 0, 0, 0)
    assert acid_page(k) == {0: 25, 1: 0, 3: 0, 4: 6}            # 80 Hz (25.5), no env, tau 6.7 ms
    assert acid_page(Knobs303(66, 127, 127, 127, 127, 0)) == {0: 105, 1: 127, 3: 14, 4: 101}  # 6 k, 13 k peak
    assert bass_page(k)[0] == _index(1200, 120, 100) == 64       # the 800 Hz floor x 1.5
    assert bass_page(Knobs303(66, 0, 127, 0, 0, 0))[1] == 127
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        (td / "s.rbs").write_bytes(_fake_rbs())
        song = parse_rbs((td / "s.rbs").read_bytes())
        a1 = song.synth[0][0]
        assert (a1.steps[1].ni, a1.steps[1].oct, a1.steps[1].acc, a1.steps[1].sld) == (2, 1, True, True)
        assert a1.steps[3].rest and a1.steps[4].oct == 2 and song.tempo == 133
        assert song.synth[0][31].length == 4
        assert song.knobs == [Knobs303(*KNOBS1), Knobs303(*KNOBS2)]
        assert song.bars == [(0, 0, 0), (0, 0, 0), (31, 0, 1)]
        slots, rows, _ = song_layout(song, Options())
        assert slots == {(0, 0, 0): (1, 0), (31, 0, 1): (3, 0)}      # A01; a combination: C01
        assert rows == [("pat", 0, 2, 16), ("pat", 32, 1, 16), ("loop", 0, 0)]
        many = Song(song.synth, song.knobs, song.drums, None, [(0, 0, 0)] * 130)
        assert song_layout(many, Options())[1] == [("pat", 0, 64, 16), ("pat", 0, 64, 16), ("pat", 0, 2, 16), ("loop", 0, 0)]
        _fake_project(td / "tpl")
        o = Options()
        convert(td / "s.rbs", td / "tpl", td / "out", o)
        d1 = (td / "out" / "bank01.work").read_bytes()
        t1 = read_track(d1, 0, T_ACID)
        assert t1.trigs == 0b10011, bin(t1.trigs)                # C2, D2, B3 start notes
        assert t1.tlocks == 0b00100, bin(t1.tlocks)              # E2 = D2's slide target
        assert t1.locks[0] == {FLAT_PTCH: 52}                    # C2 (TUNE's octave is on OCT)
        assert t1.locks[1] == {FLAT_PTCH: 54, FLAT_ACC: 100}     # the ACCENT knob as the lock
        assert t1.locks[2] == {FLAT_PTCH: 56}                    # its accent dropped (slide target)
        assert t1.locks[4] == {FLAT_PTCH: 75}                    # B3 (oct up)
        assert read_track(d1, 0, T_BASS).locks[1] == {FLAT_PTCH: 54}   # ACC 0: no VOL lock
        bd = read_track(d1, 0, T_BD)
        assert bd.trigs == 0x1111 and bd.locks == {0: {FLAT_ACC: 127}}
        assert read_track(d1, 0, T_SD).trigs == 1 << 4
        assert read_track(d1, 0, T_CH).trigs == 1 << 1 and read_track(d1, 0, T_OH).trigs == 1 << 2
        assert d1[ob.trac(0, 2) + ob.DATA] == 0xff               # T3 untouched
        assert d1[ob.trac(0, T_ACID) + ob.DATA + TRIGW + 1] == 0x00   # the condition cleared
        for part in (0, 4):                                      # the Part and its saved copy
            assert [d1[pb_addr(part, T_ACID, s)] for s in range(6)] == [25, 64, 0, 83, 101, 64]
            assert [d1[pb_addr(part, T_BASS, s)] for s in range(6)] == [119, 5, 0, 0, 15, 64]
            assert d1[lfo_addr(part, T_ACID, OCT_SLOT)] == 33   # TUNE +1 octave on OCT
            assert d1[lfo_addr(part, T_BASS, OCT_SLOT)] == 32
            assert d1[lfo_addr(part, T_ACID, ACC_SLOT)] == 0 and d1[lfo_addr(part, T_BD, ACC_SLOT)] == 0
            assert d1[lfo_addr(part, T_BASS, ACC_SLOT)] == 32    # BASS's slot 2 is SHP: untouched
            assert d1[lfo_addr(part, T_ACID, FINE_SLOT)] == 64   # FINE: the stock DEP3 0 = -64 cents replaced
            assert d1[lfo_addr(part, T_BASS, BFINE_SLOT)] == 64  # BASS FINE (GARDEN36), in tune
        assert d1[lfo_addr(1, T_ACID, ACC_SLOT)] == 32           # a Part no pattern plays: untouched
        assert d1[tail(0) + 4] == 0                              # all 16 steps: the mode untouched
        d2 = (td / "out" / "bank02.work").read_bytes()
        d8 = read_track(d2, 15, T_ACID)
        assert d8.length == 4 and d8.trigs == 0b1111 and d8.tlocks == 0   # the wrap slide dropped
        assert d2[tail(15) + 4] == MODE_PER_TRACK                # D8's short tracks: PER TRACK
        assert mapping_errors(td / "out", 2, {0}) == []          # bank B got bank A's parts
        assert d2[pb_addr(0, T_ACID, 0)] == 25                   # ... and the knobs
        assert b"TEMPOx24=3192" in (td / "out" / "project.work").read_bytes()
        assert (td / "out" / "project.strd").is_file()
        assert check(td / "out", song, o, quiet=True) == []
        assert (td / "out" / "arr01.work").read_bytes() == build_arr(rows)
        d3 = (td / "out" / "bank03.work").read_bytes()               # C01 = 303#1 D8, 303#2 A1, 909 A2
        assert read_track(d3, 0, T_ACID) == read_track(d2, 15, T_ACID) and read_track(d3, 0, T_ACID).length == 4
        assert read_track(d3, 0, T_BASS) == read_track(d1, 0, T_BASS) and d3[tail(0) + 4] == MODE_PER_TRACK
        assert read_track(d3, 0, T_BD).trigs == 0 and mapping_errors(td / "out", 3, {0}) == []
        # the BASS accent rides on the Part's VOL; --keep-knobs leaves the Part
        kk = Options(knobs=False)
        convert(td / "s.rbs", td / "tpl", td / "out3", kk)
        d3 = (td / "out3" / "bank01.work").read_bytes()
        assert d3[pb_addr(0, T_ACID, 0)] == 64 and read_track(d3, 0, T_ACID).locks[0] == {FLAT_PTCH: 52}
        assert read_track(d3, 0, T_ACID).locks[1][FLAT_ACC] == 127
        # --no-oct (GARDEN35): the octave on the locks, LFO slot 1 untouched
        convert(td / "s.rbs", td / "tpl", td / "out4", Options(oct_knob=False))
        d4 = (td / "out4" / "bank01.work").read_bytes()
        assert read_track(d4, 0, T_ACID).locks[0] == {FLAT_PTCH: 64} and d4[lfo_addr(0, T_ACID, OCT_SLOT)] == 32
        assert d4[lfo_addr(0, T_BASS, BFINE_SLOT)] == 0              # GARDEN35: LFO 2's depth, untouched
        assert octave_split(127, -1) == (0, 0) and octave_split(127, 3) == (3, 12)   # spill past +3
        assert octave_split(0, 0) == (-1, 0) and octave_split(66, -1) == (-1, 0)
        # a template without the layout is refused, and leaves no DEST behind
        _fake_project(td / "bad", layout=False)
        try:
            convert(td / "s.rbs", td / "bad", td / "out2", o)
            raise AssertionError("a bad template was accepted")
        except SystemExit as e:
            assert "GARDEN layout" in str(e) and not (td / "out2").exists()
    print("selftest: OK")


# ---- serve: a local web page over convert (drag .rbs files in, one project each) ----
PAGE = r"""<!doctype html>
<html lang="ro"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ReBirth to Octatrack</title>
<style>
:root{--bg:#111214;--panel:#1b1d21;--line:#2c2f35;--text:#e8e6e1;--muted:#8d9098;--acc:#e8a33d;--ok:#6cc28a;--bad:#e5655a}
@media (prefers-color-scheme: light){:root{--bg:#f4f2ee;--panel:#fff;--line:#dedad2;--text:#1d1d1f;--muted:#6b6b70;--acc:#b86e00;--ok:#2f8a4f;--bad:#c23b30}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.45 -apple-system,BlinkMacSystemFont,"Helvetica Neue",sans-serif}
main{max-width:860px;margin:0 auto;padding:28px 16px 60px}
h1{font-size:22px;margin:0 0 4px;letter-spacing:.02em}.sub{color:var(--muted);margin:0 0 22px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px;margin-bottom:16px}
label{display:block;font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:0 0 4px}
input[type=text],input[type=number]{width:100%;background:var(--bg);color:var(--text);border:1px solid var(--line);border-radius:6px;padding:8px 10px;font:13px ui-monospace,Menlo,monospace}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.row3{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:12px}
.check{display:flex;gap:8px;align-items:center;margin-top:12px;font-size:14px}
#drop{border:2px dashed var(--line);border-radius:10px;padding:40px 16px;text-align:center;color:var(--muted);cursor:pointer;transition:.15s}
#drop.on{border-color:var(--acc);color:var(--text);background:color-mix(in srgb,var(--acc) 8%,transparent)}
#drop b{color:var(--text)}
.item{border-top:1px solid var(--line);padding:10px 0}.item:first-child{border-top:0}
.head{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}.name{font-weight:600}.dest{color:var(--muted);font:12px ui-monospace,Menlo,monospace;word-break:break-all}
.st{font-size:12px;font-weight:700;letter-spacing:.06em;padding:2px 7px;border-radius:4px}
.st.wait{color:var(--muted);border:1px solid var(--line)}.st.ok{color:var(--ok);border:1px solid var(--ok)}.st.bad{color:var(--bad);border:1px solid var(--bad)}
pre{white-space:pre-wrap;margin:8px 0 0;font:12px/1.5 ui-monospace,Menlo,monospace;color:var(--muted)}
button{background:none;border:1px solid var(--line);color:var(--text);border-radius:6px;padding:4px 10px;font-size:12px;cursor:pointer}
@media (max-width:560px){.grid,.row3{grid-template-columns:1fr}}
</style></head><body><main>
<h1>ReBirth &rarr; Octatrack</h1>
<p class="sub">Trage fi&#537;iere <b>.rbs</b> (ReBirth 2.0). Fiecare devine un proiect GARDEN: T1 ACID, T2 BASS 101, T5&ndash;T8 Rhythm 9 (BD SD CH OH).</p>
<div class="card">
 <div class="grid">
  <div><label>Proiect &#537;ablon (salvat pe OT)</label><input type="text" id="template"></div>
  <div><label>Folder destina&#539;ie (acela&#537;i Set ca &#537;ablonul)</label><input type="text" id="out"></div>
 </div>
 <div class="row3">
  <div><label>Bank (song-ul ia 2)</label><input type="number" id="bank" min="1" max="15" value="1"></div>
  <div><label>Octav&#259; T1</label><input type="number" id="oct1" min="-3" max="3" value="0"></div>
  <div><label>Octav&#259; T2</label><input type="number" id="oct2" min="-3" max="3" value="0"></div>
 </div>
 <div class="check"><input type="checkbox" id="octknob" checked><span>GARDEN36+: octavele pe knob-ul OCT, cen&#539;ii pe FINE la BASS (debifat: pentru GARDEN35)</span></div>
 <div class="check"><input type="checkbox" id="song" checked><span>Song-ul ReBirth &icirc;n arranger (ARR 1, se reia de la cap&#259;t); pornesti arranger-ul pe OT cu FUNC + PATTERN</span></div>
</div>
<div id="drop" class="card"><b>Trage aici fi&#537;ierele .rbs</b><br>sau d&#259; click ca s&#259; le alegi<input type="file" id="pick" accept=".rbs" multiple hidden></div>
<div class="card" id="list" hidden></div>
<script>
const D = __DEFAULTS__;
const $ = id => document.getElementById(id);
for (const k of ["template","out"]) { let v = null; try { v = localStorage.getItem("rbs2ot." + k); } catch (e) {} $(k).value = v || D[k]; $(k).onchange = () => { try { localStorage.setItem("rbs2ot." + k, $(k).value); } catch (e) {} }; }
const drop = $("drop"), pick = $("pick"), list = $("list");
drop.onclick = () => pick.click();
pick.onchange = () => run([...pick.files]);
drop.ondragover = e => { e.preventDefault(); drop.classList.add("on"); };
drop.ondragleave = () => drop.classList.remove("on");
drop.ondrop = e => { e.preventDefault(); drop.classList.remove("on"); run([...e.dataTransfer.files]); };
function el(tag, cls, text) { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }
async function run(files) {
  files = files.filter(f => /\.rbs$/i.test(f.name));
  if (!files.length) return;
  list.hidden = false;
  for (const f of files) {
    const item = el("div", "item"), head = el("div", "head"), st = el("span", "st wait", "…");
    head.append(st, el("span", "name", f.name));
    const dest = el("span", "dest"); head.append(dest);
    item.append(head); list.prepend(item);
    const q = new URLSearchParams({name: f.name, template: $("template").value, out: $("out").value,
      bank: $("bank").value, oct1: $("oct1").value, oct2: $("oct2").value, octknob: $("octknob").checked ? "1" : "0",
      song: $("song").checked ? "1" : "0"});
    let r;
    try { r = await (await fetch("/convert?" + q, {method: "POST", body: await f.arrayBuffer()})).json(); }
    catch (e) { r = {ok: false, log: String(e)}; }
    st.className = "st " + (r.ok ? "ok" : "bad"); st.textContent = r.ok ? "OK" : "EROARE";
    if (r.dest) { dest.textContent = r.dest; const b = el("button", null, "Arată în Finder");
      b.onclick = () => fetch("/reveal?" + new URLSearchParams({path: r.dest}), {method: "POST"}); head.append(b); }
    item.append(el("pre", null, r.log));
  }
  pick.value = "";
}
</script></main></body></html>
"""


def project_name(filename, out):
    """An Octatrack project name from a song's file name: A-Z 0-9 space _ -, 16 at most,
    a number appended while that folder exists."""
    stem = pathlib.Path(filename).stem.upper()
    base = re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 _-]", "", stem)).strip()[:16] or "REBIRTH"
    name, n = base, 2
    while (out / name).exists():
        tag = f" {n}"
        name, n = base[:16 - len(tag)] + tag, n + 1
    return name


def convert_upload(data: bytes, filename, template, out, o: Options):
    """-> (ok, dest or None, log). Each song converts in a process of its own, running this
    file as it is on disk now: a fix needs no server restart, and one song's failure
    cannot touch the server."""
    import subprocess
    out = pathlib.Path(out).expanduser()
    if not out.is_dir():
        return False, None, f"{out}: no such folder"
    with tempfile.TemporaryDirectory() as td:
        rbs = pathlib.Path(td) / "song.rbs"
        rbs.write_bytes(data)
        dest = out / project_name(filename, out)
        cmd = [sys.executable, str(pathlib.Path(__file__).resolve()), "convert", str(rbs),
               str(pathlib.Path(template).expanduser()), str(dest),
               "--bank", str(o.bank), "--oct1", str(o.oct1), "--oct2", str(o.oct2), "--arr", str(o.arr)]
        cmd += [] if o.oct_knob else ["--no-oct"]
        cmd += [] if o.song else ["--no-song"]
        r = subprocess.run(cmd, capture_output=True, text=True)
    log = (r.stdout + r.stderr).strip()
    if r.returncode and log and "Traceback" in log:      # a crash: keep its last line, not the trace
        log = "\n".join(l for l in log.splitlines() if not l.startswith((" ", "Traceback")))
    ok = r.returncode == 0
    return ok, (str(dest) if ok else None), log


def serve(template, out, port=8338, open_browser=True):
    import http.server
    import json
    import subprocess
    import urllib.parse
    import webbrowser
    page = PAGE.replace("__DEFAULTS__", json.dumps({"template": str(template), "out": str(out)}))

    class Handler(http.server.BaseHTTPRequestHandler):
        def _send(self, code, body, ctype):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if urllib.parse.urlparse(self.path).path == "/":
                self._send(200, page.encode(), "text/html; charset=utf-8")
            else:
                self._send(404, b"", "text/plain")

        def do_POST(self):
            u = urllib.parse.urlparse(self.path)
            q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
            body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
            if u.path == "/convert":
                try:
                    o = Options(bank=int(q.get("bank", 1)), oct1=int(q.get("oct1", 0)), oct2=int(q.get("oct2", 0)),
                                oct_knob=q.get("octknob", "1") == "1", song=q.get("song", "1") == "1")
                    if not 1 <= o.bank <= 15:
                        raise ValueError("bank: 1..15")
                    ok, dest, log = convert_upload(body, q.get("name", "song.rbs"), q.get("template", template),
                                                   q.get("out", out), o)
                except ValueError as e:
                    ok, dest, log = False, None, str(e)
                print(f"{'OK ' if ok else 'ERR'} {q.get('name')} -> {dest or '-'}", flush=True)
                self._send(200, json.dumps({"ok": ok, "dest": dest, "log": log}).encode(), "application/json")
            elif u.path == "/reveal" and q.get("path") and pathlib.Path(q["path"]).exists():
                subprocess.run(["open", "-R", q["path"]], check=False)
                self._send(204, b"", "text/plain")
            else:
                self._send(404, b"", "text/plain")

        def log_message(self, *args):
            pass

    try:
        srv = http.server.HTTPServer(("127.0.0.1", port), Handler)
    except OSError as e:
        sys.exit(f"rbs2ot: port {port} is taken ({e.strerror}) -- an older `serve` still running? "
                 f"Stop it with Ctrl-C in its terminal, or use --port {port + 1}")
    url = f"http://127.0.0.1:{port}/"
    print(f"rbs2ot: {url}  (template {template}, out {out}; Ctrl-C stops)", flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


def _opts(args):
    def val(flag, default):
        return int(args[args.index(flag) + 1]) if flag in args else default
    o = Options(bank=val("--bank", 1), oct1=val("--oct1", 0), oct2=val("--oct2", 0),
                bass_vol=val("--bass-vol", None), knobs="--keep-knobs" not in args,
                oct_knob="--no-oct" not in args, song="--no-song" not in args, arr=val("--arr", 1))
    if not 1 <= o.arr <= 8:
        sys.exit("--arr: 1..8")
    if not 1 <= o.bank <= 15:
        sys.exit("--bank: 1..15 (the song takes two banks)")
    return o


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    cmd = a[0]
    try:
        if cmd == "show" and len(a) >= 2:
            show(a[1], a[a.index("--pattern") + 1] if "--pattern" in a else None)
        elif cmd == "convert" and len(a) >= 4:
            convert(a[1], a[2], a[3], _opts(a), check_tracks="--no-check" not in a)
        elif cmd == "check" and len(a) >= 3:
            o = _opts(a)
            sys.exit(1 if check(a[1], parse_rbs(pathlib.Path(a[2]).read_bytes()), o) else 0)
        elif cmd == "serve":
            tpl = pathlib.Path(a[a.index("--template") + 1] if "--template" in a else "~/Desktop/Octatrack/ReBirth").expanduser()
            out = pathlib.Path(a[a.index("--out") + 1]).expanduser() if "--out" in a else tpl.parent
            serve(tpl, out, int(a[a.index("--port") + 1]) if "--port" in a else 8338, "--no-browser" not in a)
        elif cmd == "selftest":
            selftest()
        else:
            sys.exit(__doc__)
    except ValueError as e:
        sys.exit(f"rbs2ot: {e}")
