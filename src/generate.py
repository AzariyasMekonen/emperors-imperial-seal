#!/usr/bin/env python3
"""
On-Demand Dynamic Challenge File Generator for The Emperor's Imperial Seal (AdwaCTF).

Dual-layered forensics:
  1. Pixel Raster LSB (Red channel): holds IMPERIAL_PASSKEY=MOA_ANBESSA_1888
  2. Appended Container (past PNG IEND): ZIP archive containing XOR-encrypted proclamation
     requiring the raster passkey to decipher.

Environment variables:
  - FLAG: Dynamic participant-specific flag (e.g. 'AdwaCTF{...}')
  - USER_ID: Optional participant or team identifier
  - OUTPUT_FILENAME: Primary output file name (default: 'imperial_seal.png')
  - OUTPUT_DIR: Target directory to write to (default: 'output' or '/output')
"""

import io
import os
import sys
import zipfile
from pathlib import Path

PASSKEY = b"MOA_ANBESSA_1888"


def get_flag() -> str:
    flag = os.environ.get("FLAG", "").strip()
    if flag:
        return flag

    candidates = ["flag.txt", "/app/flag.txt", "../flag.txt"]
    for c in candidates:
        if os.path.isfile(c):
            try:
                with open(c, "r", encoding="utf-8") as f:
                    val = f.read().strip()
                    if val:
                        return val
            except OSError:
                pass

    return "AdwaCTF{m04_4nb3554_z31mn3g3d3_y1hud4}"


def get_base_png() -> bytes:
    """
    Load pre-rendered base seal image containing visual art and Red-channel LSB passkey.
    Falls back to dynamic PIL rendering if Pillow is available and base image is missing.
    """
    src_dir = Path(__file__).resolve().parent
    base_candidates = [
        src_dir / "base_seal.png",
        Path("/app/src/base_seal.png"),
        Path("base_seal.png"),
    ]
    for p in base_candidates:
        if p.is_file():
            try:
                data = p.read_bytes()
                if data.startswith(b"\x89PNG\r\n\x1a\n"):
                    return data
            except OSError:
                pass

    try:
        from PIL import Image, ImageDraw

        width, height = 400, 400
        img = Image.new("RGB", (width, height), color=(245, 235, 220))
        draw = ImageDraw.Draw(img)

        # Ethiopian Tricolor (Green, Yellow, Red)
        draw.rectangle([20, 20, 380, 80], fill=(0, 150, 60))
        draw.rectangle([20, 80, 380, 140], fill=(250, 210, 0))
        draw.rectangle([20, 140, 380, 200], fill=(220, 20, 30))

        # Borders and inscription
        draw.rectangle([15, 15, 385, 385], outline=(80, 50, 20), width=4)
        draw.text((100, 230), "IMPERIAL SEAL OF ETHIOPIA", fill=(40, 20, 10))
        draw.text((120, 260), "MOA ANBESSA ZE'IMNEGEDE YIHUDA", fill=(60, 30, 15))
        draw.text((90, 290), "BATTLE OF ADWA - YEKATIT 1888", fill=(80, 40, 20))
        draw.text((140, 330), "EMPEROR MENELIK II", fill=(100, 50, 25))

        # Red-channel LSB: passkey
        passkey_str = f"IMPERIAL_PASSKEY={PASSKEY.decode()}\x00"
        bits = []
        for c in passkey_str:
            for b in range(8):
                bits.append((ord(c) >> b) & 1)

        pixels = img.load()
        bit_idx = 0
        for y in range(height):
            for x in range(width):
                if bit_idx < len(bits):
                    r, g, b = pixels[x, y]
                    r = (r & ~1) | bits[bit_idx]
                    pixels[x, y] = (r, g, b)
                    bit_idx += 1

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        raise RuntimeError("No base_seal.png found and Pillow is not installed.")


