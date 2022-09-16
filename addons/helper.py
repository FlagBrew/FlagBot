import discord
import json
import functools
import re
from datetime import datetime
from discord.ext import commands


async def check_mute_expiry(mutes_dict, member):
    if not str(member.id) in mutes_dict.keys():
        return None
    end_time = mutes_dict[str(member.id)]
    if end_time == "Indefinite":
        return True
    elif end_time == "":
        return None
    end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    diff = end_time - discord.utils.utcnow()
    return diff.total_seconds() < 0  # Return False if expired, else True


def spam_limiter(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        func_self = args[0]  # assume self is at args[0]
        ctx = args[1]  # and assume ctx is at args[1]
        count = 0
        async for message in ctx.channel.history(limit=10):
            if message.content.startswith(func_self.bot.command_prefix[0] + ctx.invoked_with) and (len(message.mentions) > 0 or message.reference is not None):
                if len(message.mentions) == 0:
                    msg_ref_auth = message.reference.resolved.author
                else:
                    msg_ref_auth = None
                if ctx.author not in message.mentions and not ctx.author == msg_ref_auth:
                    break
                elif count > 0:
                    return await ctx.send(f"{ctx.author.mention} read the goddamned message I sent, instead of just using the command again and spamming. If you ignore the contents of *this* message, you will be warned.")
            count += 1
        await func(*args, **kwargs)
    return wrapper


def restricted_to_bot(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        func_self = args[0]  # assume self is at args[0]
        ctx = args[1]  # and assume ctx is at args[1]
        if ctx.author in (func_self.bot.allen, func_self.bot.creator, func_self.bot.pie):
            pass
        elif ctx.channel not in (func_self.bot.bot_channel, func_self.bot.bot_channel2) and ctx.guild.id == 278222834633801728:
            await ctx.message.delete()
            return await ctx.send(f"{ctx.author.mention} This command is restricted to {func_self.bot.bot_channel.mention}.", delete_after=10)
        await func(*args, **kwargs)
    return wrapper


def faq_decorator(func):
    @functools.wraps(func)
    async def wrapper(self, ctx, faq_doc, faq_item):
        if ctx.invoked_with in ("faq", "rtfm"):
            pass
        elif ctx.invoked_with == "vc":
            faq_doc = "general"
            faq_item = "1"
        elif ctx.invoked_with == "entitled":
            faq_doc = "general"
            faq_item = "2"
        elif ctx.invoked_with == "rules":
            faq_doc = "general"
            faq_item = "4"
        elif ctx.invoked_with in ("lgpe", "swsh", "bdsp", "pla", "scvi", "switchsupport"):
            faq_doc = "pksm"
            faq_item = "2"
        elif ctx.invoked_with == "emulator":
            faq_doc = "pksm"
            faq_item = "3"
        elif ctx.invoked_with == "sendpkx":
            faq_doc = "pksm"
            faq_item = "7"
        elif ctx.invoked_with in ("wc3", "gen3events"):
            faq_doc = "pksm"
            faq_item = "9"
        elif ctx.invoked_with == "romhacks":
            faq_doc = "pksm"
            faq_item = "10"
        elif ctx.invoked_with in ("addcode", "fixcheat"):
            faq_doc = "checkpoint"
            faq_item = "1"
        elif ctx.invoked_with == "wheregame":
            faq_doc = "checkpoint"
            faq_item = "2"
        elif ctx.invoked_with == "pkcrash":
            faq_doc = "checkpoint"
            faq_item = "4"
        elif ctx.invoked_with == "updatedb":
            faq_doc = "checkpoint"
            faq_item = "6"
        await func(self=self, ctx=ctx, faq_doc=faq_doc, faq_item=faq_item)
    return wrapper


def get_string_from_regex(regex_pattern, data):
    match = re.search(regex_pattern, data)
    if match:
        return match.group(0)  # Return entire match
    return ""  # Handle failed matches by returning an empty string


def get_sprite_url(pokemon, generation, form, shiny, gender, species_name):
    with open('saves/sprite_forms.json', 'r', encoding='utf-8') as file:
        sprite_json = json.load(file)
    pokemon_num = pokemon if len(pokemon) == 3 else "0" + pokemon if len(pokemon) == 2 else "00" + pokemon
    sprite_url = "https://cdn.sigkill.tech/sprites/pokemon-gen" + ("7x/" if generation not in ("8", "BDSP", "PLA") else "8/")
    sprite_url += "shiny/" if shiny else "regular/"
    if form is not None:
        forms = sprite_json[pokemon_num]["gen-8"] if generation == "8" else sprite_json[pokemon_num]["gen-7"]
        form_name = re.sub("[^a-zA-Z0-9 -]", "", form).replace(" ", "")
        for formlist_name in forms["forms"]:
            if form_name in formlist_name:
                try:
                    if forms["forms"][formlist_name]["is_alias_of"] is not None:
                        form_json_name = str(forms["forms"][formlist_name]["is_alias_of"])
                except KeyError:
                    form_json_name = formlist_name
                break
        else:
            form_json_name = "$"
    else:
        form_json_name = "$"
    try:
        has_female = sprite_json[pokemon_num]["gen-8" if generation == 8 else ["gen-7"]]["forms"][form_json_name]["has_female"]
    except (TypeError, KeyError):
        has_female = False
    if has_female and gender == "F":
        sprite_url += "female/"
    sprite_url += species_name
    sprite_url += ("-" + form_json_name) if form_json_name != "$" else ""
    sprite_url += ".png"
    sprite_url = sprite_url.replace(" ", "-")
    return sprite_url


game_dict = {
    "RD": "Red (VC)",
    "BU": "Blue (VC)",
    "GN": "Green (VC)",
    "YW": "Yellow (VC)",
    "GD": "Gold (VC)",
    "SV": "Silver (VC)",
    "C": "Crystal (VC)",
    "R": "Ruby",
    "S": "Sapphire",
    "E": "Emerald",
    "FR": "FireRed",
    "LG": "LeafGreen",
    "D": "Diamond",
    "P": "Pearl",
    "Pt": "Platinum",
    "HG": "Heart Gold",
    "SS": "Soul Silver",
    "B": "Black",
    "W": "White",
    "B2": "Black 2",
    "W2": "White 2",
    "OR": "Omega Ruby",
    "AS": "Alpha Sapphire",
    "SN": "Sun",
    "MN": "Moon",
    "US": "Ultra Sun",
    "UM": "Ultra Moon",
    "GP": "Let's Go Pikachu",
    "GE": "Let's Go Eevee",
    "SW": "Sword",
    "SH": "Shield",
    "BD": "Brilliant Diamond",
    "SP": "Shining Pearl",
    "PLA": "Legends Arceus",
    "LA": "Legends Arceus"  # Not sure if this is used anywhere, adding for safety.
}

default_forms = {
    "unown": "a",
    "deoxys": "normal",
    "burmy": "plant",
    "wormadam": "plant",
    "cherrim": "overcast",
    "shellos": "east",
    "gastrodon": "east",
    "rotom": "normal",
    "giratina": "origin",
    "shaymin": "sky",
    "arceus": "normal",
    "basculin": "blue",
    "deerling": "spring",
    "sawsbuck": "spring",
    "tornadus": "incarnate",
    "thundurus": "incarnate",
    "landorus": "incarnate",
    "kyurem": "normal",
    "keldeo": "ordinary",
    "meloetta": "aria",
    "vivillon": "poke ball",
    "flabébé": "red",
    "floette": "eternal",
    "florges": "red",
    "meowstic": "f",
    "aegislash": "shield",
    "pumpkaboo": "average",
    "gourgeist": "average",
    "hoopa": "unbound",
    "oricorio": "baile",
    "lycanroc": "dusk",
    "wishiwashi": "school",
    "minior": "red",

    "cramorant": "normal",
    "toxtricity": "amped",
    "indeedee": "f",
    "sinistea": "antique",
    "polteageist": "antique",
    "alcremie": "rainbow-swirl-plain",
    "morpeko": "default",
    "eiscue": "ice",
    "zacian": "crownedsword",
    "zamazenta": "crownedshield",
    "urshifu": "singlestrike"
}

key_inputs = {
    "0x1": ["A", "A"],
    "0x2": ["B", "B"],
    "0x4": ["Select", "X"],
    "0x8": ["Start", "Y"],
    "0x10": ["Right", "Left stick pressed"],
    "0x20": ["Left", "Right stick pressed"],
    "0x40": ["Up", "L"],
    "0x80": ["Down", "R"],
    "0x100": ["R", "ZL"],
    "0x200": ["L", "ZR"],
    "0x400": ["X", "Plus"],
    "0x800": ["Y", "Minus"],
    "0x1000": ["Debug", "Left"],
    "0x2000": ["Not-Folded", "Up"],
    "0x4000": ["ZL (N3DS Only)", "Right"],
    "0x8000": ["ZR (N3DS Only)", "Down"],
    "0x10000": ["None", "Left stick left"],
    "0x20000": ["None", "Left stick up"],
    "0x40000": ["None", "Left stick right"],
    "0x80000": ["None", "Left stick down"],
    "0x100000": ["Touchpad (Any Position)", "Right stick left"],
    "0x200000": ["None", "Right stick up"],
    "0x400000": ["None", "Right stick right"],
    "0x800000": ["None", "Right stick down"],
    "0x1000000": ["C stick right (N3DS Only)", "SL"],
    "0x2000000": ["C stick left (N3DS Only)", "SR"],
    "0x4000000": ["C stick up (N3DS Only)", "None"],
    "0x8000000": ["C stick down (N3DS Only)", "None"],
    "0x10000000": ["Circle pad right", "None"],
    "0x20000000": ["Circle pad left", "None"],
    "0x40000000": ["Circle pad up", "None"],
    "0x80000000": ["Circle pad down", "None"]
}
