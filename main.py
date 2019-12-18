#!/usr/bin/env python3

description = """FlagBot server helper bot by GriffinG1"""

# import dependencies
import os
from discord.ext import commands
import discord
import datetime
import asyncio
import copy
import traceback
import sys
import os
import re
import ast
import argparse

try:
    import config
    heroku = False
except Exception as e:
    heroku = True


def parse_cmd_arguments():  # travis handler, taken from https://github.com/appu1232/Discord-Selfbot/blob/master/appuselfbot.py#L33
    parser = argparse.ArgumentParser(description="Flagbot")
    parser.add_argument("-test", "--test-run",  # test run flag for Travis
                        action="store_true",
                        help="Makes the bot quit before trying to log in")
    return parser
args = parse_cmd_arguments().parse_args()
_test_run = args.test_run
if _test_run:
    try:
        os.path.isfile("saves/faqs/faq.json")
        os.path.isfile("/saves/key_inputs.json")
    except:
        print('faq.json or key_inputs.json is missing')  # only visible in Travis
    print("Quitting: test run")
    exit(0)

# sets working directory to bot's folder
dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)

if heroku:
    prefix = ['!', '.']
    token = os.environ['TOKEN']
else:
    prefix = config.prefix
    token = config.token

bot = commands.Bot(command_prefix=prefix, description=description)

if heroku:
    bot.site_secret = os.environ['SECRET']
    bot.github_user = os.environ['GITHUB-USER']
    bot.github_pass = os.environ['GITHUB-PASS']
else:
    bot.site_secret = config.secret
    bot.github_user = config.github_username
    bot.github_pass = config.github_password

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
        await ctx.message.delete()
        await ctx.send("This command is on cooldown.", delete_after=10)
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
    print(args[0])
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
                bot.reload_counter = 0
                if guild.id == bot.flagbrew_id:
                    bot.logs_channel = discord.utils.get(guild.channels, id=351002624721551371)
                    bot.bot_channel = discord.utils.get(guild.channels, id=379201279479513100)
                    bot.flagbrew_team_role = discord.utils.get(guild.roles, id=482928611809165335)
                    bot.discord_moderator_role = discord.utils.get(guild.roles, id=396988600480301059)
                    bot.patrons_role = discord.utils.get(guild.roles, id=330078911704727552)
                    bot.protected_roles = (discord.utils.get(guild.roles, id=279598900799864832), bot.discord_moderator_role, bot.flagbrew_team_role, discord.utils.get(guild.roles, id=381053929389031424))
                    bot.patrons_channel = discord.utils.get(guild.channels, id=381000988246540292)

                if guild.id == bot.testing_id:
                    if config.is_beta:
                        id = 614206536394342533
                    else:
                        id = 468877079023321089
                    bot.err_logs_channel = discord.utils.get(guild.channels, id=id)

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
    bot.creator = await bot.fetch_user(177939404243992578)
    bot.pie = await bot.fetch_user(307233052650635265)


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


@bot.command()
async def reload(ctx):
    """Reloads an addon."""
    bot.reload_counter += 1
    if ctx.author == ctx.guild.owner or ctx.author == bot.creator:
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
    """Get response time."""
    msgtime = ctx.message.created_at.now()
    await (await bot.ws.ping())
    now = datetime.datetime.now()
    ping = now - msgtime
    await ctx.send('🏓 Response time is {} milliseconds.'.format(str(ping.microseconds / 1000.0)))

# Execute
print('Bot directory: ', dir_path)
bot.run(token)
