#!/usr/bin/env python3

import json, requests
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
        
        
    @commands.command(aliases=['releases', 'latest'])
    async def release(self, ctx, app = ""):
        """Returns the latest release for Bernardo's projects"""
        if app.lower() == "pksm" or ctx.invoked_with == "latest":
            embed = discord.Embed(description=desc.format(desc_pksm))
            releases = requests.get("https://api.github.com/repos/BernardoGiordano/PKSM/releases").json()
            for asset in releases[0]['assets']:
                if asset['name'] == "PKSM.cia":
                    embed.set_image(url="https://chart.googleapis.com/chart?chs=300x300&cht=qr&chl=" + asset['browser_download_url'] + "&choe=UTF-8.png")
        elif app.lower() == "checkpoint":
            embed = discord.Embed(description=desc.format(desc_checkpoint))
            releases = requests.get("https://api.github.com/repos/BernardoGiordano/Checkpoint/releases").json()
            for asset in releases[0]['assets']:
                if asset['name'] == "Checkpoint.cia":
                    embed.set_image(url="https://chart.googleapis.com/chart?chs=300x300&cht=qr&chl=" + asset['browser_download_url'] + "&choe=UTF-8.png")
        elif app.lower() == "pksm-tools":
            embed = discord.Embed(description=desc.format(desc_tools))
        elif app.lower() == "pickr":
            embed = discord.Embed(description=desc.format(desc_pickr))
            releases = requests.get("https://api.github.com/repos/BernardoGiordano/Pickr3DS/releases").json()
            for asset in releases[0]['assets']:
                if asset['name'] == "Pickr3DS.cia":
                    embed.set_image(url="https://chart.googleapis.com/chart?chs=300x300&cht=qr&chl=" + asset['browser_download_url'] + "&choe=UTF-8.png")
        else:
            embed = discord.Embed(description=desc.format(desc_pksm) + "\n" + desc.format(desc_checkpoint) + "\n" + desc.format(desc_tools) + "\n" + desc.format(desc_pickr))
        await ctx.send(embed=embed)
        
    @commands.command()
    async def about(self, ctx):
        """Information about the bot"""
        await ctx.send("This is a bot coded in python for use in the PKSM server, made by Griffin#2329. You can view the current source code here: <https://github.com/BernardoGiordano/PKSMBot>.")
        
    @commands.command()
    async def readme(self, ctx):
        """PKSM Readme"""
        embed = discord.Embed(description="You can read PKSM's readme [here](https://github.com/BernardoGiordano/PKSM/blob/master/README.md).")
        await ctx.send(embed=embed)
		
    @commands.command()
    async def storage(self, ctx):
        """Storage from 5.0.0+"""
        await ctx.send("If you can't see your storage correctly anymore, make sure you read what changed here: https://github.com/BernardoGiordano/PKSM#storage-changes-from-500")
        
    @commands.command(aliases=['patron'])
    async def patreon(self, ctx):
        """Support here"""
        await ctx.send("You can support Bernardo on Patreon here: <https://www.patreon.com/bernardogiordano>.")
        
def setup(bot):
    bot.add_cog(Info(bot))
