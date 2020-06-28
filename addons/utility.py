#!/usr/bin/env python3

import discord
from discord.ext import commands
import sys
import os
import json
import secrets
import http
import aiohttp
import qrcode
import io
import hashlib


class Utility(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        print('Addon "{}" loaded'.format(self.__class__.__name__))
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
    async def togglerole(self, ctx, role):
        """Allows user to toggle update roles. You can use .masstoggle to apply all roles at once.
        Available roles: 3DS, Switch, Bot"""
        user = ctx.message.author
        role = role.lower()
        if not role in ('3ds', 'switch', 'bot'):
            return await ctx.send("{} That isn't a toggleable role!".format(user.mention))
        had_role = await self.toggleroles(ctx, discord.utils.get(ctx.guild.roles, id=int(self.role_mentions_dict[role])), user)
        if had_role:
            info_string = "You will no longer be pinged for {} updates.".format(role)
        else:
            info_string = "You will now receive pings for {} updates!".format(role)
        await ctx.send(user.mention + ' ' + info_string)

    @commands.command()
    async def masstoggle(self, ctx):
        """Allows a user to toggle all possible update roles, except bot. Use .help toggleroles to see possible roles."""
        toggle_roles = [
            discord.utils.get(ctx.guild.roles, id=int(self.role_mentions_dict["3ds"])),
            discord.utils.get(ctx.guild.roles, id=int(self.role_mentions_dict["switch"]))
        ]
        user = ctx.message.author
        for role in toggle_roles:
            await self.toggleroles(ctx, role, user)
        await ctx.send("{} Successfully toggled all possible roles.".format(user.mention))

    @commands.command(aliases=['brm'])
    @commands.has_any_role("Discord Moderator", "FlagBrew Team", "Bot Dev")
    async def role_mention_bot(self, ctx):
        """Securely mention anyone with the bot updates role"""
        role = discord.utils.get(ctx.guild.roles, id=int(self.role_mentions_dict['bot']))
        try:
            await role.edit(mentionable=True, reason="{} wanted to mention users with this role.".format(ctx.author))  # Reason -> Helps pointing out folks that abuse this
        except:
            await role.edit(mentionable=True, reason="A staff member, or Griffin, wanted to mention users with this role, and I couldn't log properly. Check {}.".format(self.bot.logs_channel.mention))  # Bypass the TypeError it kept throwing
        await ctx.channel.send("{}".format(role.mention))
        await role.edit(mentionable=False, reason="Making role unmentionable again.")
        try:
            await self.bot.logs_channel.send("{} pinged bot updates in {}".format(ctx.author, ctx.channel))
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
            await role.edit(mentionable=True, reason="{} wanted to mention users with this role.".format(ctx.author))  # Reason -> Helps pointing out folks that abuse this
        except:
            await role.edit(mentionable=True, reason="A staff member wanted to mention users with this role, and I couldn't log properly. Check {}.".format(self.bot.logs_channel.mention))  # Bypass the TypeError it kept throwing
        await channel.send("{}".format(role.mention))
        await role.edit(mentionable=False, reason="Making role unmentionable again.")
        try:
            await self.bot.logs_channel.send("{} pinged {} in {}".format(ctx.author, role.name, channel))
        except discord.Forbidden:
            pass  # beta bot can't log

    @commands.command(aliases=['srm_list'])
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    async def secure_role_mention_list(self, ctx):
        """Lists all available roles for srm"""
        embed = discord.Embed(title="Mentionable Roles")
        embed.description = "\n".join(self.role_mentions_dict)
        embed.description += "\nflagbrew"
        await ctx.send(embed=embed)

    @commands.command(aliases=['srm_add'])
    @commands.has_any_role("Discord Moderator")
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
        await ctx.send("`{}` can now be mentioned via srm.".format(role_name.lower()))
        try:
            await self.bot.logs_channel.send("{} added {} to the mentionable roles.".format(ctx.author, role_name.lower()))
        except discord.Forbidden:
            pass # beta bot can't log

    @commands.command(aliases=['srm_remove'])
    @commands.has_any_role("Discord Moderator")
    async def secure_role_mention_remove(self, ctx, role_name):
        """Allows removing a role from the dict for secure_role_mention. Role_name should be the name that is used when srm is called"""
        try:
            self.role_mentions_dict[role_name.lower()]
        except KeyError:
            return await ctx.send("That role isn't in the dict. Please use `.srm_list` to confirm.")
        del self.role_mentions_dict[role_name.lower()]
        with open("saves/role_mentions.json", "w") as f:
            json.dump(self.role_mentions_dict, f, indent=4)
        await ctx.send("`{}` can no longer be mentioned via srm.".format(role_name.lower()))
        try:
            await self.bot.logs_channel.send("{} removed {} from the mentionable roles.".format(ctx.author, role_name.lower()))
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
    async def regen_token(self, ctx, user: discord.Member, old_token: str):
        """Regenerates a patron's token"""
        new_token = secrets.token_urlsafe(16)
        data = {
            "secret": self.bot.site_secret,
            "user_id": str(user.id),
            "token": new_token,
            "old_token": old_token
        }
        url = "https://flagbrew.org/patron/regen"
        async with self.bot.session.post(url=url, data=data):
            pass
        message = ("Your patron token for PKSM was regenerated by staff on FlagBrew. Your new token is `{}`."
                   " In case you forgot, to access the hidden Patron settings menu, press the four corners of the touch screen while on the configuration screen."
                   " Until you update your token, you won't be able to use the patron specific features.".format(new_token))
        qr = self.gen_token_qr(new_token)
        try:
            await user.send(message, file=qr)
        except discord.Forbidden:
            await ctx.author.send("Could not message user {} about regenerated token. Please reach out manually. Message below.\n\n{}".format(user, message))
        await ctx.send("Token regenerated for {}".format(user))

    @commands.command()
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    async def delete_token(self, ctx, user: discord.Member, *, reason="No reason provided"):
        """Deletes a patron's token"""
        data = {
            "secret": self.bot.site_secret,
            "user_id": str(user.id)
        }
        url = "https://flagbrew.org/patron/remove"
        message = "Your patron token has been revoked for reason: `{}`. If you feel this has been done in error, please contact a member of the FlagBrew team.".format(reason)
        async with self.bot.session.post(url=url, data=data):
            pass
        try:
            await user.send(message)
        except discord.Forbidden:
            await ctx.author.send("Could not message user {} about token deletion. Please reach out manually. Message below.\n\n{}".format(user, message))
        await ctx.send("Token for user {} successfully deleted.".format(user))

    @commands.command()
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    async def generate_token(self, ctx, user: discord.Member):
        """Generates a patron token. If user already in system, use regen_token"""
        token = secrets.token_urlsafe(16)
        data = {
            "secret": self.bot.site_secret,
            "user_id": str(user.id),
            "token": token
        }
        url = "https://flagbrew.org/patron/generate"
        message = ("You have had a patron token generated for you! You can add the token below to PKSM's config to access some special patron only stuff."
                   " To access the hidden Patron settings menu, press the four corners of the touch screen while on the configuration screen."
                   " If you need any further help setting it up, ask in {}!\n\n`{}`".format(self.bot.patrons_channel.mention, token))
        async with self.bot.session.post(url=url, data=data):
            pass
        qr = self.gen_token_qr(token)
        try:
            await user.send(message, file=qr)
        except discord.Forbidden:
            await ctx.author.send("Could not message user {} about token generation. Please reach out manually. Message below.\n\n{}".format(user, message))
        await ctx.send("Token for user {} successfully generated.".format(user))

    @commands.command(aliases=['report', 'rc'])  # Modified from https://gist.github.com/JeffPaine/3145490
    async def report_code(self, ctx, game_id: str, code_name: str, issue):
        """Allow reporting a broken code through the bot. Example: .report_code 00040000001B5000, 'PP Not Decrease v1.0', 'PP still decreases with code enabled'"""
        async with self.bot.session.get("https://api.github.com/repos/FlagBrew/Sharkive/contents/3ds") as r:
            db_3ds = await r.json()
        async with self.bot.session.get("https://api.github.com/repos/FlagBrew/Sharkive/contents/switch") as r:
            db_switch = await r.json()
        content_3ds = [x['name'].replace(".txt", "") for x in db_3ds]
        content_switch = [x['name'] for x in db_switch]
        if game_id not in content_3ds and game_id not in content_switch:
            return await ctx.send("That game ID isn't in the database! Please confirm the game is in the database.")
        elif game_id in content_3ds and game_id not in content_switch:
            console = "3DS"
        else:
            console = "Switch"
        repo_owner = "FlagBrew"
        repo_name = "Sharkive"
        url = "https://api.github.com/repos/{}/{}/issues".format(repo_owner, repo_name)
        session_auth = aiohttp.BasicAuth(self.bot.github_user, self.bot.github_pass)
        issue_body = "Game ID: {}\nConsole: {}\nCode name: {}\n\n Issue: {}\n\n Submitted by: {} | User id: {}".format(game_id, console, code_name, issue, ctx.author, ctx.author.id)
        issue = {
            "title": "Broken code submitted through bot",
            "body": issue_body
        }
        async with self.bot.session.post(url=url, auth=session_auth, data=json.dumps(issue)) as r:
            json_content = await r.json()
            if r.status == 201:
                await ctx.send("Successfully created issue! You can find it here: https://github.com/{}/{}/issues/{}".format(repo_owner, repo_name, json_content["number"]))
            else:
                status_name = http.HTTPStatus(r.status).name  # pylint: disable=no-member
                await ctx.send("There was an issue creating the issue. {} please take a look.\n\n`{}` - `{}`".format(self.bot.creator.mention, r.status, status_name))

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
        await msg.edit(content="{} users would be kicked as a result of a prune.".format(prune_amount))

    @commands.command()
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
                return await ctx.send("There is no command named `{}`.".format(command))
            self.bot.disabled_commands.append(command)
            with open('saves/disabled_commands.json', 'w') as f:
                json.dump(self.bot.disabled_commands, f, indent=4)
            return await ctx.send("Successfully disabled the `{}` command.".format(command))
        try:
            self.bot.get_command(command).enabled = True
        except AttributeError:
            return await ctx.send("There is no command named `{}`.".format(command))
        self.bot.disabled_commands.remove(command)
        with open('saves/disabled_commands.json', 'w') as f:
            json.dump(self.bot.disabled_commands, f, indent=4)
        await ctx.send("Successfully re-enabled the `{}` command.".format(command))

    @commands.command(hidden=True)
    async def listdisabled(self, ctx):
        """Lists disabled commands"""
        if len(self.bot.disabled_commands) == 0:
            return await ctx.send("There are currently no disabled commands.")
        await ctx.send("```{}```".format(",\n".join(c for c in self.bot.disabled_commands)))

    @commands.command()
    @commands.has_any_role("Discord Moderator")
    async def dm(self, ctx, user: discord.User, *, message):
        """DMs a user"""
        if user == ctx.me:
            return await ctx.send("{} I can't DM myself, you snarky little shit.".format(ctx.author.mention))
        try:
            await user.send(message)
        except discord.Forbidden:
            await ctx.send("Failed to DM the user. Do they have me blocked? 😢")
        else:
            await self.bot.logs_channel.send("Message sent to {} by {}.".format(user, ctx.author), embed=discord.Embed(description=message))

    def get_hash(self, file): # Src: https://www.programiz.com/python-programming/examples/hash-file
        h = hashlib.sha1()
        chunk = 0
        while chunk != b'':
            chunk = file.read(1024)
            h.update(chunk)
        return h.hexdigest()

    @commands.command(aliases=['scd'])
    async def submit_crash_dump(self, ctx, *, description):
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
        msg = await self.bot.crash_log_channel.send("Dump submitted by {}".format(ctx.author), file=file_log)
        embed = discord.Embed(title="New Crash Dump!")
        embed.add_field(name="Submitted By", value=ctx.author.mention)
        embed.add_field(name="Submitted At", value=ctx.message.created_at.strftime('%b %d, %Y'))
        async with self.bot.session.get("https://api.github.com/repos/FlagBrew/PKSM/commits/master") as r:
            commit = await r.json()
        commit_sha = commit["sha"][:7]
        embed.add_field(name="Latest Commit", value=commit_sha)
        embed.add_field(name="File Download URL", value="[Download]({})".format(msg.attachments[0].url))
        embed.add_field(name="Description of issue", value=description, inline=False)
        embed.set_footer(text="The hash for this file is {}".format(file_hash))
        await self.bot.crash_dump_channel.send(embed=embed)
        self.submitted_hashes.append(file_hash)
        with open("saves/submitted_hashes.json", "w") as f:
            json.dump(self.submitted_hashes, f, indent=4)
        await ctx.send("{} your crash dump was successfully submitted!".format(ctx.author.mention))

    @commands.command()
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
        async with self.bot.session.post(url=url, data=data) as r:
            if not r.status in (200, 410):
                return await ctx.send("Failed to post the banned word to the server. Status code: `{}`.".format(r.status))
            elif r.status == 410:
                return await ctx.send("Successfully unbanned the word `{}` from the GPSS.".format(word))
            await ctx.send("Successfully banned the word `{}` from the GPSS.".format(word))


def setup(bot):
    bot.add_cog(Utility(bot))