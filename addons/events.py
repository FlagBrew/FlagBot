#!/usr/bin/env python3

import discord
import secrets
import qrcode
import io
import sys
import addons.helper as helper
from discord.ext import commands
from datetime import datetime


class Events(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
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
                    if guild.me.permissions_in(channel).send_messages and isinstance(channel, discord.TextChannel):
                        await channel.send("Left your server, as this bot should only be used on the PKSM server under this token.")
                        break
            finally:
                await guild.leave()

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        try:
            async for ban in guild.audit_logs(limit=20, action=discord.AuditLogAction.ban):  # 20 to handle multiple staff bans in quick succession
                if ban.target == user:
                    if ban.reason:
                        reason = ban.reason
                    else:
                        reason = "No reason was given. Please do that in the future!"
                    admin = ban.user
                    break
                else:
                    return
            embed = discord.Embed(title=f"{user} banned")
            embed.description = f"{user} was banned by {admin} for:\n\n{reason}"
            await self.bot.logs_channel.send(embed=embed)
        except discord.Forbidden:
            pass  # beta bot can't log

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            mute_exp = self.bot.mutes_dict[str(member.id)]
        except KeyError:
            mute_exp = ""
        embed = discord.Embed(title="New member!")
        embed.description = f"{member.mention} | {member.name}#{member.discriminator} | {member.id}"
        if (datetime.now() - member.created_at).days < 1:
            embed.description += f"\n**Account was created {(datetime.now() - member.created_at).days} days ago.**"
        if mute_exp != "" and not await helper.check_mute_expiry(self.bot.mutes_dict, member):
            embed.add_field(name="Muted Until", value=mute_exp + " UTC")
            await member.add_roles(self.bot.mute_role)
        try:
            await member.send(f"Welcome to {member.guild.name}! Please read the rules, as you won't be able to access the majority of the server otherwise. This is an automated message, no reply is necessary.")
        except discord.Forbidden:
            embed.description += "\n**Failed to DM user on join.**"
        if member.guild.id == self.bot.flagbrew_id:
            try:
                await self.bot.logs_channel.send(embed=embed)
            except discord.Forbidden:
                pass  # beta bot can't log

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        embed = discord.Embed(title="Member left :(")
        embed.description = f"{member.mention} | {member.name}#{member.discriminator} | {member.id}"
        if member.guild.id == self.bot.flagbrew_id:
            try:
                await self.bot.logs_channel.send(embed=embed)
            except discord.Forbidden:
                pass  # beta bot can't log

    @commands.Cog.listener()
    async def on_message(self, message):
        # auto ban on 15+ pings
        if len(message.mentions) > 15:
            await message.delete()
            await message.author.ban()
            await message.channel.send(f"{message.author} was banned for attempting to spam user mentions.")

        # auto restart on update
        if message.channel.id == 672536257934655529:
            if message.webhook_id == 482998461646766080 and "new commits" in message.embeds[0].title:
                sys.exit(0)

        # log dm messages
        if isinstance(message.channel, discord.abc.PrivateChannel) and not message.author == self.bot.guild.me:
            if not message.content:
                return
            embed = discord.Embed(description=message.content)
            try:
                await self.bot.dm_logs_channel.send(f"New DM recieved from {message.author} | {message.author.id}.", embed=embed)
            except discord.Forbidden:
                pass  # beta bot can't log

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if isinstance(message.channel, discord.abc.GuildChannel) and message.author.id != self.bot.user.id and message.guild.id == self.bot.flagbrew_id:
            if message.channel != self.bot.logs_channel:
                if not message.content:
                    return
                embed = discord.Embed(description=message.content)
                try:
                    await self.bot.logs_channel.send(f"Message by {message.author} deleted in channel {message.channel.mention}:", embed=embed)
                except discord.Forbidden:
                    pass  # beta bot can't log

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if not self.bot.ready:
            return

        # Handle token stuff
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
                                                    " You can find up to date PKSM builds in <#531117773754073128>, and all patron news will be role pinged in <#330065133978255360>.")
                message = ("Congrats on becoming a patron! You can add the token below to PKSM's config to access some special patron only stuff. It's only valid until your"
                           " patron status is cancelled, so keep up those payments!"
                           " To access the hidden Patron settings menu, press the four corners of the touch screen while on the configuration screen."
                           f" If you need any further help setting it up, ask in {self.bot.patrons_channel.mention}!\n\n`{token}`")
                qr = qrcode.QRCode(version=None)
                qr.add_data(token)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                bytes = io.BytesIO()
                img.save(bytes, format='PNG')
                bytes = bytes.getvalue()
                f = discord.File(io.BytesIO(bytes), filename="qr.png")
            else:
                message = ("Unfortunately, your patreon subscription has been cancelled, or stopped renewing automatically. This means your token, and the special features,"
                           " have all expired. If you do end up renewing your subscription at a later date, you will recieve a new token.")
                self.db['patrons'].delete_one({"discord_id": str(before.id)})
                f = None
            try:
                await before.send(message, file=f)
            except discord.Forbidden:
                if len(before.roles) < len(after.roles):
                    await self.bot.fetch_user(211923158423306243).send(f"Could not send token `{token}` to user {before}.")
                else:
                    await self.bot.fetch_user(211923158423306243).send(f"Could not notify user {before} of token expiration.")

        # Handle nick logging
        elif before.nick != after.nick:
            embed = discord.Embed(title="Nickname Change!")
            embed.description = f"{before} | {before.id} changed their nickname from `{before.nick}` to `{after.nick}`."
            try:
                await self.bot.logs_channel.send(embed=embed)
            except discord.Forbidden:
                pass

        # Handle activity logging
        elif before.activities != after.activities:
            has_activity = True
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
            embed = discord.Embed(title="Activity Change!", colour=discord.Colour.blue())
            bef_custom = ()
            aft_custom = ()
            for activity in before.activities:
                if isinstance(activity, discord.CustomActivity):
                    if not activity.emoji:
                        bef_custom = (activity.name, "No Emoji")
                    else:
                        bef_custom = (activity.name, activity.emoji.name)
            for activity in after.activities:
                if isinstance(activity, discord.CustomActivity):
                    if activity.name == " ":
                        continue
                    if not activity.emoji:
                        aft_custom = (activity.name, "No Emoji")
                    else:
                        aft_custom = (activity.name, activity.emoji.name)
            bef_acts = [activity.name for activity in before.activities if not isinstance(activity, discord.CustomActivity) and activity.name not in blacklist]
            aft_acts = [activity.name for activity in after.activities if not isinstance(activity, discord.CustomActivity) and activity.name not in blacklist]
            if len(aft_acts) == 0:
                has_activity = False
            elif bef_acts == aft_acts and bef_custom == aft_custom:
                return
            embed.description = f"{before} | {before.id} changed their activity."
            embed.add_field(name="Old Activities", value=(", ".join(bef_acts) if len(bef_acts) > 0 else "None"))
            embed.add_field(name="New Activities", value=(", ".join(aft_acts)))
            if has_activity:
                try:
                    await self.bot.activity_logs_channel.send(embed=embed)
                except discord.Forbidden:
                    pass
                except:
                    if len(before.activities) == 0 or len(after.activities) == 0:
                        return
                    else:
                        if (len(bef_acts) > 1 and bef_acts[0] == bef_acts[1]) or (len(aft_acts) > 1 and aft_acts[0] == aft_acts[1]):
                            return
                    await self.bot.err_logs_channel.send(f"Failed to log activity for user `{before}` (`{before.id}`) with before activity list of `{before.activities}` and after activity list of `{after.activities}`. Cause?")
            if len(aft_custom) == 0 and len(bef_custom) == 0:
                return

            if len(aft_custom) == 0:
                return
            elif len(bef_custom) == 0:
                bef_custom = ("None", "None")
            elif bef_custom[0] == aft_custom[0] and bef_custom[1] == aft_custom[1]:
                return
            embed_custom = discord.Embed(title="Custom Activity Change!", colour=discord.Colour.red())
            embed_custom.description = f"{before} | {before.id} changed their custom activity."
            embed_custom.add_field(name="Old Custom Activity", value=f"Name: `{bef_custom[0]}`\nEmoji: `{bef_custom[1]}`")
            embed_custom.add_field(name="New Custom Activity", value=f"Name: `{aft_custom[0]}`\nEmoji: `{aft_custom[1]}`")
            try:
                await self.bot.activity_logs_channel.send(embed=embed_custom)
            except discord.Forbidden:
                pass
            except:
                await self.bot.err_logs_channel.send(f"Failed to log activity for user `{before}` (`{before.id}`) with before activity list of `{before.activities}` and after activity list of `{after.activities}`. Cause?")

    async def process_reactions(self, reaction):
        positive_votes = 0
        negative_votes = 0
        vote_barrier = 3
        reactions = reaction.message.reactions
        for r in reactions:
            if '🆒' == r.emoji:
                users = await r.users().flatten()
                for u in users:
                    if self.bot.flagbrew_team_role in u.roles:
                        if reaction.message.pinned:
                            await reaction.message.unpin()
                        return  # Used to signify idea is implemented
            if '✅' == r.emoji:
                positive_votes = r.count
            if '❌' == r.emoji:
                negative_votes = r.count
        total_votes = positive_votes - negative_votes
        if total_votes >= vote_barrier and not reaction.message.pinned:
            try:
                await reaction.message.pin()
                await self.bot.logs_channel.send(f"Idea pinned after passing {vote_barrier} votes.\nJump link: {reaction.message.jump_url}")
            except discord.HTTPException as e:
                await reaction.message.channel.send("Error pinning message. Please make sure that there are less than 50 pins."
                                                    f" If issue persists, contact {self.bot.creator}.\nMessage link: {reaction.message.jump_url}")
                await self.bot.err_logs_channel.send(e.text)
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


def setup(bot):
    bot.add_cog(Events(bot))
