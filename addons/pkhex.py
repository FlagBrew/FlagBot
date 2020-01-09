import discord
import asyncio
import aiohttp
import io
import json
import base64
import validators
import os
import urllib
from exceptions import APIConnectionError
from datetime import datetime
from discord.ext import commands

class pkhex(commands.Cog):

    """Handles all the PKHeX Related Commands. Does not load if api_url is not defined in config"""

    def __init__(self, bot):
        self.bot = bot
        raise APIConnectionError("Connection not established")
        print('Addon "{}" loaded'.format(self.__class__.__name__))

    async def ping_api(self):
        async with self.bot.session.get(self.bot.api_url + "api/v1/bot/ping") as r:
            return r.status

    async def process_file(self, ctx, data, attachments, url, is_gpss=False):
        if not data and not attachments:
            await ctx.send("Error: No data was provided and no pkx file was attached.")
            return 400
        elif not data:
            atch = attachments[0]
            if atch.size > 400:
                await ctx.send("The attached file was too large.")
                return 400
            b = io.BytesIO()
            await atch.save(b)
            file = b.getvalue()
        else:
            if not validators.url(data):
                await ctx.send("That's not a real link!")
                return 400
            elif not data[-4:-1] == ".pk":
                await ctx.send("That isn't a pkx file!")
                return 400
            try:
                async with self.bot.session.get(data) as r:
                    file = io.BytesIO(await r.read())
            except aiohttp.client_exceptions.InvalidURL:
                await ctx.send("The provided data was not valid.")
                return 400
        url = self.bot.api_url + url
        files = {'pkmn': file}
        async with self.bot.session.post(url=url, data=files) as r:
            if not is_gpss and (r.status == 400 or r.status == 413):
                await ctx.send("The provided file was invalid.")
                return 400
            try:
                rj = await r.json()
            except aiohttp.client_exceptions.ContentTypeError:
                rj = {}
            content = await r.content.read()
            if content is b'':
                content = await r.read()
            if content is b'':
                await ctx.send("Couldn't get response content. {} and {} please investigate!".format(self.bot.creator.mention, self.bot.allen.mention))
                return 400
            return [r.status, rj, content]

    def embed_fields(self, ctx, embed, data):
        embed.add_field(name="Species", value=data["Species"])
        embed.add_field(name="Level", value=data["Level"])
        embed.add_field(name="Nature", value=data["Nature"])
        if int(data["Generation"]) > 2:
            embed.add_field(name="Ability", value=data["Ability"])
        else:
            embed.add_field(name="Ability", value="N/A")
        embed.add_field(name="Original Trainer", value=data["OT"])
        embed.add_field(name="Handling Trainer", value=data["HT"])
        if int(data["Generation"]) > 2 and not data["MetLoc"] is "":
            embed.add_field(name="Met Location", value=data["MetLoc"])
        else:
            embed.add_field(name="Met Location", value="N/A")
        if int(data["Generation"]) > 2:
            embed.add_field(name="Origin Game", value=data["Version"])
        else:
            embed.add_field(name="Origin Game", value="N/A")
        embed.add_field(name="Captured In", value=data["Ball"])
        embed.add_field(name="EVs", value="**HP**: {}\n**Atk**: {}\n**Def**: {}\n**SpAtk**: {}\n**SpDef**: {}\n**Spd**: {}".format(data["HP_EV"], data["ATK_EV"], data["DEF_EV"], data["SPA_EV"], data["SPD_EV"], data["SPE_EV"]))
        embed.add_field(name="IVs", value="**HP**: {}\n**Atk**: {}\n**Def**: {}\n**SpAtk**: {}\n**SpDef**: {}\n**Spd**: {}".format(data["HP_IV"], data["ATK_IV"], data["DEF_IV"], data["SPA_IV"], data["SPD_IV"], data["SPE_IV"]))
        embed.add_field(name="Moves", value="**1**: {}\n**2**: {}\n**3**: {}\n**4**: {}".format(data["Move1"], data["Move2"], data["Move3"], data["Move4"]))
        return embed

    def list_to_embed(self, embed, l):
        for x in l:
            values = x.split(": ")
            values[0] = "**" + values[0] + "**: "
            val = ""
            for x in values[1:]:
                val += x + " "
            embed.description += values[0] + val
        return embed

    @commands.command(hidden=True)
    async def ping_cc(self, ctx):
        """Pings the CoreConsole server"""
        if not ctx.author in (self.bot.creator, self.bot.allen):
            raise commands.errors.CheckFailure()
        msgtime = ctx.message.created_at.now()
        r = await self.ping_api() 
        now = datetime.now()
        ping = now - msgtime
        await ctx.send("🏓 CoreConsole response time is {} milliseconds. Current CoreConsole status code is {}.".format(str(ping.microseconds / 1000.0), r))

    @commands.command(name='legality', aliases=['illegal'])
    async def check_legality(self, ctx, *, data=""):
        """Checks the legality of either a provided URL or attached pkx file. URL *must* be a direct download link"""
        if not await self.ping_api() == 200:
            return await ctx.send("The CoreConsole server is currently down, and as such no commands in the PKHeX module can be used.")
        r = await self.process_file(ctx, data, ctx.message.attachments, "api/v1/bot/pkmn_info")
        if r == 400:
            return
        rj = r[1]
        reasons = rj["IllegalReasons"].split("\n")
        if reasons[0] == "Legal!":
            return await ctx.send("That Pokemon is legal!")
        embed = discord.Embed(title="Legality Issues", description="", colour=discord.Colour.red())
        embed = self.list_to_embed(embed, reasons)
        await ctx.send(embed=embed)

    @commands.command(name='pokeinfo')
    async def poke_info(self, ctx, data=""):
        """Returns an embed with a Pokemon's nickname, species, and a few others. Takes a provided URL or attached pkx file. URL *must* be a direct download link"""
        if not await self.ping_api() == 200:
            return await ctx.send("The CoreConsole server is currently down, and as such no commands in the PKHeX module can be used.")
        r = await self.process_file(ctx, data, ctx.message.attachments, "api/v1/bot/pkmn_info")
        if r == 400:
            return
        rj = r[1]
        embed = discord.Embed(title="Data for {}".format(rj["Nickname"]))
        embed = self.embed_fields(ctx, embed, rj)
        embed.set_thumbnail(url=rj["SpeciesSpriteURL"])
        embed.colour = discord.Colour.green() if rj["IllegalReasons"] == "Legal!" else discord.Colour.red()
        try:
            await ctx.send(embed=embed)
        except Exception as e:
            return await ctx.send("There was an error showing the data for this pokemon. {}, {}, or {} please check this out!\n{} please do not delete the file. Exception below.\n\n```{}```".format(self.bot.creator.mention, self.bot.pie.mention, self.bot.allen.mention, ctx.author.mention, e))

    @commands.command(name='qr')
    async def gen_pkmn_qr(self, ctx, data=""):
        """Gens a QR code that PKSM can read. Takes a provided URL or attached pkx file. URL *must* be a direct download link"""
        if not await self.ping_api() == 200:
            return await ctx.send("The CoreConsole server is currently down, and as such no commands in the PKHeX module can be used.")
        r = await self.process_file(ctx, data, ctx.message.attachments, "api/v1/bot/pkmn_qr")
        if r == 400:
            return
        d = await self.process_file(ctx, data, ctx.message.attachments, "api/v1/bot/pkmn_info")
        d = d[1]
        qr = discord.File(io.BytesIO(r[2]), 'pokemon_qr.png')
        await ctx.send("QR containing a {} for Generation {}".format(d["Species"], d["Generation"]), file=qr)

    @commands.command(name='learns', aliases=['learn'])
    async def check_moves(self, ctx, *, input_data):
        """Checks if a given pokemon can learn moves. Separate moves using pipes. Example: .cm pikachu | quick attack | hail"""
        if not await self.ping_api() == 200:
            return await ctx.send("The CoreConsole server is currently down, and as such no commands in the PKHeX module can be used.")
        input_data = input_data.replace("| ", "|").replace(" |", "|").replace(" | ", "|")
        input_data = input_data.split("|")
        pokemon = input_data[0]
        moves = input_data[1:]
        if not moves:
            return await ctx.send("No moves provided, or the data provided was in an incorrect format.\n```Example: .cm pikachu | quick attack | hail```")
        data = {
            "query": pokemon + "|" + "|".join(moves)
        }
        async with self.bot.session.post(self.bot.api_url + "api/v1/bot/query/move_learn", data=data) as r:
            if r.status == 400:
                return await ctx.send("Something you sent was invalid. Please double check your data and try again.")
            rj = await r.json()
            embed = discord.Embed(title="Move Lookup for {}".format(pokemon.title()), description="")
            for move in rj:
                embed.description += "**{}** is {} learnable.\n".format(move["MoveName"].title(), "not" if not move["Learnable"] else "")
            await ctx.send(embed=embed)

    @commands.command(name='find')
    async def check_encounters(self, ctx, generation: int, *, input_data):
        """Outputs the locations a given pokemon can be found. Separate data using pipes. Example: .cm 6 pikachu | volt tackle"""
        if not await self.ping_api() == 200:
            return await ctx.send("The CoreConsole server is currently down, and as such no commands in the PKHeX module can be used.")
        input_data = input_data.replace("| ", "|").replace(" |", "|").replace(" | ", "|")
        input_data = input_data.split("|")
        pokemon = input_data[0]
        moves = input_data[1:]
        data = {
            "query": pokemon + "|" + "|".join(moves)
        }
        async with self.bot.session.post(self.bot.api_url + "api/v1/bot/query/encounter", data=data) as r:
            if r.status == 400:
                return await ctx.send("Something you sent was invalid. Please double check your data and try again.")
            rj = await r.json()
            print(rj)
            embed = discord.Embed(title="Encounter Data for {} in Generation {}{}{}".format(pokemon.title(), generation, " with move(s) " if len(moves) > 0 else "", ", ".join([move.title() for move in moves])))
            generation_data = rj["Gen{}".format(generation)]
            for encs in generation_data:
                locations = {}
                for loc in encs["Locations"]:
                    if loc["Location"] == "":
                        locations[", ".join(loc["Games"])] = "N/A"
                        continue
                    locations[", ".join(loc["Games"])] = loc["Location"]
                field_values = ""
                for location in locations:
                    field_values += "{} in **{}**.\n".format(location, locations[location])
                embed.add_field(name="As {}".format(encs["EncounterType"]), value=field_values, inline=False)
            if len(embed.fields) == 0:
                return await ctx.send("Could not find matching encounter data for {} in Generation {}{}{}.".format(pokemon.title(), generation, " with move(s) " if len(moves) > 0 else "", ", ".join([move.title() for move in moves])))
            await ctx.send(embed=embed)

    @commands.command(name="gpssfetch")
    async def gpss_lookup(self, ctx, code):
        """Looks up a pokemon from the GPSS using its download code"""
        if not code.isdigit():
            return await ctx.send("GPSS codes are solely comprised of numbers. Please try again.")
        async with self.bot.session.get(self.bot.api_url) as r:
            if not r.status == 200:
                return await ctx.send("I could not make a connection to flagbrew.org, so this command cannot be used currently.")
        msg = await ctx.send("Attempting to fetch pokemon...")
        async with self.bot.session.get(self.bot.api_url + "api/v1/gpss/search/" + code) as r:
            rj = await r.json()
            for pkmn in rj["results"]:
                if pkmn["code"] == code:
                    pkmn_data = pkmn["pokemon"]
                    embed = discord.Embed(description="[GPSS Page]({})".format(self.bot.api_url + "gpss/view/" + code))
                    embed = self.embed_fields(ctx, embed, pkmn_data)
                    embed.set_author(icon_url=pkmn_data["SpeciesSpriteURL"], name="Data for {}".format(pkmn_data["Nickname"]))
                    embed.set_thumbnail(url=self.bot.api_url + "gpss/qr/{}".format(code))
                    return await msg.edit(embed=embed, content=None)
        await msg.edit(content="There was no pokemon on the GPSS with the code `{}`.".format(code))

    @commands.command(name="gpsspost")
    async def gpss_upload(self, ctx, data=""):
        """Allows uploading a pokemon to the GPSS. Takes a provided URL or attached pkx file. URL *must* be a direct download link"""
        async with self.bot.session.get(self.bot.api_url) as r:
            if not r.status == 200:
                return await ctx.send("I could not make a connection to flagbrew.org, so this command cannot be used currently.")
        r = await self.process_file(ctx, data, ctx.message.attachments, "gpss/share", True)
        code = str(r[2], encoding='utf-8')
        if r[0] == 400:
            return await ctx.send("That file is either not a pokemon, or something went wrong.")
        elif r[0] == 413:
            return await ctx.send("That file is too large. {} and {}, please investigate.".format(self.bot.pie.mention, self.bot.allen.mention))
        elif r[0] == 503:
            return await ctx.send("GPSS uploading is currently disabled. Please try again later.")
        elif r[0] == 200:
            return await ctx.send("The provided pokemon has already been uploaded. You can find it at: {}gpss/view/{}".format(self.bot.api_url, code))
        await ctx.send("Your pokemon has been uploaded! You can find it at: {}gpss/view/{}".format(self.bot.api_url, code))

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def legalize(self, ctx, data=""):
        """Legalizes a pokemon as much as possible. Takes a provided URL or attached pkx file. URL *must* be a direct download link"""
        upload_channel = await self.bot.fetch_channel(664548059253964847)  # Points to #legalize-file-upload on FlagBrew
        if not await self.ping_api() == 200:
            return await ctx.send("The CoreConsole server is currently down, and as such no commands in the PKHeX module can be used.")
        msg = await ctx.send("Attempting to legalize pokemon...")
        r = await self.process_file(ctx, data, ctx.message.attachments, "api/v1/bot/auto_legality")
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
        m = await upload_channel.send(file=pokemon)
        embed = discord.Embed(title="Fixed Legality Issues for {}".format(rj["species"]), description="[Download link]({})\n".format(m.attachments[0].url))
        embed = self.list_to_embed(embed, rj["report"])
        embed.set_thumbnail(url="attachment://pokemon_qr.png")
        await msg.delete()
        await ctx.send(embed=embed, file=qr)


def setup(bot):
    bot.add_cog(pkhex(bot))
