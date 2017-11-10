import discord
from discord.ext import commands

stop_message = """
Ultra Sun and Ultra Moon support for PKSM is expected in {} weeks
"""

class Events:

    def __init__(self, bot):
        self.bot = bot
        print('Addon "{}" loaded'.format(self.__class__.__name__))
            

    async def on_message(self, message):
        if "usum" in message.content.lower() and "support" in message.content.lower():
            await ctx.send(stop_message.format(self.bot.tally))

def setup(bot):
    bot.add_cog(Events(bot))