#!/usr/bin/env python3
"""Pokémon FireRed DMV Edition v0.4: randomized three starter choices and rival line.

Run: python3 apply_dmv_starters_v04.py --check
     python3 apply_dmv_starters_v04.py --apply

Targets the pret/pokefirered decomp on branch dev/dmv-v04-combined.
All modifications are verified for expected anchors before any file is written.
"""
import argparse
from pathlib import Path
import re
import subprocess
import sys

FILES = [
    'include/constants/vars.h',
    'include/field_specials.h',
    'src/field_specials.c',
    'src/battle_main.c',
    'data/specials.inc',
    'data/maps/PalletTown_ProfessorOaksLab/scripts.inc',
    'data/maps/PalletTown_ProfessorOaksLab/text.inc',
]


def replace_once(src, old, new, label):
    n = src.count(old)
    if n != 1:
        raise ValueError(f'{label}: expected 1 occurrence, found {n}')
    return src.replace(old, new, 1)


def patch_vars(src):
    return replace_once(src,
        '#define VARS_END                   0x40FF',
        '''// DMV Edition: persistent randomized lab choices (reserved former unnamed vars).
#define VAR_DMV_RIVAL_SPECIES         VAR_0x40FB
#define VAR_DMV_STARTER_0            VAR_0x40FC
#define VAR_DMV_STARTER_1            VAR_0x40FD
#define VAR_DMV_STARTER_2            VAR_0x40FE

#define VARS_END                   0x40FF''', 'persistent variables')


def patch_header(src):
    return replace_once(src,
        'u16 GetStarterSpecies(void);',
        '''u16 GetStarterSpecies(void);
void DMVGenerateStarterChoices(void);
u16 DMVGetRivalPokemonSpecies(u16 originalSpecies);''', 'special declarations')


