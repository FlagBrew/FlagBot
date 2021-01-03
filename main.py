#!/usr/bin/env python3

description = """FlagBot server helper bot by GriffinG1"""

# import dependencies
import os
import discord
import asyncio
import traceback
import sys
import argparse
import json
import pymongo
import aiohttp
import concurrent
import psutil
from exceptions import PKHeXMissingArgs
from discord.ext import commands

try:
    import config
except ModuleNotFoundError:
    if "-args" not in sys.argv:
        print("Config not available, and '-args' not passed. Bot will not be able to run in this state.")

def parse_cmd_arguments():  # travis handler, taken from https://github.com/appu1232/Discord-Selfbot/blob/master/appuselfbot.py#L33
    parser = argparse.ArgumentParser(description="Flagbot")
    parser.add_argument("-test", "--test-run",  # test run flag for Travis
                        action="store_true",
                        help="Makes the bot quit before trying to log in")
    parser.add_argument("-args",
                        action="store_true",
                        help="Allows using args")
    return parser
argpar, unknown = parse_cmd_arguments().parse_known_args()
print(unknown)
_test_run = argpar.test_run
if _test_run:
    try:
        os.path.isfile("saves/faqs/faq.json")
        os.path.isfile("/saves/key_inputs.json")
    except:
        print('faq.json or key_inputs.json is missing')  # only visible in Travis
    print("Quitting: test run")
    exit(0)
_args_run = argpar.args
if _args_run:
    is_using_args = True
    args = sys.argv[2:]
    print("Running using command line arguments...")
else:
    is_using_args = False

# sets working directory to bot's folder
dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)

if not is_using_args:  # handles pulling the config/args needed for creating the bot object
    prefix = config.prefix
    token = config.token
    default_activity = discord.Activity(name=config.default_activity, type=discord.ActivityType.watching)
else:
    token, prefix = args[0:2]
    default_activity = discord.Activity(name=args[2], type=discord.ActivityType.watching)

intents = discord.Intents().all()
intents.members = True
intents.presences = True
bot = commands.Bot(command_prefix=prefix, description=description, activity=default_activity, intents=intents)

if not is_using_args:  # handles setting up the bot vars
    bot.is_mongodb = config.is_mongodb
    bot.api_url = config.api_url
    bot.flagbrew_url = config.flagbrew_url
    bot.sprite_url = config.sprite_url
else:
    bot.is_mongodb, bot.api_url, bot.flagbrew_url, bot.sprite_url = args[3:7]
bot.gpss_url = bot.flagbrew_url

if not os.path.exists('saves/warns.json'):
    data = {}
    with open('saves/warns.json', 'w') as f:
        json.dump(data, f, indent=4)
with open('saves/warns.json', 'r') as f:
    bot.warns_dict = json.load(f)

if not os.path.exists('saves/disabled_commands.json'):
    with open('saves/disabled_commands.json', 'w') as f:
        json.dump([], f, indent=4)
with open('saves/disabled_commands.json', 'r') as f:
    bot.disabled_commands = json.load(f)

if not os.path.exists("saves/mutes.json"):
    with open("saves/mutes.json", "w") as f:
        json.dump({}, f, indent=4)
with open("saves/mutes.json", "r") as f:
    bot.mutes_dict = json.load(f)

if bot.is_mongodb:
    if not is_using_args:
        db_address = config.db_address
    else:
        db_address = args[7]
    connected = False
    try:
        # try connecting to the database
        bot.db = pymongo.MongoClient(db_address, serverSelectionTimeoutMS=3000)
        # try get server info, if the server is down it will error out after 3 seconds
        bot.db.server_info()
        connected = True
    except pymongo.errors.ServerSelectionTimeoutError:
        # when the database connection fails
        bot.is_mongodb = False
    # sync the database with the warns file on start up, only if the database is online
    if connected:
        for warn in bot.warns_dict:
            bot.db['flagbrew']['warns'].update_one({"user": warn}, 
            { 
                "$set": {
                    "user": warn,
                    "warns": bot.warns_dict[warn]
                }
            }, upsert=True)
    
