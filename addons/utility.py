#!/usr/bin/env python3

import discord
from discord.ext import commands
from datetime import datetime
import sys
import os
import json
import secrets
import http
import aiohttp
import qrcode
import io
import hashlib
from addons.helper import restricted_to_bot


class Utility(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        print(f'Addon "{self.__class__.__name__}" loaded')
        with open("saves/role_mentions.json", "r") as f:
            self.role_mentions_dict = json.load(f)
        if not os.path.exists('saves/submitted_hashes.json'):
            data = []
            with open('saves/submitted_hashes.json', 'w') as f:
                json.dump(data, f, indent=4)
        with open("saves/submitted_hashes.json", "r") as f:
            self.submitted_hashes = json.load(f)

    async def toggleroles(self, ctx, role, user):
        author_roles = user.roles[1:]
        if role not in author_roles:
            await user.add_roles(role)
            return False
        else:
            await user.remove_roles(role)
            return True

    @commands.command()
    @restricted_to_bot
    async def togglerole(self, ctx, role):
        """Allows user to toggle update roles. Available roles: see #welcome-and-rules, as well as 'bot'"""
        user = ctx.message.author
        role = role.lower()
        if not role in ('3ds', 'switch', 'bot'):
            return await ctx.send(f"{user.mention} That isn't a toggleable role!")
        had_role = await self.toggleroles(ctx, discord.utils.get(ctx.guild.roles, id=int(self.role_mentions_dict[role])), user)
        if had_role:
            info_string = f"You will no longer be pinged for {role} updates."
        else:
            info_string = f"You will now receive pings for {role} updates!"
        await ctx.send(user.mention + ' ' + info_string)

    @commands.command(hidden=True)
    @restricted_to_bot
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

    @commands.command(aliases=['brm'])
    @commands.has_any_role("Discord Moderator", "FlagBrew Team", "Bot Dev")
    @restricted_to_bot
    async def role_mention_bot(self, ctx):
        """Securely mention anyone with the bot updates role"""
        role = discord.utils.get(ctx.guild.roles, id=int(self.role_mentions_dict['bot']))
        try:
            await role.edit(mentionable=True, reason=f"{ctx.author} wanted to mention users with this role.")  # Reason -> Helps pointing out folks that abuse this
        except:
            await role.edit(mentionable=True, reason=f"A staff member, or Griffin, wanted to mention users with this role, and I couldn't log properly. Check {self.bot.logs_channel.mention}.")  # Bypass the TypeError it kept throwing
        await ctx.channel.send(f"{role.mention}")
        await role.edit(mentionable=False, reason="Making role unmentionable again.")
        try:
            await self.bot.logs_channel.send(f"{ctx.author} pinged bot updates in {ctx.channel}")
        except discord.Forbidden:
            pass  # beta bot can't log

    @commands.command(aliases=['srm', 'mention'])
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    async def secure_role_mention(self, ctx, update_role: str, channel: discord.TextChannel=None):
        """Securely mention a role. Can input a channel at the end for remote mentioning. More can be added with srm_add"""
        if not channel:
            channel = ctx.channel
        if update_role.lower() == "flagbrew":
            role = self.bot.flagbrew_team_role
        else:
            try:
                role = discord.utils.get(ctx.guild.roles, id=int(self.role_mentions_dict[update_role.lower()]))
            except KeyError:
                role = None
        if role is None:
            return await ctx.send("You didn't give a valid role. Do `.srm_list` to see all available roles.")
        try:
            await role.edit(mentionable=True, reason=f"{ctx.author} wanted to mention users with this role.")  # Reason -> Helps pointing out folks that abuse this
        except:
            await role.edit(mentionable=True, reason=f"A staff member wanted to mention users with this role, and I couldn't log properly. Check {self.bot.logs_channel.mention}.")  # Bypass the TypeError it kept throwing
        await channel.send(f"{role.mention}")
        await role.edit(mentionable=False, reason="Making role unmentionable again.")
        try:
            await self.bot.logs_channel.send(f"{ctx.author} pinged {role.name} in {channel}")
        except discord.Forbidden:
            pass  # beta bot can't log

    @commands.command(aliases=['srm_list'])
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    @restricted_to_bot
    async def secure_role_mention_list(self, ctx):
        """Lists all available roles for srm"""
        embed = discord.Embed(title="Mentionable Roles")
        embed.description = "\n".join(self.role_mentions_dict)
        embed.description += "\nflagbrew"
        await ctx.send(embed=embed)

    @commands.command(aliases=['srm_add'])
    @commands.has_any_role("Discord Moderator")
    @restricted_to_bot
    async def secure_role_mention_add(self, ctx, role_name, role_id:int):
        """Allows adding a role to the dict for secure_role_mention. Role_name should be the name that will be used when srm is called"""
        role = discord.utils.get(ctx.guild.roles, id=role_id)
        if role is None:
            return await ctx.send("That's not a role on this guild.")
        not_new = True
        try:
            self.role_mentions_dict[role_name.lower()]
        except KeyError:
            not_new = False
        if not_new:
            return await ctx.send("There's already a key with that name.")
        self.role_mentions_dict[role_name.lower()] = str(role_id)
        with open("saves/role_mentions.json", "w") as f:
            json.dump(self.role_mentions_dict, f, indent=4)
        await ctx.send(f"`{role_name.lower()}` can now be mentioned via srm.")
        try:
            await self.bot.logs_channel.send(f"{ctx.author} added {role_name.lower()} to the mentionable roles.")
        except discord.Forbidden:
            pass # beta bot can't log

    @commands.command(aliases=['srm_remove'])
    @commands.has_any_role("Discord Moderator")
    @restricted_to_bot
    async def secure_role_mention_remove(self, ctx, role_name):
        """Allows removing a role from the dict for secure_role_mention. Role_name should be the name that is used when srm is called"""
        try:
            self.role_mentions_dict[role_name.lower()]
        except KeyError:
            return await ctx.send("That role isn't in the dict. Please use `.srm_list` to confirm.")
        del self.role_mentions_dict[role_name.lower()]
        with open("saves/role_mentions.json", "w") as f:
            json.dump(self.role_mentions_dict, f, indent=4)
        await ctx.send(f"`{role_name.lower()}` can no longer be mentioned via srm.")
        try:
            await self.bot.logs_channel.send(f"{ctx.author} removed {role_name.lower()} from the mentionable roles.")
        except discord.Forbidden:
            pass # beta bot can't log

    def gen_token_qr(self, token):
        qr = qrcode.QRCode(version=None)
        qr.add_data(token)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        bytes = io.BytesIO()
        img.save(bytes, format='PNG')
        bytes = bytes.getvalue()
        f = discord.File(io.BytesIO(bytes), filename="qr.png")
        return f

    @commands.command()
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    @restricted_to_bot
    async def regen_token(self, ctx, user: discord.Member):
        """Regenerates a patron's token"""
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
    @restricted_to_bot
    async def delete_token(self, ctx, user: discord.Member, *, reason="No reason provided"):
        """Deletes a patron's token"""
        self.db['patrons'].delete_one({"discord_id": str(user.id)})
        message = f"Your patron token has been revoked for reason: `{reason}`. If you feel this has been done in error, please contact a member of the FlagBrew team."
        try:
            await user.send(message)
        except discord.Forbidden:
            await ctx.author.send(f"Could not message user {user} about token deletion. Please reach out manually. Message below.\n\n{message}")
        await ctx.send(f"Token for user {user} successfully deleted.")

    @commands.command()
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    @restricted_to_bot
    async def generate_token(self, ctx, user: discord.Member):
        """Generates a patron token. If user already in system, use regen_token"""
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
    @restricted_to_bot
    async def report_code(self, ctx, game_id: str, code_name: str, issue):
        """Allow reporting a broken code through the bot. Example: .report_code 00040000001B5000, 'PP Not Decrease v1.0', 'PP still decreases with code enabled'"""
        async with self.bot.session.get("https://api.github.com/repos/FlagBrew/Sharkive/contents/3ds") as r:
            db_3ds = await r.json()
        async with self.bot.session.get("https://api.github.com/repos/FlagBrew/Sharkive/contents/switch") as r:
            db_switch = await r.json()
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
            "body": issue_body
        }
        async with self.bot.session.post(url=url, auth=session_auth, data=json.dumps(issue)) as r:
            json_content = await r.json()
            if r.status == 201:
                await ctx.send(f"Successfully created issue! You can find it here: https://github.com/{repo_owner}/{repo_name}/issues/{json_content['number']}")
            else:
                status_name = http.HTTPStatus(r.status).name  # pylint: disable=no-member
                await ctx.send(f"There was an issue creating the issue. {self.bot.creator.mention} please take a look.\n\n`{r.status}` - `{status_name}`")

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
    @restricted_to_bot
    async def toggledmfaq(self, ctx):
        """Allows a user to toggle getting the faq dm'd to them instead of it posting in channel"""
        if ctx.author.id in self.bot.dm_list:
            self.bot.dm_list.remove(ctx.author.id)
            await ctx.send("You will no longer have the FAQ dm'd to you.")
        else:
            self.bot.dm_list.append(ctx.author.id)
            await ctx.send("You'll now have the FAQ dm'd to you on use instead.")
        with open('saves/faqdm.json', 'w') as f:
            json.dump(self.bot.dm_list, f, indent=4)

    @commands.command(hidden=True)
    async def togglecommand(self, ctx, command):
        """Allows disabling of commands. Restricted to Griffin and Allen"""
        if not ctx.author in (self.bot.creator, self.bot.allen):
            raise commands.errors.CheckFailure()
        elif command == "togglecommand":
            return await ctx.send("This command cannot be disabled.")
        elif command not in self.bot.disabled_commands:
            try:
                self.bot.get_command(command).enabled = False
            except AttributeError:
                return await ctx.send(f"There is no command named `{command}`.")
            self.bot.disabled_commands.append(command)
            with open('saves/disabled_commands.json', 'w') as f:
                json.dump(self.bot.disabled_commands, f, indent=4)
            return await ctx.send(f"Successfully disabled the `{command}` command.")
        try:
            self.bot.get_command(command).enabled = True
        except AttributeError:
            return await ctx.send(f"There is no command named `{command}`.")
        self.bot.disabled_commands.remove(command)
        with open('saves/disabled_commands.json', 'w') as f:
            json.dump(self.bot.disabled_commands, f, indent=4)
        await ctx.send(f"Successfully re-enabled the `{command}` command.")

    @commands.command(hidden=True)
    async def listdisabled(self, ctx):
        """Lists disabled commands"""
        if len(self.bot.disabled_commands) == 0:
            return await ctx.send("There are currently no disabled commands.")
        split_list = ",\n".join(c for c in self.bot.disabled_commands)
        await ctx.send(f"```{split_list}```")

    @commands.command()
    @commands.has_any_role("Discord Moderator")
    async def dm(self, ctx, user: discord.User, *, message):
        """DMs a user"""
        if user == ctx.me:
            return await ctx.send(f"{ctx.author.mention} I can't DM myself, you snarky little shit.")
        try:
            await user.send(message)
        except discord.Forbidden:
            await ctx.send("Failed to DM the user. Do they have me blocked? 😢")
        else:
            await self.bot.logs_channel.send(f"Message sent to {user} by {ctx.author}.", embed=discord.Embed(description=message))

    def get_hash(self, file): # Src: https://www.programiz.com/python-programming/examples/hash-file
        h = hashlib.sha1()
        chunk = 0
        while chunk != b'':
            chunk = file.read(1024)
            h.update(chunk)
        return h.hexdigest()

    @commands.command(aliases=['scd'])
    @restricted_to_bot
    async def submit_crash_dump(self, ctx, *, description):
        """Allows submitting a PKSM crash dump. Must provide a dump file, and a description. Abusers will be warned."""
        if not ctx.message.attachments or not ctx.message.attachments[0].filename.endswith(".dmp"):
            return await ctx.send("You must provide a crash dump with this command!")
        elif len(description.split(" ")) < 14:
            return await ctx.send("Please give a longer description of the issue.")
        async with self.bot.session.get(ctx.message.attachments[0].url) as r:
            file = io.BytesIO(await r.read())
        file_hash = self.get_hash(file)
        if file_hash in self.submitted_hashes:
            return await ctx.send("That crash dump has already been submitted.")
        file.seek(0)
        file_log = discord.File(file, filename=ctx.message.attachments[0].filename)
        msg = await self.bot.crash_log_channel.send(f"Dump submitted by {ctx.author}", file=file_log)
        embed = discord.Embed(title="New Crash Dump!")
        embed.add_field(name="Submitted By", value=ctx.author.mention)
        embed.add_field(name="Submitted At", value=ctx.message.created_at.strftime('%b %d, %Y'))
        async with self.bot.session.get("https://api.github.com/repos/FlagBrew/PKSM/commits/master") as r:
            commit = await r.json()
        commit_sha = commit["sha"][:7]
        embed.add_field(name="Latest Commit", value=commit_sha)
        embed.add_field(name="File Download URL", value=f"[Download]({msg.attachments[0].url})")
        embed.add_field(name="Description of issue", value=description, inline=False)
        embed.set_footer(text=f"The hash for this file is {file_hash}")
        await self.bot.crash_dump_channel.send(embed=embed)
        self.submitted_hashes.append(file_hash)
        with open("saves/submitted_hashes.json", "w") as f:
            json.dump(self.submitted_hashes, f, indent=4)
        await ctx.send(f"{ctx.author.mention} your crash dump was successfully submitted!")

    @commands.command()
    @restricted_to_bot
    @commands.has_any_role("FlagBrew Team", "Bot Dev")
    async def clear_hash(self, ctx):
        """Clears the submitted_hashes file"""
        data = []
        with open("saves/submitted_hashes.json", "w") as f:
            json.dump(data, f, indent=4)
        self.submitted_hashes = []
        await ctx.send("Cleared the submitted hashes file.")

    @commands.command(name="toggleword")
    @commands.has_any_role("Discord Moderator")
    async def toggle_ban_word_from_gpss(self, ctx, word):
        """Bans a word from the GPSS. Restricted to Discord Moderator"""
        url = self.bot.api_url + "api/v1/bot/ban-word"
        data = {
            "word": word
        }
        headers = {
            "secret": self.bot.site_secret
        }
        async with self.bot.session.post(url=url, data=data, headers=headers) as r:
            if not r.status in (200, 410):
                return await ctx.send(f"Failed to post the banned word to the server. Status code: `{r.status}`.")
            elif r.status == 410:
                return await ctx.send(f"Successfully unbanned the word `{word}` from the GPSS.")
            await ctx.send(f"Successfully banned the word `{word}` from the GPSS.")

    @commands.command()
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
        async with self.bot.session.get(url=url) as r:
            if r.status != 200:
                return await ctx.send(f"Couldn't fetch tranlation file! status code: `{r.status}`.")
            contents = await r.read()
            bytes_contents = io.BytesIO(contents)
            file = discord.File(bytes_contents, "gui.json")
            await ctx.send(f"{ctx.author.mention} Here's the {lang.lower()} language file:", file=file)

    @commands.command(aliases=['ui', 'user'])  # Smth smth stolen from GriffinG1/Midnight but it's *my* license and I do what I want
    @restricted_to_bot
    async def userinfo(self, ctx, user: discord.Member=None, depth=False):
        """Pulls a user's info. Passing no member returns your own. depth is a bool that will specify account creation and join date, and account age"""
        if not user:
            user = ctx.author
        embed = discord.Embed(colour=user.colour)
        embed.set_author(name=f"User info for {user} ({user.id})", icon_url=str(user.avatar_url))
        if user.nick:
            embed.add_field(name="Nickname", value=user.nick)
        embed.add_field(name="Avatar Link", value=f"[Here]({str(user.avatar_url)})")
        status = str(user.status).capitalize()
        if user.is_on_mobile():
            status += " (Mobile)"
        embed.add_field(name="Status", value=status)
        if user.activity and not depth:
            embed.add_field(name="Top Activity", value=f"`{user.activity}`")
        if len(user.roles) > 1 and not depth:
            embed.add_field(name="Highest Role", value=user.top_role)
        if depth:
            embed.add_field(name=u"\u200B", value=u"\u200B", inline=False)
            embed.add_field(name="Created At", value=f"{user.created_at.strftime('%m-%d-%Y %H:%M:%S')} UTC")
            embed.add_field(name="Joined At", value=f"{user.joined_at.strftime('%m-%d-%Y %H:%M:%S')} UTC")
            embed.add_field(name="Account Age", value=f"{(datetime.now() - user.created_at).days} Days")
            if len(user.roles) > 1:
                embed.add_field(name="Roles", value=f"`{'`, `'.join(role.name for role in user.roles[1:])}`")
            if len(user.activities) > 0:
                embed.add_field(name="Activities" if len(user.activities) > 1 else "Activity", value=f"`{'`, `'.join(str(activity.name) for activity in user.activities)}`", inline=False)
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

def setup(bot):
    bot.add_cog(Utility(bot))
