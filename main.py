#!/usr/bin/env python3

description = """FlagBot server helper bot by GriffinG1"""

# import dependencies
import os
from discord.ext import commands
import discord
import datetime
import json, asyncio
import copy
import configparser
import traceback
import sys
import os
import re
import ast

# sets working directory to bot's folder
dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)

config = configparser.ConfigParser()
config.read("config.ini")

try:
    prefix = config['Main']['prefix']
except KeyError:
    prefix = ['!', '.']

bot = commands.Bot(command_prefix=prefix, description=description)

bot.dir_path = os.path.dirname(os.path.realpath(__file__))

bot.flagbrew_id = 278222834633801728
bot.testing_id = 378420595190267915

try:
    token = os.environ['TOKEN']
    heroku = True
except KeyError:
    token = config['Main']['token']
    heroku = False
    
@bot.check # taken and modified from https://discordpy.readthedocs.io/en/rewrite/ext/commands/commands.html#global-checks
async def globally_block_dms(ctx):
    if ctx.guild is None:
        raise discord.ext.commands.NoPrivateMessage('test')
        return False
    return True
        

# mostly taken from https://github.com/Rapptz/discord.py/blob/async/discord/ext/commands/bot.py
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.CommandNotFound):
        pass  # ...don't need to know if commands don't exist
    elif isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        formatter = commands.formatter.HelpFormatter()
        await ctx.send("You are missing required arguments.\n{}".format(formatter.format_help_for(ctx, ctx.command)[0]))
    elif isinstance(error, discord.ext.commands.NoPrivateMessage):
        await ctx.send("You cannot use this command in DMs! Please go to <#379201279479513100>")
    elif isinstance(error, discord.ext.commands.errors.BadArgument):
        await ctx.send("A bad argument was provided, please try again.")
    elif isinstance(error, discord.ext.commands.errors.CheckFailure):
        await ctx.send("You don't have permission to use this command.")
    else:
        if ctx.command:
            await ctx.send("An error occurred while processing the `{}` command.".format(ctx.command.name))
        print('Ignoring exception in command {0.command} in {0.message.channel}'.format(ctx))
        tb = traceback.format_exception(type(error), error, error.__traceback__)
        error_trace = "".join(tb)
        print(error_trace)
        embed = discord.Embed(description=error_trace)
        await bot.err_logs_channel.send("An error occurred while processing the `{}` command in channel `{}`.".format(ctx.command.name, ctx.message.channel), embed=embed)

@bot.event
async def on_error(event_method, *args, **kwargs):
    if isinstance(args[0], commands.errors.CommandNotFound):
        return
    print("Ignoring exception in {}".format(event_method))
    tb = traceback.format_exc()
    error_trace = "".join(tb)
    print(error_trace)
    embed = discord.Embed(description=error_trace)
    await bot.err_logs_channel.send("An error occurred while processing `{}`.".format(event_method), embed=embed)
    


@bot.event
async def on_ready():
    # this bot should only ever be in one server anyway
    for guild in bot.guilds:
        try:
            if guild.id == bot.testing_id or guild.id == bot.flagbrew_id:
                bot.guild = guild
                
                try:
                    with open("restart.txt") as f:
                        channel = bot.get_channel(int(f.readline()))
                        f.close()
                    await channel.send("Restarted!")
                    os.remove("restart.txt")
                except:
                    pass
                
                if guild.id == bot.flagbrew_id:
                    bot.logs_channel = discord.utils.get(guild.channels, id=351002624721551371)
                    bot.patron_role = discord.utils.get(guild.roles, id=330078911704727552)
                    bot.pksm_update_role = discord.utils.get(guild.roles, id=467719280163684352)
                    bot.checkpoint_update_role = discord.utils.get(guild.roles, id=467719471746777088)
                    bot.general_update_role = discord.utils.get(guild.roles, id=467719755822792730)
                    
                if guild.id == bot.testing_id:
                    bot.err_logs_channel = discord.utils.get(guild.channels, id=468877079023321089)
                    
                bot.creator = discord.utils.get(guild.members, id=177939404243992578)
                    
            else:
                try:
                    await guild.owner.send("Left your server, `{}`, as this bot should only be used on the PKSM server under this token.".format(guild.name))
                except discord.Forbidden:
                    for channel in guild.channels:
                       if guild.me.permissions_in(channel).send_messages and isinstance(channel, discord.TextChannel):
                            await channel.send("Left your server, as this bot should only be used on the PKSM server under this token.")
                            break
                finally:
                    await guild.leave()
                
            print("Initialized on {}.".format(guild.name))
        except:
            print("Failed to initialize on {}".format(guild.name))

    
# loads extensions
addons = [
    'addons.utility',
    'addons.info',
    'addons.mod',
    'addons.events'
]

failed_addons = []

for extension in addons:
    try:
        bot.load_extension(extension)
    except Exception as e:
        print('{} failed to load.\n{}: {}'.format(extension, type(e).__name__, e))
        failed_addons.append([extension, type(e).__name__, e])
if not failed_addons:
    print('All addons loaded!')
        
@bot.command(hidden=True)
async def load(ctx, *, module):
    """Loads an addon"""
    if ctx.author == ctx.guild.owner or ctx.author == bot.creator:
        try:
            bot.load_extension("addons.{}".format(module))
        except Exception as e:
            await ctx.send(':anger: Failed!\n```\n{}: {}\n```'.format(type(e).__name__, e))
        else:
            await ctx.send(':white_check_mark: Extension loaded.')
    else:
        await ctx.send("You don't have permission to do that!")
        
# Execute
print('Bot directory: ', dir_path)
bot.run(token)
