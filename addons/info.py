import discord
from discord.ext import commands

class Info:

    def __init__(self, bot):
        self.bot = bot
        print('Addon "{}" loaded'.format(self.__class__.__name__))
        
        
    @commands.command(aliases=['releases'])
    async def release(self, ctx, app = ""):
        """Gives the latest releases for PKSM and Checkpoint"""
        if app.lower() == "pksm":
            embed = discord.Embed(description="You can get the latest release of PKSM [here](https://github.com/BernardoGiordano/PKSM/releases/latest).")
        elif app.lower() == "checkpoint":
            embed = discord.Embed(description="You can get the latest release of Checkpoint [here](https://github.com/BernardoGiordano/Checkpoint/releases/latest).")
        else:
            embed = discord.Embed(description="You can get the latest release of PKSM [here](https://github.com/BernardoGiordano/PKSM/releases/latest)\nYou can get the latest release of Checkpoint [here](https://github.com/BernardoGiordano/Checkpoint/releases/latest)")
        await ctx.send(embed=embed)
        
    @commands.command()
    async def about(self, ctx):
        """Information about the bot"""
        await ctx.send("This is a bot coded in python for use in the PKSM server, made by Griffin#2329. You can view the source code here: <https://github.com/GriffinG1/PKSMBot>.")
    
    @commands.command()
    async def why(self, ctx):
        """Why the wait?"""
        await ctx.send("The wait is for two reasons.\n**1.** Bernardo wants to enjoy the game first. Sun and Moon wasn't enjoyable because PKSM was updated right away.\n**2.** People keep asking, when it'll be released, refusing to let Bernardo have a break.")
        
    @commands.command()
    async def patreon(self, ctx):
        """Donate here"""
        await ctx.send("You can donate to Bernardo on Patreon here: <https://www.patreon.com/bernardogiordano>.")
        
def setup(bot):
    bot.add_cog(Info(bot))
