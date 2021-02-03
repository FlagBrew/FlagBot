#!/usr/bin/env python3

import json
import aiohttp
import discord
import qrcode
import io
import json
import math
from addons.helper import faq_decorator, restricted_to_bot, spam_limiter
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
        with open("saves/faqs/general.json", "r") as f:
            self.general_faq_dict = json.load(f)
        with open("saves/faqs/pksm.json", "r") as f:
            self.pksm_faq_dict = json.load(f)
        with open("saves/faqs/checkpoint.json", "r") as f:
            self.checkpoint_faq_dict = json.load(f)
        with open("saves/key_inputs.json", "r") as f:
            self.key_dict = json.load(f)

    async def gen_qr(self, ctx, app):
        releases = None
        async with aiohttp.ClientSession() as session:
            url = "https://api.github.com/repos/FlagBrew/{}/releases".format(app)
            async with session.get(url) as r:
                releases = await r.json()
        for asset in releases[0]["assets"]:
            if asset["name"] == "{}.cia".format(app):
                qr = qrcode.QRCode(version=None)
                qr.add_data(asset["browser_download_url"])
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                bytes = io.BytesIO()
                img.save(bytes, format='PNG')
                bytes = bytes.getvalue()
                return bytes, releases[0]["tag_name"]

    async def format_faq_embed(self, ctx, faq_num, channel, loaded_faq, faq_doc):
        embed = discord.Embed(title="Frequently Asked Questions")
        embed.title += f" - {'PKSM' if faq_doc.lower() == 'pksm' else faq_doc.title()}"
        embed.title += f" #{faq_num}"
        current_faq = loaded_faq[faq_num - 1]
        embed.add_field(name=current_faq["title"], value=current_faq["value"], inline=False)
        if "thumbnail" in current_faq.keys():
            embed.set_thumbnail(url=current_faq["thumbnail"])
        if "image" in current_faq.keys():
            embed.set_image(url=current_faq["image"])
        if "footer" in current_faq.keys():
            embed.set_footer(text=current_faq["footer"])
        await channel.send(embed=embed)

    @commands.command(aliases=["releases", "latest"])
    async def release(self, ctx, *, app=""):
        """Returns the latest release for FlagBrew"s projects. If pulling checkpoint or pickr release, you can add "switch" to the end to get one without a qr code for ease of use"""
        img = 0
        version = "1.0"
        if app.lower().startswith("pksm"):
            embed = discord.Embed(description=desc_temp.format(desc_pksm))
            img, version = await self.gen_qr(self, "PKSM")
        elif app.lower().startswith("checkpoint"):
            embed = discord.Embed(description=desc_temp.format(desc_checkpoint))
            str_list = app.lower().split()
            if "switch" not in str_list:
                img, version = await self.gen_qr(self, "Checkpoint")
        elif app.lower().startswith("pickr"):
            embed = discord.Embed(description=desc_temp.format(desc_pickr))
            str_list = app.lower().split()
            if "switch" not in str_list:
                img, version = await self.gen_qr(self, "Pickr")
        elif app.lower().startswith("2048"):
            embed = discord.Embed(description=desc_temp.format(desc_2048))
        else:
            embed = discord.Embed(description=desc_temp.format(desc_pksm) + "\n" + desc_temp.format(desc_checkpoint) + "\n" + desc_temp.format(desc_pickr) + "\n" +
                                  desc_temp.format(desc_2048))
        if img == 0:
            return await ctx.send(embed=embed)
        f = discord.File(io.BytesIO(img), filename="qr.png")
        embed.set_image(url="attachment://qr.png")
        embed.set_footer(text="Version: {}".format(version))
        await ctx.send(file=f, embed=embed)

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

    faq_aliases = [  # putting this here to make keeping track ez, as well as updates
        'rtfm',  # general usage
        'vc',  # general faq #1 - vc support
        'entitled',  # general faq #2 - new releases
        'rules',  # general faq #4 - toggling roles
        "swsh",  # pksm faq #2 - switch support
        "emulator",  # pksm faq #3 - emulator cross-use
        "sendpkx",  # pksm faq #7 - sending pkx files
        "wc3", "gen3events",  # pksm faq #9 - gen 3 events
        "addcode", "fixcheat",  # checkpoint faq #1 - pls add cheat
        "wheregame",  # checkpoint faq #2 - missing games
        "pkcrash",  # checkpoint faq #4 - cheat crash in pkmn games
    ]

    @commands.command(aliases=faq_aliases)
    @spam_limiter
    @faq_decorator
    async def faq(self, ctx, faq_doc="", *, faq_item=""):
        """Frequently Asked Questions. Allows numeric input for specific faq, or multiple numbers in a row for multiple at a time.
        Requires general, pksm, or checkpoint to be given as faq_doc"""
        if faq_doc.lower() == "general":
            loaded_faq = self.general_faq_dict
        elif faq_doc.lower() == "pksm":
            loaded_faq = self.pksm_faq_dict
        elif faq_doc.lower() == "checkpoint":
            loaded_faq = self.checkpoint_faq_dict
        else:
            return await ctx.send("Available FAQ categories are `general`, `pksm`, and `checkpoint`.")
        faq_item = faq_item.replace(' ', ',').split(',')
        faq_item = [item for item in faq_item if not item == ""]  # stupid? yes! do i care? no! (removes any blank entries which can cause errors w/ loop)
        last_index = -1  # used to ensure that faq entries used are next to each other during invoke
        invoked_faqs = []  # used to track faq entries to send
        usage_dm = (self.bot.creator, self.bot.pie)  # Handles DMs on full command usage outside bot-channel
        for faq_num in faq_item:
            if not faq_num.isdigit():
                if len(invoked_faqs) == 0:
                    break
                else:
                    continue
            elif not faq_item.index(faq_num) == last_index + 1:
                break
            last_index = faq_item.index(faq_num)
            faq_num = int(faq_num)
            invoked_faqs.append(faq_num)
            if faq_num > 0 and not faq_num <= len(loaded_faq):
                return await ctx.send("Faq number {} doesn't exist.".format(faq_num))
        for i_faq in invoked_faqs:
            await self.format_faq_embed(self, i_faq, ctx.channel, loaded_faq, faq_doc)
        embed = discord.Embed(title="Frequently Asked Questions")
        embed.title += " - {}".format("PKSM" if faq_doc.lower() == "pksm" else faq_doc.title())
        for faq_arr in loaded_faq:
            embed.add_field(name="{}: {}".format(loaded_faq.index(faq_arr) + 1, faq_arr["title"]), value=faq_arr["value"], inline=False)
        if faq_item == [""]: faq_item = ["0"]
        if not len(invoked_faqs) > 0:
            if ctx.author.id in self.bot.dm_list:
                await ctx.message.delete()
                try:
                    return await ctx.author.send(embed=embed)
                except discord.Forbidden:
                    pass  # Bot blocked, or api bug
            elif ctx.channel not in (self.bot.bot_channel, self.bot.testing_channel, self.bot.bot_channel2) and not ctx.guild.id == 378420595190267915:
                for user in usage_dm:
                    try:
                        await user.send("Full faq command was attempted to be used in {} by {}\n\nHyperlink to command invoke: {}".format(ctx.channel.mention, ctx.author, ctx.message.jump_url))
                    except discord.Forbidden:
                        pass  # Bot blocked
                return await ctx.send("If you want to see the full faq, please use {}, as it is very spammy.".format(self.bot.bot_channel.mention))
            await ctx.send(embed=embed)

    @commands.command()  # Taken (and adjusted slightly) from https://github.com/nh-server/Kurisu/blob/master/addons/assistance.py#L198-L205
    async def vguides(self, ctx):
        """Information about video guides relating to custom firmware"""
        embed = discord.Embed(title="Why you shouldn't use video guides")
        embed.description = ("\"Video guides\" are not recommended for use. Their contents generally become outdated very quickly for them to be of any use, and they are harder to update unlike a written guide.\n\n"
                             "When this happens, video guides become more complicated than current methods, having users do certain tasks which may not be required anymore.\n\n"
                             "There is also a risk of the uploader spreading misinformation or including potentially harmful files, sometimes unintentionally.")
        await ctx.send(embed=embed)

    @commands.command()
    @spam_limiter
    async def question(self, ctx):
        """Reminder for those who won't just ask their question"""
        await ctx.send("Reminder: if you would like someone to help you, please be as descriptive as possible, of your situation, things you have done, "
                       "as little as they may seem, as well as assisting materials. Asking to ask wont expedite your process, and may delay assistance. "
                       "***WE ARE NOT PSYCHIC.***")

    @commands.command(aliases=['readthedocs', 'docs', '<:wikidiot:558815031836540940>'])
    async def wiki(self, ctx, option=""):
        """Sends wiki link. storage, editor, events, scripts, bag, config, gameid, faq, gpss, hex, and bridge are all options"""
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
            wiki_link_ext = "/Settings"
        elif option == "gameid":
            extra_info = " entry for game ID info"
            wiki_link_ext = "/FAQs#what-backup-folder-corresponds-to-which-game"
        elif option == "faq":
            extra_info = " frequently asked questions"
            wiki_link_ext = "/FAQs"
        elif option == "gpss":
            extra_info = " entry for the GPSS"
            wiki_link_ext = "/GPSS"
        elif option == "hex" or option == "hexeditor":
            extra_info = " entry for the hex editor"
            wiki_link_ext = "/Hex-Editor"
        elif option == "bridging" or option == "bridge":
            extra_info = " on network bridging"
            wiki_link_ext = "/Basics#loading-a-save-over-a-network"
        else:
            extra_info = ""
            wiki_link_ext = ""
        m = await ctx.send("You can read PKSM's wiki{} here: <https://github.com/FlagBrew/PKSM/wiki{}>".format(extra_info, wiki_link_ext))
        await m.add_reaction("<:wikidiot:558815031836540940>")

    @commands.command()
    async def assets(self, ctx):
        """Gives instructions on manually downloading assets for PKSM"""
        embed = discord.Embed(title="How to manually download PKSM assets")
        embed.description = ("1. Download the assets from [here](https://github.com/piepie62/PKResources).\n"
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
        embed.set_thumbnail(url="https://raw.githubusercontent.com/FlagBrew/Sharkive/766456e8a605330a6e2e9f982ec359b6d19c54bb/assets/icon.png")
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
        try:
            decval = int(hexval, 16)
        except ValueError:
            return 400
        while decval != 0:
            key_index = math.floor(math.log(decval, 2))
            try:
                key_3ds = self.key_dict.get(hex(2**key_index))[0]
                if key_3ds != "None":
                    final_indices['3ds'].append(key_3ds)
                key_switch = self.key_dict.get(hex(2**key_index))[1]
                if key_switch != "None" and hexval.replace('0x', '')[0] == "8":
                    final_indices['switch'].append(key_switch)
            except IndexError:
                return 400
            decval -= 2**key_index
        return final_indices

    @commands.command()
    @restricted_to_bot
    async def cheatkeys(self, ctx, key):
        """Byte decoder for sharkive codes. Input should be the second half of the line starting with DD000000"""
        if len(key) != 8:
            return await ctx.send("That isn't a valid key!")
        indexes = self.get_keys(key)
        if indexes == 400:
            return await ctx.send("That isn't a valid key!")
        embed = discord.Embed(title="Matching inputs for `{}`".format(key))
        if len(indexes["3ds"]) > 0:
            embed.add_field(name="3DS inputs", value='`' + '` + `'.join(indexes["3ds"]) + '`')
        if len(indexes["switch"]) > 0:
            embed.add_field(name="Switch inputs", value='`' + '` + `'.join(indexes["switch"]) + '`', inline=False)
        await ctx.send(embed=embed)

    @commands.command(aliases=['dg'])
    @spam_limiter
    async def downgrade(self, ctx):
        """Don't. Fucking. Downgrade."""
        embed = discord.Embed(title="Should you downgrade?")
        embed.description = "If you downgrade, you will fuck things up. Don't do it for fucks sake."
        embed.set_thumbnail(url="https://media.giphy.com/media/ToMjGpx9F5ktZw8qPUQ/giphy.gif")
        await ctx.send(embed=embed)

    @commands.command(aliases=['es'])
    @spam_limiter
    async def extrasaves(self, ctx):
        """Extrasaves info"""
        embed = discord.Embed(title="How do I access my external saves?")
        embed.description = ("Open PKSM's settings from the game select menu by pressing `x`, and go to **Misc**. Then choose **Extra Saves**.\n"
                             "Then, select the game you want to add a save for, choose add save, and navigate to the save.\n"
                             "Afterwards, hit `y` on the game select screen to view the absent games menu.")
        await ctx.send(embed=embed)

    @commands.command(aliases=["tid"])
    @spam_limiter
    async def titleid(self, ctx):
        """Title ID adding info"""
        embed = discord.Embed(title="How do I access my GBA games?")
        embed.description = ("Open PKSM's settings from the game select menu by pressing `x`, and go to **Misc**. Then choose **Title IDs**.\n"
                             "Then, select the game you want to set a custom title ID for, and enter the game's title ID. You can check this in FBI.\n"
                             "Afterwards, select `VC Games` at the top of the game select screen (or hit R).")
        embed.set_footer(text="Please note: your inject *must* have a save type of 1024kbit. Otherwise, it will not load in PKSM.")
        await ctx.send(embed=embed)

    @commands.command()
    async def batchedit(self, ctx):
        """Lists info about the batch editor"""
        edit_types = (
            "Original Trainer Name\n"
            "Original Trainer TID\n"
            "Original Trainer SID\n"
            "Original Trainer Gender\n"
            "Level\n"
            "Shiny\n"
            "All IVs\n"
            "Language\n"
            "Pokerus\n"
            "Nature\n"
            "Ball\n"
            "PP Ups\n"
            "Reset Moves (Move 1 is set to Pound, and moves 2 through 4 are cleared)\n"
            "Randomize PIDs"
        )
        embed = discord.Embed(title="Batch Editor Information")
        embed.description = "Please keep in mind that the script will affect *everything* in the boxes of the loaded save, or of the selected bank."
        embed.add_field(name="Editing Types", value=edit_types)
        embed.set_footer(text="Please note that LGPE and SWSH have not yet been tested.")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Info(bot))
