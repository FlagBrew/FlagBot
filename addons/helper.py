import discord
import json
from datetime import datetime
from discord.ext import commands

async def check_mute_expiry(mutes_dict, member):
    if not str(member.id) in mutes_dict.keys():
        return None
    end_time = mutes_dict[str(member.id)]
    if end_time is "Indefinite":
        return True
    elif end_time == "":
        return None
    end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    diff = end_time - datetime.utcnow()
    return diff.total_seconds() < 0  # Return False if expired, else True