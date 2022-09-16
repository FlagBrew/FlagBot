# Handling for the following commands: legality, legalize, convert
# type: ignore reportMissingImports

import sys
import os
import clr
import io
import base64
import addons.pkhex_cores.pkhex_helper as pkhex_helper
import addons.pkhex_cores.pokeinfo as pokeinfo

# Import PKHeX stuff
sys.path.append(os.getcwd() + r"/addons/pkhex_cores/deps")
clr.AddReference("PKHeX.Core")
clr.AddReference("PKHeX.Core.AutoMod")
from PKHeX.Core import EntityFormat, LegalityAnalysis, LegalityFormatting, EncounterEvent, RibbonStrings, GameInfo, SaveUtil, SimpleTrainerInfo, ShowdownSet  # Import classes
from PKHeX.Core import Species  # Import Enums
from PKHeX.Core.AutoMod import Legalizer, APILegality, BattleTemplateLegality, RegenTemplate, LegalizationResult
# Import base C# Objects
from System import Enum, UInt16, Convert


def get_legality_report(file):
    pokemon = EntityFormat.GetFromBytes(file)
    for key, value in pkhex_helper.generation_version_dict.items():
        if pokemon.Version in value:
            generation = key
            break
    if generation in ("1", "2"):
        pokemon = pkhex_helper.pkx_version_dict[generation](file)[0]
    else:
        pokemon = pkhex_helper.pkx_version_dict[generation](file)
    if pokemon.Species <= 0 or ((generation == "1" and pokemon.Species > 151) or (generation == "2" and pokemon.Species > 251) or (generation == "3" and pokemon.Species > 386) or (generation in ("4", "BDSP") and pokemon.Species > 493) or (generation == "5" and pokemon.Species > 649) or (generation == "6" and pokemon.Species > 721) or (generation == "7" and pokemon.Species > 809) or (generation == "LGPE" and pokemon.Species > 151 and pokemon.Species not in (808, 809)) or (generation == "8" and pokemon.Species > 896) or (generation == "PLA" and pokemon.Species not in pkhex_helper.pla_species)):
        return 500
    analysis = LegalityAnalysis(pokemon)
    report = LegalityFormatting.Report(analysis)
    if report == "Legal!":
        return 200
    elif report == "Analysis not available for this Pokémon.":
        return 201
    return report.replace('\r', '').split('\n')


def legalize_pokemon(file):
    pokemon = EntityFormat.GetFromBytes(file)
    for key, value in pkhex_helper.generation_version_dict.items():
        if pokemon.Version in value:
            generation = key
            break
    if generation in ("1", "2"):
        pokemon = pkhex_helper.pkx_version_dict[generation](file)[0]
    else:
        pokemon = pkhex_helper.pkx_version_dict[generation](file)
    if pokemon.Species <= 0 or ((generation == "1" and pokemon.Species > 151) or (generation == "2" and pokemon.Species > 251) or (generation == "3" and pokemon.Species > 386) or (generation in ("4", "BDSP") and pokemon.Species > 493) or (generation == "5" and pokemon.Species > 649) or (generation == "6" and pokemon.Species > 721) or (generation == "7" and pokemon.Species > 809) or (generation == "LGPE" and pokemon.Species > 151 and pokemon.Species not in (808, 809)) or (generation == "8" and pokemon.Species > 896) or (generation == "PLA" and pokemon.Species not in pkhex_helper.pla_species)):
        return 500
    legality_report = LegalityFormatting.Report(LegalityAnalysis(pokemon)).replace('\r', '').split('\n')
    if legality_report[0] == "Legal!":
        return 200
    elif legality_report[0] == "Analysis not available for this Pokémon.":
        return 201
    trainer_data = SimpleTrainerInfo(pkhex_helper.game_version_dict[generation])
    trainer_data.OT = pokemon.OT_Name
    trainer_data.TID = pokemon.TID
    trainer_data.SID = pokemon.SID
    trainer_data.Language = pokemon.Language
    trainer_data.Gender = pokemon.OT_Gender
    new_pokemon = Legalizer.Legalize(trainer_data, pokemon)
    analysis = LegalityAnalysis(pokemon)
    if not analysis.Valid and not analysis.Parsed:
        return 201
    elif not analysis.Valid:
        return 202
    legal_data = {}
    legal_data["pokemon"] = Convert.ToBase64String(new_pokemon.DecryptedPartyData)
    legal_data["species"] = Enum.GetName(Species, UInt16(pokemon.Species))
    legal_data["report"] = legality_report
    img = pkhex_helper.get_raw_qr_data(new_pokemon)
    bytes = io.BytesIO()
    img.save(bytes, kind='PNG', scale=4)
    legal_data["qr"] = bytes.getvalue()
    return legal_data


def convert_pokemon(showdown_set, generation):
    showdown = ShowdownSet(showdown_set)
    regen = RegenTemplate(showdown)
    blank_sav = SaveUtil.GetBlankSAV(pkhex_helper.game_version_dict[generation], "FlagBot")
    pokemon, result = Legalizer.GetLegalFromSet(blank_sav, regen)
    pokemon_bytes = Convert.ToBase64String(pokemon.DecryptedPartyData)
    pokemon_info = pokeinfo.get_pokemon_file_info(base64.b64decode(pokemon_bytes))
    pokemon_info["pokemon"] = pokemon_bytes
    img = pkhex_helper.get_raw_qr_data(pokemon)
    bytes = io.BytesIO()
    img.save(bytes, kind='PNG', scale=4)
    pokemon_info["qr"] = bytes.getvalue()
    pokemon_info["analysis"] = "No issues!"
    pokemon_info["status"] = 200
    if result in (LegalizationResult.Failed, LegalizationResult.Timeout):
        analysis = "Timed out converting this set"
        if result == LegalizationResult.Failed:
            analysis = BattleTemplateLegality.SetAnalysis(regen, blank_sav, blank_sav.BlankPKM)
        pokemon_info["analysis"] = analysis
        pokemon_info["status"] = 400
    return pokemon_info


EncounterEvent.RefreshMGDB("")
RibbonStrings.ResetDictionary(GameInfo.Strings.ribbons)
Legalizer.EnableEasterEggs = True
APILegality.PrioritizeGame = True
APILegality.UseTrainerData = False
