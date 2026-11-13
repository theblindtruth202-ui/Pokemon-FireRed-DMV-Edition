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
        assert len(chunks[b"PLTE"])//3<=16, "too many colors for 4bpp"
        zlib.decompress(b"".join(idats))
        print("OK  ",name, f"{w}x{h}")
    except Exception as exc:
        failures+=1
        print("FAIL",name,str(exc))
print("Art validation:", "PASS" if not failures else f"{failures} errors")
sys.exit(bool(failures))
