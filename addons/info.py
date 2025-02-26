#!/usr/bin/env python3

import json
import aiohttp
import discord
import qrcode
import io
import json
import addons.helper as helper
from discord.ext import commands
from datetime import datetime


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

    async def gen_qr(self, ctx, app):
        latest_release = None
        async with aiohttp.ClientSession() as session:
            url = f"https://api.github.com/repos/FlagBrew/{app}/releases/latest"
            async with session.get(url) as resp:
                latest_release = await resp.json()
        if not latest_release:
            return await ctx.send("Failed to get latest release from GitHub.")
        for asset in latest_release["assets"]:
            if asset["name"] == f"{app}.cia":
                qr = qrcode.QRCode(version=None)
                qr.add_data(asset["browser_download_url"])
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                bytes = io.BytesIO()
                img.save(bytes, format='PNG')
                bytes = bytes.getvalue()
                release_date = latest_release["published_at"][:10]
                release_date_dt = datetime.strptime(release_date, "%Y-%m-%d")
                return bytes, latest_release["tag_name"], release_date_dt

    async def format_faq_embed(self, ctx, faq_num, channel, loaded_faq, faq_doc):
        current_faq = loaded_faq[faq_num - 1]
        embed = discord.Embed.from_dict(current_faq)
        embed.title = "Frequently Asked Questions"
        embed.title += f" - {'PKSM' if faq_doc.lower() == 'pksm' else faq_doc.title()} #{faq_num}"
        await channel.send(embed=embed)

    @commands.command(aliases=["releases", "latest"])
    async def release(self, ctx, *, app=""):
        """Returns the latest release for FlagBrew"s projects. If pulling checkpoint or pickr release, you can add "switch" to the end to get one without a qr code for ease of use"""
        img = None
        version = "N/A"
        release_date = None
        if app.lower().startswith("pksm"):
            embed = discord.Embed(description="You can get the latest release of PKSM [here](https://github.com/FlagBrew/PKSM/releases/latest).")
            img, version, release_date = await self.gen_qr(self, "PKSM")
        elif app.lower().startswith("checkpoint"):
            embed = discord.Embed(description="You can get the latest release of Checkpoint [here](https://github.com/FlagBrew/Checkpoint/releases/latest).")
            str_list = app.lower().split()
            if "switch" not in str_list:
                # Manual formatting due to 3.8.0 being broken...
                # img, version = await self.gen_qr(self, "Checkpoint")
                embed.description += "\nCheckpoint 3.8.0 is currently broken on 3DS. Please use 3.7.4 found [here](https://github.com/FlagBrew/Checkpoint/releases/tag/v3.7.4)."
                qr = qrcode.QRCode(version=None)
                qr.add_data("https://github.com/BernardoGiordano/Checkpoint/releases/download/v3.7.4/Checkpoint.cia")
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white")
                bytes = io.BytesIO()
                qr_img.save(bytes, format='PNG')
                bytes = bytes.getvalue()
                img = bytes
                version = "3.7.4"
                release_date = datetime.strptime("2019-12-09", "%Y-%m-%d")
            else:
                version = "3.8.0"  # Temporary until 3.8.0 is fixed
        else:
            embed = discord.Embed(description="You can get the latest release of PKSM [here](https://github.com/FlagBrew/PKSM/releases/latest).\nYou can get the latest release of Checkpoint [here](https://github.com/FlagBrew/Checkpoint/releases/latest).")
        embed.set_author(name="FlagBrew", url="https://github.com/FlagBrew", icon_url="https://avatars.githubusercontent.com/u/42673825")
        embed.set_footer(text=f"Version: {version}")
        if not img:
            return await ctx.send(embed=embed)
        qr_file = discord.File(io.BytesIO(img), filename="qr.png")
        embed.set_image(url="attachment://qr.png")
        if release_date:
            embed.description += f"\nReleased on: {discord.utils.format_dt(release_date, style='D')}"
        await ctx.send(file=qr_file, embed=embed)

    @commands.command()
    async def readme(self, ctx, app=""):
        """READMEs for FlagBrew's projects."""
        readme_template = "You can read {}'s README [here](https://github.com/FlagBrew/{}/blob/master/README.md)."
        if app.lower() == "script" or app.lower() == "pksmscript" or app.lower() == "scripts" or app.lower() == "pksmscripts":
            embed = discord.Embed(description=readme_template.format("PKSM Scripts", "PKSM-Scripts"))
            author = "SpiredMoth"
        elif app.lower() == "checkpoint":
            embed = discord.Embed(description=readme_template.format("Checkpoint", "Checkpoint"))
            author = "LiquidFenrir"
        elif app.lower() == "pksm":
            embed = discord.Embed(description=readme_template.format("PKSM", "PKSM"))
            author = "piepie62"
        elif app.lower() == "sharkive":
            embed = discord.Embed(description=readme_template.format("Sharkive", "Sharkive"))
            author = "JourneyOver"
        else:
            return await ctx.send("Input not given or recognized. Available READMEs: `scripts`, `checkpoint`, `pksm`, `sharkive`.")
        embed.set_author(name=author, url=f"https://github.com/{author}", icon_url="https://avatars.githubusercontent.com/u/42673825")
        await ctx.send(embed=embed)

    faq_aliases = [  # putting this here to make keeping track ez, as well as updates
        'rtfm',  # general usage

        # General FAQ items
        'vc',  # 1 - vc support
        'entitled',  # 2 - new releases
        'rules',  # 4 - toggling roles

        # PKSM FAQ items
        "helplegal",  # 1 - legality
        "lgpe", "swsh", "bdsp", "pla", "scvi", "switchsupport",  # 2 - switch support
        "emulator",  # 3 - emulator cross-use
        "scripts", "universal",  # 4 - how do universal scripts work
        "badqr",  # 6 - why QR no worky
        "sendpkx",  # 7 - sending pkx files
        "wc3",  # 9 - gen 3 events
        "romhacks",  # 10 - rom hack support
        "azure",  # 11
        "trades",  # 12 - trade evos

        # Checkpoint FAQ items
        "addcode", "fixcheat",  # 1 - pls add cheat
        "wheregame",  # 2 - missing games
        "applet",  # 3 - applet mode issues
        "pkcrash",  # 4 - cheat crash in pkmn games
        "updatedb",  # 6 - how to update the cheat db
    ]

    @commands.command(aliases=['faqaliases', 'faqalias', 'lfaq'])
    async def list_faq_aliases(self, ctx):
        """Lists all available aliases for the faq command."""
        embed = discord.Embed(title="FAQ Aliases")
        embed.description = f"`{'`, `'.join(self.faq_aliases)}`"
        await ctx.send(embed=embed)

    @commands.command(aliases=faq_aliases)
    @helper.spam_limiter
    @helper.faq_decorator
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
                    embed.add_field(name=f"**{loaded_faq.index(faq_arr)+1}**: " + field.name, value=field.value, inline=False)
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
    @helper.spam_limiter
    async def question(self, ctx):
        """Reminder for those who won't just ask their question"""
        embed = discord.Embed(title="How to Ask a Proper Question")
        embed.description = "If you would like someone to help you, please be as descriptive as possible. Some (non-exhaustive) examples of info that you should provide:"
        embed.add_field(name="Your Working Environment", value="\u2022 Console\n\u2022 System Software Version\n\u2022 Luma/Atmosphere Version\n\u2022 Application Version")
        embed.add_field(name="Steps You've Taken", value="This should include __**ALL**__ steps you have taken to cause the issue, as well as any you have taken to resolve the issue.")
        embed.add_field(name="Assisting Materials", value="Any and all assisting materials you have used to get to your current point, being **as specific** as possible. This includes __**any**__ crash dumps or error messages that you encounter.")
        embed.add_field(name="Please keep in mind that doing things such as:", value="\u2022 Asking if you can ask a question while in the correct channel\n"
                        "\u2022 Asking if anyone is available to help\n\u2022 Asking any other vague question that is not your actual question\n"
                        "Will only delay your assistance. Please keep in mind that we are *all* volunteers. and that ***WE ARE NOT PSYCHIC.***", inline=False)
        await ctx.send(embed=embed)

    @commands.command(aliases=['readthedocs', 'docs', '<:wikidiot:558815031836540940>'])
    async def wiki(self, ctx, option=""):
        """Sends wiki link. storage, editor, events, scripts, bag, config, gameid, faq, hex, bridge, and gbainject are all options"""
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

    @commands.command(aliases=['dg'])
    @helper.spam_limiter
    async def downgrade(self, ctx):
        """Don't. Fucking. Downgrade."""
        embed = discord.Embed(title="Should you downgrade?")
        embed.description = "If you downgrade, you will fuck things up. Don't do it for fucks sake."
        embed.set_thumbnail(url="https://media.giphy.com/media/ToMjGpx9F5ktZw8qPUQ/giphy.gif")
        await ctx.send(embed=embed)

    @commands.command(aliases=['es'])
    @helper.spam_limiter
    async def extrasaves(self, ctx):
        """Extrasaves info"""
        embed = discord.Embed(title="How do I access my external saves?")
        embed.description = ("Open PKSM's settings from the game select menu by pressing `x`, and go to **Misc**. Then choose **Extra Saves**.\n"
                             "Then, select the game you want to add a save for, choose add save, and navigate to the save.\n"
                             "Afterwards, hit `y` on the game select screen to view the absent games menu.")
        await ctx.send(embed=embed)

    @commands.command(aliases=["tid"])
    @helper.spam_limiter
    async def titleid(self, ctx):
        """Title ID adding info"""
        embed = discord.Embed(title="How do I access my Generation 3 or non-English Generation 1/2 games?")
        embed.description = ("Open PKSM's settings from the game select menu by pressing `x`, and go to **Misc**. Then choose **Title IDs**.\n"
                             "Then, select the game you want to set a custom title ID for, and enter the game's title ID. You can check this in FBI.\n"
                             "Afterwards, select `VC Games` at the top of the game select screen (or hit R).")
        embed.set_footer(text="Please note: GBA injects *must* have a save type of 1024kbit. Otherwise, it will not load in PKSM.")
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
            "Randomize PIDs\n"
            "Set Met Date\n"
            "Set Egg Date\n"
            "Remove All Ribbons (Untested)"
        )
        embed = discord.Embed(title="Batch Editor Information")
        embed.description = "Please keep in mind that the script will affect *everything* in the boxes of the loaded save, or of the selected bank."
        embed.add_field(name="Editing Types", value=edit_types)
        embed.set_footer(text="Please note that LGPE and SWSH have not yet been tested. Generation 1 and 2 games are not supported.")
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
            "Sword and Shield (Base Game)": "The gift Charmander, Eternatus, all 3 starters, the gift Toxel, the battle tower Type: Null, the Wedgehurst Slowpoke, Zacian, and Zamazenta",
            "Sword and Shield (Isle of Armour)": "Every gift Pokemon",
            "Sword and Shield (The Crown Tundra)": "Galarian Articuno, Calyrex, the gift Cosmog, Glastrier, Keldeo, Galarian Moltres, the gift Poipole, Spectrier, and Galarian Zapdos",
            "Brilliant Diamond and Shining Pearl": "The gift Jirachi and the gift Mew",
            "Legends Arceus": "All 3 starters, Arceus, Azelf, Cresselia, Darkrai, Dialga, Enamorus, Giratina, Heatran, Landorus, Manaphy, Mesprit, Palkia, Phione, Regigigas, Shaymin, Thundurus, Tornadus, Uxie, all forced encounters in requests and missions, and the gift Alolan Vulpix",
            "Scarlet and Violet": 'All 3 starters, all Gimmighoul, both Koraidon, both Miraidon, the 4 Sub-Legends, the 6 former Titans, and the Artazon Sunflora\n*There are also a handful of fixed symbol encounters, such as the Squawkabilly on top of your house, that are shiny locked. These are not listed here for brevity.*'
        }
        permanently_unavailable = [
            "All Gen 4 and 5 non-shiny event Pokemon (with very few exceptions)",
            "All Hat Pikachu (except Partner Cap)",
            "Ash-Greninja",
            "Calyrex",
            "Chi-Yu",
            "Chien-Pao",
            "Cosmoem",
            "Cosmog",
            "Enamorus",
            "Gholdengo",
            "Gigantamax Melmetal",
            "Gimmighoul",
            "Glastrier",
            "Hoopa",
            "Keldeo",
            "Koraidon",
            "Kubfu",
            "Magearna (Standard and Original Color)",
            "Marshadow",
            "Meloetta",
            "Miraidon",
            "Spectrier",
            "Ting-Lu",
            "Urshifu (Both Forms)",
            "Victini",
            "Vivillon (Poké Ball Pattern)",
            "Volcanion",
            "Wo-Chien",
            "Zarude (Both Forms)"
        ]
        embed = discord.Embed(title="Shiny Locked Encounters", description="[Source](https://www.serebii.net/games/shiny.shtml)")
        for key, val in encs.items():
            embed.add_field(name=key, value=val, inline=False)
        embed.add_field(name="Never Been Available Shiny", value=", ".join(permanently_unavailable))
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
    @helper.spam_limiter
    async def banrisks(self, ctx):
        """Posts current known NS ban risks"""
        ban_info = {
            "guaranteed": ("\u2022 Piracy of any sort (**If you're wondering whether something counts, the answer is almost certainly yes.**)\n"
                           "\u2022 Homebrew NSPs: See above.\n"
                           "\u2022 Changing user icon through homebrew\n"
                           "\u2022 Sketchy eShop behavior"),
            "semi": ("\u2022 Modding online games, except in some niche circumstances\n"
                     "\u2022 Cheating in online games\n"
                     "\u2022 Clearing error logs after they've been uploaded to Nintendo (this extends to using both emummc and sysmmc online, due to mismatched logs)"),
            "no": ("\u2022 Atmosphere, online or offline\n"
                   "\u2022 Most homebrew, online or offline\n"
                   "\u2022 Custom themes\n"
                   "\u2022 Custom sysmodules (sys-ftpd-light, missioncontrol, fizeau, etc.)\n"
                   "\u2022 Mods/cheating in offline games\n"
                   "\u2022 Overclocking with sys-clk (just don't do it competitively, for all of our sakes)\n"
                   "\u2022 emummc"),
            "unknown": ("\u2022 Modifying PRODINFO, or using the experimental PRODINFO dummying included in Atmosphere 0.11.2 and later.\n"
                        "\u2022 Using sys-tweak to change game icons (which may be sent to Nintendo)")
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
    @helper.spam_limiter
    async def legit(self, ctx):
        """Information about legality versus legitimacy"""
        embed = discord.Embed(title="Terms used by genners")
        embed.description = "**Note**: All in the context of the official release (not emulated, no ROM hacks, etc.)"
        embed.add_field(name="Legitimacy", value=("**Legit**: Obtained by legitimate means, no save editing involved\n"
                                                  "**Illegitimate**: Obtained by means that are not intended (cheats, save editing, etc.)"))
        embed.add_field(name="Legality", value=("**Legal**: Has fully legal values, obtained either in game or via save editing\n"
                                                "**Illegal**: Not a legal pokemon, any value of the pokemon isn't possible to obtain in game"))
        embed.add_field(name="Examples", value=("**Legal and legit**: Pokemon I hatched from the daycare without any cheats or save edits\n"
                                                "**Legal and not legit**: Pokemon I generated via PKHeX or PKSM\n"
                                                "**Illegal and legit**: Void glitch Arceus or other pokemon obtained legitimately via a glitch\n"
                                                "**Illegal and not legitimate**: Shiny Victini (a shiny locked Pokemon)"), inline=False)
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
