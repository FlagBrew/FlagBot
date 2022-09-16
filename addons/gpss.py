import discord
import asyncio
import aiohttp
import io
import base64
import validators
from exceptions import PKHeXMissingArgs
from addons.helper import restricted_to_bot
from discord.ext import commands


class gpss(commands.Cog):

    """Handles all the GPSS related commands. Does not load if api_url is not defined in config"""

    def __init__(self, bot):
        self.bot = bot
        print(f'Addon "{self.__class__.__name__}" loaded')

    @commands.command(name="gpssfetch", aliases=['gpssfind', 'gpsssearch'])
    async def gpss_lookup(self, ctx, code):
        """Looks up a pokemon from the GPSS using its download code"""
        if not code.isdigit():
            return await ctx.send("GPSS codes are solely comprised of numbers. Please try again.")
        async with self.bot.session.get(self.bot.flagbrew_url) as resp:
            if not resp.status == 200:
                return await ctx.send("I could not make a connection to flagbrew.org, so this command cannot be used currently.")
        upload_channel = await self.bot.fetch_channel(664548059253964847)  # Points to #legalize-log on FlagBrew
        msg = await ctx.send("Attempting to fetch pokemon...")
        try:
            async with self.bot.session.get(self.bot.flagbrew_url + "api/v2/gpss/view/" + code) as resp:
                resp_json = await resp.json()
                code_data = resp_json["pokemon"]
                pkmn_data = code_data["pokemon"]
                filename = pkmn_data["species"] + f" Code_{code}"
                if pkmn_data["generation"] == "LGPE":
                    filename += ".pb7"
                elif pkmn_data["generation"] == "BDSP":
                    filename += ".pb8"
                elif pkmn_data["generation"] == "PLA":
                    filename += ".pa8"
                else:
                    filename += ".pk" + pkmn_data["generation"]
                pk64 = code_data["base_64"].encode("ascii")
                pkx = base64.decodebytes(pk64)
                pkmn_file = discord.File(io.BytesIO(pkx), filename)
                await asyncio.sleep(1)
                log_msg = await upload_channel.send(f"Pokemon fetched from the GPSS by {ctx.author}", file=pkmn_file)
                embed = discord.Embed(description=f"[GPSS Page]({self.bot.gpss_url + 'gpss/' + code}) | [Download link]({log_msg.attachments[0].url})")
                embed.add_field(name="Species", value=pkmn_data["species"])
                embed.add_field(name="Level", value=pkmn_data["level"])
                embed.add_field(name="Nature", value=pkmn_data["nature"])
                if (pkmn_data["generation"].lower() in ('bdsp', 'pla', 'lgpe')) or int(pkmn_data["generation"]) > 2:
                    embed.add_field(name="Ability", value=pkmn_data["ability"])
                else:
                    embed.add_field(name="Ability", value="N/A")
                ot = pkmn_data["ot"]
                sid = pkmn_data["sid"]
                tid = pkmn_data["tid"]
                if (pkmn_data["generation"].lower() in ('bdsp', 'pla', 'lgpe')) or int(pkmn_data["generation"]) > 2:
                    embed.add_field(name="Original Trainer", value=f"{ot}\n({tid}/{sid})")
                else:
                    embed.add_field(name="Original Trainer", value=f"{ot}\n({tid})")
                if "ht" in pkmn_data.keys() and not pkmn_data["ht"] == "":
                    embed.add_field(name="Handling Trainer", value=pkmn_data["ht"])
                else:
                    embed.add_field(name="Handling Trainer", value="N/A")
                if ((pkmn_data["generation"].lower() in ('bdsp', 'pla', 'lgpe')) or int(pkmn_data["generation"]) > 2) and not pkmn_data["met_loc"] == "":
                    embed.add_field(name="Met Location", value=pkmn_data["met_loc"])
                else:
                    embed.add_field(name="Met Location", value="N/A")
                if (pkmn_data["generation"].lower() in ('bdsp', 'pla', 'lgpe')) or int(pkmn_data["generation"]) > 2:
                    if pkmn_data["version"] == "":
                        return await ctx.send(f"Something in that pokemon is *very* wrong. Please do not try to check that code again.\n\n{self.bot.pie.mention}: Mon was gen3+ and missing origin game. Code: `{code}`")
                    embed.add_field(name="Origin Game", value=pkmn_data["version"])
                else:
                    embed.add_field(name="Origin Game", value="N/A")
                embed.add_field(name="Captured In", value=pkmn_data["ball"])
                if pkmn_data["held_item"] != "(None)":
                    embed.add_field(name="Held Item", value=pkmn_data["held_item"])
                stats = pkmn_data["stats"]
                embed.add_field(name="EVs", value=f"**HP**: {stats[0]['stat_ev']}\n**Atk**: {stats[1]['stat_ev']}\n**Def**: {stats[2]['stat_ev']}\n**SpAtk**: {stats[3]['stat_ev']}\n**SpDef**: {stats[4]['stat_ev']}\n**Spd**: {stats[5]['stat_ev']}")
                embed.add_field(name="IVs", value=f"**HP**: {stats[0]['stat_iv']}\n**Atk**: {stats[1]['stat_iv']}\n**Def**: {stats[2]['stat_iv']}\n**SpAtk**: {stats[3]['stat_iv']}\n**SpDef**: {stats[4]['stat_iv']}\n**Spd**: {stats[5]['stat_iv']}")
                moves = pkmn_data["moves"]
                embed.add_field(name="Moves", value=f"**1**: {moves[0]['move_name']}\n**2**: {moves[1]['move_name']}\n**3**: {moves[2]['move_name']}\n**4**: {moves[3]['move_name']}")
                embed.title = f"Data for {pkmn_data['nickname']} ({pkmn_data['gender']})"
                embed.set_thumbnail(url=pkmn_data["species_sprite_url"])
                return await msg.edit(embed=embed, content=None)
        except aiohttp.ContentTypeError:
            await msg.edit(content=f"There was no pokemon on the GPSS with the code `{code}`.")

    @commands.command(name="gpsspost", aliases=['gpssupload'])
    @restricted_to_bot
    async def gpss_upload(self, ctx, data=""):
        """Allows uploading a pokemon to the GPSS. Takes a provided URL or attached pkx file. URL *must* be a direct download link"""
        if self.bot.gpss_banned_role in ctx.author.roles:
            raise commands.errors.CheckFailure()
            return
        if not data and not ctx.message.attachments:
            raise PKHeXMissingArgs()
        async with self.bot.session.get(self.bot.flagbrew_url) as resp:
            if not resp.status == 200:
                return await ctx.send("I could not make a connection to flagbrew.org, so this command cannot be used currently.")
        if not data:
            atch = ctx.message.attachments[0]
            if atch.size > 400:
                await ctx.send("The attached file was too large.")
                return
            io_bytes = io.BytesIO()
            try:
                await atch.save(io_bytes)
            except discord.Forbidden:
                await ctx.send("The file seems to have been deleted, so I can't complete the task.")
                return
            file = io_bytes.getvalue()
        else:
            if not validators.url(data):
                await ctx.send("That's not a real link!")
                return
            elif data.strip("?raw=true")[-4:-1] not in (".pk", ".pb", ".pa"):
                await ctx.send("That isn't a valid pkx, pbx, or pa8 file!")
                return
            try:
                async with self.bot.session.get(data) as resp:
                    file = io.BytesIO(await resp.read())
            except aiohttp.InvalidURL:
                await ctx.send("The provided data was not valid.")
                return
        url = self.bot.flagbrew_url + "api/v2/gpss/upload/pokemon"
        files = {'pkmn': file}
        headers = {'discord-user': str(ctx.author.id), 'secret': self.bot.site_secret, 'source': "FlagBot"}
        async with self.bot.session.post(url=url, data=files, headers=headers) as resp:
            if resp.status == 503:
                return await ctx.send("GPSS uploading is currently disabled. Please try again later.")
            try:
                resp_json = await resp.json()
            except aiohttp.client_exceptions.ContentTypeError:
                resp_json = {}
            content = await resp.content.read()
            if content == b'':
                content = await resp.read()
            if content == b'':
                await ctx.send(f"Couldn't get response content. {self.bot.creator.mention} and {self.bot.allen.mention} please investigate!")
                await ctx.send(content)
                return
            try:
                code = resp_json['code']
                uploaded = resp_json['uploaded']
                approved = resp_json['approved']
            except KeyError as e:
                if not e.args[0] == "approved":
                    return await ctx.send(f"JSON content was empty on the response.\nStatus: {resp[0]}\nContent: {resp.status}")
                approved = True
        if not uploaded:
            error = resp_json['error']
            if error == "Failed to get pkmn info from CoreAPI, error details: There is an error in your provided information!":
                return await ctx.send("That file is either not a pokemon, or something went wrong.")
            elif error == "Your Pokemon is already uploaded":
                return await ctx.send(f"The provided pokemon has already been uploaded. You can find it at: {self.bot.gpss_url}gpss/{code}")
            else:
                await ctx.send(f"There seems to have been an issue getting the code for this upload. Please check <#586728153985056801> to confirm upload. If it didn't upload, try again later. {self.bot.creator.mention} and {self.bot.allen.mention} please investigate!")
                return await self.bot.err_logs_channel.send(f"Error processing GPSS upload in {ctx.channel.mention}. Code length greater than 10. Code: `{code}`")
        elif not approved:
            return await ctx.send(f"Your pokemon has been uploaded, but currently is waiting on approval. If it is approved, you can find it at: {self.bot.gpss_url}gpss/{code}")
        await ctx.send(f"Your pokemon has been uploaded! You can find it at: {self.bot.gpss_url}gpss/{code}")


async def setup(bot):
    await bot.add_cog(gpss(bot))
