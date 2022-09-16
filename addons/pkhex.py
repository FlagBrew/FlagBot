import discord
import aiohttp
import io
import base64
import validators
import os
import urllib
import inspect
import segno
from exceptions import PKHeXMissingArgs
import addons.helper as helper
import addons.pkhex_cores.encounters as encounters_module
import addons.pkhex_cores.pokeinfo as pokeinfo_module
import addons.pkhex_cores.legality as legality_module
from addons.helper import restricted_to_bot
from discord.ext import commands


class pkhex(commands.Cog):

    """Handles all the PKHeX and ALM Core related commands. Does not load if api_url is not defined in config"""

    def __init__(self, bot):
        self.bot = bot
        print(f'Addon "{self.__class__.__name__}" loaded')

    async def process_file(self, ctx, data, attachments, func):
        if not data and not attachments:
            await ctx.send("Error: No data was provided and no pkx file was attached.")
            return 400
        elif not data:
            atch = attachments[0]
            if atch.size > 400:
                await ctx.send("The attached file was too large.")
                return 400
            io_bytes = io.BytesIO()
            try:
                await atch.save(io_bytes)
            except discord.Forbidden:
                await ctx.send("The file seems to have been deleted, so I can't complete the task.")
                return 400
            file = io_bytes.getvalue()
        else:
            if not validators.url(data):
                await ctx.send("That's not a real link!")
                return 400
            elif data.strip("?raw=true")[-4:-1] not in (".pk", ".pb", ".pa"):
                await ctx.send("That isn't a valid pkx, pbx, or pa8 file!")
                return 400
            try:
                async with self.bot.session.get(data) as resp:
                    file = io.BytesIO(await resp.read()).getvalue()
            except aiohttp.InvalidURL:
                await ctx.send("The provided data was not valid.")
                return 400
        if func == "pokemon_info":
            return_data = pokeinfo_module.get_pokemon_file_info(file)
        elif func == "generate_qr":
            return_data = pokeinfo_module.generate_qr(file)
        elif func == "legality_check":
            return_data = legality_module.get_legality_report(file)
        elif func == "legalize":
            return_data = legality_module.legalize_pokemon(file)
        if return_data == 200:
            await ctx.send("That Pokemon is legal!")
            return 400
        elif return_data == 201:
            await ctx.send("That pokemon could not be analyzed for some reason.")
            return 400
        elif return_data == 202:
            await ctx.send("That pokemon could not be legalized.")
            return 400
        elif return_data == 400:
            await ctx.send("The provided file was invalid.")
            return 400
        elif return_data == 500:
            await ctx.send("Pokemon does not exist in generation.")
            return 400
        elif return_data == 501:
            await ctx.send("This command does not support that generation.")
            return 400
        return return_data

    def embed_fields(self, embed, data):
        embed.add_field(name="Species", value=data["species"])
        embed.add_field(name="Level", value=data["level"])
        embed.add_field(name="Nature", value=data["nature"])
        if (data["generation"].lower() in ('bdsp', 'pla', 'lgpe')) or int(data["generation"]) > 2:
            embed.add_field(name="Ability", value=data["ability"])
        else:
            embed.add_field(name="Ability", value="N/A")
        ot = data["ot"]
        sid = data["sid"]
        tid = data["tid"]
        if (data["generation"].lower() in ('bdsp', 'pla', 'lgpe')) or int(data["generation"]) > 2:
            embed.add_field(name="Original Trainer", value=f"{ot}\n({tid}/{sid})")
        else:
            embed.add_field(name="Original Trainer", value=f"{ot}\n({tid})")
        if "ht" in data.keys() and not data["ht"] == "":
            embed.add_field(name="Handling Trainer", value=data["ht"])
        if ((data["generation"].lower() in ('bdsp', 'pla', 'lgpe')) or int(data["generation"]) > 2) and not data["met_loc"] == "":
            embed.add_field(name="Met Location", value=data["met_loc"])
        if (data["generation"].lower() in ('bdsp', 'pla', 'lgpe')) or int(data["generation"]) > 2:
            if data["version"] == "":
                return 400
            embed.add_field(name="Origin Game", value=data["version"])
        else:
            embed.add_field(name="Origin Game", value="N/A")
        embed.add_field(name="Captured In", value=data["ball"])
        if data["held_item"] != "(None)":
            embed.add_field(name="Held Item", value=data["held_item"])
        stats = data["stats"]
        embed.add_field(name="EVs", value=f"**HP**: {stats[0]['ev']}\n**Atk**: {stats[1]['ev']}\n**Def**: {stats[2]['ev']}\n**SpAtk**: {stats[3]['ev']}\n**SpDef**: {stats[4]['ev']}\n**Spd**: {stats[5]['ev']}")
        embed.add_field(name="IVs", value=f"**HP**: {stats[0]['iv']}\n**Atk**: {stats[1]['iv']}\n**Def**: {stats[2]['iv']}\n**SpAtk**: {stats[3]['iv']}\n**SpDef**: {stats[4]['iv']}\n**Spd**: {stats[5]['iv']}")
        moves = data["moves"]
        embed.add_field(name="Moves", value=f"**1**: {moves[0]}\n**2**: {moves[1]}\n**3**: {moves[2]}\n**4**: {moves[3]}")
        return embed

    def list_to_embed(self, embed, input_list):
        for x in input_list:
            values = x.split(": ")
            values[0] = "**" + values[0] + "**: "
            val = ""
            for x in values[1:]:
                val += x + " "
            embed.description += values[0] + val + "\n"
        return embed

    @commands.command(name='legality', aliases=['illegal'])
    async def check_legality(self, ctx, *, data=""):
        """Checks the legality of either a provided URL or attached pkx file. URL *must* be a direct download link"""
        legality = await self.process_file(ctx, data, ctx.message.attachments, "legality_check")
        if legality == 400:
            return
        embed = discord.Embed(title="Legality Issues", description="", colour=discord.Colour.red())
        embed = self.list_to_embed(embed, legality)
        await ctx.send(embed=embed)

    @commands.command(name='forms')
    async def check_forms(self, ctx, pokemon):
        """Returns a list of a given Pokemon's forms."""
        forms = pokeinfo_module.get_pokemon_forms(pokemon.capitalize())
        if forms == 400:
            return await ctx.send("Are you sure that's a real pokemon?")
        elif len(forms) == 0:
            return await ctx.send(f"No forms available for `{pokemon.capitalize()}`.")
        await ctx.send(f"Available forms for {pokemon.capitalize()}: `{'`, `'.join(forms)}`.")

    @commands.command(name='pokeinfo', aliases=['pi'])
    @restricted_to_bot
    async def poke_info(self, ctx, species_form_pair_or_url: str = "", generation: str = None, shiny: bool = False):
        ("""Returns an embed with a Pokemon's nickname, species, and a few others. Takes a provided URL or attached pkx file. URL *must* be a direct download link.
         Alternatively can take a single Pokemon as an entry, and will return basic information on the species. 'generation' must be passed for this, shiny is bool.""")

        # Get info for inputted pokemon
        if not validators.url(species_form_pair_or_url) and not ctx.message.attachments:
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
            if not generation:
                raise commands.MissingRequiredArgument((inspect.Parameter(name='generation', kind=inspect.Parameter.POSITIONAL_ONLY)))
            try:
                int(generation)
            except ValueError:
                if generation.lower() not in ("bdsp", "pla", "lgpe"):
                    return await ctx.send(f"There is no generation {generation}.")
            except TypeError:
                raise commands.MissingRequiredArgument((inspect.Parameter(name='generation', kind=inspect.Parameter.POSITIONAL_ONLY)))
            else:
                if int(generation) not in range(1, 9):
                    return await ctx.send(f"There is no generation {generation}.")
            species_form_pair_or_url = species_form_pair_or_url.split('-')
            pokemon = "flabébé" if species_form_pair_or_url[0].lower() == "flabebe" else species_form_pair_or_url[0].lower()
            form = None
            if pokemon in helper.default_forms.keys():
                form = helper.default_forms[pokemon]
            if len(species_form_pair_or_url) > 1:
                form = species_form_pair_or_url[1].lower()
            elif form == "female":
                form = "f"
            pokeinfo = pokeinfo_module.get_base_info(pokemon.capitalize(), form.capitalize() if form else form, generation.upper(), shiny)
            if pokeinfo == 400:
                return await ctx.send("Are you sure that's a real pokemon (or proper form)?")
            embed = discord.Embed(colour=colours[pokeinfo["colour"]])
            type_str = f"Type 1: {pokeinfo['types'][0]}"
            if pokeinfo["types"][1] is not None:
                type_str += f"\nType 2: {pokeinfo['types'][1]}"
            embed.add_field(name="Types", value=type_str)
            ability_str = f"Ability (1): {pokeinfo['ability1']}"
            if not pokeinfo["ability2"] == pokeinfo["ability1"]:
                ability_str += f"\nAbility (2): {pokeinfo['ability2']}"
            if pokeinfo["ability_h"] is not None:
                ability_str += f"\nAbility (H): {pokeinfo['ability_h']}"
            embed.add_field(name="Abilities", value=ability_str)
            embed.add_field(name="Height & Weight", value=f"{pokeinfo['height'] / 100} meters\n{pokeinfo['weight'] / 10} kilograms")
            if pokeinfo["is_dual_gender"]:
                ratio = (pokeinfo["gender"] / 254) * 100
                ratio = round(ratio, 2)
                embed.add_field(name="Gender Ratio", value=f"~{ratio}% Female")
            else:
                embed.add_field(name="Gender", value="Genderless" if pokeinfo["is_genderless"] else "Female" if pokeinfo["only_female"] else "Male")
            embed.add_field(name="EXP Growth", value=pokeinfo["exp_growth"])
            embed.add_field(name="Evolution Stage", value=pokeinfo["evo_stage"])
            embed.add_field(name="Hatch Cycles", value=pokeinfo["hatch_cycles"])
            embed.add_field(name="Base Friendship", value=pokeinfo["base_friendship"])
            embed.add_field(name="Catch Rate", value=f"{pokeinfo['catch_rate']}/255")
            egg_str = f"Egg Group 1: {pokeinfo['egg_groups'][0]}"
            if len(pokeinfo["egg_groups"]) > 1 and pokeinfo["egg_groups"][1] != pokeinfo["egg_groups"][0]:
                egg_str += f"\nEgg Group 2: {pokeinfo['egg_groups'][1]}"
            embed.add_field(name="Egg Groups", value=egg_str)
            embed.add_field(name=f"Base stats ({pokeinfo['bst']})", value=f"```HP:    {pokeinfo['hp']} Atk:   {pokeinfo['atk']}\nDef:   {pokeinfo['def']} SpAtk: {pokeinfo['spa']} \nSpDef: {pokeinfo['spd']} Spd:   {pokeinfo['spe']}```")
            embed.title = f"Basic info for {pokemon.title()}{'-' + form.title() if form else ''} in Generation {generation.upper()}"
            embed.set_thumbnail(url=pokeinfo['species_sprite_url'])
            return await ctx.send(embed=embed)

        # Get info for inputted file
        pokeinfo = await self.process_file(ctx, species_form_pair_or_url, ctx.message.attachments, "pokemon_info")
        if pokeinfo == 400:
            return
        embed = discord.Embed()
        embed = self.embed_fields(embed, pokeinfo)
        if embed == 400:
            return await ctx.send(f"{ctx.author.mention} Something in that pokemon is *very* wrong. Your request has been canceled. Please do not try that mon again.")
        embed.title = f"Data for {pokeinfo['nickname']} ({pokeinfo['gender']})"
        embed.set_thumbnail(url=pokeinfo["species_sprite_url"])
        embed.colour = discord.Colour.green() if pokeinfo["is_legal"] else discord.Colour.red()
        try:
            await ctx.send(embed=embed)
        except Exception as exception:
            return await ctx.send(f"There was an error showing the data for this pokemon. {self.bot.creator.mention}, {self.bot.pie.mention}, or {self.bot.allen.mention} please check this out!\n{ctx.author.mention} please do not delete the file. Exception below.\n\n```{exception}```")

    @commands.command(name='qr')
    @restricted_to_bot
    async def gen_pkmn_qr(self, ctx, data=""):
        """Gens a QR code that PKSM can read. Takes a provided URL or attached pkx file. URL *must* be a direct download link. Only Generations 3 through 6 are supported
        Can also be used to generate a QR code for a GPSS code. Example: .qr 5782149727 --> QR for https://flagbrew.org/gpss/5782149727"""
        try:
            int(data)
        except ValueError:
            pokeinfo = await self.process_file(ctx, data, ctx.message.attachments, "generate_qr")
            if pokeinfo == 400:
                return
            send_message = f"QR containing a {pokeinfo[1].title()} for Generation {pokeinfo[2].title()}"
        else:
            qr = segno.make_qr(data)
            bytes = io.BytesIO()
            qr.save(bytes, kind='PNG', scale=8)
            pokeinfo = [bytes.getvalue()]
            send_message = f"QR for GPSS Code {data}"
        qr = discord.File(io.BytesIO(pokeinfo[0]), 'pokemon_qr.png')
        await ctx.send(send_message, file=qr)

    @commands.command(name='learns', aliases=['learn'])
    async def check_moves(self, ctx, pokemon, *, moves):
        """Checks if a given pokemon can learn provided moves. Separate move data using pipes.
        Example: .learns pikachu | quick attack | hail"""
        moves = moves.replace("| ", "|").replace(" |", "|").replace(" | ", "|")
        moves = moves.split("|")
        if not moves:
            return await ctx.send("No moves provided, or the data provided was in an incorrect format.\n```Example: .learns pikachu | quick attack | hail```")
        learnables = encounters_module.get_moves(pokemon.capitalize(), moves)
        if learnables == 400:
            return await ctx.send("Something you sent was invalid. Please double check your data and try again.")
        elif learnables == 500:
            return await ctx.send("No moves included could be resolved.")
        embed = discord.Embed(title=f"Move Lookup for {pokemon.title()}", description="")
        for move in learnables:
            embed.description += f"**{move['name']}** is {'not ' if not move['learnable'] else ''}learnable.\n"
        await ctx.send(embed=embed)

    @commands.command(name='find')
    async def check_encounters(self, ctx, generation: str, pokemon, *, moves: str = None):
        """Outputs the locations a given pokemon can be found, possibly with provided moves. Separate move data using pipes. Provided moves must be legal, can be checked with .learns
            Example: .find 6 pikachu | volt tackle"""
        try:
            int(generation)
        except ValueError:
            if generation.lower() not in ("bdsp", "pla", "lgpe"):
                return await ctx.send(f"There is no generation {generation}.")
        else:
            if int(generation) not in range(1, 9):
                return await ctx.send(f"There is no generation {generation}.")
        if moves:
            moves = moves.replace("| ", "|").replace(" |", "|").replace(" | ", "|")
            moves = moves.split("|")
        encounters = encounters_module.get_encounters(pokemon.capitalize(), generation.upper(), moves)
        if encounters == 400:
            return await ctx.send("Something you sent was invalid. Please double check your data and try again.")
        elif encounters == 500:
            return await ctx.send(f"Could not find matching encounter data for {pokemon.title()} in Generation {generation.upper()}{' with move(s) ' if moves else ''}{', '.join([move.title() for move in moves]) if moves else ''}.")
        embed = discord.Embed(title=f"Encounter Data for {pokemon.title()} in Generation {generation.upper()}{' with move(s) ' if moves else ''}{', '.join([move.title() for move in moves]) if moves else ''}")
        for encounter in encounters:
            field_values = ""
            for location in encounter["location"]:
                games = (helper.game_dict[x] if x in helper.game_dict.keys() else x for x in location["games"])
                games_str = ", ".join(games)
                games_str = games_str.replace("GG", "LGPE")
                if encounter["encounter_type"] == "Egg":
                    field_values += f"{games_str} as **egg**.\n"
                elif not location["name"] == "":
                    field_values += f"{games_str} in **{location['name']}**.\n"
                elif generation == 1:
                    field_values += f"{games_str} in **Unknown**.\n"
                    embed.set_footer(text="Please ask Kurt#6024 to add route names to gen 1 location data")
            if field_values:
                embed.add_field(name=f"As {encounter['encounter_type']}", value=field_values, inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def legalize(self, ctx, data=""):
        """Legalizes a pokemon as much as possible. Takes a provided URL or attached pkx file. URL *must* be a direct download link"""
        upload_channel = await self.bot.fetch_channel(664548059253964847)  # Points to #legalize-log on FlagBrew
        msg = await ctx.send("Attempting to legalize pokemon...")
        legalized = await self.process_file(ctx, data, ctx.message.attachments, "legalize")
        if legalized == 400:
            return
        pokemon_decoded = base64.b64decode(legalized["pokemon"])
        if data:
            filename = os.path.basename(urllib.parse.urlparse(data).path)
        else:
            filename = ctx.message.attachments[0].filename
        pokemon = discord.File(io.BytesIO(pokemon_decoded), "fixed-" + filename)
        qr = discord.File(io.BytesIO(legalized["qr"]), 'pokemon_qr.png')
        log_msg = await upload_channel.send(f"Pokemon legalized by {ctx.author}", file=pokemon)
        embed = discord.Embed(title=f"Fixed Legality Issues for {legalized['species']}", description=f"[Download link]({log_msg.attachments[0].url})\n")
        embed = self.list_to_embed(embed, legalized["report"])
        embed.set_thumbnail(url="attachment://pokemon_qr.png")
        await msg.delete()
        await ctx.send(embed=embed, file=qr)

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    @restricted_to_bot
    async def convert(self, ctx, generation: str, *, showdown_set):
        """Converts a given showdown set into a pkx from a given generation. WIP."""
        try:
            int(generation)
        except ValueError:
            if generation.lower() not in ("bdsp", "pla", "lgpe"):
                return await ctx.send(f"There is no generation {generation}.")
        else:
            if int(generation) not in range(1, 9):
                return await ctx.send(f"There is no generation {generation}.")
        showdown_set = showdown_set.replace('`', '')
        upload_channel = await self.bot.fetch_channel(664548059253964847)  # Points to #legalize-log on FlagBrew
        converted = legality_module.convert_pokemon(showdown_set, generation.upper())
        if converted["status"] == 400:
            await ctx.send(f"Converting that set failed, meaning it is likely illegal. Please review your set.\n```{converted['analysis']}```")
        pokemon_decoded = base64.b64decode(converted["pokemon"])
        file_extension = (".pb7" if generation.lower() == "lgpe" else ".pb8" if generation.lower() == "bdsp" else ".pa8" if generation.lower() == "pla" else ".pk" + generation)
        pokemon_file = discord.File(io.BytesIO(pokemon_decoded), "showdownset" + file_extension)
        qr = discord.File(io.BytesIO(converted["qr"]), 'pokemon_qr.png')
        embed = discord.Embed(title=f"Data for {converted['nickname']} ({converted['gender']})")
        embed.set_thumbnail(url=converted["species_sprite_url"])
        embed = self.embed_fields(embed, converted)
        log_msg = await upload_channel.send(f"Showdown set converted by {ctx.author}", files=[pokemon_file, qr])
        embed.description = f"[{'PB7' if generation.lower() == 'lgpe' else 'PB8' if generation.lower() == 'bdsp' else 'PA8' if generation.lower() == 'pla' else 'PK' + generation} Download Link]({log_msg.attachments[0].url})\n[QR Code]({log_msg.attachments[1].url})"
        embed.colour = discord.Colour.green() if converted["is_legal"] else discord.Colour.red()
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(pkhex(bot))
