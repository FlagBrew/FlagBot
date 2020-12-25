import discord
import json
import functools
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
    diff = end_time - datetime.utcnow()
    return diff.total_seconds() < 0  # Return False if expired, else True

def restricted_to_bot(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        func_self = args[0]  # assume self is at args[0]
        ctx = args[1]  # and assume ctx is at args[1]
        if not ctx.channel in (func_self.bot.bot_channel, func_self.bot.bot_channel2) and ctx.guild.id == 278222834633801728:
            return await ctx.send(f"This command is restricted to {func_self.bot.bot_channel.mention}.")
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
        elif ctx.invoked_with == "swsh":
            faq_doc = "pksm"
            faq_item = "2"
        elif ctx.invoked_with == "emulator":
            faq_doc = "pksm"
            faq_item = "3"
        elif ctx.invoked_with == "sendpkx":
            faq_doc = "pksm"
            faq_item = "7"
        elif ctx.invoked_with == "wc3" or ctx.invoked_with == "gen3events":
            faq_doc = "pksm"
            faq_item = "9"
        elif ctx.invoked_with == "addcode" or ctx.invoked_with == "fixcheat":
            faq_doc = "checkpoint"
            faq_item = "1"
        elif ctx.invoked_with == "wheregame":
            faq_doc = "checkpoint"
            faq_item = "2"
        elif ctx.invoked_with == "pkcrash":
            faq_doc = "checkpoint"
            faq_item = "4"
        await func(self=self, ctx=ctx, faq_doc=faq_doc, faq_item=faq_item)
    return wrapper

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
            "SH": "Shield"
        }
