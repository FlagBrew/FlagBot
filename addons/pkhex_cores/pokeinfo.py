# Handling for the following commands: pokeinfo, qr, forms
# type: ignore reportMissingImports

import sys
import os
import io
import clr
from addons.pkhex_cores.sprites import Sprites
import addons.pkhex_cores.pkhex_helper as pkhex_helper

# Import PKHeX stuff
sys.path.append(os.getcwd() + r"/addons/pkhex_cores/deps")
clr.AddReference("PKHeX.Core")
from PKHeX.Core import FormConverter, GameInfo, EntityFormat, EntitySummary  # Import classes
from PKHeX.Core import Species, Ability  # Import Enums
# Import base C# Objects
from System import Enum, UInt16, Byte


def get_pokemon_forms(pokemon, generation):
    pokemon_id = [int(item) for item in Enum.GetValues(Species) if Enum.GetName(Species, item) == pokemon]
    if len(pokemon_id) == 0:
        return 400
    csharp_pokemon = UInt16(pokemon_id[0])
    game_info_strings = GameInfo.Strings
    if pokemon == "Alcremie":
        forms = FormConverter.GetAlcremieFormList(game_info_strings.forms)
    else:
        forms = FormConverter.GetFormList(csharp_pokemon, game_info_strings.Types, game_info_strings.forms, GameInfo.GenderSymbolASCII, pkhex_helper.entity_context_dict[generation])
    return [form for form in forms]


def get_base_info(pokemon, form, generation: str, shiny: bool = False):
    if pokemon.lower() in ('jangmo', 'hakamo', 'kommo') and species_form_pair[1] == "o":
        pokemon += '-o'
        species_form_pair.pop(1)
    elif pokemon.lower() == "ho" and species_form_pair[1] == "oh":
        pokemon = "ho-oh"
        species_form_pair.pop(1)
    elif pokemon.lower() == "porygon" and species_form_pair[1].lower() == "z":
        pokemon = "porygon-z"
        species_form_pair.pop(1)
    pokemon_id = [int(item) for item in Enum.GetValues(Species) if Enum.GetName(Species, item) == pokemon]
    if len(pokemon_id) == 0:
        return 400
    elif (generation == "1" and pokemon_id[0] > 151) or (generation == "2" and pokemon_id[0] > 251) or (generation == "3" and pokemon_id[0] > 386) or (generation in ("4", "BDSP") and pokemon_id[0] > 493) or (generation == "5" and pokemon_id[0] > 649) or (generation == "6" and pokemon_id[0] > 721) or (generation == "7" and pokemon_id[0] > 809) or (generation == "LGPE" and pokemon_id[0] > 251 and pokemon_id[0] not in (808, 809)) or (generation == "8" and pokemon_id[0] > 896) or (generation == "PLA" and pokemon_id[0] not in pkhex_helper.pla_species):
        return 500
    csharp_pokemon = UInt16(pokemon_id[0])
    csharp_form_num = Byte(0)
    game_info_strings = GameInfo.Strings
    if form is not None:
        if pokemon == "Alcremie":
            forms = FormConverter.GetAlcremieFormList(game_info_strings.forms)
        else:
            forms = FormConverter.GetFormList(csharp_pokemon, game_info_strings.Types, game_info_strings.forms, GameInfo.GenderSymbolASCII, pkhex_helper.entity_context_dict[generation])
        try:
            form_num = forms.index(form)
        except ValueError:
            return 400
        if form_num >= 0 or form_num < len([csharp_form for csharp_form in forms]):
            csharp_form_num = Byte(form_num)
    pokemon_info = pkhex_helper.personal_table_switcher(generation).GetFormEntry(csharp_pokemon, csharp_form_num)
    if pokemon_info == 400:
        return 400
    types = [game_info_strings.types[pokemon_info.Type1]]
    types.append(game_info_strings.types[pokemon_info.Type2]) if pokemon_info.Type2 != -1 and pokemon_info.Type2 != pokemon_info.Type1 else types.append(None)
    groups = []
    groups.append(pkhex_helper.pokemon_egg_groups[pokemon_info.EggGroup1 - 1]) if pokemon_info.EggGroup1 != -1 else types.append(None)
    groups.append(pkhex_helper.pokemon_egg_groups[pokemon_info.EggGroup2 - 1]) if pokemon_info.EggGroup2 != -1 and pokemon_info.EggGroup2 != pokemon_info.EggGroup1 else types.append(None)
    sprites_obj = Sprites()
    sprite_url = sprites_obj.get_pokemon_sprite(pokemon.lower(), "female" if pokemon_info.OnlyFemale else "", shiny, form.lower() if form else "", (False if generation not in ("BDSP, LGPE, PLA") and int(generation) < 8 else True))
    base_pokemon = {
        "hp": pokemon_info.HP,
        "atk": pokemon_info.ATK,
        "def": pokemon_info.DEF,
        "spe": pokemon_info.SPE,
        "spa": pokemon_info.SPA,
        "spd": pokemon_info.SPD,
        "catch_rate": pokemon_info.CatchRate,
        "evo_stage": pokemon_info.EvoStage,
        "gender": pokemon_info.Gender,
        "hatch_cycles": pokemon_info.HatchCycles,
        "base_friendship": pokemon_info.BaseFriendship,
        "exp_growth": pokemon_info.EXPGrowth,
        "ability1": Enum.GetName(Ability, UInt16(pokemon_info.Ability1)) if hasattr(pokemon_info, "Ability1") else None,
        "ability2": Enum.GetName(Ability, UInt16(pokemon_info.Ability2)) if hasattr(pokemon_info, "Ability2") else None,
        "ability_h": Enum.GetName(Ability, UInt16(pokemon_info.AbilityH)) if hasattr(pokemon_info, "AbilityH") else None,
        "colour": pkhex_helper.pokemon_colour_index[pokemon_info.Color],
        "height": pokemon_info.Height,
        "weight": pokemon_info.Weight,
        "types": types,
        "egg_groups": groups,
        "is_dual_gender": True if pokemon_info.OnlyMale == pokemon_info.OnlyFemale and not pokemon_info.Genderless else False,
        "is_genderless": pokemon_info.Genderless,
        "only_female": pokemon_info.OnlyFemale,
        "bst": (pokemon_info.ATK + pokemon_info.DEF + pokemon_info.SPE + pokemon_info.SPA + pokemon_info.SPD + pokemon_info.HP),
        "species_sprite_url": sprite_url
    }
    return base_pokemon


