import discord
from discord.ext import commands

class Info:

    def __init__(self, bot):
        self.bot = bot
        print('Addon "{}" loaded'.format(self.__class__.__name__))
        
        
    @commands.command()
    async def release(self, ctx):
        embed = discord.Embed(description="You can get the latest release of PKSM [here](https://github.com/BernardoGiordano/PKSM/releases/latest)")
        await ctx.send(embed=embed)
        
def setup(bot):
    bot.add_cog(Info(bot))