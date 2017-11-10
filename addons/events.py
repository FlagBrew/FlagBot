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
            with open("tally.txt") as f:
                tally = f.read()
                f.close()
            with open("tally.txt", "w") as f:
                tally = int(tally) + 1
                f.write(str(tally))
                f.close()
            await message.channel.send(stop_message.format(tally))

def setup(bot):
    bot.add_cog(Events(bot))