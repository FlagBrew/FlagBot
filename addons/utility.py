#!/usr/bin/env python3

import discord
from discord.ext import commands
import os
import json
import secrets
import http
import aiohttp
import qrcode
import io
import hashlib
import validators
import lxml.etree
import math
import addons.helper as helper


class Utility(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        if bot.is_mongodb:
            self.db = bot.db
        print(f'Addon "{self.__class__.__name__}" loaded')
        if not os.path.exists('saves/role_mentions.json'):
            with open('saves/role_mentions.json', 'w') as file:
                json.dump({}, file, indent=4)
        with open("saves/role_mentions.json", "r") as file:
            self.role_mentions_dict = json.load(file)
        if not os.path.exists('saves/submitted_hashes.json'):
            data = []
            with open('saves/submitted_hashes.json', 'w') as file:
                json.dump(data, file, indent=4)
        with open("saves/submitted_hashes.json", "r") as file:
            self.submitted_hashes = json.load(file)
        if not os.path.isdir('saves/xmls'):
            os.mkdir('saves/mkdir')

    async def toggleroles(self, ctx, role, user):
        author_roles = user.roles[1:]
        if role not in author_roles:
            await user.add_roles(role)
            return False
        else:
            await user.remove_roles(role)
            return True

    @commands.command()
    @helper.restricted_to_bot
    async def togglerole(self, ctx, role):
        """Allows user to toggle update roles. Available roles: see #welcome-and-rules, as well as 'bot'"""
        user = ctx.message.author
        role = role.lower()
        if role not in ('3ds', 'switch', 'bot'):
            return await ctx.send(f"{user.mention} That isn't a toggleable role!")
        had_role = await self.toggleroles(ctx, discord.utils.get(ctx.guild.roles, id=int(self.role_mentions_dict[role])), user)
        if had_role:
            info_string = f"You will no longer be pinged for {role} updates."
        else:
            info_string = f"You will now receive pings for {role} updates!"
        await ctx.send(user.mention + ' ' + info_string)

    @commands.command(hidden=True)
    @helper.restricted_to_bot
    async def masstoggle(self, ctx):
        """Allows a user to toggle both console update roles"""
        toggle_roles = [
            discord.utils.get(ctx.guild.roles, id=int(self.role_mentions_dict["3ds"])),
            discord.utils.get(ctx.guild.roles, id=int(self.role_mentions_dict["switch"]))
        ]
        user = ctx.message.author
        for role in toggle_roles:
            await self.toggleroles(ctx, role, user)
        await ctx.send(f"{user.mention} Successfully toggled all possible roles.")

    @commands.group(aliases=['srm', 'mention'])
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    async def secure_role_mention(self, ctx):
        """Main handler for SRM commands"""
        if ctx.invoked_subcommand is None:
            return await ctx.send("Possible subcommands: `send`, `list`, `add`, `remove`")

    @secure_role_mention.command(name="send")
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    async def secure_role_message_send(self, ctx, update_role: str, *, message: str):
        """Securely mention a role with a message."""
        if update_role.lower() == "flagbrew":
            role = self.bot.flagbrew_team_role
        else:
            try:
                role = discord.utils.get(ctx.guild.roles, id=int(self.role_mentions_dict[update_role.lower()]))
            except KeyError:
                role = None
        if role is None:
            return await ctx.send("You didn't provide a valid role name. Do `.srm list` to see all available roles.")
        try:
            await role.edit(mentionable=True, reason=f"{ctx.author} wanted to mention users with this role.")  # Reason -> Helps to point out folks that abuse this
        except Exception:
            await role.edit(mentionable=True, reason=f"A staff member wanted to mention users with this role, and I couldn't log properly. Check {self.bot.logs_channel.mention}.")  # Bypass the TypeError it kept throwing
        embed = discord.Embed(description=message)
        embed.set_footer(text=f"Sent by: {ctx.author}")
        await ctx.message.delete()
        await ctx.send(f"{role.mention}", embed=embed)
        await role.edit(mentionable=False, reason="Making role unmentionable again.")
        try:
            await self.bot.logs_channel.send(f"{ctx.author} pinged {role.name} in {ctx.channel} with the following message: ", embed=embed)
        except discord.Forbidden:
            pass  # beta bot can't log

    @secure_role_mention.command(name="list")
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    @helper.restricted_to_bot
    async def secure_role_message_list(self, ctx):
        """Lists all available roles for secure_role_mention"""
        embed = discord.Embed(title="Mentionable Roles")
        combined_list = list(self.role_mentions_dict) + ["flagbrew"]
        combined_list = sorted(combined_list)
        embed.description = "\n".join(combined_list)
        await ctx.send(embed=embed)

    @secure_role_mention.command(name="add")
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    @helper.restricted_to_bot
    async def secure_role_message_add(self, ctx, role_name, role: discord.Role):
        """Allows adding a role to the dict for secure_role_mention. 'role_name' should be the name that will be used for srm invoking, 'role' should be the ID or a mention of the pinged role"""
        try:
            self.role_mentions_dict[role_name.lower()]
            return await ctx.send("That name is already set. Please use `.srm remove` to delete it first.")
        except KeyError:
            self.role_mentions_dict[role_name.lower()] = role.id
        with open("saves/role_mentions.json", "w") as file:
            json.dump(self.role_mentions_dict, file, indent=4)
        await ctx.send(f"`{role.name}` can now be mentioned via srm under the name `{role_name.lower()}`.")
        try:
            await self.bot.logs_channel.send(f"{ctx.author} added {role_name.lower()} to the mentionable roles.")
        except discord.Forbidden:
            pass  # beta bot can't log

    @secure_role_mention.command(name="remove")
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    @helper.restricted_to_bot
    async def secure_role_mention_remove(self, ctx, role_name):
        """Allows removing a role from the dict for secure_role_mention. 'role_name' should be the name that will be used for srm invoking"""
        try:
            self.role_mentions_dict[role_name.lower()]
        except KeyError:
            return await ctx.send("That role isn't in the dict. Please use `.srm list` to confirm.")
        del self.role_mentions_dict[role_name.lower()]
        with open("saves/role_mentions.json", "w") as file:
            json.dump(self.role_mentions_dict, file, indent=4)
        await ctx.send(f"`{role_name.lower()}` can no longer be mentioned via srm.")
        try:
            await self.bot.logs_channel.send(f"{ctx.author} removed {role_name.lower()} from the mentionable roles.")
        except discord.Forbidden:
            pass  # beta bot can't log

    def gen_token_qr(self, token):
        qr = qrcode.QRCode(version=None)
        qr.add_data(token)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        bytes = io.BytesIO()
        img.save(bytes, format='PNG')
        bytes = bytes.getvalue()
        qr_file = discord.File(io.BytesIO(bytes), filename="qr.png")
        return qr_file

    @commands.command()
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    @helper.restricted_to_bot
    async def regen_token(self, ctx, user: discord.Member):
        """Regenerates a patron's token"""
        if not self.bot.is_mongodb:
            return await ctx.send("No DB available, cancelling...")
        new_token = secrets.token_urlsafe(16)
        self.db['patrons'].update_one(
            {
                "discord_id": str(user.id)
            },
            {
                "$set": {
                    "discord_id": str(user.id),
                    "code": new_token
                }
            }, upsert=True)
        message = (f"Your patron token for PKSM was regenerated by staff on FlagBrew. Your new token is `{new_token}`."
                   " In case you forgot, to access the hidden Patron settings menu, press the four corners of the touch screen while on the configuration screen."
                   " Until you update your token, you won't be able to use the patron specific features.")
        qr = self.gen_token_qr(new_token)
        try:
            await user.send(message, file=qr)
        except discord.Forbidden:
            await ctx.author.send(f"Could not message user {user} about regenerated token. Please reach out manually. Message below.\n\n{message}")
        await ctx.send(f"Token regenerated for {user}")

    @commands.command()
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    @helper.restricted_to_bot
    async def delete_token(self, ctx, user: discord.Member, *, reason="No reason provided"):
        """Deletes a patron's token"""
        if not self.bot.is_mongodb:
            return await ctx.send("No DB available, cancelling...")
        self.db['patrons'].delete_one({"discord_id": str(user.id)})
        message = f"Your patron token has been revoked for reason: `{reason}`. If you feel this has been done in error, please contact a member of the FlagBrew team."
        try:
            await user.send(message)
        except discord.Forbidden:
            await ctx.author.send(f"Could not message user {user} about token deletion. Please reach out manually. Message below.\n\n{message}")
        await ctx.send(f"Token for user {user} successfully deleted.")

    @commands.command()
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    @helper.restricted_to_bot
    async def generate_token(self, ctx, user: discord.Member):
        """Generates a patron token. If user already in system, use regen_token"""
        if not self.bot.is_mongodb:
            return await ctx.send("No DB available, cancelling...")
        token = secrets.token_urlsafe(16)
        self.db['patrons'].update_one(
            {
                "discord_id": str(user.id)
            },
            {
                "$set": {
                    "discord_id": str(user.id),
                    "code": token
                }
            }, upsert=True)
        message = ("You have had a patron token generated for you! You can add the token below to PKSM's config to access some special patron only stuff."
                   " To access the hidden Patron settings menu, press the four corners of the touch screen while on the configuration screen."
                   f" If you need any further help setting it up, ask in {self.bot.patrons_channel.mention}!\n\n`{token}`")
        qr = self.gen_token_qr(token)
        try:
            await user.send(message, file=qr)
        except discord.Forbidden:
            await ctx.author.send(f"Could not message user {user} about token generation. Please reach out manually. Message below.\n\n{message}")
        await ctx.send(f"Token for user {user} successfully generated.")

    @commands.command(aliases=['report', 'rc'])  # Modified from https://gist.github.com/JeffPaine/3145490
    @helper.restricted_to_bot
    async def report_code(self, ctx, game_id: str, code_name: str, issue):
        """Allow reporting a broken code through the bot. Example: .report_code 00040000001B5000, 'PP Not Decrease v1.0', 'PP still decreases with code enabled'"""
        async with self.bot.session.get("https://api.github.com/repos/FlagBrew/Sharkive/contents/3ds") as resp:
            db_3ds = await resp.json()
        async with self.bot.session.get("https://api.github.com/repos/FlagBrew/Sharkive/contents/switch") as resp:
            db_switch = await resp.json()
        content_3ds = [x['name'].replace(".txt", "") for x in db_3ds]
        content_switch = [x['name'] for x in db_switch]
        if not [content for content in (content_3ds, content_switch) if game_id in content]:
            return await ctx.send("That game ID isn't in the database! Please confirm the game is in the database.")
        elif game_id in content_3ds and game_id not in content_switch:
            console = "3DS"
        else:
            console = "Switch"
        repo_owner = "FlagBrew"
        repo_name = "Sharkive"
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
        session_auth = aiohttp.BasicAuth(self.bot.github_user, self.bot.github_pass)
        issue_body = f"Game ID: {game_id}\nConsole: {console}\nCode name: {code_name}\n\n Issue: {issue}\n\n Submitted by: {ctx.author} | User id: {ctx.author.id}"
        issue = {
            "title": "Broken code submitted through bot",
            "body": issue_body,
            "labels": ['bot submission']
        }
        async with self.bot.session.post(url=url, auth=session_auth, data=json.dumps(issue)) as resp:
            json_content = await resp.json()
            if resp.status == 201:
                await ctx.send(f"Successfully created issue! You can find it here: https://github.com/{repo_owner}/{repo_name}/issues/{json_content['number']}")
            else:
                status_name = http.HTTPStatus(resp.status).name  # pylint: disable=no-member
                await ctx.send(f"There was an issue creating the issue. {self.bot.creator.mention} please take a look.\n\n`{resp.status}` - `{status_name}`")

    @commands.command(aliases=['estpurge'])
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    async def estprune(self, ctx, days=30):
        """Shows how many users would be kicked for inactivity. Defaults to maximum of 30 days"""
        if not 0 < days <= 30:
            return await ctx.send("Error, day count must be a positive number and less than 31 days.")
        msg = await ctx.send("Processing. This may take a minute.")
        prune_amount = await ctx.guild.estimate_pruned_members(days=days)
        if prune_amount == 0:
            return await msg.edit(content="There are no users that would be kicked in that time frame.")  # Unlikely to be triggered on FlagBrew
        await msg.edit(content=f"{prune_amount} users would be kicked as a result of a prune.")

    @commands.command()
    @helper.restricted_to_bot
    async def toggledmfaq(self, ctx):
        """Allows a user to toggle getting the faq dm'd to them instead of it posting in channel"""
        if ctx.author.id in self.bot.dm_list:
            self.bot.dm_list.remove(ctx.author.id)
            await ctx.send("You will no longer have the FAQ dm'd to you.")
        else:
            self.bot.dm_list.append(ctx.author.id)
            await ctx.send("You'll now have the FAQ dm'd to you on use instead.")
        with open('saves/faqdm.json', 'w') as file:
            json.dump(self.bot.dm_list, file, indent=4)

    @commands.command(hidden=True)
    async def togglecommand(self, ctx, command):
        """Allows disabling of commands. Restricted to Griffin and Allen"""
        if ctx.author not in (self.bot.creator, self.bot.allen):
            raise commands.errors.CheckFailure()
        elif command == "togglecommand":
            return await ctx.send("This command cannot be disabled.")
        elif command not in self.bot.disabled_commands:
            try:
                self.bot.get_command(command).enabled = False
            except AttributeError:
                return await ctx.send(f"There is no command named `{command}`.")
            self.bot.disabled_commands.append(command)
            with open('saves/disabled_commands.json', 'w') as file:
                json.dump(self.bot.disabled_commands, file, indent=4)
            return await ctx.send(f"Successfully disabled the `{command}` command.")
        try:
            self.bot.get_command(command).enabled = True
        except AttributeError:
            return await ctx.send(f"There is no command named `{command}`.")
        self.bot.disabled_commands.remove(command)
        with open('saves/disabled_commands.json', 'w') as file:
            json.dump(self.bot.disabled_commands, file, indent=4)
        await ctx.send(f"Successfully re-enabled the `{command}` command.")

    @commands.command(hidden=True)
    async def listdisabled(self, ctx):
        """Lists disabled commands"""
        if len(self.bot.disabled_commands) == 0:
            return await ctx.send("There are currently no disabled commands.")
        split_list = ",\n".join(c for c in self.bot.disabled_commands)
        await ctx.send(f"```{split_list}```")

    @commands.command()
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    async def dm(self, ctx, user: discord.User, *, message):
        """DMs a user"""
        if user == ctx.me:
            return await ctx.send(f"{ctx.author.mention} I can't DM myself, you snarky little shit.")
        has_attch = bool(ctx.message.attachments)
        embed = discord.Embed(description=message)
        if has_attch:
            img_bytes = await ctx.message.attachments[0].read()
            client_img = discord.File(io.BytesIO(img_bytes), 'image.png')
            log_img = discord.File(io.BytesIO(img_bytes), 'dm_image.png')
            embed.set_thumbnail(url="attachment://dm_image.png")
            try:
                await user.send(message, file=client_img)
            except discord.Forbidden:
                return await ctx.send("Failed to DM the user. Do they have me blocked? 😢")
            await self.bot.logs_channel.send(f"Message sent to {user} by {ctx.author}.", embed=embed, file=log_img)
        else:
            try:
                await user.send(message)
            except discord.Forbidden:
                return await ctx.send("Failed to DM the user. Do they have me blocked? 😢")
            await self.bot.logs_channel.send(f"Message sent to {user} by {ctx.author}.", embed=embed)
        await ctx.send(f"Successfully DMed {user}.")

    @commands.command()
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    async def say(self, ctx, channel: discord.TextChannel, *, message):
        """Sends a message to the specified TextChannel"""
        if channel == ctx.channel or ctx.channel.name == "logs":
            return await ctx.send("Sending messages to the current channel or a logs channel is prohibited.")
        message = message.replace("@everyone", "`everyone`").replace("@here", "`here`")
        has_attch = bool(ctx.message.attachments)
        embed = discord.Embed(description=message)
        if has_attch:
            img_bytes = await ctx.message.attachments[0].read()
            channel_img = discord.File(io.BytesIO(img_bytes), 'image.png')
            log_img = discord.File(io.BytesIO(img_bytes), 'channel_send_image.png')
            embed.set_thumbnail(url="attachment://channel_send_image.png")
            await channel.send(message, file=channel_img)
            await self.bot.logs_channel.send(f"Message sent in {channel} by {ctx.author}.", embed=embed, file=log_img)
        else:
            await channel.send(message)
            await self.bot.logs_channel.send(f"Message sent in {channel} by {ctx.author}.", embed=embed)
        await ctx.send(f"Successfully sent message in {channel.mention}.")

    def get_hash(self, file):  # Src: https://www.programiz.com/python-programming/examples/hash-file
        hash = hashlib.sha1()
        chunk = 0
        while chunk != b'':
            chunk = file.read(1024)
            hash.update(chunk)
        return hash.hexdigest()

    @commands.command(aliases=['scd'])
    @helper.restricted_to_bot
    async def submit_crash_dump(self, ctx, *, description):
        """Allows submitting a PKSM crash dump. Must provide a dump file, and a description. Abusers will be warned."""
        if not ctx.message.attachments or not ctx.message.attachments[0].filename.endswith(".dmp"):
            return await ctx.send("You must provide a crash dump with this command!")
        elif len(description.split(" ")) < 14:
            return await ctx.send("Please give a longer description of the issue.")
        async with self.bot.session.get(ctx.message.attachments[0].url) as resp:
            file = io.BytesIO(await resp.read())
        file_hash = self.get_hash(file)
        if file_hash in self.submitted_hashes:
            return await ctx.send("That crash dump has already been submitted.")
        file.seek(0)
        file_log = discord.File(file, filename=ctx.message.attachments[0].filename)
        msg = await self.bot.crash_log_channel.send(f"Dump submitted by {ctx.author}", file=file_log)
        embed = discord.Embed(title="New Crash Dump!", colour=discord.Colour.green())
        embed.add_field(name="Submitted By", value=f"{ctx.author} ({ctx.author.id})")
        embed.add_field(name="Submitted At", value=discord.utils.format_dt(ctx.message.created_at))
        async with self.bot.session.get("https://api.github.com/repos/FlagBrew/PKSM/commits/master") as resp:
            commit = await resp.json()
        commit_sha = commit["sha"][:7]
        embed.add_field(name="Latest Commit", value=commit_sha)
        embed.add_field(name="File Download URL", value=f"[Download]({msg.attachments[0].url})")
        embed.add_field(name="Resolution Status", value="Received")
        embed.add_field(name="Description of issue", value=description, inline=False)
        embed.set_footer(text=f"The hash for this file is {file_hash}")
        await self.bot.crash_dump_channel.send(embed=embed)
        self.submitted_hashes.append(file_hash)
        with open("saves/submitted_hashes.json", "w") as file:
            json.dump(self.submitted_hashes, file, indent=4)
        await ctx.send(f"{ctx.author.mention} your crash dump was successfully submitted!")

    @commands.command(aliases=['ccs'])
    @commands.has_any_role("FlagBrew Team", "Bot Dev")
    @commands.cooldown(rate=1, per=10.0, type=commands.BucketType.channel)
    async def change_crash_status(self, ctx, message_id: int, new_value):
        """Allows changing the resolution status of a crash report. Permissible values: received, unreproducible, reproducible, duplicate, fixed, closed"""
        if not new_value.lower() in ("received", "unreproducible", "reproducible", "duplicate", "fixed", "closed"):
            return await ctx.send(f"`{new_value}` is not a permissible value for crash status. Permissible values: `received`, `unreproducible`, `reproducible`, `duplicate`, `fixed`, and `closed`.")
        try:
            message = await self.bot.crash_dump_channel.fetch_message(message_id)
        except (discord.NotFound, discord.HTTPException):
            return await ctx.send(f"There was an issue finding a crash report with a message ID of `{message_id}`. Please double check the ID.")
        old_embed = message.embeds[0]
        if new_value.title() == old_embed.fields[4].value:
            return await ctx.send(f"That crash report already is set to `{new_value.title()}`!")
        new_embed = discord.Embed(title=old_embed.title)
        for i in range(4):
            new_embed.add_field(name=old_embed.fields[i].name, value=old_embed.fields[i].value)
        new_embed.add_field(name=old_embed.fields[4].name, value=new_value.title())
        new_embed.add_field(name=old_embed.fields[5].name, value=old_embed.fields[5].value, inline=False)
        if new_value.lower() == "received":
            new_embed.colour = discord.Colour.green()
        elif new_value.lower() == "unreproducible":
            new_embed.colour = discord.Colour.red()
        elif new_value.lower() == "reproducible":
            new_embed.colour = discord.Colour.dark_green()
        elif new_value.lower() == "duplicate":
            new_embed.colour = discord.Colour.gold()
        elif new_value.lower() == "fixed":
            new_embed.colour = discord.Colour.purple()
        elif new_value.lower() == "closed":
            new_embed.colour = discord.Colour.magenta()
        await message.edit(embed=new_embed)
        await ctx.send(f"Successfully changed the crash report's status from `{old_embed.fields[4].value}` to `{new_value.title()}`!\nJump link to the edited crash: {message.jump_url}")

    @commands.command()
    @helper.restricted_to_bot
    @commands.has_any_role("FlagBrew Team", "Bot Dev")
    async def clear_hash(self, ctx):
        """Clears the submitted_hashes file"""
        data = []
        with open("saves/submitted_hashes.json", "w") as file:
            json.dump(data, file, indent=4)
        self.submitted_hashes = []
        await ctx.send("Cleared the submitted hashes file.")

    @commands.command(enabled=False)  # Currently broken due to structure changes
    async def translate(self, ctx, lang):
        """Fetches the translation file for the provided language"""
        url = "https://raw.githubusercontent.com/FlagBrew/PKSM/master/assets/gui_strings/{}/gui.json"
        langs = {
            "chinese-simplified": "chs",
            "chinese-traditional": "cht",
            "english": "eng",
            "french": "fre",
            "german": "ger",
            "italian": "ita",
            "japanese": "jpn",
            "korean": "kor",
            "dutch": "nl",
            "portuguese": "pt",
            "romanian": "ro",
            "spanish": "spa"
        }
        if not lang.lower() in langs.keys():
            return await ctx.send(f"Inputted language of `{lang.lower()}` is not an available language. Possible languages: `{', '.join(l for l in langs.keys())}`.")
        url = url.format(langs[lang.lower()])
        async with self.bot.session.get(url=url) as resp:
            if resp.status != 200:
                return await ctx.send(f"Couldn't fetch tranlation file! status code: `{resp.status}`.")
            contents = await resp.read()
            bytes_contents = io.BytesIO(contents)
            gui_file = discord.File(bytes_contents, "gui.json")
            await ctx.send(f"{ctx.author.mention} Here's the {lang.lower()} language file:", file=gui_file)

    @commands.command(aliases=['ui', 'user'])  # Smth smth stolen from GriffinG1/Midnight but it's *my* license and I do what I want
    @helper.restricted_to_bot
    async def userinfo(self, ctx, user: discord.Member = None, depth=False):
        """Pulls a user's info. Passing no member returns your own. depth is a bool that will specify account creation and join date, and account age"""
        if not user:
            user = ctx.author
        embed = discord.Embed(colour=user.colour)
        embed.set_author(name=f"User info for {user} ({user.id})", icon_url=str(user.display_avatar))
        if user.nick:
            embed.add_field(name="Nickname", value=user.nick)
        embed.add_field(name="Avatar Link", value=f"[Here]({str(user.display_avatar)})")
        status = str(user.status).capitalize()
        if user.is_on_mobile():
            status += " (Mobile)"
        embed.add_field(name="Status", value=status)
        if user.activity and not depth:
            embed.add_field(name="Top Activity", value=f"`{user.activity}`")
        if len(user.roles) > 1 and not depth:
            embed.add_field(name="Highest Role", value=user.top_role)
        embed.add_field(name="Created At", value=f"{discord.utils.format_dt(user.created_at)}")
        embed.add_field(name="Joined At", value=f"{discord.utils.format_dt(user.joined_at)}")
        acc_age_days = (discord.utils.utcnow() - user.created_at).days
        acc_age_years = acc_age_days // 365
        acc_age_months = (acc_age_days % 365) // 30
        embed.add_field(name="Account Age", value=f"About {acc_age_years} Years, {acc_age_months} Months, {(acc_age_days % 365) % 30} Days")
        if depth:
            embed.add_field(name=u"\u200B", value=u"\u200B", inline=False)
            if len(user.roles) > 1:
                embed.add_field(name="Roles", value=f"`{'`, `'.join(role.name for role in user.roles[1:])}`")
            if len(user.activities) > 0:
                embed.add_field(name="Activities" if len(user.activities) > 1 else "Activity", value=f"`{'`, `'.join(str(activity.name) for activity in user.activities)}`", inline=False)
        await ctx.send(embed=embed)

    @commands.command(aliases=['fui'])  # Fetches discord.User instead of discord.Member
    @helper.restricted_to_bot
    async def fetch_user_info(self, ctx, user: discord.User):
        """Pulls a discord.User instead of discord.Member. More limited than userinfo"""
        embed = discord.Embed(colour=user.colour)
        embed.set_author(name=f"User info for {user} ({user.id})", icon_url=str(user.display_avatar))
        embed.add_field(name="Avatar Link", value=f"[Here]({str(user.display_avatar)})")
        embed.add_field(name="Created At", value=f"{discord.utils.format_dt(user.created_at)}")
        embed.add_field(name="On FlagBrew?", value=str("FlagBrew" in [guild.name for guild in user.mutual_guilds]))
        await ctx.send(embed=embed)

    @commands.command(aliases=['si', 'guild', 'gi', 'server', 'serverinfo'])
    @helper.restricted_to_bot
    async def guildinfo(self, ctx, depth=False):
        embed = discord.Embed()
        embed.set_author(name=f"Guild info for {ctx.guild.name} ({ctx.guild.id})", icon_url=str(ctx.guild.icon))
        embed.add_field(name="Guild Owner", value=f"{ctx.guild.owner} ({ctx.guild.owner.mention})")
        embed.add_field(name="Highest Role", value=f"{ctx.guild.roles[-1].name} ({ctx.guild.roles[-1].id})")
        embed.add_field(name="Member Count", value=str(ctx.guild.member_count))
        if depth:
            embed.add_field(name="Emoji Slots", value=f"{len(ctx.guild.emojis)}/{ctx.guild.emoji_limit} slots used")
            since_creation = (discord.utils.utcnow() - ctx.guild.created_at).days
            embed.add_field(name="Created At", value=f"{discord.utils.format_dt(ctx.guild.created_at)}\n({since_creation//365} years, {since_creation%365} days)")
            embed.add_field(name="Total Boosts", value=f"{ctx.guild.premium_subscription_count} boosters (Current level: {ctx.guild.premium_tier})")
        await ctx.send(embed=embed)

    @commands.command(aliases=["hexstring", "hexlify", "hs"])
    async def utf16string(self, ctx, *, string_to_convert):
        """Turns a string into its UTF-16LE format in hex, for use with PKSM's hex editor"""
        for character in string_to_convert:
            if not (0 <= ord(character) <= 0xD7FF or (0xE000 <= ord(character) <= 0xFFFF)):
                return await ctx.send(f"`{character}` is not representable on the 3DS.")
        # string plus null terminator
        hexstring = string_to_convert.encode("utf_16_le").hex() + "0000"
        bytelist = [f"0x{hexstring[x:x+2]}" for x in range(0, len(hexstring), 2)]
        await ctx.send(f"`{' '.join(bytelist)}`")

    @commands.group()
    async def emote(self, ctx):
        """Main handler for emote commands"""
        if ctx.invoked_subcommand is None:
            return await ctx.send("Possible subcommands: `add`, `addurl`, `delete`, `steal`, and `view`.")

    @emote.command()
    @commands.has_any_role("Bot Dev", "Discord Moderator")
    async def add(self, ctx, name, *, role_ids=None):
        """Allows adding an attached emote image to the server. Pass in a list of role IDs to restrict the emote"""
        roles = []
        if len(name) > 16:
            return await ctx.send("Emote names must be 16 characters or less.")
        elif len(ctx.message.attachments) < 1:
            return await ctx.send("You need to attach an image.")
        if role_ids is not None:
            role_ids = role_ids.replace(' ', '').split(',')
            role_ids += [482900527730917376, 483024700767993866]
            roles = [ctx.guild.get_role(int(role)) for role in role_ids]
        roles = [role for role in roles if role]  # Clears out None values
        image = await ctx.message.attachments[0].read()
        if len(image) > 256000:
            await ctx.send("Images need to be smaller than 256 kb.")
            return await ctx.send("https://tenor.com/view/eric-andre-bitch-gif-11075039")
        try:
            emoji = await ctx.guild.create_custom_emoji(name=name, image=image, roles=roles)
        except discord.InvalidArgument:
            return await ctx.send("You didn't attach a JPG, PNG, or GIF. Fuck you.")
        msg = f"Successfully added the emote `{name}` {str(emoji)}!"
        if len(roles) > 0:
            msg += f"\nThis emote is restricted to: `{'`, `'.join(role.name for role in roles if not 'FlagBot' in role.name)}`"
        await ctx.send(msg)

    @emote.command()
    @commands.has_any_role("Bot Dev", "Discord Moderator")
    async def addurl(self, ctx, name, url: str, *, role_ids=None):
        """Allows adding an emote by URL. Pass in a list of role IDs to restrict the emote"""
        roles = []
        if len(name) > 16:
            return await ctx.send("Emote names must be 16 characters or less.")
        elif not validators.url(url):
            await ctx.send("That's not a real link!")
        if role_ids is not None:
            role_ids = role_ids.replace(' ', '').split(',')
            role_ids += [482900527730917376, 483024700767993866]
            roles = [ctx.guild.get_role(int(role)) for role in role_ids]
        roles = [role for role in roles if role]  # Clears out None values
        async with self.bot.session.get(url=url) as resp:
            emoji = await ctx.guild.create_custom_emoji(name=name, image=(await resp.content.read()), roles=roles)
        msg = f"Successfully added the emote `{name}` {str(emoji)}!"
        if len(roles) > 0:
            msg += f"\nThis emote is restricted to: `{'`, `'.join(role.name for role in roles if not 'FlagBot' in role.name)}`"
        await ctx.send(msg)

    @emote.command()
    @commands.has_any_role("Bot Dev", "Discord Moderator")
    async def steal(self, ctx, emote: discord.PartialEmoji, *, role_ids=None):
        """Allows stealing an emote from another server. Pass in a list of role IDs to restrict the emote"""
        name = emote.name
        roles = []
        if role_ids is not None:
            role_ids = role_ids.replace(' ', '').split(',')
            role_ids += [482900527730917376, 483024700767993866]
            roles = [ctx.guild.get_role(int(role)) for role in role_ids]
        roles = [role for role in roles if role]  # Clears out None values
        async with self.bot.session.get(url=str(emote.url)) as resp:
            emoji = await ctx.guild.create_custom_emoji(name=name, image=(await resp.content.read()), roles=roles)
        msg = f"Successfully added the emote `{name}` {str(emoji)}!"
        if len(roles) > 0:
            msg += f"\nThis emote is restricted to: `{'`, `'.join(role.name for role in roles if not 'FlagBot' in role.name)}`"
        await ctx.send(msg)

    @emote.command(aliases=['del'])
    @commands.has_any_role("Bot Dev", "Discord Moderator")
    async def delete(self, ctx, emote: discord.Emoji):
        """Allows removing a provided emote"""
        for e in ctx.guild.emojis:
            if e == emote:
                await e.delete()
                break
        await ctx.send(f"Successfully deleted the emote `{emote.name}`.")

    @emote.command()
    async def view(self, ctx, emote: discord.Emoji):
        """Allows viewing the properties of a server emote"""
        embed = discord.Embed(title=f"Emote properties for {emote} ({emote.id})")
        embed.add_field(name="Emote Name", value=emote.name)
        embed.add_field(name="Emote Link", value=f"[Here]({str(emote.url)})")
        if len(emote.roles) > 0:
            embed.add_field(name="Permitted Roles", value=f"`{'`, `'.join(role.name for role in emote.roles if not 'FlagBot' in role.name)}`", inline=False)
        embed.add_field(name="Added On", value=f"{discord.utils.format_dt(emote.created_at)}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(aliases=['flagbrew', 'nintendohomebrew', 'nh', 'dsimode', 'twlmenu', 'reswitched', 'rs', 'projectpokemon', 'pporg', 'pkhexdev', 'pdp', 'nanquitas', 'cheathelp'])
    @commands.cooldown(rate=1, per=10.0, type=commands.BucketType.channel)
    async def invites(self, ctx):
        """Invoke with the guild name to get that guild's invite. Use '.invites' to see the full list. 10 second cooldown"""
        guild_invites = {
            "FlagBrew": "https://discord.gg/bGKEyfY",
            "Nintendo Homebrew": "https://discord.gg/C29hYvh",
            "DS(i) Mode Hacking": "https://discord.gg/yD3spjv",
            "Reswitched": "https://discord.gg/ZdqEhed",
            "Project Pokemon": "https://discord.gg/66PzPgD",
            "PKHeX Development Projects": "https://discord.gg/tDMvSRv",
            "Nanquitas's Playground": "https://discord.gg/z4ZMh27"
        }
        if ctx.invoked_with == "invites":
            embed = discord.Embed(title="Guild invites available via this command")
            embed.description = """FlagBrew: `.flagbrew`
            Nintendo Homebrew: `.nintendohomebrew`/`.nh`
            DS(i)Mode Hacking: `.dsimode`/`.twlmenu`
            Reswitched: `.reswitched`/`.rs`
            Project Pokemon: `.projectpokemon`/`.pporg`
            PKHeX Development Projects: `.pkhexdev`, `.pdp`
            Nanquitas's Playground: `.nanquitas`/`.cheathelp`"""
            ctx.command.reset_cooldown(ctx)
        else:
            embed = discord.Embed()
            if ctx.invoked_with == "flagbrew":
                invite = await self.bot.fetch_invite(guild_invites["FlagBrew"])
                embed.add_field(name="Guild Description", value="FlagBrew application support", inline=False)
            elif ctx.invoked_with in ('nintendohomebrew', 'nh'):
                invite = await self.bot.fetch_invite(guild_invites["Nintendo Homebrew"])
                embed.add_field(name="Guild Description", value="General Nintendo console homebrew support", inline=False)
            elif ctx.invoked_with in ('dsimode', 'twlmenu'):
                invite = await self.bot.fetch_invite(guild_invites["DS(i) Mode Hacking"])
                embed.add_field(name="Guild Description", value="TWiLight Menu++ support, as well as other DS(i)Mode related topics", inline=False)
            elif ctx.invoked_with in ('reswitched', 'rs'):
                invite = await self.bot.fetch_invite(guild_invites["Reswitched"])
                embed.add_field(name="Guild Description", value="Atmosphere development and support", inline=False)
            elif ctx.invoked_with in ('projectpokemon', 'pporg'):
                invite = await self.bot.fetch_invite(guild_invites["Project Pokemon"])
                embed.add_field(name="Guild Description", value="Project Pokemon forums and PKHeX support", inline=False)
            elif ctx.invoked_with in ('pkhexdev', 'pdp'):
                invite = await self.bot.fetch_invite(guild_invites["PKHeX Development Projects"])
                embed.add_field(name="Guild Description", value="PKHeX-Plugins and SysBot hosting support. Do not go here for non-dev base PKHeX support", inline=False)
            elif ctx.invoked_with in ('nanquitas', 'cheathelp'):
                invite = await self.bot.fetch_invite(guild_invites["Nanquitas's Playground"])
                embed.add_field(name="Guild Description", value="Nanquitas's server, go here for cheat creation support", inline=False)
            embed.title = f"Guild info and invite for {invite.guild.name}"
            embed.add_field(name="Member Count", value=str(invite.approximate_member_count))
            embed.add_field(name="Landing Channel", value=invite.channel.name)
            embed.add_field(name="Invite URL", value=f"Click [here]({invite.url})")
            embed.set_thumbnail(url=str(invite.guild.icon))
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
                key_3ds = helper.key_inputs.get(hex(2**key_index))[0]
                if key_3ds != "None":
                    final_indices['3ds'].append(key_3ds)
                key_switch = helper.key_inputs.get(hex(2**key_index))[1]
                if key_switch != "None" and hexval.replace('0x', '')[0] == "8":
                    final_indices['switch'].append(key_switch)
            except IndexError:
                return 400
            decval -= 2**key_index
        return final_indices

    @commands.command()
    @helper.restricted_to_bot
    async def cheatkeys(self, ctx, *, key):
        """Byte decoder for sharkive codes. Input should be the second half of the line starting with DD000000"""
        key = key.replace(' ', '').replace('DD000000', '')
        if key == "00000000":
            return await ctx.send("All 0s is a null input combo.")
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
        if len(indexes["3ds"]) == 0 and len(indexes["switch"]) == 0:
            embed.description = "No inputs could be found for the provided key."
        await ctx.send(embed=embed)

    @commands.command(aliases=['csp'])
    async def create_save_path(self, ctx, console: str, *, games):
        """Returns a formed save path for the provided console and game(s). Separate inputted games with '|'. Game names must be complete"""
        games = games.replace(' | ', '|').replace(' |', '|').replace('| ', '|')  # Cleanup string for uniformity
        games_list = games.split('|')
        games_info = {}
        save_path = "~/{}/Checkpoint/saves/{} <game_name_here>/<save_folder_here>/<save_content_here>"
        failed_games = []
        if console == "switch":
            for game in games_list:
                if "Pokemon" in game and "Arceus" not in game:
                    games_list.append(games_list.pop(games_list.index(game)).replace('Pokemon', 'Pokémon'))
        elif console != "3ds":
            return await ctx.send(f"This command only supports `3ds` and `switch` consoles. `{console}` is not a supported console.")
        xmltree = lxml.etree.parse(f'saves/xmls/{console}.xml')
        xmlroot = xmltree.getroot()
        for elem in xmlroot.findall("release"):  # Code taken and modified from the docs.py script in FlagBrew/Sharkive
            game_name = elem.find("name").text
            if game_name in games_list:
                titleid = elem.find("titleid").text.split(' ')[0]
                region = elem.find("region").text
                if titleid in games_info.keys():
                    games_info[titleid]['region'] = "UNV"
                    continue
                games_info[titleid] = {'name': game_name, 'region': region}
        embed = discord.Embed(title="Save Paths")
        failed_games = [game for game in games_list if game not in [games_info[titleid]['name'] for titleid in games_info]]
        if len(failed_games) > 0:
            embed.description = f"Could not find any games matching any of these games:\n`{'`, `'.join(failed_games)}`\nPlease double check [here]({'http://www.3dsdb.com/' if console == '3ds' else 'http://nswdb.com/'}) for your game's DB name."
        for game_id in games_info.keys():
            if console == "3ds":
                hex_id = int(game_id, 16)  # Converts titleID to hex, then:
                game_path = f"0x{((hex_id & 0xFFFFFFFF) >> 8):0{5}X}"  # Takes lower 32 bits of TID, shifts by 8, then pads with leading zeros to 5 characters
            else:
                game_path = f"0x{game_id}"
            embed.add_field(name=f"{games_info[game_id]['name']} ({games_info[game_id]['region']})", value=f"`{save_path.format(console, game_path)}`", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    async def update_tid_xml(self, ctx, console):
        """Updates the XML files used for create_save_path. Pass in 3ds or switch"""
        if console == "3ds":
            url = "http://3dsdb.com/xml.php"
        elif console == "switch":
            url = "http://nswdb.com/xml.php"
        async with self.bot.session.get(url) as resp:
            if resp.status == 200:
                content = await resp.read()
                with open(f'saves/xmls/{console}.xml', 'wb') as file:
                    file.write(content)
        await ctx.send(f"Downloaded an updated xml for {console}.")

    @commands.command(name='genqr')  # Todo: move to utility.py
    @commands.has_any_role("Patrons", "FlagBrew Team")
    async def generate_qr(self, ctx, app, ext):
        """Generates a Patron QR code for installing via FBI"""
        if not self.bot.is_mongodb:
            return await ctx.send("No DB available, cancelling...")
        async with self.bot.session.get(self.bot.flagbrew_url) as resp:
            if not resp.status == 200:
                return await ctx.send("I could not make a connection to flagbrew.org, so this command cannot be used currently.")
        accepted_apps = {
            "pksm": "PKSM",
            "checkpoint": "Checkpoint"
        }
        if not app.lower() in accepted_apps.keys():
            return await ctx.send(f"The application `{app}` is not currently supported. Sorry.")
        elif not ext.lower() in ("cia", "3dsx"):
            return await ctx.send("The only supported file types are `CIA` and `3dsx`.")
        patron_code = self.db['patrons'].find_one({"discord_id": str(ctx.author.id)})
        if patron_code is None:
            return await ctx.send("Sorry, you don't have a patron code!")
        patron_code = patron_code['code']
        headers = {
            "patreon": patron_code
        }
        async with self.bot.session.get(f"{self.bot.flagbrew_url}api/v2/patreon/update-check/{accepted_apps[app.lower()]}", headers=headers) as commit_resp:
            commit = await commit_resp.json()
        commit_sha = commit['hash']
        url = f"{self.bot.flagbrew_url}api/v2/patreon/update-qr/{accepted_apps[app.lower()]}/{commit_sha}/{ext.lower()}"
        async with self.bot.session.get(url=url, headers=headers) as resp:
            if not resp.status == 200:
                return await ctx.send("Failed to get the QR.")
            qr_bytes = await resp.read()
            qr = discord.File(io.BytesIO(qr_bytes), 'patron_qr.png')
            embed = discord.Embed(title=f"Patron Build for {accepted_apps[app.lower()]}")
            embed.add_field(name="Direct Download", value=f"[Here]({self.bot.flagbrew_url}api/v2/patreon/update/{patron_code}/{accepted_apps[app.lower()]}/{commit_sha}/{ext})")
            embed.add_field(name="File Type", value=ext.upper())
            embed.set_footer(text=f"Commit Hash: {commit_sha}")
            embed.set_image(url="attachment://patron_qr.png")
            try:
                await ctx.author.send(embed=embed, file=qr)
            except discord.Forbidden:
                return await ctx.send(f"Failed to DM you {ctx.author.mention}. Are your DMs closed?")
            await ctx.send(f"{ctx.author.mention} I have DM'd you the QR code.")


async def setup(bot):
    await bot.add_cog(Utility(bot))
