# Handling for the following commands: find, learns
# type: ignore reportMissingImports

import sys
import os
import re
import clr
from addons.helper import get_string_from_regex

# Import PKHeX stuff
sys.path.append(os.getcwd() + r"/addons/pkhex_cores/deps")
clr.AddReference("PKHeX.Core")
from PKHeX.Core import EncounterLearn  # Import classes
from PKHeX.Core import Species, Move  # Import Enums
# Import base C# Objects
from System import Enum, UInt16


def get_encounters(pokemon, generation: str, moves: list = None):
    pokemon_id = [int(item) for item in Enum.GetValues(Species) if Enum.GetName(Species, item) == pokemon]
    if len(pokemon_id) == 0:
        return 400
    csharp_pokemon = UInt16(pokemon_id[0])
    special = generation if generation in ("LGPE", "BDSP", "PLA") else None
    gen = "7" if generation == "LGPE" else "8" if generation in ("BDSP", "PLA") else generation
    csharp_moves_list = []
    if moves:
        for move in moves:
            formatted_move = move.title().replace(" ", "")
            move_id = [int(item) for item in Enum.GetValues(Move) if Enum.GetName(Move, item) == formatted_move]
            csharp_moves_list.append(move_id[0])
    encounters = EncounterLearn.Summarize(EncounterLearn.GetLearn(csharp_pokemon, csharp_moves_list))
    encounter_type = ""
    genlocs = []
    locations = []
    for encounter in encounters:
        if encounter.startswith("="):
            if len(locations) > 0:
                genlocs.append(
                    {
                        "encounter_type": encounter_type,
                        "location": locations
                    })
            locations = []
            encounter_type = encounter.replace("=", "")
            continue
        reg_gen = get_string_from_regex("Gen[1-9]", encounter)
        if gen not in reg_gen:
            continue
        loc = get_string_from_regex("(?<=.{8}).+?(?=:)", encounter)  # Get location
        games = get_string_from_regex("([\t ][A-Z , a-z 0-9]{1,100}$|Any)", encounter)  # Get games for location
        games = games.replace(" ", "").replace(":", "").strip()
        if not special and any(iter_gen for iter_gen in ("BD", "SP", "PLA", "GG", "GE", "GO", "GP") if iter_gen in (game for game in games.split(','))):
            continue
        if special == "BDSP" and not any(iter_gen for iter_gen in ("BD", "SP") if iter_gen in (game for game in games.split(','))):
            continue
        elif special == "PLA" and "PLA" not in games:
            continue
        elif special == "LGPE" and not any(iter_gen for iter_gen in ("GO", "GG", "GP", "GE") if iter_gen in (game for game in games.split(','))):
            continue
        elif not special and "Gen" in games:
            games = re.sub(",Gen[0-9]{1,2}", "", games)
        games_list = games.split(',')
        locations.append(
            {
                "name": loc,
                "games": games_list
            })
    if len(locations) > 0:  # Add last entry if locations > 0
        genlocs.append(
            {
                "encounter_type": encounter_type,
                "location": locations
            })
    if len(genlocs) == 0:
        return 500
    return genlocs


def get_moves(pokemon, moves: list):
    pokemon_id = [int(item) for item in Enum.GetValues(Species) if Enum.GetName(Species, item) == pokemon]
    if len(pokemon_id) == 0:
        return 400
    csharp_pokemon = UInt16(pokemon_id[0])
    learnables = []
    for move in moves:
        formatted_move = move.title().replace(" ", "")
        move_id = [int(item) for item in Enum.GetValues(Move) if Enum.GetName(Move, item) == formatted_move]
        if len(move_id) == 0:
            continue
        csharp_move_in_array = [move_id[0]]
        summary = EncounterLearn.Summarize(EncounterLearn.GetLearn(csharp_pokemon, csharp_move_in_array))
        can_learn = len([item for item in summary]) > 0
        learnables.append(
            {
                "name": move.title(),
                "learnable": can_learn
            })
    if len(learnables) == 0:
        return 500
    return learnables
