import discord
import json
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
