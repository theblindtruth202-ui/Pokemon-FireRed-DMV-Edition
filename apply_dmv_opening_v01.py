#!/usr/bin/env python3
"""Pokémon FireRed: DMV Edition — Opening Scene Patch 0.1.

A safe, idempotent source-file patch for the public pret/pokefirered fork.
Run from repository root with: python3 apply_dmv_opening_v01.py
Use --check to show whether paths/markers exist before modifying anything.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def update_section(src: str, label: str, lines: list[str]) -> str:
    """Replace the .string lines of one existing text section, without changing its label."""
    marker = f"{label}::\n"
    start = src.find(marker)
    if start == -1:
        raise ValueError(f"Missing FireRed script label: {label}")
    end = src.find("\n\n", start)
    if end == -1:
        end = len(src)
    previous = src[start:end]
    # Preserve game text script syntax; lines include literal \n and \p control codes.
    updated = marker + "\n".join('    .string "' + line + '"' for line in lines)
    if previous == updated:
        return src
    return src[:start] + updated + src[end:]


def update_region(src: str, section_id: str, old: str, new: str) -> str:
    pat = rf'("id": "{re.escape(section_id)}",\s*"name": ")([^"\n]+)(")'
    found = list(re.finditer(pat, src))
    if len(found) != 1:
        raise ValueError(f"Expected exactly one matching region {section_id}, found {len(found)}")
    current = found[0].group(2)
    if current not in (old, new):
        raise ValueError(f"Unexpected current name for {section_id}: {current!r}")
    return re.sub(pat, lambda m: m.group(1) + new + m.group(3), src, count=1)


SECTIONS = {
    "data/maps/PalletTown/text.inc": {
        "PalletTown_Text_OakDontGoOut": [
            r"OAK: Hold up!\n", r"Not out there alone!$",
        ],
        "PalletTown_Text_OakGrassUnsafeNeedMon": [
            r"OAK: Wild POKéMON are in the\n", r"grass outside ANACOSTIA!\p",
            r"You need a partner first.\p", r"Come with me to the lab!$",
        ],
        "PalletTown_Text_OakPokemonResearchLab": [
            r"PROF. OAK'S\n", r"ANACOSTIA RESEARCH LAB$",
        ],
        "PalletTown_Text_TownSign": [
            r"ANACOSTIA\n", r"SOUTHEAST WASHINGTON, D.C.\p",
            r"Your journey starts here!$",
        ],
        "PalletTown_Text_PlayersHouse": [r"DAME FLOSS'S HOUSE$"],
        "PalletTown_Text_RivalsHouse": [r"DJ THE PARK BOY'S HOUSE$"],
    },
    "data/maps/PalletTown_PlayersHouse_1F/text.inc": {
        "PalletTown_PlayersHouse_1F_Text_AllBoysLeaveOakLookingForYou": [
            r"MOM: Ready for today?\p", r"ANACOSTIA is where you start.\n",
            r"But the whole DMV is waiting!\p", r"PROF. OAK is looking for you.\n",
            r"DJ's headed over there, too!$",
        ],
        "PalletTown_PlayersHouse_1F_Text_AllGirlsLeaveOakLookingForYou": [
            r"MOM: Ready for today?\p", r"ANACOSTIA is where you start.\n",
            r"But the whole DMV is waiting!\p", r"PROF. OAK is looking for you.\n",
            r"DJ's headed over there, too!$",
        ],
        "PalletTown_PlayersHouse_1F_Text_YouShouldTakeQuickRest": [
            r"MOM: {PLAYER}!\n", r"Rest up before you head out.$",
        ],
        "PalletTown_PlayersHouse_1F_Text_LookingGreatTakeCare": [
            r"MOM: Your team looks great!\n", r"Take care out in the DMV.$",
        ],
    },
    "data/maps/PalletTown_PlayersHouse_2F/text.inc": {
        "PalletTown_PlayersHouse_2F_Text_PlayedWithNES": [
            r"{PLAYER} checked the game\n", r"system in the bedroom.\p",
            r"Time to explore ANACOSTIA!$",
        ],
    },
    "data/maps/PalletTown_ProfessorOaksLab/text.inc": {
        "PalletTown_ProfessorOaksLab_Text_RivalGrampsIsntAround": [
            r"{RIVAL}: Hey, {PLAYER}!\n", r"Oak still isn't here, moe.$",
        ],
        "PalletTown_ProfessorOaksLab_Text_RivalGoChoosePlayer": [
            r"{RIVAL}: You pick first.\p", r"But don't think I'm going\n",
            r"easy on you!$",
        ],
        "PalletTown_ProfessorOaksLab_Text_RivalIllTakeThisOneThen": [
            r"{RIVAL}: Aight, this one's mine!$",
        ],
        "PalletTown_ProfessorOaksLab_Text_RivalLetsCheckOutMons": [
            r"{RIVAL}: Hold up, {PLAYER}!\p", r"We grew up on the same block.\n",
            r"Let's see who's really ready!$",
        ],
        "PalletTown_ProfessorOaksLab_Text_RivalGoToughenMyMon": [
            r"{RIVAL}: I'm training harder.\n", r"This isn't over!\p",
            r"See you up the road, moe!$",
        ],
        "PalletTown_ProfessorOaksLab_Text_OakThreeMonsChooseOne": [
            r"OAK: Welcome to ANACOSTIA!\p",
            r"Every great journey starts\n", r"with one trusted partner.\p",
            r"I've prepared three POKéMON.\n", r"Pick the one for you.\p",
            r"{RIVAL}, you'll pick next.\n", r"Ready, {PLAYER}?$",
        ],
    },
    "data/maps/Route1/text.inc": {
        "Route1_Text_WorkAtPokeMartTakeSample": [
            r"Hey! I work at ALABAMA\n", r"CONVENIENCE in CONGRESS HTS.\p",
            r"We have supplies for folks\n", r"traveling across the DMV.\p",
            r"Here's a sample for you!$",
        ],
        "Route1_Text_ComeSeeUsIfYouNeedPokeBalls": [
            r"Need POKé BALLS or POTIONS?\n", r"Come visit our corner store!$",
        ],
        "Route1_Text_CanJumpFromLedges": [
            r"See those ledges by the road?\p", r"Hop down to take a shortcut\n",
            r"back to ANACOSTIA.$",
        ],
        "Route1_Text_RouteSign": [
            r"ROUTE 1\n", r"ANACOSTIA - CONGRESS HTS.$",
        ],
    },
}

REGIONS = {
    "MAPSEC_PALLET_TOWN": ("PALLET TOWN", "ANACOSTIA"),
    "MAPSEC_VIRIDIAN_CITY": ("VIRIDIAN CITY", "CONGRESS HEIGHTS"),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check markers but write nothing")
    args = parser.parse_args()
    sources: dict[Path, str] = {}
    paths = [Path(p) for p in SECTIONS]
    paths.append(Path("src/data/region_map/region_map_sections.json"))
    if not Path("Makefile").is_file():
        print("ERROR: Run this script from the root of your Pokémon FireRed fork (where Makefile is).", file=sys.stderr)
        return 2
    for path in paths:
        if not path.is_file():
            print(f"ERROR: Expected FireRed file not found: {path}", file=sys.stderr)
            return 2
        sources[path] = path.read_text(encoding="utf-8")

    changes: dict[Path, str] = {}
    try:
        for rel, section_dict in SECTIONS.items():
            path = Path(rel)
            content = sources[path]
            for label, text_lines in section_dict.items():
                content = update_section(content, label, text_lines)
            changes[path] = content
        region_path = Path("src/data/region_map/region_map_sections.json")
        region_content = sources[region_path]
        for region_id, (old, new) in REGIONS.items():
            region_content = update_region(region_content, region_id, old, new)
        changes[region_path] = region_content
    except ValueError as exc:
        print(f"ERROR: No files changed. {exc}", file=sys.stderr)
        return 3

    modified = [p for p in paths if changes[p] != sources[p]]
    if args.check:
        print("[CHECK ONLY] All expected source files and text markers exist.")
    else:
        for path in modified:
            path.write_text(changes[path], encoding="utf-8", newline="\n")
        print("Opening Scene v0.1 source patch applied successfully.")
    for path in modified:
        print(f"  {'WOULD UPDATE' if args.check else 'UPDATED'}: {path}")
    if not modified:
        print("Already applied. No changes were necessary.")
    print("Next step: git diff --check, then build/test in a configured pokefirered environment.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
