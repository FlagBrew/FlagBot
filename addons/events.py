import discord
from discord.ext import commands

stop_message = """
Ultra Sun and Ultra Moon support for PKSM is expected in **{}** weeks 🙃
"""
usum = [
    'us',
    'um',
    'ultra moon',
    'ultra sun',
]
support = [
    'support',
    'updated',
    'available',
    'working',
    'compatible'
]

class Events:

    def __init__(self, bot):
        self.bot = bot
        print('Addon "{}" loaded'.format(self.__class__.__name__))


    async def on_message(self, message):
        bad = False
        if not message.author.name == self.bot.user.name:
            for x in usum:
                for y in support:
                    if x in message.content.lower() and y in message.content.lower():
                        bad = True
                        break
        if bad == True:
            with open("tally.txt") as f:
                tally = f.read()
                f.close()
            with open("tally.txt", "w") as f:
                tally = int(tally) + 1
                f.write(str(tally))
                f.close()
            await message.channel.send(stop_message.format(tally))
            bad = False
        else:
            pass

def setup(bot):
    bot.add_cog(Events(bot))