def main():
    flag = get_flag()
    user_id = os.environ.get("USER_ID", "imperial_courier_adwa").strip()
    here = Path(__file__).resolve().parent.parent

    # Determine primary output target directory
    output_path = os.environ.get("OUTPUT_PATH", "").strip()
    if output_path:
        target_file = Path(output_path).resolve()
        target_dir = target_file.parent
        target_seal_name = target_file.name
    elif len(sys.argv) > 1 and sys.argv[1].strip():
        arg_path = Path(sys.argv[1].strip()).resolve()
        if arg_path.is_dir() or sys.argv[1].endswith("/"):
            target_dir = arg_path
            target_seal_name = "imperial_seal.png"
        else:
            target_dir = arg_path.parent
            target_seal_name = arg_path.name
    else:
        env_dir = os.environ.get("OUTPUT_DIR", "").strip()
        if env_dir:
            target_dir = Path(env_dir).resolve()
        elif Path("/output").is_dir():
            target_dir = Path("/output")
        else:
            target_dir = here / "output"
        target_seal_name = os.environ.get("OUTPUT_FILENAME", "imperial_seal.png").strip()

    target_dir.mkdir(parents=True, exist_ok=True)

    # 1. Base PNG bytes (contains LSB IMPERIAL_PASSKEY in Red channel)
    raw_png = get_base_png()

    # 2. Dynamic proclamation plaintext
    proclamation_plaintext = (
        f"IMPERIAL WAR PROCLAMATION (KITET AWAJ)\n"
        f"Issued by His Imperial Majesty Atse Menelik II, King of Kings of Ethiopia:\n"
        f"Courier Verification ID: {user_id}\n\n"
        f"An enemy has come from across the sea to subvert our country and destroy our faith.\n"
        f"He has begun to encroach on our borders. Now, rise up and defend your heritage!\n\n"
        f"Royal Order Clearance Flag:\n"
        f"{flag}\n"
    )

    # 3. XOR encipher proclamation with PASSKEY
    enc_bytes = bytes(
        b ^ PASSKEY[i % len(PASSKEY)]
        for i, b in enumerate(proclamation_plaintext.encode("utf-8"))
    )
    hex_ciphertext = enc_bytes.hex()

    # Content of imperial_proclamation.txt inside the carved ZIP
    carved_file_content = (
        f"===============================================================================\n"
        f"IMPERIAL WAR PROCLAMATION (KITET AWAJ)\n"
        f"COURIER REGISTRATION: {user_id}\n"
        f"===============================================================================\n\n"
        f"This royal decree was enciphered by the Imperial Court Scribes.\n"
        f"Only those with the Imperial Passkey may read the Emperor's words.\n\n"
        f"CIPHERTEXT (HEX):\n"
        f"{hex_ciphertext}\n"
        f"===============================================================================\n"
    )

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("imperial_proclamation.txt", carved_file_content)
    raw_zip = zip_buf.getvalue()

    # Concatenate PNG + ZIP payload (Forensic file carving)
    final_data = raw_png + raw_zip

    # Companion intelligence dossier
    dossier_content = (
        "===============================================================================\n"
        "IMPERIAL COURIER INTELLIGENCE DOSSIER\n"
        "RECONNAISSANCE HEADQUARTERS - SOLODA VANTAGE\n"
        f"COURIER REGISTRATION: {user_id}\n"
        "===============================================================================\n\n"
        "HISTORICAL INCIDENT REPORT:\n"
        "A swift royal messenger was intercepted near the Italian lines at Mount Raio,\n"
        "carrying an illuminated parchment of the Imperial Seal of Ethiopia (Moa Anbessa).\n\n"
        "General Baratieri's staff inspected the document and dismissed it as ceremonial art.\n"
        "However, our lookouts report that Emperor Menelik's scribes concealed a secret\n"
        "imperial decree within the artifact itself.\n\n"
        "Examine the courier's banner and recover the hidden decree.\n"
        "===============================================================================\n"
    )

    env_dir = os.environ.get("OUTPUT_DIR", "").strip()

    dirs_to_write = {target_dir}
    if Path("/output").is_dir():
        dirs_to_write.add(Path("/output"))

    if (here / "output").is_dir() and not env_dir and not output_path and len(sys.argv) <= 1:
        dirs_to_write.add(here / "output")

    for d in dirs_to_write:
        try:
            d.mkdir(parents=True, exist_ok=True)
            seal_file = d / target_seal_name
            with open(seal_file, "wb") as f:
                f.write(final_data)
            try:
                os.chmod(seal_file, 0o666)
            except OSError:
                pass

            dossier_file = d / "courier_dossier.txt"
            with open(dossier_file, "w", encoding="utf-8") as f:
                f.write(dossier_content)
            try:
                os.chmod(dossier_file, 0o666)
            except OSError:
                pass
        except OSError:
            pass

    if (here / "dist").is_dir() and not env_dir and not output_path and len(sys.argv) <= 1:
        try:
            with open(here / "dist" / "imperial_seal.png", "wb") as f:
                f.write(final_data)
            with open(here / "dist" / "courier_dossier.txt", "w", encoding="utf-8") as f:
                f.write(dossier_content)
        except OSError:
            pass

    print(f"[generator] user_id={user_id}")
    print(f"[generator] target_dir={target_dir}")
    print(f"[generator] generated output files: {target_seal_name}, courier_dossier.txt")
    print(f"[generator] total size={len(final_data)} bytes (PNG={len(raw_png)}, ZIP={len(raw_zip)})")


if __name__ == "__main__":
    main()
