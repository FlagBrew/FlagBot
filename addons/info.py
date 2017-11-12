import discord
from discord.ext import commands

class Info:

    def __init__(self, bot):
        self.bot = bot
        print('Addon "{}" loaded'.format(self.__class__.__name__))
        
        
    @commands.command(aliases=['releases'])
    async def release(self, ctx):
        """Gives the latest PKSM release"""
        embed = discord.Embed(description="You can get the latest release of PKSM [here](https://github.com/BernardoGiordano/PKSM/releases/latest)")
        await ctx.send(embed=embed)
        
    @commands.command()
    async def about(self, ctx):
        """Information about the bot"""
        await ctx.send("This is a bot coded in python for use in the PKSM server, made by Griffin#2329. You can view the source code [here](https://github.com/GriffinG1/PKSMBot).")
        
def setup(bot):
    bot.add_cog(Info(bot))