def patch_field_specials(src):
    src = replace_once(src, '#include "constants/items.h"',
        '#include "constants/items.h"\n#include "constants/species.h"', 'species include')
    anchor = '''static u16 GetStarterSpeciesById(u16 idx)
{
    if (idx >= NELEMS(sStarterSpecies))
        idx = 0;
    return sStarterSpecies[idx];
}'''
    replacement = '''static u16 GetStarterSpeciesById(u16 idx)
{
    u16 species;

    if (idx >= NELEMS(sStarterSpecies))
        idx = 0;
    species = VarGet(VAR_DMV_STARTER_0 + idx);
    if (species != SPECIES_NONE)
        return species;
    return sStarterSpecies[idx];
}'''
    src = replace_once(src, anchor, replacement, 'starter species getter')

    addon = '''

// Each line has a first stage, middle evolution, and final evolution.
// The randomized lab uses complete three-stage lines, so DJ can evolve
// his chosen starter consistently throughout the original rival battles.
static const u16 sDMVEvolutionLines[][3] =
{
    {SPECIES_BULBASAUR,  SPECIES_IVYSAUR,     SPECIES_VENUSAUR},
    {SPECIES_CHIKORITA,  SPECIES_BAYLEEF,     SPECIES_MEGANIUM},
    {SPECIES_TREECKO,    SPECIES_GROVYLE,     SPECIES_SCEPTILE},
    {SPECIES_CHARMANDER, SPECIES_CHARMELEON,  SPECIES_CHARIZARD},
    {SPECIES_CYNDAQUIL,  SPECIES_QUILAVA,     SPECIES_TYPHLOSION},
    {SPECIES_TORCHIC,    SPECIES_COMBUSKEN,   SPECIES_BLAZIKEN},
    {SPECIES_SQUIRTLE,   SPECIES_WARTORTLE,   SPECIES_BLASTOISE},
    {SPECIES_TOTODILE,   SPECIES_CROCONAW,    SPECIES_FERALIGATR},
    {SPECIES_MUDKIP,     SPECIES_MARSHTOMP,   SPECIES_SWAMPERT},
};

// One random Grass, Fire, and Water starter per New Game, shuffled into
// the three lab ball positions. All are first-stage, non-legendary.
void DMVGenerateStarterChoices(void)
{
    u16 picks[3];
    u16 temp;
    s32 i;
    s32 j;

    if (VarGet(VAR_DMV_STARTER_0) != SPECIES_NONE)
        return;

    picks[0] = sDMVEvolutionLines[Random() % 3][0];
    picks[1] = sDMVEvolutionLines[3 + Random() % 3][0];
    picks[2] = sDMVEvolutionLines[6 + Random() % 3][0];

    for (i = 2; i > 0; i--)
    {
        j = Random() % (i + 1);
        temp = picks[i];
        picks[i] = picks[j];
        picks[j] = temp;
    }

    VarSet(VAR_DMV_STARTER_0, picks[0]);
    VarSet(VAR_DMV_STARTER_1, picks[1]);
    VarSet(VAR_DMV_STARTER_2, picks[2]);
}

// Replaces only DJ's normal starter line (not his other Pokémon).
// His first battle uses stage 0, later battles stage 1/2 as in FireRed.
u16 DMVGetRivalPokemonSpecies(u16 originalSpecies)
{
    static const u16 sKantoOriginalLines[][3] =
    {
        {SPECIES_BULBASAUR, SPECIES_IVYSAUR, SPECIES_VENUSAUR},
        {SPECIES_CHARMANDER, SPECIES_CHARMELEON, SPECIES_CHARIZARD},
        {SPECIES_SQUIRTLE, SPECIES_WARTORTLE, SPECIES_BLASTOISE},
    };
    u16 rivalSpecies = VarGet(VAR_DMV_RIVAL_SPECIES);
    s32 line;
    s32 stage;
    s32 rivalLine;

    if (rivalSpecies == SPECIES_NONE)
        return originalSpecies;

    for (rivalLine = 0; rivalLine < NELEMS(sDMVEvolutionLines); rivalLine++)
    {
        if (sDMVEvolutionLines[rivalLine][0] == rivalSpecies)
        {
            for (line = 0; line < NELEMS(sKantoOriginalLines); line++)
            {
                for (stage = 0; stage < 3; stage++)
                {
                    if (sKantoOriginalLines[line][stage] == originalSpecies)
                        return sDMVEvolutionLines[rivalLine][stage];
                }
            }
            break;
        }
    }
    return originalSpecies;
}
'''
    anchor = '''u16 GetStarterSpecies(void)
{
    return GetStarterSpeciesById(VarGet(VAR_STARTER_MON));
}'''
    src = replace_once(src, anchor, anchor + addon, 'randomizer functions')
    return src


def patch_battle(src):
    src = replace_once(src, '#include "event_data.h"',
        '#include "event_data.h"\n#include "field_specials.h"', 'battle include')
    anchor = '        gBattleTypeFlags |= gTrainers[trainerNum].doubleBattle;'
    replacement = '''        // DMV Edition: DJ retains his randomly chosen starter through the
        // early, late, and championship rival battle trainer parties.
        if (gTrainers[trainerNum].trainerPic == TRAINER_PIC_RIVAL_EARLY
         || gTrainers[trainerNum].trainerPic == TRAINER_PIC_RIVAL_LATE
         || gTrainers[trainerNum].trainerPic == TRAINER_PIC_CHAMPION_RIVAL)
        {
            for (i = 0; i < gTrainers[trainerNum].partySize; i++)
            {
                u16 oldSpecies = GetMonData(&party[i], MON_DATA_SPECIES);
                u16 newSpecies = DMVGetRivalPokemonSpecies(oldSpecies);
                if (newSpecies != oldSpecies)
                {
                    u8 level = GetMonData(&party[i], MON_DATA_LEVEL);
                    u16 heldItem = GetMonData(&party[i], MON_DATA_HELD_ITEM);
                    CreateMon(&party[i], newSpecies, level, fixedIV, FALSE, 0, OT_ID_RANDOM_NO_SHINY, 0);
                    SetMonData(&party[i], MON_DATA_HELD_ITEM, &heldItem);
                }
            }
        }

''' + anchor
    src = replace_once(src, anchor, replacement, 'rival team override')
    return src


