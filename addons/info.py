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
from datetime import datetime

desc_temp = "You can get the latest release of {}."
desc_pksm = "PKSM [here](https://github.com/FlagBrew/PKSM/releases/latest)"
desc_checkpoint = "Checkpoint [here](https://github.com/FlagBrew/Checkpoint/releases/latest)"
desc_pickr = "Pickr [here](https://github.com/FlagBrew/Pickr/releases/latest)"
desc_2048 = "2048 [here](https://github.com/FlagBrew/2048/releases/latest)"
readme_temp = "You can read {}'s README [here](https://github.com/FlagBrew/{}/blob/master/README.md)."


class Info(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        print(f"Addon \"{self.__class__.__name__}\" loaded")
        with open("saves/faqs/general.json", "r") as file:
            self.general_faq_dict = json.load(file)
        with open("saves/faqs/pksm.json", "r") as file:
            self.pksm_faq_dict = json.load(file)
        with open("saves/faqs/checkpoint.json", "r") as file:
            self.checkpoint_faq_dict = json.load(file)
        with open("saves/key_inputs.json", "r") as file:
            self.key_dict = json.load(file)

    async def gen_qr(self, ctx, app):
        releases = None
        async with aiohttp.ClientSession() as session:
            url = f"https://api.github.com/repos/FlagBrew/{app}/releases"
            async with session.get(url) as resp:
                releases = await resp.json()
        for asset in releases[0]["assets"]:
            if asset["name"] == f"{app}.cia":
                qr = qrcode.QRCode(version=None)
                qr.add_data(asset["browser_download_url"])
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                bytes = io.BytesIO()
                img.save(bytes, format='PNG')
                bytes = bytes.getvalue()
                released_on = releases[0]["published_at"][:10]
                released_on_dt = datetime.strptime(released_on, "%Y-%m-%d")
                return bytes, releases[0]["tag_name"], released_on_dt

    async def format_faq_embed(self, ctx, faq_num, channel, loaded_faq, faq_doc):
        current_faq = loaded_faq[faq_num - 1]
        embed = discord.Embed.from_dict(current_faq)
        embed.title = "Frequently Asked Questions"
        embed.title += f" - {'PKSM' if faq_doc.lower() == 'pksm' else faq_doc.title()}"
        embed.title += f" #{faq_num}"
        await channel.send(embed=embed)

    @commands.command(aliases=["releases", "latest"])
    async def release(self, ctx, *, app=""):
        """Returns the latest release for FlagBrew"s projects. If pulling checkpoint or pickr release, you can add "switch" to the end to get one without a qr code for ease of use"""
        img = 0
        version = "1.0"
        released_on = None
        if app.lower().startswith("pksm"):
            embed = discord.Embed(description=desc_temp.format(desc_pksm))
            img, version, released_on = await self.gen_qr(self, "PKSM")
        elif app.lower().startswith("checkpoint"):
            embed = discord.Embed(description=desc_temp.format(desc_checkpoint))
            str_list = app.lower().split()
            if "switch" not in str_list:
                # Manual formatting due to 3.8.0 being broken...
                # img, version = await self.gen_qr(self, "Checkpoint")
                embed.description += "\nCheckpoint 3.8.0 is currently broken on 3DS. Please use 3.7.4 found [here](https://github.com/FlagBrew/Checkpoint/releases/tag/v3.7.4)."
                qr = qrcode.QRCode(version=None)
                qr.add_data("https://cdn.discordapp.com/attachments/377425394866847744/942325638960934952/qr.png")
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white")
                bytes = io.BytesIO()
                qr_img.save(bytes, format='PNG')
                bytes = bytes.getvalue()
                img = bytes
                version = "3.7.4"
                released_on = datetime.strptime("2019-12-09", "%Y-%m-%d")
        elif app.lower().startswith("pickr"):
            embed = discord.Embed(description=desc_temp.format(desc_pickr))
            str_list = app.lower().split()
            if "switch" not in str_list:
                img, version, released_on = await self.gen_qr(self, "Pickr")
        elif app.lower().startswith("2048"):
            embed = discord.Embed(description=desc_temp.format(desc_2048))
        else:
            embed = discord.Embed(description=desc_temp.format(desc_pksm) + "\n" + desc_temp.format(desc_checkpoint) + "\n" + desc_temp.format(desc_pickr) + "\n" + desc_temp.format(desc_2048))
        if img == 0:
            return await ctx.send(embed=embed)
        qr_file = discord.File(io.BytesIO(img), filename="qr.png")
        embed.set_image(url="attachment://qr.png")
        embed.set_footer(text=f"Version: {version}")
        if released_on:
            embed.description += f"\nReleased on: {discord.utils.format_dt(released_on, style='D')}"
        await ctx.send(file=qr_file, embed=embed)

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
        await ctx.send("You can donate to FlagBrew on Patreon here: <https://www.patreon.com/FlagBrew>.")

    faq_aliases = [  # putting this here to make keeping track ez, as well as updates
        'rtfm',  # general usage
        'vc',  # general faq #1 - vc support
        'entitled',  # general faq #2 - new releases
        'rules',  # general faq #4 - toggling roles
        "swsh",  # pksm faq #2 - switch support
        "emulator",  # pksm faq #3 - emulator cross-use
        "sendpkx",  # pksm faq #7 - sending pkx files
        "wc3", "gen3events",  # pksm faq #9 - gen 3 events
        "romhacks",  # pksm faq #10 - rom hack support
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

        # Handle specific FAQ entries display
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
                return await ctx.send(f"Faq number {faq_num} doesn't exist.")
        for i_faq in invoked_faqs:
            await self.format_faq_embed(self, i_faq, ctx.channel, loaded_faq, faq_doc)

        # Handle full FAQ display
        if len(invoked_faqs) <= 0:
            embed = discord.Embed(title="Frequently Asked Questions")
            embed.title += f" - {'PKSM' if faq_doc.lower() == 'pksm' else faq_doc.title()}"
            for faq_arr in loaded_faq:
                temp_emb = discord.Embed.from_dict(faq_arr)
                for field in temp_emb.fields:
                    embed.add_field(name=field.name, value=field.value, inline=False)
            if ctx.author.id in self.bot.dm_list:
                await ctx.message.delete()
                try:
                    return await ctx.author.send(embed=embed)
                except discord.Forbidden:
                    pass  # Bot blocked, or api bug
            elif ctx.channel not in (self.bot.bot_channel, self.bot.testing_channel, self.bot.bot_channel2) and not ctx.guild.id == 378420595190267915:
                for user in usage_dm:
                    try:
                        await user.send(f"Full faq command was attempted to be used in {ctx.channel.mention} by {ctx.author}\n\nHyperlink to command invoke: {ctx.message.jump_url}")
                    except discord.Forbidden:
                        pass  # Bot blocked
                return await ctx.send(f"If you want to see the full faq, please use {self.bot.bot_channel.mention}, as it is very spammy.")
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
        """Sends wiki link. storage, editor, events, scripts, bag, config, gameid, faq, gpss, hex, bridge, and gbainject are all options"""
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
        elif option == "gbainject":
            extra_info = " on creating a GBA inject"
            wiki_link_ext = "/GBA-Injection"
        else:
            extra_info = ""
            wiki_link_ext = ""
        msg = await ctx.send(f"You can read PKSM's wiki{extra_info} here: <https://github.com/FlagBrew/PKSM/wiki{wiki_link_ext}>")
        await msg.add_reaction("<:wikidiot:558815031836540940>")

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
        """Links to 3ds & switch guides. Each can be given for specific"""
        embed = discord.Embed(title="Console Hacking Guides", description="")
        ds, switch = (True,) * 2
        if option.lower() == "switch":
            ds = False
        elif option.lower() == "3ds":
            switch = False
        if ds:
            embed.description += "You can use [this guide](https://3ds.hacks.guide) to hack your 3ds.\n"
        if switch:
            embed.description += "You can use [this guide](https://nh-server.github.io/switch-guide/) to hack your switch."
        embed.set_thumbnail(url='https://avatars.githubusercontent.com/u/45153157')
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
        embed = discord.Embed(title=f"Matching inputs for `{key}`")
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
        beta_types = (
            "Set Met Date\n"
            "Set Egg Date\n"
            "Remove All Ribbons (Untested)"
        )
        embed = discord.Embed(title="Batch Editor Information")
        embed.description = "Please keep in mind that the script will affect *everything* in the boxes of the loaded save, or of the selected bank."
        embed.add_field(name="Editing Types", value=edit_types)
        if len(beta_types) > 0:
            embed.add_field(name="Beta Types", value=f"**These batch edit options are not included in the latest release. You can get the beta version of the script from the pins in <#389780983869603852>**.\n\n{beta_types}", inline=False)
        embed.set_footer(text="Please note that LGPE and SWSH have not yet been tested.")
        await ctx.send(embed=embed)

    @commands.command(aliases=["shinylocked"])
    async def shinylocks(self, ctx):
        """Lists all shiny locked encounters"""
        encs = {
            "VC Red, Blue, and Yellow": "Any tall grass, cave, or surfing encounters",
            "Colosseum": "Any non-Shadow Pokemon",
            "XD: Gale of Darkness": "All Shadow Pokemon",
            "Black and White": "Reshiram, Victini, and Zekrom",
            "Black 2 and White 2": "Reshiram and Zekrom",
            "X and Y": "Articuno, Mewtwo, Moltres, Xerneas, Yveltal, Zapdos, and Zygarde",
            "Omega Ruby and Alpha Sapphire": "Deoxys, Groudon, Kyogre, and Rayquaza",
            "Sun and Moon": "Cosmog, Lunala, Necrozma, Solgaleo, all 4 Tapus, and all 7 Ultra Beasts",
            "Ultra Sun and Ultra Moon": "Cosmog, Lunala, Necrozma, Solgaleo, all 4 Tapus, and Zygarde",
            "Let's Go Eevee and Pikachu": "Partner Eevee and Partner Pikachu",
            "Sword and Shield (Base Game)": "The gift Charmander, Eternatus, All 3 starters, the gift Toxel, the battle tower Type: Null, the Wedgehurst Slowpoke, Zacian, and Zamazenta",
            "Sword and Shield (Isle of Armour)": "Every gift Pokemon",
            "Sword and Shield (The Crown Tundra)": "Galarian Articuno, Calyrex, the gift Cosmog, Glastrier, Keldeo, Galarian Moltres, the gift Poipole, Spectrier, and Galarian Zapdos"
        }
        embed = discord.Embed(title="Shiny Locked Encounters", description="[Source](https://www.serebii.net/games/shiny.shtml)")
        for key, val in encs.items():
            embed.add_field(name=key, value=val, inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def pksmdata(self, ctx):
        """Instructions on backing up and restoring PKSM's data"""
        embed = discord.Embed()
        embed.description = "PKSM's data is stored in ExtData. As such, the only way to interact with it is via [Checkpoint](https://github.com/FlagBrew/Checkpoint)."
        embed.add_field(name="Backing Up", value="To back up PKSM's ExtData, simply open Checkpoint, press `X`, find PKSM, and hit `Backup`.")
        embed.add_field(name="Restoring", value="To restore PKSM's ExtData, simply open Checkpoint, press `X`, find PKSM, choose your backup, and hit `Restore`.")
        embed.add_field(name="Manual Restore", value="If you haven't made a backup and something happens to your bank, you can use the one-time backup PKSM automatically makes.\n1. Get your bank backup files from `/3ds/PKSM/backup/`. They will end with either `.bnk.bak` or `.bnk.bak.old`.\n2. Copy those files to `/3ds/Checkpoint/saves/0xEC100 PKSM/<folder name here>/<files go here>`. Create a folder if one does not exist.\n3. Remove `.bak`/`.bak.old` from the end of the file extension.\n4. Restore in Checkpoint per the above steps.\n\n**Please Note**: This backup is overwritten every time you save your bank. If you screw something up in your bank, then open it up again and save it, your backup will be gone.", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @spam_limiter
    async def banrisks(self, ctx):
        """Posts current known NS ban risks"""
        ban_info = {
            "guaranteed": """• Piracy of any sort (**If you're wondering whether something counts, the answer is almost certainly yes.**)
                • Homebrew NSPs: See above.
                • Changing user icon through homebrew
                • Sketchy eShop behavior""",
            "semi": """• Modding online games, except in some niche circumstances
                • Cheating in online games
                • Clearing error logs after they've been uploaded to Nintendo (this extends to using both emummc and sysmmc online, due to mismatched logs)""",
            "no": """• Atmosphere, online or offline
                • Most homebrew, online or offline
                • Custom themes
                • Custom sysmodules (sys-ftpd-light, missioncontrol, fizeau, etc.)
                • Mods/cheating in offline games
                • Overclocking with sys-clk (just don't do it competitively, for all of our sakes)
                • emummc""",
            "unknown": """• Modifying PRODINFO, or using the experimental PRODINFO dummying included in Atmosphere 0.11.2 and later.
                • Using sys-tweak to change game icons (which may be sent to Nintendo)"""
        }
        last_updated = datetime.strptime("2021-12-02", "%Y-%m-%d")
        embed = discord.Embed(title="Current known Nintendo Switch ban risks", description=f"Last updated on: {discord.utils.format_dt(last_updated, style='D')}")
        embed.add_field(name="Instant ban", value=ban_info['guaranteed'], inline=False)
        embed.add_field(name="Ban-bait (not always an instant ban, but can get you banned/restricted)", value=ban_info['semi'], inline=False)
        embed.add_field(name="Not a ban, so far", value=ban_info['no'], inline=False)
        embed.add_field(name="We just don't know enough yet", value=ban_info['unknown'], inline=False)
        embed.set_footer(text="Info taken from Val#8035's pin in ReSwitched #user-support")
        await ctx.send(embed=embed)

    @commands.command()
    @spam_limiter
    async def legit(self, ctx):
        """Information about legality versus legitimacy"""
        embed = discord.Embed(title="Terms used by genners")
        embed.description = "**Note**: All in the context of the official release (not emulated, no ROM hacks, etc.)"
        embed.add_field(name="Legitimacy", value="""**Legit**: Obtained by legitimate means, no save editing involved
            **Illegitimate**: Obtained by means that are not intended (cheats, save editing, etc.)""")
        embed.add_field(name="Legality", value="""**Legal**: Has fully legal values, obtained either in game or via save editing
            **Illegal**: Not a legal pokemon, any value of the pokemon isn't possible to obtain in game""")
        embed.add_field(name="Examples", value="""**Legal and legit**: Pokemon I hatched from the daycare without any cheats or save edits
            **Legal and not legit**: Pokemon I generated via PKHeX or PKSM
            **Illegal and legit**: Void glitch Arceus or other pokemon obtained legitimately via a glitch
            **Illegal and not legitimate**: Shiny Victini (a shiny locked Pokemon)""", inline=False)
        embed.add_field(name="But I can trade this fine? Why is it illegal?", value="GameFreak has famously bad hack checks. The shiny victini example mentioned above can trade.", inline=False)
        embed.set_footer(text="Info taken and modified from thecommondude#8240's pin in PKHeX Development Project #general-pkhex")
        await ctx.send(embed=embed)

    @commands.command()
    async def locklair(self, ctx):
        """This person should not be allowed to make youtube videos."""
        embed = discord.Embed(title="So, you're following a video by Blaine Locklair to hack your 3DS")
        embed.add_field(name="What's the issue with video guides, and Blaine's specifically?", value="Video guides in general get outdated extremely quickly. You should only be following [this guide](https://3ds.hacks.guide) if you're hacking your 3DS, or [this guide](https://nh-server.github.io/switch-guide/) if you're hacking your Switch.\nBlaine in particular tends to just reupload the same video guide over and over again with no real change, leading to issues.", inline=False)
        embed.add_field(name="I've followed their 3DS guide this far, what should I do now?", value="Continue on from [this page](https://3ds.hacks.guide/finalizing-setup) of the 3ds guide linked above. That will run you through getting all the files you need from the correct links.", inline=False)
        embed.add_field(name="Well why can't I find the Checkpoint.cia file?", value="Checkpoint 3.8.0 is unstable on 3DS currently. As such, the CIA file for it was removed from the release. Please use [3.7.4](https://github.com/FlagBrew/Checkpoint/releases/tag/v3.7.4).", inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Info(bot))