def get_pokemon_file_info(file):
    pokemon = EntityFormat.GetFromBytes(file)
    if pokemon is None:  # Invalid file
        return 400
    generation = pkhex_helper.extension_version_dict[pokemon.Extension.upper()]
    if not pkhex_helper.personal_table_switcher(generation).IsPresentInGame(pokemon.Species, pokemon.Form):
        return 500
    game_info_strings = GameInfo.Strings
    entity_summary = EntitySummary(pokemon, game_info_strings)
    moves = [
        entity_summary.Move1,
        entity_summary.Move2,
        entity_summary.Move3,
        entity_summary.Move4
    ]
    stats = [
        {"iv": entity_summary.HP_IV, "ev": entity_summary.HP_EV, "total": entity_summary.HP},
        {"iv": entity_summary.ATK_IV, "ev": entity_summary.ATK_EV, "total": entity_summary.ATK},
        {"iv": entity_summary.DEF_IV, "ev": entity_summary.DEF_EV, "total": entity_summary.DEF},
        {"iv": entity_summary.SPA_IV, "ev": entity_summary.SPA_EV, "total": entity_summary.SPA},
        {"iv": entity_summary.SPD_IV, "ev": entity_summary.SPD_EV, "total": entity_summary.SPD},
        {"iv": entity_summary.SPE_IV, "ev": entity_summary.SPE_EV, "total": entity_summary.SPE}
    ]
    form_value = entity_summary.Form
    if entity_summary.Form != 0:
        forms = FormConverter.GetFormList(pokemon.Species, game_info_strings.Types, game_info_strings.forms, GameInfo.GenderSymbolASCII, pkhex_helper.entity_context_dict[generation])
        try:
            form_value = forms[form_value]
        except IndexError:
            form_value = str(form_value)  # Form outside index range; PKSM generated?
    else:
        form_value = str(form_value)
    sprites_obj = Sprites()
    sprite_url = sprites_obj.get_pokemon_sprite(entity_summary.Species.lower(), "female" if entity_summary.Gender == "F" else "", entity_summary.IsShiny, form_value.lower() if form_value else "", (False if generation not in ("BDSP, LGPE, PLA") and int(generation) < 8 else True), str(pokemon.FormArgument) if hasattr(pokemon, "FormArgument") else None)
    pokemon_info = {
        "species": entity_summary.Species,
        "form": form_value + f' ({sprites_obj.ALCREMIE_DECORATIONS[str(pokemon.FormArgument)].title()})' if pokemon.Species == 869 and hasattr(pokemon, "FormArgument") and pokemon.FormArgument != 0 else form_value if form_value != "0" else None,
        "nickname": entity_summary.Nickname,
        "gender": entity_summary.Gender,
        "level": entity_summary.Level,
        "nature": entity_summary.Nature,
        "generation": generation,
        "ability": entity_summary.Ability if hasattr(entity_summary, "Ability") else "N/A",
        "ot": entity_summary.OT,
        "sid": entity_summary.SID,
        "tid": entity_summary.TID,
        "ht": pokemon.HT_Name if hasattr(pokemon, "HT_Name") and pokemon.HT_Name != "" else "N/A",
        "met_loc": entity_summary.MetLoc,
        "version": entity_summary.Version,
        "ball": entity_summary.Ball,
        "held_item": entity_summary.HeldItem,
        "stats": stats,
        "moves": moves,
        "species_sprite_url": sprite_url,
        "is_legal": True if entity_summary.Legal == "True" else False
    }
    return pokemon_info


def generate_qr(file):
    pokemon = EntityFormat.GetFromBytes(file)
    species_name = Enum.GetName(Species, UInt16(pokemon.Species))
    generation = pkhex_helper.extension_version_dict[pokemon.Extension.upper()]
    if generation in ("1", "2", "LGPE", "8", "BDSP", "PLA"):
        return 501
    if pokemon.Species <= 0 or ((generation == "3" and pokemon.Species > 386) or (generation in ("4", "BDSP") and pokemon.Species > 493) or (generation == "5" and pokemon.Species > 649) or (generation == "6" and pokemon.Species > 721) or (generation == "7" and pokemon.Species > 809)):
        return 500
    img = pkhex_helper.get_raw_qr_data(pokemon)
    bytes = io.BytesIO()
    img.save(bytes, kind='PNG', scale=4)
    return [bytes.getvalue(), species_name, generation]