if not is_using_args:
    bot.site_secret = config.secret
    bot.github_user = config.github_username
    bot.github_pass = config.github_password
    bot.ready = False
    bot.is_beta = config.is_beta
else:
    bot.site_secret, bot.github_user, bot.github_pass, bot.is_beta = args[8:12]
    bot.ready = False

bot.dir_path = os.path.dirname(os.path.realpath(__file__))

bot.flagbrew_id = 278222834633801728
bot.testing_id = 378420595190267915

@bot.check  # taken and modified from https://discordpy.readthedocs.io/en/rewrite/ext/commands/commands.html#global-checks
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
        await ctx.send("You are missing required arguments.")
        await ctx.send_help(ctx.command)
    elif isinstance(error, discord.ext.commands.NoPrivateMessage):
        await ctx.send("You cannot use this command in DMs! Please go to <#379201279479513100>")
    elif isinstance(error, discord.ext.commands.errors.BadArgument):
        await ctx.send("A bad argument was provided, please try again.")
    elif isinstance(error, discord.ext.commands.errors.CheckFailure):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
        await ctx.send("{} This command is on a cooldown.".format(ctx.author.mention))
    elif isinstance(error, commands.DisabledCommand):
        await ctx.send("This command is currently disabled.")
    elif isinstance(error, aiohttp.client_exceptions.ServerDisconnectedError) or isinstance(error, concurrent.futures._base.TimeoutError):
        pass  # hopefully fix the disconnect errors that keep popping up
    elif isinstance(error, PKHeXMissingArgs):
        if ctx.command.name == "pokeinfo":
            await ctx.send("This command requires a pokemon or species be given!")
        else:
            await ctx.send("This command requires a pokemon be inputted!")
        await ctx.send_help(ctx.command)
    else:
        if ctx.command:
            await ctx.send("An error occurred while processing the `{}` command.".format(ctx.command.name))
        print('Ignoring exception in command {0.command} in {0.message.channel}'.format(ctx))
        tb = traceback.format_exception(type(error), error, error.__traceback__)
        error_trace = "".join(tb)
        print(error_trace)
        embed = discord.Embed(description=error_trace.replace("__", "_\\_").replace("**", "*\\*"))
        await bot.err_logs_channel.send("An error occurred while processing the `{}` command in channel `{}`.".format(ctx.command.name, ctx.message.channel), embed=embed)


@bot.event
async def on_error(event_method, *args, **kwargs):
    print(args[0])
    if isinstance(args[0], commands.errors.CommandNotFound):
        return
    print("Ignoring exception in {}".format(event_method))
    tb = traceback.format_exc()
    error_trace = "".join(tb)
    print(error_trace)
    embed = discord.Embed(description=error_trace.replace("__", "_\\_").replace("**", "*\\*"))
    await bot.err_logs_channel.send("An error occurred while processing `{}`.".format(event_method), embed=embed)


