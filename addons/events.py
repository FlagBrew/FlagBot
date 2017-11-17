import discord
from discord.ext import commands

stop_message = """
Ultra Sun and Ultra Moon support for PKSM is expected in **{}** weeks :upside_down:
"""
usum = [
    'us',
    'um',
    'ultra moon',
    'ultra sun',
    'usum',
]
support = [
    'support',
    'updated',
    'available',
    'working',
    'compatible',
    'compatibility',
]

class Events:

    def __init__(self, bot):
        self.bot = bot
        print('Addon "{}" loaded'.format(self.__class__.__name__))


    async def on_message(self, message):
        if self.bot.counter:
            usumCtn = False
            supCtn = False
            badStr = False
            words = message.content.lower().replace(',', '').replace('`', '').split()
            if not message.author.name == self.bot.user.name:
                for word in words:
                    for x in usum:
                        if x == word:
                            usumCtn = True
                            break
                    for y in support:
                        if y == word:
                            supCtn = True
                            break
                if supCtn and usumCtn:
                    badStr = True
                    
                if badStr is True:
                    with open("tally.txt") as f:
                        tally = f.read()
                        f.close()
                    with open("tally.txt", "w") as f:
                        tally = int(tally) + 1
                        f.write(str(tally))
                        f.close()
                    await message.channel.send(stop_message.format(tally))
                else:
                    pass
            else:
                pass

def setup(bot):
    bot.add_cog(Events(bot))
