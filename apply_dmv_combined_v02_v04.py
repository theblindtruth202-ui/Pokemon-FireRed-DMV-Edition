#!/usr/bin/env python3
"""Pokémon FireRed DMV Edition — combined v0.2–0.4 foundation patch.

Run at the root of the user's pret/pokefirered fork.
--check performs a dry run. --apply makes the edits. Edits are not committed automatically.
This patch intentionally DOES NOT expand PLAYER_NAME_LENGTH and does not yet implement
random starters or new map tiles.  Those require separately tested engine work.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent

# All writes are prevalidated in memory to avoid partial application on mismatch.
def replace_exact(source: str, old: str, new: str, name: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"{name}: expected one original text match, found {source.count(old)}")
    return source.replace(old, new, 1)

def replace_function(src: str, name: str, body: str) -> str:
    signature = f"static void {name}(u8 taskId)\n{{"
    pos = src.find(signature)
    if pos < 0 or src.count(signature) != 1:
        raise ValueError(f"Could not uniquely find function: {name}")
    brace = src.find('{', pos)
    depth = 0
    end = None
    for i in range(brace, len(src)):
        ch = src[i]
        if ch == '{': depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end is None: raise ValueError(f"Unterminated function: {name}")
    return src[:pos] + signature + "\n" + body.strip('\n') + "\n}" + src[end:]

def patch_oak(src: str) -> str:
    # Save-compatible internal identifiers: full display names will be addressed
    # by a separate name/UI refactor; expanding PLAYER_NAME_LENGTH directly can
    # change save formats and overflow numerous fixed-size trainer name fields.
    src = replace_function(src, 'Task_OakSpeech_AskPlayerGender', '''
    s16 *data = gTasks[taskId].data;
    if (tTrainerPicFadeState != 0)
    {
        if (tTimer != 0)
        {
            tTimer--;
        }
        else
        {
            gSaveBlock2Ptr->playerGender = MALE;
            tTrainerPicPosX = -60;
            ClearTrainerPic();
            ClearDialogWindowAndFrame(WIN_INTRO_TEXTBOX, TRUE);
            FillBgTilemapBufferRect_Palette0(0, 0, 0, 0, 30, 20);
            CopyBgTilemapBufferToVram(0);
            gTasks[taskId].func = Task_OakSpeech_LoadPlayerPic;
        }
    }
''')
    src = replace_function(src, 'Task_OakSpeech_YourNameWhatIsIt', '''
    s16 *data = gTasks[taskId].data;
    if (tTrainerPicFadeState != 0)
    {
        if (tTimer != 0)
        {
            tTimer--;
        }
        else
        {
            StringCopy(gSaveBlock2Ptr->playerName, _("FLOSS"));
            tTrainerPicPosX = 0;
            ClearDialogWindowAndFrame(WIN_INTRO_TEXTBOX, TRUE);
            CreateFadeInTask(taskId, 2);
            tTimer = 40;
            gTasks[taskId].func = Task_OakSpeech_FadeOutPlayerPic;
        }
    }
''')
    src = replace_function(src, 'Task_OakSpeech_AskRivalsName', '''
    s16 *data = gTasks[taskId].data;
    if (tTrainerPicFadeState != 0)
    {
        StringCopy(gSaveBlock1Ptr->rivalName, _("DJ"));
        StringExpandPlaceholders(gStringVar4, gOakSpeech_Text_RememberRivalsName);
        OakSpeechPrintMessage(gStringVar4, sOakSpeechResources->textSpeed);
        sOakSpeechResources->hasPlayerBeenNamed = TRUE;
        gTasks[taskId].func = Task_OakSpeech_FadeOutRivalPic;
    }
''')
    return src

PHONE_LABELS = '''// DMV Edition: early phone home-screen labels, wired to the ORIGINAL actions.
// A graphic app-icon grid is planned for a later separately tested art/UI pass.
static const u8 sDMVAppDex[]      = _("DEX APP");
static const u8 sDMVAppTeam[]     = _("MY TEAM");
static const u8 sDMVAppBag[]      = _("BAG");
static const u8 sDMVAppTrainer[]  = _("PROFILE");
static const u8 sDMVAppSave[]     = _("SAVE");
static const u8 sDMVAppSettings[] = _("SETTINGS");
static const u8 sDMVAppClose[]    = _("CLOSE");
static const u8 sDMVAppRetire[]   = _("RETIRE");
static const u8 sDMVPhoneHeader[] = _("TBT PHONE");

'''

def patch_menu(src: str) -> str:
    marker = 'static const struct MenuAction sStartMenuActionTable[] = {'
    src = replace_exact(src, marker, PHONE_LABELS + marker, 'Add phone labels')
    items = {
        'STARTMENU_POKEDEX':'sDMVAppDex',
        'STARTMENU_POKEMON':'sDMVAppTeam',
        'STARTMENU_BAG':'sDMVAppBag',
        'STARTMENU_PLAYER':'sDMVAppTrainer',
        'STARTMENU_SAVE':'sDMVAppSave',
        'STARTMENU_OPTION':'sDMVAppSettings',
        'STARTMENU_EXIT':'sDMVAppClose',
        'STARTMENU_RETIRE':'sDMVAppRetire',
        'STARTMENU_PLAYER2':'sDMVAppTrainer',
    }
    for k,v in items.items():
        pat = r'(?m)^(\s*\['+k+r'\]\s*=\s*\{\s*)(gText_Menu\w+)(\s*,\s*\{\.u8_void\s*=)'
        src, n = re.subn(pat, lambda m:m.group(1)+v+m.group(3), src)
        if n != 1: raise ValueError(f'Missing action table row: {k}, matches {n}')
    # Keep the original menu input/actions; draw a phone-like larger shell and title.
    old = '''        if (sStartMenuOrder[i] == STARTMENU_PLAYER || sStartMenuOrder[i] == STARTMENU_PLAYER2)
        {
            Menu_PrintFormatIntlPlayerName(GetStartMenuWindowId(), sStartMenuActionTable[sStartMenuOrder[i]].text, 8, i * 15);
        }
        else
        {
            StringExpandPlaceholders(gStringVar4, sStartMenuActionTable[sStartMenuOrder[i]].text);
            AddTextPrinterParameterized(GetStartMenuWindowId(), FONT_NORMAL, gStringVar4, 8, i * 15, 0xFF, NULL);
        }'''
    new = '''        if (i == 0)
            AddTextPrinterParameterized(GetStartMenuWindowId(), FONT_NORMAL, sDMVPhoneHeader, 8, 0, 0xFF, NULL);
        StringExpandPlaceholders(gStringVar4, sStartMenuActionTable[sStartMenuOrder[i]].text);
        AddTextPrinterParameterized(GetStartMenuWindowId(), FONT_NORMAL, gStringVar4, 8, (i + 1) * 15, 0xFF, NULL);'''
    src = replace_exact(src, old, new, 'Print phone apps and header')
    src = replace_exact(src, 'DrawStdWindowFrame(CreateStartMenuWindow(sNumStartMenuItems), FALSE);', 'DrawStdWindowFrame(CreateStartMenuWindow(sNumStartMenuItems + 1), FALSE);', 'Phone window height')
    src = replace_exact(src, 'Menu_InitCursor(GetStartMenuWindowId(), FONT_NORMAL, 0, 0, 15, sNumStartMenuItems, sStartMenuCursorPos)', 'Menu_InitCursor(GetStartMenuWindowId(), FONT_NORMAL, 0, 16, 15, sNumStartMenuItems, sStartMenuCursorPos)', 'Shift phone cursor')
    return src

def patch_menu_window(src: str) -> str:
    old = 'SetWindowTemplateFields(0, 0x16, 1, 7, height * 2 - 1, DLG_WINDOW_PALETTE_NUM, 0x13D)'
    new = 'SetWindowTemplateFields(0, 14, 1, 14, height * 2 - 1, DLG_WINDOW_PALETTE_NUM, 0x13D)'
    return replace_exact(src, old, new, 'Widen phone shell')

CITY_NAMES = {
    'MAPSEC_PEWTER_CITY': ('PEWTER CITY', 'BROOKLAND'),
    'MAPSEC_CERULEAN_CITY': ('CERULEAN CITY', 'TAKOMA'),
    'MAPSEC_LAVENDER_TOWN': ('LAVENDER TOWN', 'DEANWOOD'),
    'MAPSEC_VERMILION_CITY': ('VERMILION CITY', 'NAVY YARD'),
    'MAPSEC_CELADON_CITY': ('CELADON CITY', 'U STREET'),
    'MAPSEC_FUCHSIA_CITY': ('FUCHSIA CITY', 'OXON HILL'),
    'MAPSEC_CINNABAR_ISLAND': ('CINNABAR ISLAND', 'NATIONAL HARBOR'),
    'MAPSEC_INDIGO_PLATEAU': ('INDIGO PLATEAU', 'CAPITOL HILL'),
    'MAPSEC_SAFFRON_CITY': ('SAFFRON CITY', 'CLARENDON'),
}

def patch_regions(src: str) -> str:
    for section,(old,new) in CITY_NAMES.items():
        pattern = '("id": "'+ section +'",\n      "name": "'+old+'")'
        replacement = '"id": "'+section+'",\n      "name": "'+new+'"'
        src = replace_exact(src, pattern, replacement, f'Rename {section}')
    return src

PATCHES = {
    'src/oak_speech.c': patch_oak,
    'src/start_menu.c': patch_menu,
    'src/new_menu_helpers.c': patch_menu_window,
    'src/data/region_map/region_map_sections.json': patch_regions,
}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    choice=parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--check', action='store_true', help='Validate and preview without modifying files')
    choice.add_argument('--apply', action='store_true', help='Write the changes (back up with git first)')
    args=parser.parse_args()
    try:
        to_write={}
        for path,patch in PATCHES.items():
            original=(ROOT/path).read_text(encoding='utf-8')
            updated=patch(original)
            if updated==original: raise ValueError(f'No changes produced: {path}')
            to_write[path]=updated
        print('OK: All four source files passed preflight validation.')
        for p in to_write: print(('READY' if args.check else 'UPDATED')+': '+p)
        if args.apply:
            for path,updated in to_write.items():
                (ROOT/path).write_text(updated, encoding='utf-8')
            print('Patch applied. Run: git diff --check; make -j2 firered_rev1')
        else:
            print('CHECK ONLY. Nothing has been modified.')
    except (OSError, ValueError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        print('No source files were changed by this invocation.', file=sys.stderr)
        sys.exit(1)
if __name__ == '__main__':
    main()
