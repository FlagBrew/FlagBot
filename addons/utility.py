import discord
from discord.ext import commands
import sys
import os
import git
from subprocess import Popen

class Utility:

    def __init__(self, bot):
        self.bot = bot
        print('Addon "{}" loaded'.format(self.__class__.__name__))
        
        
    @commands.command()
    async def push(self, ctx):
        """Pull git changes, owner only."""
        if ctx.author == ctx.guild.owner or ctx.author.name == "bernardogiordano":
            await ctx.send("Pulling changes...")
            p = Popen("update.bat", cwd=rself.bot.dir_path)
            await ctx.send("Changes pulled!")
        else:
            await ctx.send("You don't have permission to do that!")
            
    @commands.command()
    async def reload(self, ctx):
        """Reloads an addon."""
        if ctx.author == ctx.guild.owner or ctx.author.name == "bernardogiordano":
            errors = ""
            for addon in os.listdir("addons"):
                if ".py" in addon:
                    addon = addon.replace('.py', '')
                    try:
                        self.bot.unload_extension("addons.{}".format(addon))
                        self.bot.load_extension("addons.{}".format(addon))
                    except Exception as e:
                        errors += 'Failed to load addon: `{}.py` due to `{}: {}`\n'.format(addon, type(e).__name__, e)
            if not errors:
                await ctx.send(':white_check_mark: Extensions reloaded.')
            else:
                await ctx.send(errors)
        else:
            await ctx.send("You don't have permission to do that!")
            
    @commands.command()
    async def restart(self, ctx):
        """Restarts the bot, obviously"""
        if ctx.author == ctx.guild.owner or ctx.author.name == "bernardogiordano":
            await ctx.send("Restarting...")
            with open("restart.txt", "w+") as f:
                f.write(str(ctx.message.channel.id))
                f.close()
            sys.exit(0)
        else:
            await ctx.send("You don't have permission to do that!")
            
def setup(bot):
    bot.add_cog(Utility(bot))