def patch_specials(src):
    return replace_once(src, '\tdef_special CreateEnemyEventMon\ngSpecialsEnd::',
        '\tdef_special CreateEnemyEventMon\n\tdef_special DMVGenerateStarterChoices\ngSpecialsEnd::', 'register special')


def patch_oak_scripts(src):
    src = replace_once(src,
        'PalletTown_ProfessorOaksLab_ChooseStarterScene::\n\tlockall',
        'PalletTown_ProfessorOaksLab_ChooseStarterScene::\n\tlockall\n\tspecial DMVGenerateStarterChoices',
        'initialize lab randomization')
    sets = [
        ('BulbasaurBall', 'SPECIES_BULBASAUR', 'SPECIES_CHARMANDER', 0, 2),
        ('SquirtleBall', 'SPECIES_SQUIRTLE', 'SPECIES_BULBASAUR', 1, 0),
        ('CharmanderBall', 'SPECIES_CHARMANDER', 'SPECIES_SQUIRTLE', 2, 1),
    ]
    for name, orig, rival, index, rival_index in sets:
        old = (f'\tsetvar PLAYER_STARTER_NUM, {index}\n'
               f'\tsetvar PLAYER_STARTER_SPECIES, {orig}\n'
               f'\tsetvar RIVAL_STARTER_SPECIES, {rival}')
        new = (f'\tsetvar PLAYER_STARTER_NUM, {index}\n'
               f'\tcopyvar PLAYER_STARTER_SPECIES, VAR_DMV_STARTER_{index}\n'
               f'\tcopyvar RIVAL_STARTER_SPECIES, VAR_DMV_STARTER_{rival_index}\n'
               f'\tcopyvar VAR_DMV_RIVAL_SPECIES, RIVAL_STARTER_SPECIES')
        src = replace_once(src, old, new, name)
    src = replace_once(src,
        '\tshowmonpic PLAYER_STARTER_SPECIES, 10, 3\n\ttextcolor NPC_TEXT_COLOR_MALE',
        '\tshowmonpic PLAYER_STARTER_SPECIES, 10, 3\n\tbufferspeciesname STR_VAR_1, PLAYER_STARTER_SPECIES\n\ttextcolor NPC_TEXT_COLOR_MALE',
        'dynamic choice display')
    return src


def patch_oak_text(src):
    for mon in ('Bulbasaur', 'Squirtle', 'Charmander'):
        label = f'PalletTown_ProfessorOaksLab_Text_OakChoosing{mon}::'
        pattern = re.compile(r'(?m)^' + re.escape(label) + r'\n(?:[ \t]+\.string[^\n]*\n)+')
        if len(pattern.findall(src)) != 1:
            raise ValueError(f'{mon} text: expected exactly one complete text block')
        src = pattern.sub(lambda m: label + '\n    .string "OAK: You want to raise\\n"\n    .string "the {STR_VAR_1} POKéMON?$"\n', src, count=1)
    return src


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true')
    group.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    branch = subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip()
    if branch != 'dev/dmv-v04-combined':
        sys.exit(f'Wrong branch: {branch}; expected dev/dmv-v04-combined')
    patches = [patch_vars, patch_header, patch_field_specials, patch_battle,
               patch_specials, patch_oak_scripts, patch_oak_text]
    staged = []
    try:
        for filename, fn in zip(FILES, patches):
            file = Path(filename)
            before = file.read_text()
            if 'DMVGenerateStarterChoices' in before and fn is not patch_oak_text:
                raise ValueError(f'{filename}: code appears already patched')
            after = fn(before)
            if after == before:
                raise ValueError(f'{filename}: patch did not change contents')
            staged.append((file, after))
            print('OK:', filename)
    except (OSError, ValueError) as err:
        sys.exit('Patch validation failed; no files changed: ' + str(err))
    if args.check:
        print('\nAll 7 files passed. Run --apply to install the starter randomizer.')
        return
    for path, contents in staged:
        path.write_text(contents)
    print('\nStarter randomizer installed across all 7 files.')
    print('NEXT: make -j2 firered_rev1')


if __name__ == '__main__':
    main()