@bot.event
async def on_ready():
    # this bot should only ever be in one server anyway
    if len(bot.disabled_commands) > 0:
        for c in bot.disabled_commands:
            bot.get_command(c).enabled = False
            print('Disabled {}'.format(c))
    for guild in bot.guilds:
        try:
            if guild.id == bot.testing_id or guild.id == bot.flagbrew_id:
                bot.guild = guild
                bot.reload_counter = 0
                if guild.id == bot.flagbrew_id:
                    bot.logs_channel = discord.utils.get(guild.channels, id=351002624721551371)
                    bot.dm_logs_channel = discord.utils.get(guild.channels, id=695681340510699531)
                    bot.bot_channel = discord.utils.get(guild.channels, id=379201279479513100)
                    bot.bot_channel2 = discord.utils.get(guild.channels, id=658726241288847361)
                    bot.flagbrew_team_role = discord.utils.get(guild.roles, id=758286639784525845)
                    bot.discord_moderator_role = discord.utils.get(guild.roles, id=396988600480301059)
                    bot.patrons_role = discord.utils.get(guild.roles, id=330078911704727552)
                    bot.mute_role = discord.utils.get(guild.roles, id=519566020315185163)
                    bot.protected_roles = (discord.utils.get(guild.roles, id=279598900799864832), bot.discord_moderator_role, bot.flagbrew_team_role, discord.utils.get(guild.roles, id=381053929389031424))
                    bot.patrons_channel = discord.utils.get(guild.channels, id=381000988246540292)
                    bot.interpreter_logs_channel = discord.utils.get(guild.channels, id=672553506690826250)
                    bot.crash_dump_channel = discord.utils.get(guild.channels, id=721444652481249372)
                    bot.crash_log_channel = discord.utils.get(guild.channels, id=721465461518106624)
                    bot.activity_logs_channel = discord.utils.get(guild.channels, id=723705005122519071)
                with open('saves/faqdm.json', 'r') as f:
                    bot.dm_list = json.load(f)

                if guild.id == bot.testing_id:
                    if bot.is_beta:
                        id = 614206536394342533
                    else:
                        id = 468877079023321089
                    bot.err_logs_channel = discord.utils.get(guild.channels, id=id)
                    bot.testing_channel = discord.utils.get(guild.channels, id=385034577636491264)
                    bot.testing_logs_channel = discord.utils.get(guild.channels, id=723665111469916242)

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
            try:
                with open('restart.txt', 'r') as f:
                    restart_channel = f.readline()
                c = await bot.fetch_channel(restart_channel)
                await c.send("Successfully restarted!")
                os.remove('restart.txt')
            except (discord.NotFound, FileNotFoundError):
                pass
            print("Initialized on {}.".format(guild.name))
        except:
            print("Failed to initialize on {}".format(guild.name))
    bot.creator = await bot.fetch_user(177939404243992578)
    bot.pie = await bot.fetch_user(307233052650635265)
    bot.allen = await bot.fetch_user(211923158423306243)
    bot.session = aiohttp.ClientSession(loop=asyncio.get_event_loop())
    bot.ready = True


# loads extensions
cogs = [
    'addons.events',
    'addons.info',
    'addons.meta',
    'addons.mod', 
    'addons.pkhex',
    'addons.pyint',
    'addons.utility', 
    'addons.warns'
]

failed_cogs = []

for extension in cogs:
    try:
        bot.load_extension(extension)
    except Exception as e:
        print('{} failed to load.\n{}: {}'.format(extension, type(e).__name__, e))
        failed_cogs.append([extension, type(e).__name__, e])
if not failed_cogs:
    print('All addons loaded!')
if bot.is_beta:
    bot.load_extension('addons.devtools')  # only present in my beta environment


@bot.command(hidden=True)
async def load(ctx, *, module):
    """Loads an addon"""
    if ctx.author == ctx.guild.owner or ctx.author == bot.creator or ctx.author == bot.allen:
        try:
            bot.load_extension("addons.{}".format(module))
        except Exception as e:
            await ctx.send(':anger: Failed!\n```\n{}: {}\n```'.format(type(e).__name__, e))
        else:
            await ctx.send(':white_check_mark: Extension loaded.')
    else:
        await ctx.send("You don't have permission to do that!")

@bot.command(hidden=True)
async def unload(ctx, *, module):
    """Unloads an addon"""
    if ctx.author == ctx.guild.owner or ctx.author == bot.creator or ctx.author == bot.allen:
        try:
            bot.unload_extension("addons.{}".format(module))
        except Exception as e:
            await ctx.send(':anger: Failed!\n```\n{}: {}\n```'.format(type(e).__name__, e))
        else:
            await ctx.send(':white_check_mark: Extension unloaded.')
    else:
        await ctx.send("You don't have permission to do that!")


