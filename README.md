# ReBirth → Octatrack

Transformă song-urile **ReBirth RB-338 2.0** (`.rbs`) în proiecte **Elektron Octatrack** pentru
firmware-ul **GARDEN** (octabam). Rulează în întregime în browser: Python-ul convertorului e
încărcat prin [Pyodide](https://pyodide.org), iar fișierele tale nu pleacă din calculator.

**[Deschide aplicația](https://alexandrubelc.github.io/rebirth2octatrack/)** (după publicarea pe GitHub Pages).

## Ce face

| ReBirth | Octatrack (GARDEN) |
|---|---|
| primul TB-303 | **T1 ACID**: note (lock PTCH), slide (lock trigless pe pasul următor), accent (lock ACC) |
| al doilea TB-303 | **T2 BASS 101**: la fel; accentul e un lock AMP VOL |
| 909 BD / SD / CH / OH | **T5–T8 Rhythm 9** (CH = un OH scurtat din șablon) |
| knob-urile 303 (Tune, Cutoff, Reso, EnvMod, Decay, Accent) | Part-ul: prin legile Re:Phase, în tabelele engine-urilor; Tune → OCT + note + FINE |
| pattern-urile A1–D8 | bank-urile A și B, pattern-urile 1–16 |
| song-ul | **ARR 1**: rânduri cu repetiții, apoi `LOOP 000/∞`; combinațiile de pattern-uri primesc pattern-uri proprii din bank-ul C în sus |
| tempo-ul | tempo-ul proiectului |

Nu se convertesc: celelalte voci 909, 808-ul, mute-urile și automatizările din song, shuffle-ul,
efectele. Fișierele ReBirth 1.5 nu sunt suportate.

## Cum o folosești

1. **Proiectul șablon** (o singură dată): pe Octatrack, cu GARDEN36 sau mai nou, faci un proiect cu
   sample-urile marker `ACID.wav`, `BASS.wav`, `BD.wav`, `SD.wav`, `OH.wav` în sloturi FLEX, iar în
   bank A: T1 ACID, T2 BASS, T5 BD, T6 SD, T7 OH (cu DEC mic), T8 OH. Îl salvezi și îl copiezi de
   pe card.
2. În pagină: **Alege folderul șablon** (browserul îl ține minte), apoi **tragi `.rbs`-urile**.
3. **Descarcă .zip**, îl dezarhivezi în folderul Set-ului de pe CompactFlash, lângă șablon
   (sample-urile sunt căutate în `../AUDIO`).
4. Pe Octatrack: PROJECT → CHANGE; arranger-ul pornește cu FUNC + PATTERN (MK1).

Pentru GARDEN35 debifează „GARDEN36+”: octavele trec atunci în note, iar BASS nu primește FINE.

## Linia de comandă

Același convertor, fără browser (Python 3.10+, doar biblioteca standard):

```bash
python3 py/rbs2ot.py convert SONG.rbs SABLON/ PROIECT_NOU/
python3 py/rbs2ot.py show SONG.rbs
python3 py/rbs2ot.py selftest
```

## Local

```bash
python3 -m http.server 8000      # apoi http://127.0.0.1:8000/
```

## Proveniență

- `py/rbs2ot.py` — convertorul; formatul `.rbs` din importul RBS al aplicației Re:Phase (iOS),
  formatul de aranjament decodat din salvarea firmware-ului rulat în emulatorul octabam.
- `py/ot_bank.py`, `py/ot_project.py` — din [octabam](https://github.com/sambanks/octabam)
  (`tools/hw/`), neschimbate, sub licența MIT a autorului lor (vezi `THIRD_PARTY.md`).

Proiect independent, neafiliat cu Elektron sau Reason Studios. *Octatrack* e marcă Elektron Music
Machines; *ReBirth RB-338* e marcă Reason Studios (fost Propellerhead Software). Mărcile sunt folosite
doar ca să numească formatele cu care lucrează aplicația.
