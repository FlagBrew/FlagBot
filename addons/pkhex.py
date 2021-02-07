import discord
import asyncio
import aiohttp
import io
import json
import base64
import validators
import os
import urllib
import binascii
from exceptions import PKHeXMissingArgs
import addons.helper as helper
from addons.helper import restricted_to_bot
from datetime import datetime
from discord.ext import commands

class pkhex(commands.Cog):

    """Handles all the PKHeX Related Commands. Does not load if api_url is not defined in config"""

    def __init__(self, bot):
        self.bot = bot
        self.failure_count = 0
        self.api_check = bot.loop.create_task(self.confirm_api_link())  # loops referenced from https://github.com/chenzw95/porygon/blob/aa2454336230d7bc30a7dd715e057ee51d0e1393/cogs/mod.py#L23
        print(f'Addon "{self.__class__.__name__}" loaded')
        
    def cog_unload(self):
        self.api_check.cancel()

    async def ping_api_func(self):
        try:
            async with self.bot.session.get(self.bot.api_url + "api/ping") as r:
                return r.status
        except aiohttp.ClientConnectorError:
            return 443
        except aiohttp.InvalidURL:
            return 400

    async def confirm_api_link(self):
        while not self.bot.is_closed():
            if not self.bot.ready:
                await asyncio.sleep(30)
                continue
            r = await self.ping_api_func()
            if not r == 200:
                self.failure_count += 1
                if self.failure_count == 3:  # Only unload if it fails concurrently 3+ times, to prevent accidental unloads on server restarts
                    for x in (self.bot.creator, self.bot.allen):
                        await x.send(f"pkhex.py commands were disabled as API connection was dropped. Status code: `{r}`")
                    for command in self.get_commands():
                        if not command.name == "rpc":
                            command.enabled = False
                    self.api_check.cancel()
            else:
                self.failure_count = 0
            await asyncio.sleep(300)

    async def process_file(self, ctx, data, attachments, url, is_gpss=False, user_id=None):
        if not data and not attachments:
            await ctx.send("Error: No data was provided and no pkx file was attached.")
            return 400
        elif not data:
            atch = attachments[0]
            if atch.size > 400:
                await ctx.send("The attached file was too large.")
                return 400
            b = io.BytesIO()
            try:
                await atch.save(b)
            except discord.Forbidden:
                await ctx.send("The file seems to have been deleted, so I can't complete the task.")
                return 400
            file = b.getvalue()
        else:
            if not validators.url(data):
                await ctx.send("That's not a real link!")
                return 400
            elif not data.strip("?raw=true")[-4:-1] == ".pk":
                await ctx.send("That isn't a pkx file!")
                return 400
            try:
                async with self.bot.session.get(data) as r:
                    file = io.BytesIO(await r.read())
            except aiohttp.InvalidURL:
                await ctx.send("The provided data was not valid.")
                return 400
        if not is_gpss:
            url = self.bot.api_url + url
        else:
            url = self.bot.flagbrew_url + url
        files = {'pkmn': file}
        if user_id is None:
            user_id = ""
        headers = {'UID': user_id, 'secret': self.bot.site_secret}
        async with self.bot.session.post(url=url, data=files, headers=headers) as r:
            if not is_gpss and (r.status == 400 or r.status == 413):
                await ctx.send("The provided file was invalid.")
                return 400
            try:
                rj = await r.json()
            except aiohttp.client_exceptions.ContentTypeError:
                rj = {}
            content = await r.content.read()
            if content == b'':
                content = await r.read()
            if content == b'':
                await ctx.send(f"Couldn't get response content. {self.bot.creator.mention} and {self.bot.allen.mention} please investigate!")
                await ctx.send(content)
                return 400
            return [r.status, rj, content]

    def embed_fields(self, ctx, embed, data, is_set=False):
        embed.add_field(name="Species", value=data["Species"])
        embed.add_field(name="Level", value=data["Level"])
        embed.add_field(name="Nature", value=data["Nature"])
        if int(data["Generation"]) > 2:
            embed.add_field(name="Ability", value=data["Ability"])
        else:
            embed.add_field(name="Ability", value="N/A")
        if not is_set:
            ot = data["OT"]
            sid = data["SID"]
            tid = data["TID"]
            if int(data["Generation"]) > 2:
                embed.add_field(name="Original Trainer", value=f"{ot}\n({tid}/{sid})")
            else:
                embed.add_field(name="Original Trainer", value=f"{ot}\n({tid})")
        if not data["HT"] == "" and not is_set:
            embed.add_field(name="Handling Trainer", value=data["HT"])
        elif not is_set:
            embed.add_field(name="Handling Trainer", value="N/A")
        if int(data["Generation"]) > 2 and not data["MetLoc"] == "" and not is_set:
            embed.add_field(name="Met Location", value=data["MetLoc"])
        elif not is_set:
            embed.add_field(name="Met Location", value="N/A")
        if int(data["Generation"]) > 2:
            if data["Version"] == "":
                return 400
            embed.add_field(name="Origin Game", value=data["Version"])
        else:
            embed.add_field(name="Origin Game", value="N/A")
        embed.add_field(name="Captured In", value=data["Ball"])
        if data["HeldItem"] != "(None)" and is_set:
            embed.add_field(name="Held Item", value=data["HeldItem"])
        if is_set:
            embed.add_field(name="Gender", value=data["Gender"])
        if is_set:
            embed.add_field(name=u"\u200B", value=u"\u200B", inline=False)
        embed.add_field(name="EVs", value=f"**HP**: {data['HP_EV']}\n**Atk**: {data['ATK_EV']}\n**Def**: {data['DEF_EV']}\n**SpAtk**: {data['SPA_EV']}\n**SpDef**: {data['SPD_EV']}\n**Spd**: {data['SPE_EV']}")
        embed.add_field(name="IVs", value=f"**HP**: {data['HP_IV']}\n**Atk**: {data['ATK_IV']}\n**Def**: {data['DEF_IV']}\n**SpAtk**: {data['SPA_IV']}\n**SpDef**: {data['SPD_IV']}\n**Spd**: {data['SPE_IV']}")
        embed.add_field(name="Moves", value=f"**1**: {data['Move1']}\n**2**: {data['Move2']}\n**3**: {data['Move3']}\n**4**: {data['Move4']}")
        return embed

    def list_to_embed(self, embed, l):
        for x in l:
            values = x.split(": ")
            values[0] = "**" + values[0] + "**: "
            val = ""
            for x in values[1:]:
                val += x + " "
            embed.description += values[0] + val + "\n"
        return embed

    def set_sprite_thumbnail(self, mon_info=None, shiny=None, form=None, species=None, sprite=False):
        if mon_info:
            shiny = "shiny" if mon_info["IsShiny"] else "normal"
            form = mon_info["Form"].lower()
            species = mon_info["Species"].lower()
        if " " in form:
            form = form.replace(" ", "-")
        if species == "minior":  # fuck you fuck you fuck you
            return f"{self.bot.sprite_url}/ultra-sun-ultra-moon/normal/minior-meteor.png"
        elif species == "sinistea" and sprite is True:
            form = None
        if form and not species == "rockruff":
            if species == "flabébé":
                species = "flabebe"
            elif form == "f":
                form = "female"
            if not sprite:
                return f"{self.bot.sprite_url}/ultra-sun-ultra-moon/{shiny}/{species}-{form}.png"
            if form == "female":
                return f"{self.bot.sprite_url}/sprites/8/{shiny}/female/{species}-{form}.png"
            return f"{self.bot.sprite_url}/sprites/8/{shiny}/{species}-{form}.png"
        elif sprite:
            return f"{self.bot.sprite_url}/sprites/8/{shiny}/{species}.png"
        return f"{self.bot.sprite_url}/ultra-sun-ultra-moon/{shiny}/{species}.png"

    @commands.command(name="rpc")
    async def reactivate_pkhex_commands(self, ctx):
        """Reactivates the pkhex commands. Restricted to bot creator and Allen"""
        if not ctx.author in (self.bot.creator, self.bot.allen):
            raise commands.errors.CheckFailure()
        r = await self.ping_api_func()
        if not r == 200:
            return await ctx.send(f"Cancelled the command reactivation; status code from FlagBrew server is `{r}`.")
        for command in self.get_commands():
            if command.enabled is True:
                await ctx.send(f"Cancelled the command reactivation for `{command.name}`; command already enabled.")
                continue
            command.enabled = True
        self.api_check = self.bot.loop.create_task(self.confirm_api_link())
        return await ctx.send("Successfully reactivated the pkhex commands.")

    @commands.command(hidden=True)
    async def ping_api(self, ctx):
        """Pings the CoreAPI server"""
        if not ctx.author in (self.bot.creator, self.bot.allen):
            raise commands.errors.CheckFailure()
        msgtime = ctx.message.created_at.now()
        r = await self.ping_api_func() 
        now = datetime.now()
        ping = now - msgtime
        await ctx.send(f"🏓 CoreAPI response time is {str(ping.microseconds / 1000.0)} milliseconds. Current CoreAPI status code is {r}.")

    @commands.command(name='legality', aliases=['illegal'])
    async def check_legality(self, ctx, *, data=""):
        """Checks the legality of either a provided URL or attached pkx file. URL *must* be a direct download link"""
        if not data and not ctx.message.attachments:
            raise PKHeXMissingArgs()
        if not await self.ping_api_func() == 200:
            return await ctx.send("The CoreAPI server is currently down, and as such no commands in the PKHeX module can be used.")
        r = await self.process_file(ctx, data, ctx.message.attachments, "api/bot/check")
        if r == 400:
            return
        rj = r[1]
        reasons = rj["IllegalReasons"].split("\n")
        if reasons[0] == "Legal!":
            return await ctx.send("That Pokemon is legal!")
        embed = discord.Embed(title="Legality Issues", description="", colour=discord.Colour.red())
        embed = self.list_to_embed(embed, reasons)
        await ctx.send(embed=embed)

    @commands.command(name='forms')
    async def check_forms(self, ctx, species):
        """Returns a list of a given Pokemon's forms."""
        if not await self.ping_api_func() == 200:
            return await ctx.send("The CoreAPI server is currently down, and as such no commands in the PKHeX module can be used.")
        url = self.bot.api_url + "api/PokemonForms"
        data = {
            "pokemon": species.lower()
        }
        async with self.bot.session.post(url=url, data=data) as r:
            if not r.status == 200:
                return await ctx.send("Are you sure that's a real pokemon?")
            rj = await r.json()
            if rj[0] == "":
                return await ctx.send(f"No forms available for `{species.title()}`.")
            await ctx.send(f"Available forms for {species.title()}: `{'`, `'.join(rj)}`.")

    @commands.command(name='pokeinfo', aliases=['pi'])
    @restricted_to_bot
    async def poke_info(self, ctx, data="", shiny="normal"):
        ("""Returns an embed with a Pokemon's nickname, species, and a few others. Takes a provided URL or attached pkx file. URL *must* be a direct download link.\n"""
        """Alternatively can take a single Pokemon as an entry, and will return basic information on the species.""")
        if not data and not ctx.message.attachments:
            raise PKHeXMissingArgs()
        if not await self.ping_api_func() == 200:
            return await ctx.send("The CoreAPI server is currently down, and as such no commands in the PKHeX module can be used.")
        
        # Get info for inputted pokemon
        with open("saves/defaultforms.json", "r", encoding="utf8") as f:
            defaultforms = json.load(f)
        if not shiny in ("normal", "shiny"):
            shiny = "normal"
        if not validators.url(data) and not ctx.message.attachments:
            colours = {
                "Red": discord.Colour.red(),
                "Blue": discord.Colour.blue(),
                "Yellow": discord.Colour.gold(),
                "Green": discord.Colour.green(),
                "Black": discord.Colour(0x070e1c),
                "Brown": discord.Colour(0x8B4513),
                "Purple": discord.Colour.purple(),
                "Gray": discord.Colour.light_grey(),
                "White": discord.Colour(0xe9edf5),
                "Pink": discord.Colour(0xFF1493),
            }
            url = self.bot.api_url + "api/bot/base_info"
            data = data.split('-')
            species = data[0].lower()
            if species == "flabebe":
                species = "flabébé"
            form = ""
            if species in defaultforms.keys():
                form = defaultforms[species]
            if len(data) > 1:
                form = data[1].lower()
            elif form == "female":
                form = "f"
            data = {
                "pkmn": species,
                "form": form
            }
            async with self.bot.session.post(url=url, data=data) as r:
                if not r.status == 200:
                    return await ctx.send("Are you sure that's a real pokemon (or proper form)?")
                rj = await r.json()
                embed = discord.Embed(title=f"Basic info for {species.title()}{'-' + form.title() if form else ''}", colour=colours[rj["Color"]])
                type_str = f"Type 1: {rj['Types'][0]}"
                if not rj["Types"][1] == rj["Types"][0]:
                    type_str += f"\nType 2: {rj['Types'][1]}"
                embed.add_field(name="Types", value=type_str)
                ability_str = f"Ability (1): {rj['Ability1']}"
                if not rj["Ability2"] == rj["Ability1"]:
                    ability_str += f"\nAbility (2): {rj['Ability2']}"
                if rj["HasHiddenAbility"]:
                    ability_str += f"\nAbility (H): {rj['AbilityH']}"
                embed.add_field(name="Abilities", value=ability_str)
                embed.add_field(name="Height & Weight", value=f"{rj['Height'] / 100} meters\n{rj['Weight'] / 10} kilograms")
                if rj["IsDualGender"]:
                    ratio = (rj["Gender"] / 254) * 100
                    ratio = round(ratio, 2)
                    embed.add_field(name="Gender Ratio", value=f"~{ratio}% Female")
                else:
                    embed.add_field(name="Gender", value="Genderless" if rj["Genderless"] else "Male" if rj["OnlyMale"] else "Female")
                embed.add_field(name="EXP Growth", value=rj["EXPGrowth"])
                embed.add_field(name="Evolution Stage", value=rj["EvoStage"])
                embed.add_field(name="Hatch Cycles", value=rj["HatchCycles"])
                embed.add_field(name="Base Friendship", value=rj["BaseFriendship"])
                embed.add_field(name="Catch Rate", value=f"{rj['CatchRate']}/255")
                egg_str = f"Egg Group 1: {rj['EggGroups'][0]}"
                if not rj["EggGroups"][1] == rj["EggGroups"][0]:
                    egg_str += f"\nEgg Group 2: {rj['EggGroups'][1]}"
                embed.add_field(name="Egg Groups", value=egg_str)
                embed.add_field(name=f"Base stats ({rj['BST']})", value=f"```HP:    {rj['HP']} Atk:   {rj['ATK']}\nDef:   {rj['DEF']} SpAtk: {rj['SPA']} \nSpDef: {rj['SPD']} Spd:   {rj['SPE']}```")
                embed.set_thumbnail(url=self.set_sprite_thumbnail(shiny=shiny, species=species, form=form))
                try:
                    return await ctx.send(embed=embed)
                except discord.HTTPException:
                    embed.set_thumbnail(url="")
                    return await ctx.send(f"{ctx.author.mention} I threw an HTTPException. This is likely due to form stupidity. So don't do that again. Otherwise, you get warned. {self.bot.creator.mention} and {self.bot.pie.mention}, for logging purposes.", embed=embed)

        # Get info for inputted file
        r = await self.process_file(ctx, data, ctx.message.attachments, "api/bot/pokemon_info")
        if r == 400:
            return
        rj = r[1]
        embed = discord.Embed(title=f"Data for {rj['Nickname']}")
        embed = self.embed_fields(ctx, embed, rj)
        if embed == 400:
            return await ctx.send(f"{ctx.author.mention} Something in that pokemon is *very* wrong. Your request has been canceled. Please do not try that mon again.")
        embed.set_thumbnail(url=rj["SpeciesSpriteURL"])
        embed.colour = discord.Colour.green() if rj["IllegalReasons"] == "Legal!" else discord.Colour.red()
        try:
            await ctx.send(embed=embed)
        except Exception as e:
            return await ctx.send(f"There was an error showing the data for this pokemon. {self.bot.creator.mention}, {self.bot.pie.mention}, or {self.bot.allen.mention} please check this out!\n{ctx.author.mention} please do not delete the file. Exception below.\n\n```{e}```")

    @commands.command(name='qr')
    @restricted_to_bot
    async def gen_pkmn_qr(self, ctx, data=""):
        """Gens a QR code that PKSM can read. Takes a provided URL or attached pkx file. URL *must* be a direct download link"""
        if not data and not ctx.message.attachments:
            raise PKHeXMissingArgs()
        if not await self.ping_api_func() == 200:
            return await ctx.send("The CoreAPI server is currently down, and as such no commands in the PKHeX module can be used.")
        r = await self.process_file(ctx, data, ctx.message.attachments, "api/bot/pokemon_info")
        if r == 400:
            return
        r = r[1]
        decoded_qr = base64.decodebytes(r['QR'].encode("ascii"))
        qr = discord.File(io.BytesIO(decoded_qr), 'pokemon_qr.png')
        await ctx.send(f"QR containing a {r['Species']} for Generation {r['Generation']}", file=qr)

    @commands.command(name='learns', aliases=['learn'])
    async def check_moves(self, ctx, generation: int, *, input_data):
        """Checks if a given pokemon can learn moves. Separate moves using pipes. Example: .learns 8 pikachu | quick attack | hail"""
        if not await self.ping_api_func() == 200:
            return await ctx.send("The CoreAPI server is currently down, and as such no commands in the PKHeX module can be used.")
        input_data = input_data.replace("| ", "|").replace(" |", "|").replace(" | ", "|")
        input_data = input_data.split("|")
        pokemon = input_data[0]
        moves = input_data[1:]
        if not moves:
            return await ctx.send("No moves provided, or the data provided was in an incorrect format.\n```Example: .learns pikachu | quick attack | hail```")
        data = {
            "query": pokemon + "|" + "|".join(moves),
            "generation": str(generation)
        }
        async with self.bot.session.post(self.bot.api_url + "api/bot/moves", data=data) as r:
            if r.status == 400:
                return await ctx.send("Something you sent was invalid. Please double check your data and try again.")
            rj = await r.json()
            embed = discord.Embed(title=f"Move Lookup for {pokemon.title()} in Generation {str(generation)}", description="")
            for move in rj:
                embed.description += f"**{move['name'].title()}** is {'not ' if not move['learnable'] else ''}learnable.\n"
            await ctx.send(embed=embed)

    @commands.command(name='find')
    async def check_encounters(self, ctx, generation: int, *, input_data):
        """Outputs the locations a given pokemon can be found. Separate data using pipes. Example: .find 6 pikachu | volt tackle"""
        if not await self.ping_api_func() == 200:
            return await ctx.send("The CoreAPI server is currently down, and as such no commands in the PKHeX module can be used.")
        elif not generation in range(1, 9):
            return await ctx.send(f"The inputted generation must be a valid integer between 1 and 8 inclusive. You entered: `{generation}`")
        input_data = input_data.replace("| ", "|").replace(" |", "|").replace(" | ", "|")
        input_data = input_data.split("|")
        pokemon = input_data[0]
        moves = input_data[1:]
        data = {
            "query": pokemon + ("|" + "|".join(moves) if not len(moves) == 0 else ""),
            "generation": generation
        }
        async with self.bot.session.post(self.bot.api_url + "api/Encounter", data=data) as r:
            if r.status == 400:
                return await ctx.send("Something you sent was invalid. Please double check your data and try again.")
            rj = await r.json()
            embed = discord.Embed(title=f"Encounter Data for {pokemon.title()} in Generation {generation}{' with move(s) ' if len(moves) > 0 else ''}{', '.join([move.title() for move in moves])}")
            for encs in rj['encounters']:
                field_values = ""
                for loc in encs["locations"]:
                    games = (helper.game_dict[x] if x in helper.game_dict.keys() else x for x in loc["games"])
                    games_str = ", ".join(games)
                    games_str = games_str.replace("GG", "LGPE")
                    if encs["encounterType"] == "Egg":
                        field_values += f"{games_str} as **egg**.\n"
                    elif not loc["name"] == "":
                        field_values += f"{games_str} in **{loc['name']}**.\n"
                    elif generation == 1:
                        field_values += f"{games_str} in **Unknown**.\n"
                        embed.set_footer(text="Please ask Kurt#6024 to add route names to gen 1 location data")
                if field_values:
                    embed.add_field(name=f"As {encs['encounterType']}", value=field_values, inline=False)
            if len(embed.fields) == 0:
                return await ctx.send(f"Could not find matching encounter data for {pokemon.title()} in Generation {generation}{' with move(s) ' if len(moves) > 0 else ''}{', '.join([move.title() for move in moves])}.")
            await ctx.send(embed=embed)

    @commands.command(name="gpssfetch")
    async def gpss_lookup(self, ctx, code):
        """Looks up a pokemon from the GPSS using its download code"""
        if not code.isdigit():
            return await ctx.send("GPSS codes are solely comprised of numbers. Please try again.")
        async with self.bot.session.get(self.bot.flagbrew_url) as r:
            if not r.status == 200:
                return await ctx.send("I could not make a connection to flagbrew.org, so this command cannot be used currently.")
        upload_channel = await self.bot.fetch_channel(664548059253964847)  # Points to #legalize-log on FlagBrew
        msg = await ctx.send("Attempting to fetch pokemon...")
        async with self.bot.session.get(self.bot.flagbrew_url + "api/v1/gpss/search/" + code) as r:
            async with self.bot.session.get(self.bot.flagbrew_url + "gpss/desktop/download/" + code) as download:
                rj = await r.json()
                for pkmn in rj["results"]:
                    if pkmn["code"] == code:
                        pkmn_data = pkmn["pokemon"]
                        filename = pkmn_data["Species"] + f" Code_{code}"
                        if pkmn_data["Generation"] == "LGPE":
                            filename += ".pb7"
                        else:
                            filename += ".pk" + pkmn_data["Generation"]
                        pkmn_b64 = binascii.b2a_base64(await download.read())
                        pkmn_file = discord.File(io.BytesIO(base64.decodebytes(pkmn_b64)), filename)
                        await asyncio.sleep(1)
                        m = await upload_channel.send(f"Pokemon fetched from the GPSS by {ctx.author}", file=pkmn_file)
                        embed = discord.Embed(description=f"[GPSS Page]({self.bot.gpss_url + 'gpss/view/' + code}) | [Download link]({m.attachments[0].url})")
                        embed = self.embed_fields(ctx, embed, pkmn_data)
                        if embed == 400:
                            return await ctx.send(f"Something in that pokemon is *very* wrong. Please do not try to check that code again.\n\n{self.bot.pie.mention}: Mon was gen3+ and missing origin game. Code: `{code}`")
                        embed.set_author(icon_url=self.set_sprite_thumbnail(mon_info=pkmn_data, sprite=True), name=f"Data for {pkmn_data['Nickname']}")
                        embed.set_thumbnail(url=self.bot.gpss_url + f"gpss/qr/{code}")
                        return await msg.edit(embed=embed, content=None)
        await msg.edit(content=f"There was no pokemon on the GPSS with the code `{code}`.")

    @commands.command(name="gpsspost", aliases=['gpssupload'])
    @restricted_to_bot
    async def gpss_upload(self, ctx, data=""):
        """Allows uploading a pokemon to the GPSS. Takes a provided URL or attached pkx file. URL *must* be a direct download link"""
        if not data and not ctx.message.attachments:
            raise PKHeXMissingArgs()
        async with self.bot.session.get(self.bot.flagbrew_url) as r:
            if not r.status == 200:
                return await ctx.send("I could not make a connection to flagbrew.org, so this command cannot be used currently.")
        r = await self.process_file(ctx, data, ctx.message.attachments, "gpss/share", True, str(ctx.author.id))
        if r == 400:
            return
        code = str(r[2], encoding='utf-8')
        if len(code) > 10:
            return await ctx.send(f"There seems to have been an issue getting the code for this upload. Please check <#586728153985056801> to confirm upload. If it didn't upload, try again later. {self.bot.creator.mention} and {self.bot.allen.mention} please investigate!")
        elif r[0] == 400:
            return await ctx.send("That file is either not a pokemon, or something went wrong.")
        elif r[0] == 413:
            return await ctx.send(f"That file is too large. {self.bot.pie.mention} and {self.bot.allen.mention}, please investigate.")
        elif r[0] == 503:
            return await ctx.send("GPSS uploading is currently disabled. Please try again later.")
        elif r[0] == 200:
            return await ctx.send(f"The provided pokemon has already been uploaded. You can find it at: {self.bot.gpss_url}gpss/view/{code}")
        await ctx.send(f"Your pokemon has been uploaded! You can find it at: {self.bot.gpss_url}gpss/view/{code}")

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def legalize(self, ctx, data=""):
        """Legalizes a pokemon as much as possible. Takes a provided URL or attached pkx file. URL *must* be a direct download link"""
        if not data and not ctx.message.attachments:
            raise PKHeXMissingArgs()
        upload_channel = await self.bot.fetch_channel(664548059253964847)  # Points to #legalize-log on FlagBrew
        if not await self.ping_api_func() == 200:
            return await ctx.send("The CoreAPI server is currently down, and as such no commands in the PKHeX module can be used.")
        msg = await ctx.send("Attempting to legalize pokemon...")
        r = await self.process_file(ctx, data, ctx.message.attachments, "api/v1/bot/auto_legality")
        if r == 400:
            return
        elif r[0] == 503:
            return await msg.edit(content="Legalizing is currently disabled in CoreAPI, and as such this command cannot be used currently.")
        rj = r[1]
        if not rj["ran"]:
            return await msg.edit(content="That pokemon is already legal!")
        elif not rj["success"]:
            return await msg.edit(content="That pokemon couldn't be legalized!")
        pokemon_b64 = rj["pokemon"].encode("ascii")
        qr_b64 = rj["qr"].encode("ascii")
        pokemon_decoded = base64.decodebytes(pokemon_b64)
        qr_decoded = base64.decodebytes(qr_b64)
        if data:
            filename = os.path.basename(urllib.parse.urlparse(data).path)
        else:
            filename = ctx.message.attachments[0].filename
        pokemon = discord.File(io.BytesIO(pokemon_decoded), "fixed-" + filename)
        qr = discord.File(io.BytesIO(qr_decoded), 'pokemon_qr.png')
        m = await upload_channel.send(f"Pokemon legalized by {ctx.author}", file=pokemon)
        embed = discord.Embed(title=f"Fixed Legality Issues for {rj['species']}", description=f"[Download link]({m.attachments[0].url})\n")
        embed = self.list_to_embed(embed, rj["report"])
        embed.set_thumbnail(url="attachment://pokemon_qr.png")
        await msg.delete()
        await ctx.send(embed=embed, file=qr)

    @commands.command(enabled=True)
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    @restricted_to_bot
    async def convert(self, ctx, gen: int, *, showdown_set):
        """Converts a given showdown set into a pkx from a given generation. WIP."""
        if not gen in range(1, 9):
            return await ctx.send(f"There is no generation {gen}.")
        showdown_set = showdown_set.replace('`', '')
        upload_channel = await self.bot.fetch_channel(664548059253964847)  # Points to #legalize-log on FlagBrew
        url = self.bot.api_url + "api/showdown"
        data = {
            "set": showdown_set,
            "generation": str(gen)
        }
        async with self.bot.session.post(url=url, data=data) as r:
            if r.status == 400:
                message = await r.json()
                message = message["message"]
                if message == "Your Pokemon does not exist!":
                    return await ctx.send(f"{ctx.author} That pokemon doesn't exist!")
                else:
                    return await ctx.send(f"{ctx.author} Conversion failed with error code `{r.status}` and message:\n`{message}`")
            elif not r.status == 200:
                    return await ctx.send(f"{ctx.author} Conversion failed with error code `{r.status}`.")
            rj = await r.json()
            pk64 = rj["Base64"].encode("ascii")
            pkx = base64.decodebytes(pk64)
            qr64 = rj["QR"].encode("ascii")
            qr = base64.decodebytes(qr64)
        embed = discord.Embed(title=f"Data for {rj['Nickname']}")
        embed.set_thumbnail(url=rj["SpeciesSpriteURL"])
        embed = self.embed_fields(ctx, embed, rj, is_set=True)
        pokemon_file = discord.File(io.BytesIO(pkx), "showdownset.pk" + str(gen))
        qr_file = discord.File(io.BytesIO(qr), "qrcode.png")
        m = await upload_channel.send(f"Showdown set converted by {ctx.author}", files=[pokemon_file, qr_file])
        embed.description = f"[PKX Download Link]({m.attachments[0].url})\n[QR Code]({m.attachments[1].url})"
        embed.colour = discord.Colour.green() if rj["IllegalReasons"] == "Legal!" else discord.Colour.red()
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(pkhex(bot))
