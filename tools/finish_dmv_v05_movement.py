#!/usr/bin/env python3
"""Recolor stock Red movement frames using Dame Floss' custom palette.
Keeps every frame's original silhouette and direction. Requires only stdlib.
"""
from pathlib import Path
import struct
import zlib

FILES = (
    'red_bike.png', 'red_surf.png', 'red_surf_run.png',
    'red_fish.png', 'red_item.png', 'red_vs_seeker_bike.png',
)
# Stock Red's palette index -> Dame Floss palette index.
# 0 must stay transparent.
LOOKUP = (0, 2, 10, 8, 9, 2, 1, 4, 7, 3, 12, 5, 6, 11, 7, 1)
ROOT = Path(__file__).resolve().parent.parent
PIC_DIR = ROOT / 'graphics/object_events/pics/people'
JASC = ROOT / 'graphics/object_events/palettes/player.pal'
BACKUP = ROOT / 'backups/v05-artwork/original-movement'

def chunk(kind, body):
    return (struct.pack('>I', len(body)) + kind + body
            + struct.pack('>I', zlib.crc32(kind + body) & 0xFFFFFFFF))

def read_chunks(raw):
    assert raw[:8] == b'\x89PNG\r\n\x1a\n', 'Not PNG'
    pos = 8
    found = []
    while pos < len(raw):
        size = struct.unpack_from('>I', raw, pos)[0]
        kind = raw[pos + 4:pos + 8]
        body = raw[pos + 8:pos + 8 + size]
        crc = struct.unpack_from('>I', raw, pos + 8 + size)[0]
        assert zlib.crc32(kind + body) & 0xFFFFFFFF == crc, f'{kind!r} CRC error'
        found.append((kind, body))
        pos += 12 + size
        if kind == b'IEND':
            break
    return found

def unfilter(filt, row, prev):
    output = bytearray(len(row))
    for i, v in enumerate(row):
        left = output[i - 1] if i else 0
        above = prev[i]
        upper_left = prev[i - 1] if i else 0
        if filt == 0: estimate = 0
        elif filt == 1: estimate = left
        elif filt == 2: estimate = above
        elif filt == 3: estimate = (left + above) // 2
        elif filt == 4:
            p = left + above - upper_left
            d1, d2, d3 = abs(p - left), abs(p - above), abs(p - upper_left)
            estimate = left if d1 <= d2 and d1 <= d3 else (above if d2 <= d3 else upper_left)
        else: raise ValueError(f'PNG filter {filt} not supported')
        output[i] = (v + estimate) & 255
    return output

def recolor(raw, palette):
    chunks = read_chunks(raw)
    ihdr = next(data for kind, data in chunks if kind == b'IHDR')
    width, height, depth, color = struct.unpack_from('>IIBB', ihdr)
    assert depth == 4 and color == 3, 'Expected indexed 4-bit PNG'
    stride = (width + 1) // 2
    compressed = b''.join(body for kind, body in chunks if kind == b'IDAT')
    scanlines = zlib.decompress(compressed)
    dest = bytearray()
    previous = bytearray(stride)
    pos = 0
    for _ in range(height):
        filtered = scanlines[pos]
        row = unfilter(filtered, scanlines[pos+1:pos+1+stride], previous)
        previous = row
        pos += stride + 1
        # High and low nibble each encode an indexed pixel.
        new_row = ((LOOKUP[p >> 4] << 4) | LOOKUP[p & 15] for p in row)
        dest.append(0)
        dest.extend(new_row)
    assert pos == len(scanlines), 'Unexpected scanline data'
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
            + chunk(b'PLTE', palette) + chunk(b'tRNS', b'\x00')
            + chunk(b'IDAT', zlib.compress(dest, 9)) + chunk(b'IEND', b''))

def main():
    lines = JASC.read_text().splitlines()
    assert lines[:3] == ['JASC-PAL', '0100', '16'], 'Unexpected player palette'
    entries = [tuple(map(int, s.split())) for s in lines[3:19]]
    assert len(entries) == 16 and all(len(c) == 3 for c in entries)
    palette = bytes(x for entry in entries for x in entry)
    BACKUP.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        source = PIC_DIR / name
        backup = BACKUP / name
        if backup.exists():
            print('SKIP', name, '(backup exists; do not recolor twice)')
            continue
        original = source.read_bytes()
        result = recolor(original, palette)
        read_chunks(result)
        backup.write_bytes(original)
        source.write_bytes(result)
        print('OK  ', name)
    print('Dame Floss alternate movement palette remapping complete.')

if __name__ == '__main__':
    main()
