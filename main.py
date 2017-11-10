description = """PKSM server helper bot. Don't make me angry"""

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
import json
import ast
import git

# sets working directory to bot's folder
dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)

git = git.cmd.Git(".")

prefix = ['!', '.']
bot = commands.Bot(command_prefix=prefix, description=description)

config = configparser.ConfigParser()
config.read("config.ini")

# http://stackoverflow.com/questions/3411771/multiple-character-replace-with-python
def escape_name(name):
    chars = "\\`*_<>#@:~"
    name = str(name)
    for c in chars:
        if c in name:
            name = name.replace(c, "\\" + c)
    return name.replace("@", "@\u200b")  # prevent mentions


bot.escape_name = escape_name
bot.pruning = False  # used to disable leave logs if pruning, maybe.
bot.escape_trans = str.maketrans({
    "*": "\*",
    "_": "\_",
    "~": "\~",
    "`": "\`",
    "\\": "\\\\"
})  # used to escape a string


# mostly taken from https://github.com/Rapptz/discord.py/blob/async/discord/ext/commands/bot.py
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.CommandNotFound):
        pass  # ...don't need to know if commands don't exist
    elif isinstance(error, discord.ext.commands.errors.CheckFailure):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        formatter = commands.formatter.HelpFormatter()
        await ctx.send("You are missing required arguments.\n{}".format(formatter.format_help_for(ctx, ctx.command)[0]))
    else:
        if ctx.command:
            await ctx.send("An error occurred while processing the `{}` command.".format(ctx.command.name))
        print('Ignoring exception in command {0.command} in {0.message.channel}'.format(ctx))
        tb = traceback.format_exception(type(error), error, error.__traceback__)
        error_trace = "".join(tb)
        print(error_trace)

@bot.event
async def on_error(event_method, *args, **kwargs):
    if isinstance(args[0], commands.errors.CommandNotFound):
        return
    print("Ignoring exception in {}".format(event_method))
    tb = traceback.format_exc()
    error_trace = "".join(tb)
    print(error_trace)

bot.all_ready = False
bot._is_all_ready = asyncio.Event(loop=bot.loop)


async def wait_until_all_ready():
    """Wait until the entire bot is ready."""
    await bot._is_all_ready.wait()
bot.wait_until_all_ready = wait_until_all_ready


@bot.event
async def on_ready():
    # this bot should only ever be in one server anyway
    for guild in bot.guilds:
        bot.guild = guild
        if bot.all_ready:
            break
        print("Initialized on {}.".format(guild.name))
        
        bot.all_ready = True
        bot._is_all_ready.set()

    
# loads extensions
addons = [
    'addons.events'
]

failed_addons = []

for extension in addons:
    try:
        bot.load_extension(extension)
    except Exception as e:
        print('{} failed to load.\n{}: {}'.format(extension, type(e).__name__, e))
        failed_addons.append([extension, type(e).__name__, e])
        
        
@bot.command()
async def pull(ctx):
    """Pull git changes, owner only."""
    if ctx.author == ctx.guild.owner:
        await ctx.send("Pulling changes from Github")
        git.pull()
        await ctx.send("Changes pulled!")
    else:
        await ctx.send("You don't have permission to do that!")
        
@bot.command()
async def reload(ctx):
    """Reloads an addon."""
    if ctx.author == ctx.guild.owner:
        errors = ""
        for addon in os.listdir("addons"):
            if ".py" in addon:
                addon = addon.replace('.py', '')
                try:
                    bot.unload_extension("addons.{}".format(addon))
                    bot.load_extension("addons.{}".format(addon))
                except Exception as e:
                    errors += 'Failed to load addon: `{}.py` due to `{}: {}`\n'.format(addon, type(e).__name__, e)
        if not errors:
            await ctx.send(':white_check_mark: Extensions reloaded.')
        else:
            await ctx.send(errors)
    else:
        await ctx.send("You don't have permission to do that!")
        
@bot.command()
async def restart(ctx):
    """Restarts the bot, obviously"""
    if ctx.author == ctx.guild.owner:
        await ctx.send("Restarting...")
        sys.exit(0)
    else:
        await ctx.send("You don't have permission to do that!")

@bot.command()
async def wait(ctx):
    """Returns how long it's gonna take"""
    await ctx.send("It's gonna be {} more weeks till Ultra Sun and Ultra Moon is supported 🙂".format(bot.tally))
        
        
# Execute
print('Bot directory: ', dir_path)
bot.run(config['Main']['token'])