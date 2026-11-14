#!/usr/bin/env python3
"""
Standalone build script to render base_seal.png with embedded LSB passkey
and build initial distribution files.
"""

import io
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw

PASSKEY = b"MOA_ANBESSA_1888"


def build_seal():
    base_dir = Path(__file__).resolve().parent.parent
    dist_dir = base_dir / "dist"
    src_dir = base_dir / "src"
    dist_dir.mkdir(parents=True, exist_ok=True)

    flag = "AdwaCTF{m04_4nb3554_z31mn3g3d3_y1hud4}"
    (base_dir / "flag.txt").write_text(flag + "\n", encoding="utf-8")

    # 1. Create a 400x400 image representing the Imperial Seal
    width, height = 400, 400
    img = Image.new("RGB", (width, height), color=(245, 235, 220))
    draw = ImageDraw.Draw(img)

    # Ethiopian Tricolor bands (Green, Yellow, Red)
    draw.rectangle([20, 20, 380, 80], fill=(0, 150, 60))
    draw.rectangle([20, 80, 380, 140], fill=(250, 210, 0))
    draw.rectangle([20, 140, 380, 200], fill=(220, 20, 30))

    # Border and seal text
    draw.rectangle([15, 15, 385, 385], outline=(80, 50, 20), width=4)
    draw.text((100, 230), "IMPERIAL SEAL OF ETHIOPIA", fill=(40, 20, 10))
    draw.text((120, 260), "MOA ANBESSA ZE'IMNEGEDE YIHUDA", fill=(60, 30, 15))
    draw.text((90, 290), "BATTLE OF ADWA - YEKATIT 1888", fill=(80, 40, 20))
    draw.text((140, 330), "EMPEROR MENELIK II", fill=(100, 50, 25))

    # 2. LSB Steganography in Red channel (passkey)
    passkey_str = f"IMPERIAL_PASSKEY={PASSKEY.decode()}\x00"
    hint_bits = []
    for c in passkey_str:
        for b in range(8):
            hint_bits.append((ord(c) >> b) & 1)

    pixels = img.load()
    bit_idx = 0
    for y in range(height):
        for x in range(width):
            if bit_idx < len(hint_bits):
                r, g, b = pixels[x, y]
                r = (r & ~1) | hint_bits[bit_idx]
                pixels[x, y] = (r, g, b)
                bit_idx += 1

    # Save base PNG for container generator
    img.save(src_dir / "base_seal.png", format="PNG")

    png_buf = io.BytesIO()
    img.save(png_buf, format="PNG")
    raw_png = png_buf.getvalue()

    # 3. Create XOR-encrypted proclamation
    proclamation_plaintext = (
        f"IMPERIAL WAR PROCLAMATION (KITET AWAJ)\n"
        f"Issued by His Imperial Majesty Atse Menelik II, King of Kings of Ethiopia:\n"
        f"Courier Verification ID: imperial_courier_adwa\n\n"
        f"An enemy has come from across the sea to subvert our country and destroy our faith.\n"
        f"He has begun to encroach on our borders. Now, rise up and defend your heritage!\n\n"
        f"Royal Order Clearance Flag:\n"
        f"{flag}\n"
    )
    enc_bytes = bytes(
        b ^ PASSKEY[i % len(PASSKEY)]
        for i, b in enumerate(proclamation_plaintext.encode("utf-8"))
    )
    hex_ciphertext = enc_bytes.hex()

    carved_file_content = (
        f"===============================================================================\n"
        f"IMPERIAL WAR PROCLAMATION (KITET AWAJ) - ENCRYPTED ARCHIVE\n"
        f"COURIER REGISTRATION: imperial_courier_adwa\n"
        f"===============================================================================\n\n"
        f"NOTICE TO COURIER:\n"
        f"This imperial decree has been enciphered by the Royal Scribes of Emperor Menelik II.\n"
        f"The decryption key is the IMPERIAL_PASSKEY embedded within the least significant\n"
        f"bits (LSB) of the seal's visual image raster (Red channel).\n\n"
        f"To decipher:\n"
        f"  plaintext = XOR(hex_decode(CIPHERTEXT), imperial_passkey)\n\n"
        f"CIPHERTEXT (HEX):\n"
        f"{hex_ciphertext}\n"
        f"===============================================================================\n"
    )

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("imperial_proclamation.txt", carved_file_content)
    raw_zip = zip_buf.getvalue()

    final_data = raw_png + raw_zip
    seal_path = dist_dir / "imperial_seal.png"
    seal_path.write_bytes(final_data)

    print(f"[+] Built {seal_path} ({len(final_data)} bytes: PNG={len(raw_png)}, ZIP={len(raw_zip)})")


if __name__ == "__main__":
    build_seal()
