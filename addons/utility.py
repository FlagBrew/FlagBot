#!/usr/bin/env python3

import discord
from discord.ext import commands
import sys
import os

class Utility:

    def __init__(self, bot):
        self.bot = bot
        print('Addon "{}" loaded'.format(self.__class__.__name__))
        
    @commands.has_permissions(ban_members=True)
    @commands.command()
    async def reload(self, ctx):
        """Reloads an addon."""
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
            
    @commands.has_permissions(ban_members=True) 
    @commands.command()
    async def restart(self, ctx):
        """Restarts the bot, obviously"""
        await ctx.send("Restarting...")
        with open("restart.txt", "w+") as f:
            f.write(str(ctx.message.channel.id))
            f.close()
        sys.exit(0)
        
    @commands.command()
    async def togglestream(self, ctx):
        """Allows a patron user to toggle the stream role"""
        await ctx.message.delete()
        author_roles = ctx.message.author.roles[1:]
        if not self.bot.patron_role in author_roles:
            return await ctx.send("Sorry! This command is restricted to patrons! You can find out how to become a patron with `.patron`.")
        else:
            if not self.bot.stream_role in ctx.author.roles:
                await ctx.author.add_roles(self.bot.stream_role)
                await ctx.author.send("Added the stream role!")
                await self.bot.logs_channel.send("{0.name}#{0.discriminator} added the stream role.".format(ctx.author))
            else:
                await ctx.author.remove_roles(self.bot.stream_role)
                await ctx.author.send("Removed the stream role!")
                await self.bot.logs_channel.send("{0.name}#{0.discriminator} removed the stream role.".format(ctx.author))
            
def setup(bot):
    bot.add_cog(Utility(bot))
