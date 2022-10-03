# Handling for the following commands: pokeinfo, qr, forms
# type: ignore reportMissingImports

import sys
import clr
import os
import segno

# Import PKHeX stuff
sys.path.append(os.getcwd() + r"/addons/pkhex_cores/deps")
clr.AddReference("PKHeX.Core")

from PKHeX.Core import EntityContext, GameVersion, QRMessageUtil, PersonalTable  # Import classes

game_version_dict = {
    "1": GameVersion.RBY,
    "2": GameVersion.GSC,
    "3": GameVersion.RSE,
    "4": GameVersion.DPPt,
    "5": GameVersion.B2W2,
    "6": GameVersion.ORAS,
    "7": GameVersion.USUM,
    "LGPE": GameVersion.GG,
    "8": GameVersion.SWSH,
    "BDSP": GameVersion.BD,  # Can't use BDSP here due to varying amounts of internal validation
    "PLA": GameVersion.PLA,
}

entity_context_dict = {
    "1": EntityContext.Gen1,
    "2": EntityContext.Gen2,
    "3": EntityContext.Gen3,
    "4": EntityContext.Gen4,
    "5": EntityContext.Gen5,
    "6": EntityContext.Gen6,
    "7": EntityContext.Gen7,
    "LGPE": EntityContext.Gen7b,
    "8": EntityContext.Gen8,
    "BDSP": EntityContext.Gen8a,
    "PLA": EntityContext.Gen8b
}

extension_version_dict = {
    "PK1": "1",
    "PK2": "2",
    "PK3": "3",
    "PK4": "4",
    "PK5": "5",
    "PK6": "6",
    "PK7": "7",
    "PB7": "LGPE",
    "PK8": "8",
    "PB8": "BDSP",
    "PA8": "PLA"
}

pokemon_egg_groups = [
    "Monster",
    "Water 1",
    "Bug",
    "Flying",
    "Field",
    "Fairy",
    "Grass",
    "Human-Like",
    "Water 3",
    "Mineral",
    "Amorphous",
    "Water 2",
    "Ditto",
    "Dragon",
    "Undiscovered"
]

pokemon_colour_index = [
    "Red",
    "Blue",
    "Yellow",
    "Green",
    "Black",
    "Brown",
    "Purple",
    "Gray",
    "White",
    "Pink",
]


def get_raw_qr_data(pokemon):
    pkmn_qr_message = QRMessageUtil.GetMessage(pokemon)
    qr = segno.make_qr(pkmn_qr_message)
    return qr


def personal_table_switcher(generation):
    if generation == "1":
        return PersonalTable.Y
    elif generation == "2":
        return PersonalTable.C
    elif generation == "3":
        return PersonalTable.E
    elif generation == "4":
        return PersonalTable.HGSS
    elif generation == "5":
        return PersonalTable.B2W2
    elif generation == "6":
        return PersonalTable.AO
    elif generation == "7":
        return PersonalTable.USUM
    elif generation == "LGPE":
        return PersonalTable.GG
    elif generation == "8":
        return PersonalTable.SWSH
    elif generation == "BDSP":
        return PersonalTable.BDSP
    elif generation == "PLA":
        return PersonalTable.LA
