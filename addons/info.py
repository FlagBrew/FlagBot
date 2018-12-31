#!/usr/bin/env python3

import json, requests
import discord
from discord.ext import commands

desc = "You can get the latest release of {}."
desc_pksm = "PKSM [here](https://github.com/FlagBrew/PKSM/releases/latest)"
desc_checkpoint = "Checkpoint [here](https://github.com/FlagBrew/Checkpoint/releases/latest)"
desc_pickr = "Pickr [here](https://github.com/FlagBrew/Pickr/releases/latest)"
desc_2048 = "2048 [here](https://github.com/FlagBrew/2048/releases/latest)"
desc_scripts = "PKSM-Scripts [here](https://github.com/FlagBrew/PKSM-Scripts/releases/latest)"
desc_qraken = "QRaken [here](https://github.com/FlagBrew/QRaken/releases/latest)"
desc_sharkive = "Sharkive [here](https://github.com/FlagBrew/Sharkive/releases/latest)"
desc_servelegality = "serveLegality [here](https://github.com/FlagBrew/serveLegality/releases/latest)"
desc_servepkx = "servepkx [here](https://github.com/FlagBrew/servepkx/releases/latest)"
desc_teamlist = "TeamListFiller [here](https://github.com/FlagBrew/TeamListFiller/releases/latest)"
desc_jedecheck = "JEDECheck [here](https://github.com/FlagBrew/JEDECheck/releases/latest)"
wiki_link = "https://github.com/FlagBrew/PKSM/wiki"


