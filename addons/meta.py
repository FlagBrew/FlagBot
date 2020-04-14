import discord
import inspect
import io
from discord.ext import commands
from addons.events import Events
from addons.info import Info
from addons.mod import Moderation
from addons.pkhex import pkhex
from addons.pyint import PythonInterpreter
from addons.utility import Utility
from addons.warns import Warning

class Meta(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.addons = {
            Events.__name__: Events,
            Info.__name__: Info,
            self.__class__.__name__: self,
            Moderation.__name__: Moderation,
            pkhex.__name__: pkhex,
            PythonInterpreter.__name__: PythonInterpreter,
            Utility.__name__: Utility,
            Warning.__name__: Warning
        }
        print('Addon "{}" loaded'.format(self.__class__.__name__))

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
                return await ctx.send("I couldn't find a function named `{}` in the `{}` class.".format(function, cl))
            src = inspect.getsource(func)
        else:
            src = inspect.getsource(command.callback)
        if len(src) < 1900:
            src = src.replace('`', r'\`')
            await ctx.send("Source code for the `{}` command{}: ```py\n{}\n```".format(function, " in the `" + cl + "` class" if cl in self.addons else "", src))
        else:
            await ctx.send("Source code for the `{}` command{} (Large source code):".format(function, " in the `" + cl + "` class" if cl in self.addons else ""), file=discord.File(io.BytesIO(src.encode("utf-8")), filename="output.txt"))


def setup(bot):
    bot.add_cog(Meta(bot))
