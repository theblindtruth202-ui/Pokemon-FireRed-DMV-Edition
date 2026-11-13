#!/usr/bin/env python3
"""Basic dependency-free validation for DMV v0.5 GBA artwork."""
from pathlib import Path
import struct
import zlib
import sys

ROOT = Path(__file__).resolve().parent.parent
FILES = {
"graphics/trainers/front_pics/red_front_pic.png": (64,64),
"graphics/trainers/front_pics/rival_early_front_pic.png": (64,64),
"graphics/trainers/front_pics/rival_late_front_pic.png": (64,64),
"graphics/trainers/front_pics/champion_rival_front_pic.png": (64,64),
"graphics/trainers/back_pics/red_back_pic.png": (64,320),
"graphics/oak_speech/red/pic.png": (64,96),
"graphics/oak_speech/rival/pic.png": (64,96),
"graphics/dmv/portraits/dame_talk.png": (64,64),
"graphics/dmv/portraits/dj_talk.png": (64,64),
"graphics/dmv/portraits/dame_win.png": (64,64),
"graphics/dmv/portraits/dj_win.png": (64,64),
"graphics/object_events/pics/people/blue.png": (144,32),
"graphics/object_events/pics/people/red_bike.png": (288,32),
"graphics/object_events/pics/people/red_surf.png": (288,32),
"graphics/object_events/pics/people/red_surf_run.png": (224,32),
"graphics/object_events/pics/people/red_fish.png": (384,32),
"graphics/object_events/pics/people/red_item.png": (144,32),
"graphics/object_events/pics/people/red_vs_seeker_bike.png": (192,32),
}
failures=0
for name,expected in FILES.items():
    try:
        raw=(ROOT/name).read_bytes()
        assert raw[:8]==b"\x89PNG\r\n\x1a\n", "not a PNG"
        pos=8;chunks={};palette_count=None;idats=[]
        while pos<len(raw):
            length=struct.unpack(">I",raw[pos:pos+4])[0]
            kind=raw[pos+4:pos+8];body=raw[pos+8:pos+8+length]
            saved=struct.unpack(">I",raw[pos+8+length:pos+12+length])[0]
            assert zlib.crc32(kind+body)&0xffffffff==saved, f"{kind!r} CRC mismatch"
            chunks[kind]=body
            if kind==b"IDAT":idats.append(body)
            pos+=12+length
            if kind==b"IEND":break
        w,h,bit_depth,color_type=struct.unpack(">IIBB",chunks[b"IHDR"][:10])
        assert (w,h)==expected, f"wrong dimensions {(w,h)}"
        assert color_type==3, "must be an indexed palette PNG"
        assert len(chunks[b"PLTE"])<=768, "invalid palette length"
        palette = chunks[b"PLTE"]
        pixels = zlib.decompress(b"".join(idats))
        if name.startswith("graphics/oak_speech/"):
            # 8bpp Oak portraits use BG palette BANK 4 (Dame) and 6 (DJ).
            # Pixels must contain the absolute GBA palette indices, not 1..15.
            assert bit_depth == 8, "Oak intro must be indexed 8bpp"
            slot = 64 if "/red/" in name else 96
            assert len(palette) // 3 >= slot + 16, "palette does not contain intro slot"
            used = set()
            assert len(pixels) == h * (w + 1), "unexpected intro pixel data"
            for row in range(h):
                start = row * (w + 1)
                assert pixels[start] == 0, "expected unfiltered indexed intro image"
                used.update(pixels[start + 1:start + 1 + w])
            assert all(c == 0 or slot <= c < slot + 16 for c in used), (
                f"Oak sprite uses wrong BG palette index: {sorted(used)}")
            pal_path = ROOT / name.replace("/pic.png", "/pal.pal")
            lines = pal_path.read_text().splitlines()
            expected_pal = [tuple(map(int, line.split())) for line in lines[3:19]]
            assert len(expected_pal) == 16, "Oak JASC palette missing first 16 colors"
            for i, rgb in enumerate(expected_pal):
                actual_rgb = tuple(palette[(slot+i)*3:(slot+i+1)*3])
                assert actual_rgb == rgb, f"Oak palette mismatch at color {i}: {actual_rgb} vs {rgb}"
        else:
            assert len(palette)//3<=16, "too many colors for 4bpp"
        print("OK  ",name, f"{w}x{h}")
    except Exception as exc:
        failures+=1
        print("FAIL",name,str(exc))
print("Art validation:", "PASS" if not failures else f"{failures} errors")
sys.exit(bool(failures))
