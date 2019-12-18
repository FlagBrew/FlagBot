#!/usr/bin/env python3

import json
import requests
import discord
import qrcode
import io
import json
import math
from discord.ext import commands

desc_temp = "You can get the latest release of {}."
desc_pksm = "PKSM [here](https://github.com/FlagBrew/PKSM/releases/latest)"
desc_checkpoint = "Checkpoint [here](https://github.com/FlagBrew/Checkpoint/releases/latest)"
desc_pickr = "Pickr [here](https://github.com/FlagBrew/Pickr/releases/latest)"
desc_2048 = "2048 [here](https://github.com/FlagBrew/2048/releases/latest)"
readme_temp = "You can read {}'s README [here](https://github.com/FlagBrew/{}/blob/master/README.md)."


class Info(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        print("Addon \"{}\" loaded".format(self.__class__.__name__))
        with open("saves/faqs/faq.json", "r") as f:
            self.faq_dict = json.load(f)
        with open("saves/faqs/general.json", "r") as f:
            self.general_faq_dict = json.load(f)
        with open("saves/faqs/pksm.json", "r") as f:
            self.pksm_faq_dict = json.load(f)
        with open("saves/faqs/checkpoint.json", "r") as f:
            self.checkpoint_faq_dict = json.load(f)
        with open("saves/key_inputs.json", "r") as f:
            self.key_dict = json.load(f)

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
    async def release(self, ctx, *, app=""):
        """Returns the latest release for FlagBrew"s projects. If pulling checkpoint or pickr release, you can add "switch" to the end to get one without a qr code for ease of use"""
        img = 0
        if app.lower().startswith("pksm"):
            embed = discord.Embed(description=desc_temp.format(desc_pksm))
            img = self.gen_qr(self, "PKSM")
        elif app.lower().startswith("checkpoint"):
            embed = discord.Embed(description=desc_temp.format(desc_checkpoint))
            str_list = app.lower().split()
            if "switch" not in str_list:
                img = self.gen_qr(self, "Checkpoint")
        elif app.lower().startswith("pickr"):
            embed = discord.Embed(description=desc_temp.format(desc_pickr))
            str_list = app.lower().split()
            if "switch" not in str_list:
                img = self.gen_qr(self, "Pickr")
        elif app.lower().startswith("2048"):
            embed = discord.Embed(description=desc_temp.format(desc_2048))
        else:
            embed = discord.Embed(description=desc_temp.format(desc_pksm) + "\n" + desc_temp.format(desc_checkpoint) + "\n" + desc_temp.format(desc_pickr) + "\n" +
                                  desc_temp.format(desc_2048))
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
    async def readme(self, ctx, app=""):
        """READMEs for FlagBrew's projects."""
        if app.lower() == "script" or app.lower() == "pksmscript" or app.lower() == "scripts" or app.lower() == "pksmscripts":
            embed = discord.Embed(description=readme_temp.format("PKSM Scripts", "PKSM-Scripts"))
        elif app.lower() == "2048":
            embed = discord.Embed(description=readme_temp.format("2048", "2048"))
        elif app.lower() == "pickr":
            embed = discord.Embed(description=readme_temp.format("Pickr", "Pickr"))
        elif app.lower() == "checkpoint":
            embed = discord.Embed(description=readme_temp.format("Checkpoint", "Checkpoint"))
        elif app.lower() == "pksm":
            embed = discord.Embed(description=readme_temp.format("PKSM", "PKSM"))
        elif app.lower() == "sharkive":
            embed = discord.Embed(description=readme_temp.format("Sharkive", "Sharkive"))
        else:
            return await ctx.send("Input not given or recognized. Available READMEs: `scripts`, `2048`, `pickr`, `checkpoint`, `pksm`, `sharkive`.")
        await ctx.send(embed=embed)

    @commands.command(aliases=['patron'])
    async def patreon(self, ctx):
        """Donate here"""
        await ctx.send("You can donate to FlagBrew on Patreon here: <https://www.patreon.com/FlagBrew>.\nYou can also donate to Bernardo on Patreon here: <https://www.patreon.com/BernardoGiordano>.")

    async def format_faq_embed(self, ctx, faq_num, channel, loaded_faq):
        embed = discord.Embed(title="Frequently Asked Questions")
        embed.title += f" #{faq_num}"
        current_faq = loaded_faq[faq_num - 1]
        embed.add_field(name=current_faq["title"], value=current_faq["value"], inline=False)
        await channel.send(embed=embed)

    @commands.command()
    async def faq(self, ctx, faq_doc="", *, faq_item=""):
        """Frequently Asked Questions. Allows numeric input for specific faq."""
        if faq_doc == "general":
            loaded_faq = self.general_faq_dict
        elif faq_doc == "pksm":
            loaded_faq = self.pksm_faq_dict
        elif faq_doc == "checkpoint":
            loaded_faq = self.checkpoint_faq_dict
        else:
            loaded_faq = self.faq_dict
            faq_item = faq_doc
        faq_item = faq_item.replace(' ', ',').split(',')
        count = 0
        dm_list = (self.bot.creator, self.bot.pie)  # Handles DMs on full command usage outside bot-channel
        for faq_num in faq_item:
            if not faq_num.isdigit():
                if count == 0:
                    break
                else:
                    count += 1
                    continue
            faq_num = int(faq_num)
            count += 1
            if faq_num > 0 and faq_num < len(loaded_faq) + 1:
                await self.format_faq_embed(self, faq_num, ctx.channel, loaded_faq)
            elif count == 1:
                await ctx.send("Faq number {} doesn't exist.".format(faq_num))
        if count == len(faq_item):
            return
        embed = discord.Embed(title="Frequently Asked Questions")
        for faq_arr in loaded_faq:
            embed.add_field(name="{}: {}".format(loaded_faq.index(faq_arr) + 1, faq_arr["title"]), value=faq_arr["value"], inline=False)
        if faq_item == ['']:
            if ctx.author.id in (self.bot.creator.id, self.bot.pie.id):
                await ctx.message.delete()
                try:
                    return await ctx.author.send(embed=embed)
                except discord.Forbidden:
                    pass  # Bot blocked, or api bug
            elif ctx.channel is not self.bot.bot_channel:
                for user in dm_list:
                    try:
                        await user.send("Full faq command used in {} by {}\n\nHyperlink to command invoke: {}".format(ctx.channel.mention, ctx.author, ctx.message.jump_url))
                    except discord.Forbidden:
                        pass  # Bot blocked, or api bug
        await ctx.send(embed=embed)

    @commands.command()  # Taken from https://github.com/nh-server/Kurisu/blob/master/addons/assistance.py#L198-L205
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
        await ctx.send("Reminder: if you would like someone to help you, please be as descriptive as possible, of your situation, things you have done, "
                       "as little as they may seem, as well as assisting materials. Asking to ask wont expedite your process, and may delay assistance. "
                       "***WE ARE NOT PSYCHIC.***")

    @commands.command(aliases=['readthedocs', 'docs', '<:wikidiot:558815031836540940>'])
    async def wiki(self, ctx, option=""):
        """Sends wiki link. extrasaves, storage, editor, events, scripts, bag, config, scriptdev, and faq all as options"""
        extra_info = ""
        wiki_link_ext = ""
        option = option.lower()
        if option == "storage":
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
        elif option == "gameid":
            extra_info = " entry for game ID info"
            wiki_link_ext = "/FAQs#what-backup-folder-corresponds-to-which-game"
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

    @commands.command(aliases=['database'])
    async def db(self, ctx, console=""):
        """Links to the cheat database"""
        embed = discord.Embed(title="Cheat Code Database", description="")
        is_all = console not in ("3ds", "switch")
        if console.lower() == "3ds" or is_all:
            embed.description += "You can see the 3DS code database [here](https://github.com/FlagBrew/Sharkive/wiki/3DS-games-in-the-database).\n"
        if console.lower() == "switch" or is_all:
            embed.description += "You can view the Switch code database [here](https://github.com/FlagBrew/Sharkive/wiki/Switch-games-in-the-database)."
        await ctx.send(embed=embed)

    @commands.command()
    async def guide(self, ctx, option=""):
        """Links to 3ds & switch guides. Each can be given for specific. Defaults to 3ds in any channel that starts with pksm"""
        embed = discord.Embed(description="")
        ds, switch = (True,) * 2
        if option.lower() == "switch":
            ds = False
        elif ctx.channel.name.startswith("pksm") or option.lower() == "3ds":
            switch = False
            ds = True
        if ds:
            embed.description += "You can use [this guide](https://3ds.hacks.guide) to hack your 3ds.\n"
        if switch:
            embed.description += "You can use [this guide](https://nh-server.github.io/switch-guide/) to hack your switch."
        await ctx.send(embed=embed)

    def get_keys(self, hexval):  # thanks to architdate for the code
        final_indices = {'3ds': [], 'switch': []}
        decval = int(hexval, 16)
        while decval != 0:
            key_index = math.floor(math.log(decval, 2))
            key_3ds = self.key_dict.get(hex(2**key_index))[0]
            if key_3ds != "None":
                final_indices['3ds'].append(key_3ds)
            key_switch = self.key_dict.get(hex(2**key_index))[1]
            if key_switch != "None" and hexval.replace('0x', '')[0] == "8":
                final_indices['switch'].append(key_switch)
            decval -= 2**key_index
        return final_indices

    @commands.command()
    async def cheatkeys(self, ctx, key):
        """Byte decoder for sharkive codes. Input should be the second half of the line starting with DD000000"""
        indexes = self.get_keys(key)
        embed = discord.Embed(title="Matching inputs for `{}`".format(key))
        if len(indexes["3ds"]) > 0:
            embed.add_field(name="3DS inputs", value='`' + '` + `'.join(indexes["3ds"]) + '`')
        if len(indexes["switch"]) > 0:
            embed.add_field(name="Switch inputs", value='`' + '` + `'.join(indexes["switch"]) + '`', inline=False)
        await ctx.send(embed=embed)

    @commands.command(aliases=['dg'])
    async def downgrade(self, ctx):
        """Don't. Fucking. Downgrade."""
        embed = discord.Embed(title="Should you downgrade?")
        embed.description = "If you downgrade, you will fuck things up. Don't do it for fucks sake."
        embed.set_thumbnail(url="https://media.giphy.com/media/ToMjGpx9F5ktZw8qPUQ/giphy.gif")
        await ctx.send(embed=embed)

    @commands.command(aliases=['es'])
    async def extrasaves(self, ctx):
        """Extrasaves info"""
        embed = discord.Embed(title="How do I access my external saves?")
        embed.description = ("Open PKSM's settings from the game select menu by pressing `x`, and go to **Misc**. Choose **Extra Saves**. "
                             "Then, select the game you want to add a save for, choose add save, and navigate to the save. "
                             "Afterwards, hit `y` on the game select screen to view the absent games menu.")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Info(bot))
