#!/usr/bin/env python3

import discord
from discord.ext import commands

desc = "You can get the latest release of {}."
desc_pksm = "PKSM [here](https://github.com/BernardoGiordano/PKSM/releases/latest)"
desc_checkpoint = "Checkpoint [here](https://github.com/BernardoGiordano/Checkpoint/releases/latest)"
desc_pickr = "Pickr3DS [here](https://github.com/BernardoGiordano/Pickr3DS/releases/latest)"
desc_tools = "PKSM-Tools [here](https://github.com/BernardoGiordano/PKSM-Tools/releases/latest)"

class Info:

    def __init__(self, bot):
        self.bot = bot
        print('Addon "{}" loaded'.format(self.__class__.__name__))
        
        
    @commands.command(aliases=['releases'])
    async def release(self, ctx, app = ""):
        """Returns the latest releases for Bernardo's Projects"""
        if app.lower() == "pksm":
            embed = discord.Embed(description=desc.format(desc_pksm))
        elif app.lower() == "checkpoint":
            embed = discord.Embed(description=desc.format(desc_checkpoint))
        elif app.lower() == "pksm-tools":
            embed = discord.Embed(description=desc.format(desc_tools))
        elif app.lower() == "pickr":
            embed = discord.Embed(description=desc.format(desc_pickr))
        else:
            embed = discord.Embed(description="{}\n{}\n{}\n{}.format(desc.format(desc_pksm), desc.format(desc_checkpoint), desc.format(desc_tools), desc.format(desc_pickr))
        await ctx.send(embed=embed)
        
    @commands.command()
    async def about(self, ctx):
        """Information about the bot"""
        await ctx.send("This is a bot coded in python for use in the PKSM server, made by Griffin#2329. You can view the source code here: <https://github.com/GriffinG1/PKSMBot>.")
        
    @commands.command()
    async def readme(self, ctx):
        """PKSM Readme"""
        embed = discord.Embed(description="You can read the readme for PKSM [here](https://github.com/BernardoGiordano/PKSM/blob/master/README.md).")
        await ctx.send(embed=embed)
		
    @commands.command()
    async def storage(self, ctx):
        """Storage from 5.0.0+"""
        await ctx.send("If you can't see your storage correctly anymore, make sure you read what changed here: https://github.com/BernardoGiordano/PKSM#storage-changes-from-500")
    
    @commands.command(hidden=True)
    async def why(self, ctx):
        """Why the wait?"""
        if self.bot.counter:
            await ctx.send("The wait is for two reasons.\n**1.** Bernardo wants to enjoy the game first. Sun and Moon wasn't enjoyable because PKSM was updated right away.\n**2.** People keep asking, when it'll be released, refusing to let Bernardo have a break.")
        
    @commands.command(aliases=['patron'])
    async def patreon(self, ctx):
        """Donate here"""
        await ctx.send("You can donate to Bernardo on Patreon here: <https://www.patreon.com/bernardogiordano>.")
        
def setup(bot):
    bot.add_cog(Info(bot))
