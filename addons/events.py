#!/usr/bin/env python3

import discord
import secrets
import qrcode
import io
import time
import json
import re
import addons.helper as helper
from discord.ext import commands
from datetime import timedelta


class Events(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        if bot.is_mongodb:
            self.db = bot.db
        print(f'Addon "{self.__class__.__name__}" loaded')

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        # Don't let the bot be used elsewhere with the same token
        if guild.id != self.bot.testing_id and guild.id != self.bot.flagbrew_id:
            try:
                await guild.owner.send(f"Left your server, `{guild.name}`, as this bot should only be used on the PKSM server under this token.")
            except discord.Forbidden:
                for channel in guild.channels:
                    if channel.permissions_for(guild.me).send_messages and isinstance(channel, discord.TextChannel):
                        await channel.send("Left your server, as this bot should only be used on the PKSM server under this token.")
                        break
            finally:
                await guild.leave()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if self.bot.is_beta:
            return
        try:
            mute_exp = self.bot.mutes_dict[str(member.id)]
        except KeyError:
            mute_exp = ""
        embed = discord.Embed(title="New member!")
        embed.description = f"{member.mention} | {member.name}#{member.discriminator} | {member.id}"
        within_last_week = discord.utils.utcnow() - timedelta(days=7)
        if member.created_at > within_last_week:
            embed.description += f"\n**Account was created {(discord.utils.utcnow() - member.created_at).days} days ago.**"
        if mute_exp != "" and not await helper.check_mute_expiry(self.bot.mutes_dict, member):
            embed.add_field(name="Muted Until", value=mute_exp + " UTC")
            await member.add_roles(self.bot.mute_role)
        if member.id in self.bot.gpss_bans_array:
            embed.description += "\n**User is GPSS Banned.**"
            await member.add_roles(self.bot.gpss_banned_role)
        try:
            await member.send(f"Welcome to {member.guild.name}! Please read the rules, as you won't be able to access the majority of the server otherwise. This is an automated message, no reply is necessary.")
        except discord.Forbidden:
            embed.description += "\n**Failed to DM user on join.**"
        kick_invite_uses = (inv.uses for inv in (await member.guild.invites()) if inv.code == '95U8FEKZFZ')
        try:
            kick_invite_count = self.bot.persistent_vars_dict['kick_invite_count']
        except KeyError:
            kick_invite_count = 0
        if next(kick_invite_uses) > kick_invite_count:
            self.bot.persistent_vars_dict['kick_invite_count'] = kick_invite_count + 1
            embed.description += "\n**User joined off of an invite sent with a kick.**"
            with open('saves/persistent_vars.json', 'w') as file:
                json.dump(self.bot.persistent_vars_dict, file, indent=4)
        if member.guild.id == self.bot.flagbrew_id:
            await self.bot.logs_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if self.bot.is_beta:
            return
        embed = discord.Embed(title="Member left :(")
        embed.description = f"{member.mention} | {member.name}#{member.discriminator} | {member.id}"
        if member.guild.id == self.bot.flagbrew_id:
            await self.bot.logs_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        # if self.bot.is_beta:
        #     return
        # auto ban on 15+ pings
        if len(message.mentions) > 15:
            await message.delete()
            await message.author.ban()
            await message.channel.send(f"{message.author} was banned for attempting to spam user mentions.")

        # log dm messages
        if not isinstance(message.channel, discord.threads.Thread) and isinstance(message.channel, discord.abc.PrivateChannel) and not message.author == self.bot.guild.me:
            if message.content == "" and len(message.attachments) == 0:
                return
            guild = self.bot.get_guild(self.bot.flagbrew_id)
            member = guild.get_member(message.author.id)
            if 885261003544223744 in (role.id for role in member.roles):
                return
            attachments = []
            if len(message.attachments) > 0:
                for attachment in message.attachments:
                    attch = await attachment.to_file()
                    attachments.append(attch)
            embed = discord.Embed(description=message.content) if message.content != "" else None
            invites = re.findall(r"(discord\.gg)\/([\w\d]+)", message.content)
            if invites is not None:
                for inv in invites:
                    inv = "/".join(inv)
                    print(inv)
                    try:
                        inv = await self.bot.fetch_invite(inv)
                    except discord.NotFound:
                        continue
                    embed.add_field(name="Invite found in message", value=f"Guild name: `{inv.guild.name}`", inline=False)
            await self.bot.dm_logs_channel.send(f"New DM received from {message.author} | {message.author.id}.", embed=embed, files=attachments)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if self.bot.is_beta:
            return
        if isinstance(message.channel, discord.abc.GuildChannel) or isinstance(message.channel, discord.threads.Thread) and message.author.id != self.bot.user.id and message.guild.id == self.bot.flagbrew_id:
            if message.channel != self.bot.logs_channel:
                if not message.content or message.type == discord.MessageType.pins_add:
                    return
                embed = discord.Embed(description=message.content)
                if message.reference is not None:
                    ref = message.reference.resolved
                    embed.add_field(name="Replied To", value=f"[{'@' if len(message.mentions) > 0 and ref.author in message.mentions else ''}{ref.author}]({ref.jump_url}) ({ref.author.id})")
                if isinstance(message.channel, discord.threads.Thread):
                    embed.add_field(name="Thread Location", value=f"{message.channel.parent.mention} ({message.channel.parent.id})", inline=False)
                await self.bot.logs_channel.send(f"Message by {message.author} ({message.author.id}) deleted in {'thread' if isinstance(message.channel, discord.threads.Thread) else 'channel'} {message.channel.mention}:", embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if self.bot.is_beta:
            return
        if isinstance(before.channel, discord.abc.GuildChannel) and before.author.id != self.bot.user.id and before.guild.id == self.bot.flagbrew_id:
            if before.channel != self.bot.logs_channel and not before.author.bot:
                embed = discord.Embed()
                if len(before.content) < 1024 and len(after.content) < 1024:
                    embed.add_field(name="Original Message", value=before.content, inline=False)
                    embed.add_field(name="Edited Message", value=after.content, inline=False)
                else:
                    content = before.content + "\n\n>>>>>>>>>>>>>>>>>>>>\n\n" + after.content
                    bytes_content = bytes(content, 'utf-8')
                    file = discord.File(io.BytesIO(bytes_content), filename="edited_message_content.txt")
                embed.add_field(name="Jump URL", value=f"[Here]({before.jump_url})", inline=False)
                if before.reference is not None:
                    ref = before.reference.resolved
                    embed.add_field(name="Replied To:", value=f"[{ref.author}]({ref.jump_url}) ({ref.author.id})")
                if "file" in locals():
                    return await self.bot.logs_channel.send(f"Message by {before.author} ({before.author.id}) edited in channel {before.channel.mention}:", embed=embed, file=file)
                await self.bot.logs_channel.send(f"Message by {before.author} ({before.author.id}) edited in channel {before.channel.mention}:", embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if not self.bot.ready or self.bot.is_beta:
            return

        # Handle token stuff
        if self.bot.is_mongodb:
            token_roles = (self.bot.flagbrew_team_role, self.bot.patrons_role)
            has_roles = len(list(role for role in token_roles if role in before.roles or role in after.roles)) > 0  # True if member has one of the roles in token_roles, else False
            if before.roles != after.roles and has_roles:
                token = secrets.token_urlsafe(16)
                self.db['patrons'].update_one(
                    {
                        "discord_id": str(before.id)
                    },
                    {
                        "$set": {
                            "discord_id": str(before.id),
                            "code": token
                        }
                    }, upsert=True)
                if len(before.roles) < len(after.roles):
                    await self.bot.patrons_channel.send(f"Welcome to the super secret cool kids club {after.mention}!"
                                                        " You can find up to date PKSM builds by using the `.genqr` command, and all patron news will be role pinged in <#330065133978255360>.")
                    message = ("Congrats on becoming a patron! You can add the token below to PKSM's config to access some special patron only stuff. It's only valid until your"
                               " patron status is cancelled, so keep up those payments!"
                               " To access the hidden Patron settings menu, press the four corners of the touch screen while on the configuration screen."
                               " You can read more on Patron specific features here: https://github.com/FlagBrew/PKSM/wiki/Patron-Features."
                               f" If you need any further help setting it up, ask in {self.bot.patrons_channel.mention}!\n\n`{token}`")
                    qr = qrcode.QRCode(version=None)
                    qr.add_data(token)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="black", back_color="white")
                    bytes = io.BytesIO()
                    img.save(bytes, format='PNG')
                    bytes = bytes.getvalue()
                    qr_file = discord.File(io.BytesIO(bytes), filename="qr.png")
                elif len(before.roles) > len(after.roles) and (self.bot.patrons_role in before.roles and self.bot.patrons_role not in after.roles):
                    message = ("Unfortunately, your patreon subscription has been cancelled, or stopped renewing automatically. This means your token, and the special features,"
                               " have all expired. If you do end up renewing your subscription at a later date, you will recieve a new token.")
                    self.db['patrons'].delete_one({"discord_id": str(before.id)})
                    qr_file = None
                else:
                    return  # cancel out for none of this shit
                try:
                    await before.send(message, file=qr_file)
                except discord.Forbidden:
                    if len(before.roles) < len(after.roles):
                        await self.bot.fetch_user(211923158423306243).send(f"Could not send token `{token}` to user {before}.")
                    else:
                        await self.bot.fetch_user(211923158423306243).send(f"Could not notify user {before} of token expiration.")

        # Handle nick logging
        elif before.nick != after.nick:
            embed = discord.Embed(title="Nickname Change!")
            embed.description = f"{before} | {before.id} changed their nickname from `{before.nick}` to `{after.nick}`."
            await self.bot.logs_channel.send(embed=embed)

        # Handle timeout application logging - can't easily log expiry rn so not gonna do that
        elif not before.is_timed_out() and after.is_timed_out():
            async for timeout in after.guild.audit_logs(limit=20, action=discord.AuditLogAction.member_update):  # 20 to handle multiple staff timeouts in quick succession
                try:
                    if not timeout.after.timed_out_until:
                        return
                    elif timeout.target == after:
                        if timeout.reason:
                            reason = timeout.reason
                        else:
                            reason = "No reason was given. Please do that in the future!"
                        admin = timeout.user
                        break
                    else:
                        return
                except AttributeError:
                    return  # Weird bug where AuditLogDiff has no timed_out_until attribute
            embed = discord.Embed(title=f"{after} timed out")
            embed.add_field(name="Member", value=f"{after.mention} ({after.id})")
            embed.add_field(name="Timed out by", value=admin)
            embed.add_field(name="Timed out until", value=discord.utils.format_dt(after.timed_out_until), inline=False)
            embed.add_field(name="Reason", value=reason)
            await self.bot.logs_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        if not self.bot.ready or self.bot.is_beta:
            return
        if 1:
            return  # Temporarily disable this
        blacklist = [
            "Spotify",
            "Google Chrome",
            "Twitter",
            "Minecraft",
            "YouTube",
            "Netflix",
            "Firefox",
            " "
        ]
        if before.activities != after.activities:
            bef_custom = ()
            aft_custom = ()
            bef_acts = [activity.name for activity in before.activities if not isinstance(activity, discord.CustomActivity) and activity.name not in blacklist]
            aft_acts = [activity.name for activity in after.activities if not isinstance(activity, discord.CustomActivity) and activity.name not in blacklist]
            for activity in before.activities:
                if isinstance(activity, discord.CustomActivity):
                    if activity.emoji:
                        bef_custom = (activity.name, activity.emoji.name)
                    else:
                        bef_custom = (activity.name, "No Emoji")
            for activity in after.activities:
                if isinstance(activity, discord.CustomActivity) and not activity.name == " ":
                    if activity.emoji:
                        aft_custom = (activity.name, activity.emoji.name)
                    else:
                        aft_custom = (activity.name, "No Emoji")

            # Handle generic activities
            if len(aft_acts) + len(bef_acts) > 0 and not bef_acts == aft_acts:
                if (len(bef_acts) > 1 and bef_acts[0] == bef_acts[1]) or (len(aft_acts) > 1 and aft_acts[0] == aft_acts[1]):
                    return
                embed = discord.Embed(title="Activity Change!", colour=discord.Colour.blue())
                embed.description = f"{before} | {before.id} changed their activity."
                embed.add_field(name="Old Activities", value=(", ".join(bef_acts) if len(bef_acts) > 0 else "None"))
                embed.add_field(name="New Activities", value=(", ".join(aft_acts) if len(aft_acts) > 0 else "None"))
                try:
                    await self.bot.activity_logs_channel.send(embed=embed)
                except (discord.Forbidden, discord.DiscordServerError):
                    pass
                except discord.RateLimited:
                    await time.sleep(2)
                    await self.bot.activity_logs_channel.send(embed=embed)
                except Exception as e:
                    if len(before.activities) == 0 or len(after.activities) == 0:
                        return
                    await self.bot.err_logs_channel.send(f"Failed to log activity for user `{before}` (`{before.id}`) with before activity list of `{before.activities}` and after activity list of `{after.activities}`. Cause?")
                    await self.bot.err_logs_channel.send(embed=discord.Embed(description=e))

            # Handle custom activities
            if len(aft_custom) + len(bef_custom) > 0 and not bef_custom == aft_custom:
                if len(bef_custom) == 0:
                    bef_custom = ("None", "None")
                if len(aft_custom) == 0:
                    aft_custom = ("None", "None")
                if bef_custom[0] == aft_custom[0] and bef_custom[1] == aft_custom[1]:
                    return
                embed = discord.Embed(title="Custom Activity Change!", colour=discord.Colour.red())
                embed.description = f"{before} | {before.id} changed their custom activity."
                embed.add_field(name="Old Custom Activity", value=f"Name: `{bef_custom[0]}`\nEmoji: `{bef_custom[1]}`")
                embed.add_field(name="New Custom Activity", value=f"Name: `{aft_custom[0]}`\nEmoji: `{aft_custom[1]}`")
                try:
                    await self.bot.activity_logs_channel.send(embed=embed)
                except (discord.Forbidden, discord.DiscordServerError):
                    pass
                except Exception as e:
                    await self.bot.err_logs_channel.send(f"Failed to log activity for user `{before}` (`{before.id}`) with before activity list of `{before.activities}` and after activity list of `{after.activities}`. Cause?")
                    await self.bot.err_logs_channel.send(embed=discord.Embed(description=e))

    async def process_reactions(self, reaction):
        positive_votes = 0
        negative_votes = 0
        vote_barrier = 3
        reactions = reaction.message.reactions
        for react in reactions:
            if '🆒' == react.emoji:
                users = await react.users().flatten()
                for u in users:
                    if self.bot.flagbrew_team_role in u.roles:
                        if reaction.message.pinned:
                            await reaction.message.unpin()
                        return  # Used to signify idea is implemented
            if '✅' == react.emoji:
                positive_votes = react.count
            if '❌' == react.emoji:
                negative_votes = react.count
        total_votes = positive_votes - negative_votes
        if total_votes >= vote_barrier and not reaction.message.pinned:
            try:
                await reaction.message.pin()
                await self.bot.logs_channel.send(f"Idea pinned after passing {vote_barrier} votes.\nJump link: {reaction.message.jump_url}")
            except discord.HTTPException as exception:
                await reaction.message.channel.send("Error pinning message. Please make sure that there are less than 50 pins."
                                                    f" If issue persists, contact {self.bot.creator}.\nMessage link: {reaction.message.jump_url}")
                await self.bot.err_logs_channel.send(exception.text)
        elif total_votes < vote_barrier and reaction.message.pinned:
            await reaction.message.unpin()
            await self.bot.logs_channel.send(f"Idea unpinned due to falling below {vote_barrier} votes.\nJump link: {reaction.message.jump_url}")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.channel.id == 509857867726192641:
            await self.process_reactions(reaction)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if reaction.message.channel.id == 509857867726192641:
            await self.process_reactions(reaction)

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        embed = discord.Embed(title="New thread created!")
        embed.add_field(name="Created By", value=f"{thread.owner} ({thread.owner_id})")
        embed.add_field(name="Thread Name", value=thread.name, inline=False)
        embed.add_field(name="Created At", value=discord.utils.format_dt(thread.created_at), inline=False)
        await thread.join()
        auto_thread_joins = [
            self.bot.creator,
            self.bot.allen,
            self.bot.pie
        ]
        for member in auto_thread_joins:
            await thread.add_user(member)
        await self.bot.logs_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_thread_update(self, before, after):
        if after.archived:
            embed = discord.Embed(title="Thread Archived")
            embed.add_field(name="Thread Name", value=after.name, inline=False)
            embed.add_field(name="Archived At", value=discord.utils.format_dt(after.archive_timestamp), inline=False)
            embed.add_field(name="Thread Owner", value=f"{after.owner} ({after.owner.id})")
        else:
            return
        await self.bot.logs_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        embed = discord.Embed(title="Thread Deleted!")
        embed.add_field(name="Thread Name", value=thread.name, inline=False)
        embed.add_field(name="Created At", value=discord.utils.format_dt(thread.created_at), inline=False)
        embed.add_field(name="Thread Owner", value=f"{thread.owner} ({thread.owner_id})")
        await self.bot.logs_channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Events(bot))
