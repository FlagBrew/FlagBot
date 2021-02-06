import discord
import inspect
import io
from discord.ext import commands

#  Revised addon loading for Meta taken from https://stackoverflow.com/a/24940613
addons = {
    "addons.events": "Events",
    "addons.info": "Info",
    "addons.mod": "Moderation",
    "addons.pkhex": "pkhex",
    "addons.pyint": "PythonInterpreter",
    "addons.utility": "Utility",
    "addons.warns": "Warning"
    }
keys = {}
failed_loads = {}
for addon in addons.keys():
    try:
        keys[addons[addon]] = __import__(addon, fromlist=addons[addon])
    except Exception as e:
        failed_loads[addons[addon]] = e

class Meta(commands.Cog, command_attrs=dict(hidden=True)):

    def __init__(self, bot):
        self.bot = bot
        self.addons = {}
        for key in keys.keys():
            self.addons[keys[key].__name__] = keys[key]
        print(f'Addon "{self.__class__.__name__}" loaded')

    @commands.command(hidden=True)
    async def failedloads(self, ctx):
        if len(failed_loads) == 0:
            return await ctx.send("No modules failed to load!")
        await ctx.send(f"Failed to load: `{'`, `'.join(f'{a}` - `{e}' for a, e in failed_loads.items())}`")

    @commands.command(hidden=True)
    async def source(self, ctx, function, cl=None):
        """Gets the source code of a function / command. Limited to bot creator."""
        if not ctx.author == self.bot.creator:
            raise commands.errors.CheckFailure()
        command = self.bot.get_command(function)
        if command is None:
            if not cl in self.addons:
                return await ctx.send("That isn't a command. Please supply a valid class name for retrieving functions.")
            try:
                cl_obj = self.addons[cl]
                func = getattr(cl_obj, function)
            except AttributeError:
                return await ctx.send(f"I couldn't find a function named `{function}` in the `{cl}` class.")
            src = inspect.getsource(func)
        else:
            src = inspect.getsource(command.callback)
        if len(src) < 1900:
            src = src.replace('`', r'\`')
            await ctx.send(f"Source code for the `{function}` command{' in the `' + cl + '` class' if cl in self.addons else ''}: ```py\n{src}\n```")
        else:
            await ctx.send(f"Source code for the `{function}` command{' in the `' + cl + '` class' if cl in self.addons else ''} (Large source code):", file=discord.File(io.BytesIO(src.encode("utf-8")), filename="output.txt"))

    @commands.has_any_role("Bot Dev", "Discord Moderator")
    @commands.command()
    async def activity(self, ctx, activity_type=None, *, new_activity=None):
        """Changes the bot's activity. Giving no type and status will clear the activity."""
        activity_types = {
            "watching": discord.ActivityType.watching,
            "listening": discord.ActivityType.listening,
            "playing": discord.ActivityType.playing
        }
        if activity_type is None and new_activity is None:
            await self.bot.change_presence(activity=None)
            return await ctx.send("Cleared my activity.")
        elif not activity_type is None and new_activity is None:
            raise commands.errors.MissingRequiredArgument(inspect.Parameter(name='new_activity', kind=inspect.Parameter.POSITIONAL_ONLY))
        if not activity_type.lower() in activity_types:
            return await ctx.send(f"`{activity_type}` is not a valid activity type. Valid activity types: `{'`, `'.join(x for x in activity_types)}`.")
        elif len(new_activity) > 30:
            return await ctx.send(f"Activities must be limited to less than 30 characters. Inputted value length: {len(new_activity)} characters.")
        real_type = activity_types[activity_type.lower()]
        activity = discord.Activity(name=new_activity, type=real_type)
        await self.bot.change_presence(activity=activity)
        await ctx.send(f"Successfully changed my activity to: `{activity_type.title()} {new_activity}`.")

    @commands.has_any_role("Bot Dev", "Discord Moderator")
    @commands.command()
    async def setnick(self, ctx, *, nick=None):
        """Changes the bot's nick. Giving no nick will clear the nickname."""
        if nick is None:
            await ctx.me.edit(nick=None)
            return await ctx.send("Cleared my nickname.")
        elif len(nick) < 2 or len(nick) > 32:
            return await ctx.send(f"Nicknames must be greater than or equal to 2 characters, but less than 33 characters. Inputted value length: {len(nick)} characters.")
        await ctx.me.edit(nick=nick)
        await ctx.send(f"Successfully changed my nickname to: `{nick}`")


def setup(bot):
    bot.add_cog(Meta(bot))
