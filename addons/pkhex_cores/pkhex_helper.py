# Handling for the following commands: pokeinfo, qr, forms
# type: ignore reportMissingImports

import sys
import clr
import os
import segno

# Import PKHeX stuff
sys.path.append(os.getcwd() + r"/addons/pkhex_cores/deps")
clr.AddReference("PKHeX.Core")

from PKHeX.Core import PokeList1, PokeList2, PK3, PK4, PK5, PK6, PK7, PB7, PK8, PB8, PA8  # Import PKX classes
from PKHeX.Core import EntityContext, GameVersion, QRMessageUtil, QR7  # Import classes

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

pkx_version_dict = {
    "1": PokeList1,
    "2": PokeList2,
    "3": PK3,
    "4": PK4,
    "5": PK5,
    "6": PK6,
    "7": PK7,
    "LGPE": PB7,
    "8": PK8,
    "BDSP": PB8,
    "PLA": PA8,
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

generation_version_dict = {
    "1": [35, 36, 37, 38, 50, 51, 84, 83],
    "2": [39, 40, 41, 52, 53, 85],
    "3": [1, 2, 3, 4, 5, 54, 55, 56, 57, 58, 59],
    "4": [10, 11, 12, 7, 8, 60, 61, 62, 0x3F],
    "5": [20, 21, 22, 23, 0x40, 65],
    "6": [24, 25, 26, 27, 66, 67, 68],
    "7": [30, 0x1F, 0x20, 33, 69, 70],
    "LGPE": [71, 34, 42, 43],
    "8": [44, 45, 47, 72],
    "BDSP": [73, 48, 49],
    "PLA": [471]
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

pla_species = [
    722, 723, 724, 155, 156, 157, 501, 502, 503, 399, 400, 396, 397, 398, 403, 404, 405, 265, 266, 267,
    268, 269, 77, 78, 133, 134, 135, 136, 196, 197, 470, 471, 700, 41, 42, 169, 425, 426, 401, 402, 418,
    419, 412, 413, 414, 74, 75, 76, 234, 899, 446, 143, 46, 47, 172, 25, 26, 63, 64, 65, 390,
    391, 392, 427, 428, 420, 421, 54, 55, 415, 416, 123, 900, 212, 214, 439, 122, 190, 424, 129, 130,
    422, 423, 211, 904, 440, 113, 242, 406, 315, 407, 455, 548, 549, 114, 465, 339, 340, 453, 454, 280,
    281, 282, 475, 193, 469, 449, 450, 417, 434, 435, 216, 217, 901, 704, 705, 706, 95, 208, 111, 112,
    464, 438, 185, 108, 463, 175, 176, 468, 387, 388, 389, 137, 233, 474, 92, 93, 94, 442, 198, 430,
    201, 363, 364, 365, 223, 224, 451, 452, 58, 59, 431, 432, 66, 67, 68, 441, 355, 356, 477, 393,
    394, 395, 458, 226, 550, 902, 37, 38, 72, 73, 456, 457, 240, 126, 467, 81, 82, 462, 436, 437,
    239, 125, 466, 207, 472, 443, 444, 445, 299, 476, 100, 101, 479, 433, 358, 200, 429, 173, 35, 36,
    215, 903, 461, 361, 362, 478, 408, 409, 410, 411, 220, 221, 473, 712, 713, 459, 570, 571, 672, 628,
    447, 448, 480, 481, 482, 485, 486, 488, 641, 642, 645, 905, 483, 484, 487, 493, 489, 490, 492, 491
]


def get_raw_qr_data(pokemon):
    pkmn_qr_message = QRMessageUtil.GetMessage(pokemon)
    qr = segno.make_qr(pkmn_qr_message)
    return qr
