# The Emperor's Imperial Seal (Forensics / Dynamic Generator, Easy-Medium)

**Story:**
Before the decisive battle at Adwa, Emperor Menelik II issued his historic national mobilization proclamation (*Kitet* Awaj) summoning warriors from every corner of Ethiopia (Shoa, Gojjam, Wollo, Tigray, Begemder, Harar, and the Oromo cavaliers). Couriers carried copies sealed with the Lion of Judah (*Moa Anbessa*) emblem. An intercepted courier dispatch conceals the secret imperial war decree.

## Mechanics
- This challenge supports the CTF platform's **On-Demand Dynamic File Generator** to generate personalized challenge files with participants' unique dynamic flags.
- Players receive two files in `output/`:
  - `output/imperial_seal.png`: A valid PNG image depicting the Ethiopian imperial tricolor and imperial seal.
  - `output/courier_dossier.txt`: An intelligence dossier describing the intercepted courier and clues.
- Forensic analysis reveals two layers:
  1. **LSB Steganography** in the Red channel giving a pointer:
     `"LSB_KEY: Carve the appended zip archive past the IEND marker!"`.
  2. **Trailing PK-ZIP archive** appended immediately after the standard PNG `IEND\xae\x42\x60\x82` chunk.
- Inside the carved ZIP is `imperial_proclamation.txt` containing Emperor Menelik's proclamation and the participant's flag.

## Dynamic File Generator Settings
- **Type**: `dynamic`
- **Output Filename**: `imperial_seal.png`
- **Container Image**: `ghcr.io/azariyasmekonen/emperors-imperial-seal:latest`
- **Environment Variables**:
  - `FLAG`: Dynamic participant flag (e.g. `AdwaCTF{...}`)
  - `USER_ID`: Unique participant or team identifier
  - `OUTPUT_DIR`: Target directory (defaults to `/output`)
  - `OUTPUT_FILENAME`: Name of output file inside `/output/` (defaults to `imperial_seal.png`)

## Solution Walkthrough
1. Inspect the image with `binwalk`, `foremost`, or hex inspection:
   ```bash
   binwalk imperial_seal.png
   # Or find the IEND marker
   grep -aob "IEND" imperial_seal.png
   ```
2. Carve all bytes past the PNG `IEND` chunk (`b"IEND\xae\x42\x60\x82"`), which begin with the ZIP signature `PK\x03\x04`.
3. Extract `imperial_proclamation.txt` from the carved archive.
4. (Optional) Extract the 1-bit LSB sequence from the Red channel to read the courier's hidden routing hint.
5. Recover the flag: `AdwaCTF{m04_4nb3554_z31mn3g3d3_y1hud4}`.

Run `solve/solve.py` to solve automatically.
