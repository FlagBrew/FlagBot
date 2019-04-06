#!/usr/bin/env python3

import json, requests
import discord
import qrcode
import io
import json
from discord.ext import commands

desc = "You can get the latest release of {}."
desc_pksm = "PKSM [here](https://github.com/FlagBrew/PKSM/releases/latest)"
desc_checkpoint = "Checkpoint [here](https://github.com/FlagBrew/Checkpoint/releases/latest)"
desc_pickr = "Pickr [here](https://github.com/FlagBrew/Pickr/releases/latest)"
desc_2048 = "2048 [here](https://github.com/FlagBrew/2048/releases/latest)"
desc_sharkive = "Sharkive [here](https://github.com/FlagBrew/Sharkive/releases/latest)"
desc_jedecheck = "JEDECheck [here](https://github.com/FlagBrew/JEDECheck/releases/latest)"


class Info(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        print("Addon \"{}\" loaded".format(self.__class__.__name__))
        with open("faq.json", "r") as f:
            self.faq_dict = json.load(f)
        
    def gen_qr(self, ctx, app):
        releases = requests.get("https://api.github.com/repos/FlagBrew/{}/releases".format(app)).json()
        for asset in releases[0]["assets"]:
            if asset["name"] == "{}.cia".format(app):
                qr = qrcode.QRCode(version=None)
                qr.add_data(asset["browser_download_url"])
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                bytes = io.BytesIO()
                img.save(bytes, format='PNG')
                bytes = bytes.getvalue()
                return bytes
        
    @commands.command(aliases=["releases", "latest"])
    async def release(self, ctx, *, app = ""):
        """Returns the latest release for FlagBrew"s projects. If pulling checkpoint or pickr release, you can add "switch" to the end to get one without a qr code for ease of use"""
        img = 0
        if app.lower().startswith("pksm"):
            embed = discord.Embed(description=desc.format(desc_pksm))
            img = url=self.gen_qr(self, "PKSM")
        elif app.lower().startswith("checkpoint"):
            embed = discord.Embed(description=desc.format(desc_checkpoint))
            str_list = app.lower().split()
            if not "switch" in str_list:
                img = url=self.gen_qr(self, "Checkpoint")
        elif app.lower().startswith("pickr"):
            embed = discord.Embed(description=desc.format(desc_pickr))
            str_list = app.lower().split()
            if not "switch" in str_list:
                img = url=self.gen_qr(self, "Pickr")
        elif app.lower().startswith("sharkive"):
            embed = discord.Embed(description=desc.format(desc_sharkive))
            img = url=self.gen_qr(self, "Sharkive")
        elif app.lower().startswith("2048"):
            embed = discord.Embed(description=desc.format(desc_2048))
        elif app.lower().startswith("jedecheck") or app.lower().startswith("jede") or app.lower().startswith("jedec"):
            embed = discord.Embed(description=desc.format(desc_jedecheck))
        else:
            embed = discord.Embed(description=desc.format(desc_pksm) + "\n" + desc.format(desc_checkpoint) + "\n" + desc.format(desc_pickr) + "\n" + desc.format(desc_sharkive) + "\n" +
                                              desc.format(desc_2048) + "\n" + desc.format(desc_jedecheck))
        if img == 0: 
            return await ctx.send(embed=embed)
        f = discord.File(io.BytesIO(img), filename="qr.png")
        embed.set_image(url="attachment://qr.png")
        await ctx.send(file=f, embed=embed)
        
    @commands.command()
    async def about(self, ctx):
        """Information about the bot"""
        await ctx.send("This is a bot coded in python for use in the FlagBrew server, made by {}#{}. You can view the source code here: <https://github.com/GriffinG1/FlagBot>.".format(self.bot.creator.name, self.bot.creator.discriminator))   
        
    @commands.command()
    async def readme(self, ctx, app = ""):
        """READMEs for FlagBrew's projects."""
        if app.lower() == "script" or app.lower() == "pksmscript" or app.lower() == "scripts" or app.lower() == "pksmscripts":
            embed = discord.Embed(description="You can read about PKSM scripts [here](https://github.com/FlagBrew/PKSM-Scripts/blob/master/README.md).")
        elif app.lower() == "sharkive":
            embed = discord.Embed(description="You can read Sharkive's README [here](https://github.com/FlagBrew/Sharkive/blob/master/README.md).")
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
            return await ctx.send("Input not given or recognized. Available READMEs: `pksmscript`, `sharkive`, `teamlistfiller`, `qraken`, `2048`, `pickr`, `checkpoint`, `pksm`, 'jedecheck'.")
        await ctx.send(embed=embed)
        
    @commands.command(aliases=['patron'])
    async def patreon(self, ctx):
        """Donate here"""
        await ctx.send("You can donate to FlagBrew on Patreon here: <https://www.patreon.com/FlagBrew>.\nYou can also donate to Bernardo on Patreon here: <https://www.patreon.com/BernardoGiordano>.")
        
    @commands.command()
    async def faq(self, ctx, faq=""):
        """Frequently Asked Questions. Allows numeric input for specific faq."""
        embed = discord.Embed(title="Frequently Asked Questions")
        if faq.isdigit() and int(faq) > 0 and int(faq) < len(self.faq_dict)+1:
            faq = int(faq)
            embed.title += f" #{faq}"
            current_faq = self.faq_dict[faq-1]
            embed.add_field(name=current_faq["title"], value=current_faq["value"])
        else:
            for faq in self.faq_dict:
                embed.add_field(name=faq["title"], value=faq["value"])
        await ctx.send(embed=embed)

    @commands.command() # Taken from https://github.com/nh-server/Kurisu/blob/master/addons/assistance.py#L198-L205
    async def vguides(self, ctx):
        """Information about video guides relating to custom firmware"""
        embed = discord.Embed(title="Why you shouldn't use video guides")
        embed.description = ("\"Video guides\" are not recommended for use. Their contents generally become outdated very quickly for them to be of any use, and they are harder to update unlike a written guide.\n\n"
                            "When this happens, video guides become more complicated than current methods, having users do certain tasks which may not be required anymore.\n\n"
                            "There is also a risk of the uploader spreading misinformation or including potentially harmful files, sometimes unintentionally.")
        await ctx.send(embed=embed)
        
    @commands.command()
    async def question(self, ctx):
        """Reminder for those who won't just ask their question"""
        await ctx.send("Reminder: if you would like someone to help you, please be as descriptive as possible, of your situation, things you have done, as little as they may seem, as well as assisting materials. Asking to ask wont expedite your process, and may delay assistance.")
        
    @commands.command(aliases=['readthedocs', 'docs', 'extrasaves', 'es'])
    async def wiki(self, ctx, option=""):
        """Sends wiki link. extrasaves, storage, editor, events, scripts, bag, config, scriptdev, and faq all as options"""
        extra_info = ""
        wiki_link_ext = ""
        option = option.lower()
        if option == "extrasaves" or option == "extra-saves" or option == "saves" or option == "saveconfig" or ctx.invoked_with == "extrasaves" or ctx.invoked_with == "es":
            extra_info = " entry for extra saves"
            wiki_link_ext = "/Configuration#extra-saves"
        elif option == "storage":
            extra_info = " entry for the storage feature"
            wiki_link_ext = "/Storage"
        elif option == "editor":
            extra_info = " entry for the editor feature"
            wiki_link_ext = "/Editor"
        elif option == "event" or option == "events" or option == "eventinject" or option == "eventinjector" or option == "event-inject" or option == "event-injector":
            extra_info = " entry for the event injection feature"
            wiki_link_ext = "/Event-Injector"
        elif option == "script" or option == "scripts" or option == "scriptinject" or option == "scriptinjector" or option == "script-inject" or option == "script-injector":
            extra_info = " entry for the script injection feature"
            wiki_link_ext = "/Script-Injector"
        elif option == "bag":
            extra_info = " entry for the bag editing feature"
            wiki_link_ext = "/Bag-Editor"
        elif option == "config" or option == "configuration":
            extra_info = " entry for the config"
            wiki_link_ext = "/Configuration"
        elif option == "scriptdev":
            extra_info = " entry for script development"
            wiki_link_ext = "/Scripts-Development"
        elif option == "faq":
            extra_info = " frequently asked questions"
            wiki_link_ext = "/FAQs"
        await ctx.send("You can read PKSM's wiki{} here: <https://github.com/FlagBrew/PKSM/wiki{}>".format(extra_info, wiki_link_ext))
        
    @commands.command()
    async def assets(self, ctx):
        """Gives instructions on manually downloading assets for PKSM"""
        embed = discord.Embed(title="How to manually download PKSM assets")
        embed.description = ("1. Download the assets from [here](https://github.com/dsoldier/PKResources/tree/master/additionalassets).\n"
                             "2. Copy the assets to `/3ds/PKSM/assets/`. You may need to create the folder.\n"
                             "3. Launch PKSM, and you should be good to go.")
        await ctx.send(embed=embed)
    
    @commands.command(aliases=["template", "estemp"])
    async def estemplate(self, ctx):
        """Outputs the template for extrasaves from the wiki"""
        embed = discord.Embed(title="Extra Saves Template")
        embed.description = ("```json\n"
                       "\"extraSaves\": {\n"
                       "  \"CPUE\": [\n"
                       "    \"/roms/nds/POKEMON_PL.sav\",\n"
                       "    \"/path/to/file.save\"\n"
                       "  ],\n"
                       "  \"0x0055D\": [\n"
                       "    \"/backups/game/name/main\",\n"
                       "    \"/path/to/main\"\n"
                       "  ]\n"
                       "}```")
        embed.description += "\nYou can also use the online tool from the FlagBrew website [here](https://flagbrew.org/tools/extra_saves)."
        await ctx.send(embed=embed)
        
    @commands.command(aliases=['database'])
    async def db(self, ctx):
        """Links to the Sharkive database"""
        embed = discord.Embed(title="Sharkive Code Database")
        embed.description = "You can see the full code database [here](https://github.com/FlagBrew/Sharkive/wiki/List-of-games-in-the-database)."
        await ctx.send(embed=embed)
        
def setup(bot):
    bot.add_cog(Info(bot))
