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
        
    @commands.command()
    async def about(self, ctx):
        embed = discord.Embed(description="This is a bot coded in python for use in the PKSM server. You can view the source code [here](https://github.com/GriffinG1/PSKMBot).")
        embed.set_author(name="Griffin#2329", icon_url=self.bot.guild.get_member(177939404243992578).avatar_url_as(format="gif"))
        await ctx.send(embed=embed)
        
def setup(bot):
    bot.add_cog(Info(bot))