class Info:

    def __init__(self, bot):
        self.bot = bot
        print('Addon "{}" loaded'.format(self.__class__.__name__))
        
        
    def checkpoint_embed(self, ctx, app):
        embed = discord.Embed(description=desc.format(desc_checkpoint))
        str_list = app.lower().split()
        if "switch" in str_list:
            return embed
        releases = requests.get("https://api.github.com/repos/FlagBrew/Checkpoint/releases").json()
        for asset in releases[0]['assets']:
            if asset['name'] == "Checkpoint.cia":
                embed.set_image(url="https://chart.googleapis.com/chart?chs=300x300&cht=qr&chl=" + asset['browser_download_url'] + "&choe=UTF-8.png")
        return embed
        
    def pickr_embed(self, ctx, app):
        embed = discord.Embed(description=desc.format(desc_pickr))
        str_list = app.lower().split()
        if "switch" in str_list:
            return embed
        releases = requests.get("https://api.github.com/repos/FlagBrew/Pickr/releases").json()
        for asset in releases[0]['assets']:
            if asset['name'] == "Pickr.cia":
                embed.set_image(url="https://chart.googleapis.com/chart?chs=300x300&cht=qr&chl=" + asset['browser_download_url'] + "&choe=UTF-8.png")
        return embed
        
    @commands.command(aliases=['releases', 'latest'])
    async def release(self, ctx, *, app = ""):
        """Returns the latest release for FlagBrew's projects. If pulling checkpoint release, you can add "switch" to the end to get one without a qr code for ease of assistance"""
        if app.lower().startswith("pksm"):
            embed = discord.Embed(description=desc.format(desc_pksm))
            releases = requests.get("https://api.github.com/repos/FlagBrew/PKSM/releases").json()
            for asset in releases[0]['assets']:
                if asset['name'] == "PKSM.cia":
                    embed.set_image(url="https://chart.googleapis.com/chart?chs=300x300&cht=qr&chl=" + asset['browser_download_url'] + "&choe=UTF-8.png")
        elif app.lower().startswith("checkpoint"):
            embed = self.checkpoint_embed(self, app)
        elif app.lower().startswith("pickr"):
            embed = self.pickr_embed(self, app)
        elif app.lower().startswith("sharkive"):
            embed = discord.Embed(description=desc.format(desc_sharkive))
            releases = requests.get("https://api.github.com/repos/FlagBrew/Sharkive/releases").json()
            for asset in releases[0]['assets']:
                if asset['name'] == "Sharkive.cia":
                    embed.set_image(url="https://chart.googleapis.com/chart?chs=300x300&cht=qr&chl=" + asset['browser_download_url'] + "&choe=UTF-8.png")
        elif app.lower().startswith("teamlist") or app.lower().startswith("teamlistfiller") or app.lower().startswith("tl"):
            embed = discord.Embed(description=desc.format(desc_teamlist))
            # releases = requests.get("https://api.github.com/repos/FlagBrew/TeamListFiller/releases").json() #No releases yet, errors out.
            # for asset in releases[0]['assets']:
                # if asset['name'] == "TeamListFiller.cia":
                    # embed.set_image(url="https://chart.googleapis.com/chart?chs=300x300&cht=qr&chl=" + asset['browser_download_url'] + "&choe=UTF-8.png")
        elif app.lower().startswith("pksm-scripts") or app.lower().startswith("scripts") or app.lower().startswith("script") or app.lower().startswith("pksmscripts"):
            embed = discord.Embed(description=desc.format(desc_scripts))
        elif app.lower().startswith("legality") or app.lower().startswith("servelegality"):
            embed = discord.Embed(description=desc.format(desc_servelegality))
        elif app.lower().startswith("2048"):
            embed = discord.Embed(description=desc.format(desc_2048))
        elif app.lower().startswith("servepkx"):
            embed = discord.Embed(description=desc.format(desc_servepkx))
        elif app.lower().startswith("qraken"):
            embed = discord.Embed(description=desc.format(desc_qraken))
        elif app.lower().startswith("jedecheck") or app.lower().startswith("jede") or app.lower().startswith("jedec"):
            embed = discord.Embed(description=desc.format(desc_jedecheck))
        else:
            embed = discord.Embed(description=desc.format(desc_pksm) + "\n" + desc.format(desc_checkpoint) + "\n" + desc.format(desc_pickr) + "\n" + desc.format(desc_sharkive) + "\n" + desc.format(desc_teamlist) + "\n" +
                                              desc.format(desc_scripts) + "\n" + desc.format(desc_servelegality) + "\n" + desc.format(desc_2048) + "\n" + desc.format(desc_servepkx) + "\n" + desc.format(desc_qraken) + "\n" +
                                              desc.format(desc_jedecheck))
        await ctx.send(embed=embed)
        
    @commands.command()
    async def about(self, ctx):
        """Information about the bot"""
        await ctx.send("This is a bot coded in python for use in the FlagBrew server, made by {}#{}. You can view the source code here: <https://github.com/GriffinG1/FlagBot>.".format(self.bot.creator.name, self.bot.creator.discriminator))   
        
    @commands.command()
    async def readme(self, ctx, app = ""):
        """READMEs for FlagBrew's projects."""
        if app.lower() == "script" or app.lower() == "pksmscript" or app.lower() == "scripts" or app.lower() == "pksmscripts":
            embed = discord.Embed(description="You can read about PKSM scripts [here](https://github.com/FlagBrew/PKSM-Scripts/blob/master/README.md).")
        elif app.lower() == "servelegality" or app.lower() == "legality":
            embed = discord.Embed(description="You can read serveLegality's README [here](https://github.com/FlagBrew/serveLegality/blob/master/README.md).")
        elif app.lower() == "sharkive":
            embed = discord.Embed(description="You can read Sharkive's README [here](https://github.com/FlagBrew/Sharkive/blob/master/README.md).")
        elif app.lower() == "servepkx":
            embed = discord.Embed(title="Servepkx READMEs")
            embed.add_field(name="Servepkx-Browser", value="You can read servepkx's README [here](https://github.com/FlagBrew/servepkx/blob/master/browser/README.md).", inline=False)
            embed.add_field(name="Servepkx-Go", value="You can read servepkx-go's README [here](https://github.com/FlagBrew/servepkx/blob/master/go/README.md).", inline=False)
            embed.add_field(name="Servepkx-Java", value="You can read servepkx-java's README [here](https://github.com/FlagBrew/servepkx/tree/master/java).", inline=False)
        elif app.lower() == "teamlistfiller" or app.lower() == "teamlist" or app.lower() == "tl":
            embed = discord.Embed(description="You can read TeamListFiller's README [here](https://github.com/FlagBrew/TeamListFiller/blob/master/README.md).")
        elif app.lower() == "qraken":
            embed = discord.Embed(description="You can read QRaken's README [here](https://github.com/FlagBrew/QRaken/blob/master/README.md).")
        elif app.lower() == "2048":
            embed = discord.Embed(description="You can read 2048's README [here](https://github.com/FlagBrew/2048/blob/master/README.md).")
        elif app.lower() == "pickr":
            embed = discord.Embed(description="You can read Pickr's README [here](https://github.com/FlagBrew/Pickr/blob/master/README.md).")
        elif app.lower() == "checkpoint":
            embed = discord.Embed(description="You can read Checkpoint's README [here](https://github.com/FlagBrew/Checkpoint/blob/master/README.md).")
        elif app.lower() == "pksm":
            embed = discord.Embed(description="You can read PKSM's README [here](https://github.com/FlagBrew/PKSM/blob/master/README.md).")
        elif app.lower() == "jedecheck" or app.lower() == "jede" or app.lower() == "jedec":
            embed = discord.Embed(description="You can read JEDECheck's README [here](https://github.com/FlagBrew/JEDECheck/blob/master/README.md).")
        else:
            return await ctx.send("Input not given or recognized. Available READMEs: `pksmscript`, `servelegality`, `sharkive`, `servepkx`, `teamlistfiller`, `qraken`, `2048`, `pickr`, `checkpoint`, `pksm`, 'jedecheck'.")
        await ctx.send(embed=embed)
        
    @commands.command(aliases=['patron'])
    async def patreon(self, ctx):
        """Donate here"""
        await ctx.send("You can donate to FlagBrew on Patreon here: <https://www.patreon.com/FlagBrew>.\nYou can also donate to Bernardo on Patreon here: <https://www.patreon.com/BernardoGiordano>.")
        
    @commands.command()
    async def faq(self, ctx):
        """Frequently Asked Questions"""
        embed = discord.Embed(title="Frequently Asked Questions")
        embed.add_field(name="When will Virtual Console games be supported?", value="Never.")
        embed.add_field(name="Why do I have to wait so long for new releases?", value="Because you think you're entitled to everything.")
        embed.add_field(name="Why can't I scan this QR code?", value="FBI currently does not work with QR codes due to [changes to GitHub](https://www.reddit.com/r/3dshacks/comments/7zof0c/reminder_github_has_dropped_tlsv111_support_as_of/). You can use [QRaken](https://github.com/FlagBrew/QRaken/releases) to download via QR codes.")
        await ctx.send(embed=embed)

    @commands.command() # Taken from https://github.com/nh-server/Kurisu/blob/master/addons/assistance.py#L198-L205
    async def vguides(self, ctx):
        """Information about video guides relating to custom firmware"""
        embed = discord.Embed(title="Why you shouldn't use video guides")
        embed.description = ('"Video guides" are not recommended for use. Their contents generally become outdated very quickly for them to be of any use, and they are harder to update unlike a written guide.\n\n'
                            'When this happens, video guides become more complicated than current methods, having users do certain tasks which may not be required anymore.\n\n'
                            'There is also a risk of the uploader spreading misinformation or including potentially harmful files, sometimes unintentionally.')
        await ctx.send(embed=embed)
        
    @commands.command()
    async def question(self, ctx):
        """Reminder for those who won't just ask their question"""
        await ctx.send("Reminder: if you would like someone to help you, please be as descriptive as possible, of your situation, things you have done, as little as they may seem, aswell as assisting materials. Asking to ask wont expedite your process, and may delay assistance.")
        
    @commands.command()
    async def wiki(self, ctx, option=""):
        """Sends wiki link. extrasaves as option."""
        if option == "extrasaves":
            await ctx.send("You can read PKSM's wiki entry for extra saves here: <{}/Configuration#extra-saves>".format(wiki_link))
        else:
            await ctx.send("You can read PKSM's wiki here: <{}>".format(wiki_link))
        
def setup(bot):
    bot.add_cog(Info(bot))
