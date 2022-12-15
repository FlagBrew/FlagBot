# Handling for the following commands: legality, legalize, convert
# type: ignore reportMissingImports

import sys
import os
import clr
import io
import base64
import time
import addons.pkhex_cores.pkhex_helper as pkhex_helper
import addons.pkhex_cores.pokeinfo as pokeinfo
import multiprocessing

# Import PKHeX stuff
sys.path.append(os.getcwd() + r"/addons/pkhex_cores/deps")
clr.AddReference("PKHeX.Core")
clr.AddReference("PKHeX.Core.AutoMod")
from PKHeX.Core import EntityFormat, LegalityAnalysis, LegalityFormatting, EncounterEvent, RibbonStrings, GameInfo, SaveUtil, SimpleTrainerInfo, ShowdownSet  # Import classes
from PKHeX.Core import Species  # Import Enums
from PKHeX.Core.AutoMod import Legalizer, APILegality, BattleTemplateLegality, RegenTemplate, LegalizationResult
# Import base C# Objects
from System import Enum, UInt16, Convert

alm_process = None


def get_legality_report(file):
    pokemon = EntityFormat.GetFromBytes(file)
    if pokemon is None:  # Invalid file
        return 400
    generation = pkhex_helper.extension_version_dict[pokemon.Extension.upper()]
    if not pkhex_helper.personal_table_switcher(generation).IsPresentInGame(pokemon.Species, pokemon.Form):
        return 500
    analysis = LegalityAnalysis(pokemon)
    report = LegalityFormatting.Report(analysis)
    if report == "Legal!":
        return 200
    elif report == "Analysis not available for this Pokémon.":
        return 201
    return report.replace('\r', '').split('\n')


def autolegalityProcess(ot, tid, sid, lang, gender, generation, pkmn_bytes, out):
    trainer_data = SimpleTrainerInfo(pkhex_helper.game_version_dict[generation])
    trainer_data.OT = ot
    trainer_data.TID = tid
    trainer_data.SID = sid
    trainer_data.Language = lang
    trainer_data.Gender = gender
    pkmn = EntityFormat.GetFromBytes(base64.b64decode(pkmn_bytes))
    set = RegenTemplate(pkmn, trainer_data.Generation)
    legalization_res = LegalizationResult(0)
    pkmn, _ = APILegality.GetLegalFromTemplate(trainer_data, pkmn, set, legalization_res)
    out.put(base64.b64encode(bytearray(byte for byte in pkmn.DecryptedBoxData)).decode('UTF-8'))


def cancelThread():
    if alm_process is not None:
        alm_process.kill()


def legalize_pokemon(file, manager):
    pokemon = EntityFormat.GetFromBytes(file)
    if pokemon is None:  # Invalid file
        return 400
    generation = pkhex_helper.extension_version_dict[pokemon.Extension.upper()]
    if not pkhex_helper.personal_table_switcher(generation).IsPresentInGame(pokemon.Species, pokemon.Form):
        return 500
    legality_report = LegalityFormatting.Report(LegalityAnalysis(pokemon)).replace('\r', '').split('\n')
    if legality_report[0] == "Legal!":
        return 200
    elif legality_report[0] == "Analysis not available for this Pokémon.":
        return 201

    out = manager.Queue()
    alm_process = multiprocessing.Process(target=autolegalityProcess, args=(pokemon.OT_Name, pokemon.TID, pokemon.SID,
                                                                            pokemon.Language, pokemon.Gender, generation,
                                                                            base64.b64encode(bytearray(byte for byte in pokemon.DecryptedBoxData)).decode('UTF-8'), out))
    alm_process.daemon = True
    alm_process.start()

    i = 0
    while alm_process.is_alive():
        if i > 30:
            print("Legalization attempt taking too long, killing process...")
            alm_process.kill()
            break
        i += 1
        time.sleep(1)
    if out.empty():
        return 202  # Timeout and no result

    # Since we're getting base64 back, we'll need to decode it and then convert it to an actual Pokemon object
    result = out.get()
    new_pokemon = EntityFormat.GetFromBytes(base64.b64decode(result))

    analysis = LegalityAnalysis(new_pokemon)
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
