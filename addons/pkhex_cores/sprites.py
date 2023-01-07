# type: ignore ReportMissingImport
import json
import sys
import clr
import os

# Import PKHeX stuff
sys.path.append(os.getcwd() + r"/addons/pkhex_cores/deps")
clr.AddReference("PKHeX.Core")
from PKHeX.Core import FormConverter, GameInfo, EntityContext, GameStrings


class Sprites:
    BASE_URL = "https://cdn.sigkill.tech/sprites/"
    POKEMON_WITH_FEMALE_FORMS = [
        'frillish',
        'hippopotas',
        'hippowdon',
        'jellicent',
        'meowstic',
        'pikachu',
        'pyroar',
        'unfezant',
        'wobbuffet',
        'basculegion',
        'indeedee'
    ]
    REPLACE_CHARS = {
        "♀": "f",
        "♂": "m",
        "é": "e",
        "’": "",
        "'": "",
        ": ": "-",
        " ": "-",
        ".": "",
    }
    ALCREMIE_DECORATIONS = {
        "0": "strawberry",
        "1": "berry",
        "2": "love",
        "3": "star",
        "4": "clover",
        "5": "flower",
        "6": "ribbon",
    }

    _bindings = {}

    def __init__(self):
        with open("saves/sprite_bindings.json", mode='r') as file:
            self._bindings = json.load(file)

    def get_pokemon_sprite(self, species, gender, shiny, form, is_gen8_and_up, form_argument: int = None):
        # Check to see if the species is in the POKEMON_WITH_FEMALE_FORMS
        checkBinding = True
        path = self.BASE_URL + ('pokemon-gen7x/' if not is_gen8_and_up else 'pokemon-gen8/') + ('shiny/' if shiny else 'regular/')

        if species == "alcremie":
            split_forms = form.split(' ')
            if len(split_forms) > 2:  # Alcremie with a decoration in form name (base_info)
                form, decoration = " ".join(split_forms[:-1]), split_forms[-1].replace(')', '').replace('(', '')
            else:  # Alcremie without a decoration in form name (file)
                form = " ".join(split_forms)
                decoration = self.ALCREMIE_DECORATIONS[form_argument] if form_argument else "ribbon"

        if species in self.POKEMON_WITH_FEMALE_FORMS and gender == "female":
            path += "female/"
            if species == "pikachu" and form == "normal":
                checkBinding = False

        if checkBinding:
            lookup = f"{species.replace(' ', '_')}_{form.replace(' ', '_')}"
            binding = self._bindings.get(lookup, None)
            if binding is not None:
                path += binding['file']
                if species == "alcremie":
                    path = path.replace('.png', f'-{decoration}.png')
                return path
        # Check to see if we need to replace any characters
        for char in self.REPLACE_CHARS:
            species = species.replace(char, self.REPLACE_CHARS[char])
        path += f"{species}.png"

        return path


class LanguageStrings:
    __strings = None

    def __init__(self, language: str = "en") -> None:
        self.__strings = GameStrings(language)

    def get_move_name(self, move: int):
        try:
            return self.__strings.movelist[move]
        except Exception as exception:
            print(exception)
            return "None"

    def get_species_name(self, species: int):
        try:
            return self.__strings.specieslist[species]
        except Exception as exception:
            print(exception)
            return "None"

    def get_ability_name(self, ability: int):
        try:
            return self.__strings.abilitylist[ability]
        except Exception as exception:
            print(exception)
            return "None"

    def get_type_name(self, type: int):
        try:
            return self.__strings.types[type]
        except Exception as exception:
            print(exception)
            return "None"

    def get_nature_name(self, nature: int):
        try:
            return self.__strings.natures[nature]
        except Exception as exception:
            print(exception)
            return "None"

    def get_item_name(self, item: int):
        try:
            return self.__strings.itemlist[item]
        except Exception as exception:
            print(exception)
            return "None"

    def get_ball_name(self, ball: int):
        try:
            return self.__strings.balllist[ball]
        except Exception as exception:
            print(exception)
            return "None"

    def get_game_name(self, version: int):
        try:
            return self.__strings.gamelist[version]
        except Exception as exception:
            print(exception)
            return "None"