@bot.command(hidden=True)
async def reload(ctx):
    """Reloads an addon."""
    bot.reload_counter += 1
    if ctx.author == ctx.guild.owner or ctx.author == bot.creator:
        errors = ""
        addon_dict = {
            "DevTools": "devtools",  # not loaded by default...
            "Events": "events",
            "Info": "info",
            "Meta": "meta",
            "Moderation": "mod",
            "pkhex": "pkhex",
            "PythonInterpreter": "pyint",
            "Utility": "utility",
            "Warning": "warns"
        }
        loaded_cogs = bot.cogs.copy()
        for addon in loaded_cogs:
            try:
                bot.reload_extension("addons.{}".format(addon_dict[addon]))
            except Exception as e:
                if addon not in addon_dict.keys():
                    pass
                errors += 'Failed to load addon: `{}.py` due to `{}: {}`\n'.format(addon, type(e).__name__, e)
            if len(bot.disabled_commands) > 0:
                for c in bot.disabled_commands:
                    bot.get_command(c).enabled = False
        if not errors:
            await ctx.send(':white_check_mark: Extensions reloaded.')
        else:
            await ctx.send(errors)
        if bot.reload_counter == 1:
            await ctx.send("This is the first reload after I restarted!")
    else:
        await ctx.send("You don't have permission to do that!")


def check_is_author(ctx):
    return ctx.message.author.id == bot.creator.id


@bot.command(aliases=['drid'], hidden=True)
@commands.check(check_is_author)
async def dump_role_id(ctx):
    """Dumps role ids for guild. Creator restricted."""
    roles = {}
    for role in ctx.guild.roles[1:]:
        roles[role.name] = role.id
    formatted_roles = str(roles).replace('{', '').replace(', ', ',\n').replace('}', '').replace("'", "**")
    await bot.creator.send(formatted_roles)
    await ctx.send("Roles dumped. Cleaning messages in 5 seconds.", delete_after=5)
    await asyncio.sleep(5.1)
    await ctx.message.delete()

@bot.command(hidden=True)  # taken from https://github.com/appu1232/Discord-Selfbot/blob/873a2500d2c518e0d25ca5a6f67828de60fbda99/cogs/misc.py#L626
async def ping(ctx):
    """Get time between HEARTBEAT and HEARTBEAT_ACK in ms."""
    ping = bot.latency * 1000
    ping = round(ping, 3)
    await ctx.send(f'🏓 Response time is {ping} milliseconds.')

@bot.command(hidden=True)
async def restart(ctx):
    """Restarts the bot."""
    if not ctx.author == ctx.guild.owner and not ctx.author == bot.creator and not ctx.author == bot.allen:
        return await ctx.send("You don't have permission to do that!")
    await ctx.send("Restarting...")
    with open('restart.txt', 'w') as f:
        f.write(str(ctx.channel.id))
    sys.exit(0)

@bot.command()
async def about(ctx):
    """Information about the bot"""
    embed = discord.Embed()
    embed.description = ("Python bot utilizing [discord.py](https://github.com/Rapptz/discord.py) for use in the FlagBrew server.\n"
                            "You can view the source code [here](https://github.com/GriffinG1/FlagBot).\n"
                            "Written by {}.".format(bot.creator.mention))
    embed.set_author(name="GriffinG1", url='https://github.com/GriffinG1', icon_url='https://avatars0.githubusercontent.com/u/28538707')
    total_mem = psutil.virtual_memory().total/float(1<<30)
    used_mem = psutil.Process().memory_info().rss/float(1<<20)
    embed.set_footer(text="{} MB used out of {} GB".format(round(used_mem, 2), round(total_mem, 2)))
    await ctx.send(embed=embed)


# Execute
print('Bot directory: ', dir_path)
bot.run(token)
