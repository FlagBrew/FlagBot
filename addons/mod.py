#!/usr/bin/env python3

import discord
from discord.ext import commands
import os
import sys
import json
import asyncio
import random
import io
from datetime import timedelta
import addons.helper as helper


class Moderation(commands.Cog):
    """Bot commands for moderation."""
    def __init__(self, bot):
        self.bot = bot
        self.ban_attch_dict = {}
        self.mute_loop = bot.loop.create_task(self.check_mute_loop())  # loops referenced from https://github.com/chenzw95/porygon/blob/aa2454336230d7bc30a7dd715e057ee51d0e1393/cogs/mod.py#L23
        print(f'Addon "{self.__class__.__name__}" loaded')

    def cog_unload(self):
        self.mute_loop.cancel()

    async def check_mute_loop(self):
        guild = self.bot.get_guild(self.bot.flagbrew_id)
        while not self.bot.is_closed():
            for m in self.bot.mutes_dict.keys():
                member = guild.get_member(int(m))
                if member is None:
                    continue
                is_expired = await helper.check_mute_expiry(self.bot.mutes_dict, member)
                if not is_expired or self.bot.mutes_dict[str(member.id)] == "":
                    continue
                await member.remove_roles(self.bot.mute_role)
                self.bot.mutes_dict[str(member.id)] = ""
                with open("saves/mutes.json", "w") as file:
                    json.dump(self.bot.mutes_dict, file, indent=4)
                await member.send(f"Your mute on {self.bot.guild} has expired!")
            await asyncio.sleep(1)

    async def generic_ban_things(self, ctx, member, reason):
        """Generic stuff that is used by both ban commands.

        ctx -> Commands.Context object.
        member -> discord.User object, can be limited.
        reason -> reason to ban
        """
        has_attch = bool(ctx.message.attachments)
        if member.id == ctx.message.author.id:
            return await ctx.send("You can't ban yourself, obviously")
        try:
            member_guild = ctx.guild.get_member(member.id)
            if any(role for role in self.bot.protected_roles if role in member_guild.roles):
                return await ctx.send("That user is protected!")
        except AttributeError:
            pass  # Happens when banning via id, as they have no roles if not on guild
        try:
            if has_attch:
                img_bytes = await ctx.message.attachments[0].read()
                ban_img = discord.File(io.BytesIO(img_bytes), 'ban_image.png')
                await member.send(f"You were banned from FlagBrew for:\n\n`{reason}`\n\nIf you believe this to be in error, please contact a staff member.", file=ban_img)
                self.ban_attch_dict[str(member.id)] = io.BytesIO(img_bytes)
            else:
                await member.send(f"You were banned from FlagBrew for:\n\n`{reason}`\n\nIf you believe this to be in error, please contact a staff member.")
        except discord.Forbidden:
            pass  # bot blocked or not accepting DMs
        reason += f"\n\nAction done by {ctx.author} (This is to deal with audit log scraping)"
        try:
            if len(reason) > 512:
                await ctx.guild.ban(member, delete_message_days=0, reason=f"Failed to log reason as length was {len(reason)}. Please check bot logs.")
            else:
                await ctx.guild.ban(member, delete_message_days=0, reason=reason)
        except discord.Forbidden:  # i have no clue
            return await ctx.send("I don't have permission. Why don't I have permission.")
        embed = discord.Embed()
        img_choice = random.randint(1, 26)
        if img_choice in range(1, 13):  # ampharos
            embed.set_image(url="https://fm1337.com/static/img/ampharos-banned.jpg")
        if img_choice in range(13, 25):  # eevee
            embed.set_image(url="https://fm1337.com/static/img/eevee-banned.png")
        if img_choice in range(25, 27):  # giratina
            embed.set_image(url="https://fm1337.com/static/img/giratina-banned.png")
        await ctx.send(f"Successfully banned user {member}!", embed=embed)

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
            if user.id in self.ban_attch_dict.keys():
                ban_img = discord.File(self.ban_attch_dict.pop(str(user.id)), 'ban_image.png')
                embed.set_thumbnail(url="attachment://ban_image.png")
                await self.bot.logs_channel.send(embed=embed, file=ban_img)
            else:
                await self.bot.logs_channel.send(embed=embed)
        except discord.Forbidden:
            pass  # beta bot can't log

    @commands.command(pass_context=True)
    @commands.has_any_role("Discord Moderator")
    async def kick(self, ctx, member: discord.Member, *, reason="No reason was given."):
        """Kick a member."""
        has_attch = bool(ctx.message.attachments)
        if member == ctx.message.author:
            return await ctx.send("You can't kick yourself, obviously")
        elif any(role for role in self.bot.protected_roles if role in member.roles):
            return await ctx.send("You can't kick a staff member!")
        else:
            embed = discord.Embed(title=f"{member} kicked")
            embed.description = f"{member} was kicked by {ctx.message.author} for:\n\n{reason}"
            try:
                if has_attch:
                    img_bytes = await ctx.message.attachments[0].read()
                    kick_img = discord.File(io.BytesIO(img_bytes), 'image.png')
                    log_img = discord.File(io.BytesIO(img_bytes), 'kick_image.png')
                    await member.send(f"You were kicked from FlagBrew for:\n\n`{reason}`\n\nIf you believe this to be in error, you can rejoin here: https://discord.gg/bGKEyfY", file=kick_img)
                else:
                    await member.send(f"You were kicked from FlagBrew for:\n\n`{reason}`\n\nIf you believe this to be in error, you can rejoin here: https://discord.gg/bGKEyfY")
            except discord.Forbidden:
                pass  # bot blocked or not accepting DMs
            try:
                if has_attch:
                    embed.set_thumbnail(url="attachment://kick_image.png")
                    await self.bot.logs_channel.send(embed=embed, file=log_img)
                else:
                    await self.bot.logs_channel.send(embed=embed)
            except discord.Forbidden:
                pass  # beta bot can't log
            if len(reason) > 512:
                await member.kick(reason=f"Failed to log reason, as reason length was {len(reason)}. Please check bot logs.")
            else:
                await member.kick(reason=reason)
            await ctx.send(f"Successfully kicked user {member}!")

    @commands.command(pass_context=True)
    @commands.has_any_role("Discord Moderator")
    async def ban(self, ctx, member: discord.User, *, reason="No reason was given."):
        """Bans a user."""
        if not member:  # Edge case in which UserConverter may fail to get a User
            return await ctx.send("Could not find user. They may no longer be in the global User cache. If you are sure this is a valid user, try `.banid` instead.")
        await self.generic_ban_things(ctx, member, reason)

    @commands.command(pass_context=True)
    @commands.has_any_role("Discord Moderator")
    async def banid(self, ctx, member: int, *, reason="No reason was given."):
        """Ban a user with their user ID.

        To get a user ID, enable developer mode and right click their profile."""
        member = await self.bot.fetch_user(member)
        if not member:
            return await ctx.send("This is not a valid discord user.")
        await self.generic_ban_things(ctx, member, reason)

    @commands.command(aliases=['p', 'clear', 'clean'])
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    async def purge(self, ctx, amount=0, user: discord.User = None):
        """Purge x amount of messages. Supply user ID to target"""
        if amount <= 0:
            return await ctx.send("Why would you wanna purge no messages?", delete_after=10)
        if user:
            def purge_specific_user(m):
                return m.author == user
            await self.bot.logs_channel.send(f"{ctx.author} ({ctx.author.id}) cleared {amount} messages by {user} ({user.id}) in {ctx.channel.mention}.")
            purged = await ctx.channel.purge(limit=amount, check=purge_specific_user, before=ctx.message)
            if len(purged) == 0:
                return await ctx.send(f"Could not find any messages by {user} ({user.id}) to purge.")
            return await ctx.send(f"Purged {len(purged)} messages by {user} ({user.id}).")
        await self.bot.logs_channel.send(f"{ctx.author} ({ctx.author.id}) cleared {amount} messages in {ctx.channel.mention}.")
        await ctx.channel.purge(limit=amount, before=ctx.message)

    @commands.command(aliases=['psince', 'clearsince', 'cleansince'])
    @commands.has_any_role("Discord Moderator", "Bot Dev")
    async def purgesince(self, ctx, start_id: int, user: discord.User = None):
        """Purge all messages since x message ID. Message must be cached. Supply user ID to target"""
        start_message = discord.utils.find(lambda msg: msg.id == start_id, self.bot.cached_messages)
        if start_message is None:
            return await ctx.send(f"Could not find a message with ID `{start_id}`.")
        if user:
            def purge_specific_user(u):
                return u.author == user
            await self.bot.logs_channel.send(f"{ctx.author} ({ctx.author.id}) cleared all messages by {user} ({user.id}) after {discord.utils.format_dt(start_message.created_at)} in {ctx.channel.mention}.")
            purged = await ctx.channel.purge(before=ctx.message, after=start_message, check=purge_specific_user)
            if len(purged) == 0:
                return await ctx.send(f"Could not find any messages by {user} ({user.id}) after message with ID `{start_id}` to purge.")
            return await ctx.send(f"Purged {len(purged)} messages by {user} ({user.id}) since {discord.utils.format_dt(start_message.created_at)}.")
        await self.bot.logs_channel.send(f"{ctx.author} ({ctx.author.id}) cleared all messages after {discord.utils.format_dt(start_message.created_at)} in {ctx.channel.mention}.")
        purged = await ctx.channel.purge(before=ctx.message, after=start_message)
        if len(purged) == 0:
            return await ctx.send(f"Could not find any messages after message with ID `{start_id}` to purge.")
        return await ctx.send(f"Purged {len(purged)} messages since {discord.utils.format_dt(start_message.created_at)}.")

    @commands.command()
    @commands.has_any_role("Discord Moderator")
    async def mute(self, ctx, member: discord.Member, *, reason="No reason was given."):
        """Mutes a user"""
        has_attch = bool(ctx.message.attachments)
        if member == ctx.message.author:
            return await ctx.send("You can't mute yourself, obviously")
        elif any(role for role in self.bot.protected_roles if role in member.roles):
            return await ctx.send("You can't mute a staff member!")
        elif self.bot.mute_role in member.roles:
            return await ctx.send("That member is already muted.")
        await member.add_roles(self.bot.mute_role)
        self.bot.mutes_dict[str(member.id)] = "Indefinite"
        with open("saves/mutes.json", "w") as file:
            json.dump(self.bot.mutes_dict, file, indent=4)
        embed = discord.Embed(title=f"{member} ({member.id}) muted")
        embed.description = f"{member} was muted by {ctx.message.author} for:\n\n{reason}"
        try:
            if has_attch:
                img_bytes = await ctx.message.attachments[0].read()
                mute_img = discord.File(io.BytesIO(img_bytes), 'image.png')
                log_img = discord.File(io.BytesIO(img_bytes), 'mute_image.png')
                await member.send(f"You were muted on FlagBrew for:\n\n`{reason}`", file=mute_img)
            else:
                await member.send(f"You were muted on FlagBrew for:\n\n`{reason}`")
        except discord.Forbidden:
            pass  # blocked DMs
        try:
            if has_attch:
                embed.set_thumbnail(url="attachment://mute_image.png")
                await self.bot.logs_channel.send(embed=embed, file=log_img)
            else:
                await self.bot.logs_channel.send(embed=embed)
        except discord.Forbidden:
            pass  # beta can't log
        await ctx.send(f"Successfully muted {member}!")

    @commands.command()
    @commands.has_any_role("Discord Moderator")
    async def unmute(self, ctx, member: discord.Member, *, reason="No reason was given."):
        """Unmutes a user"""
        if member == ctx.message.author or any(role for role in self.bot.protected_roles if role in member.roles):
            return await ctx.send(f"How did {member.mention} get muted...?")
        elif self.bot.mute_role not in member.roles:
            return await ctx.send("That member isn't muted.")
        await member.remove_roles(self.bot.mute_role)
        self.bot.mutes_dict[str(member.id)] = ""
        with open("saves/mutes.json", "w") as file:
            json.dump(self.bot.mutes_dict, file, indent=4)
        embed = discord.Embed(title=f"{member} ({member.id}) unmuted")
        embed.description = f"{member} was unmuted by {ctx.message.author} for:\n\n{reason}"
        try:
            await member.send(f"You were unmuted on FlagBrew.")
        except discord.Forbidden:
            pass  # blocked DMs
        try:
            await self.bot.logs_channel.send(embed=embed)
        except discord.Forbidden:
            pass  # beta can't log
        await ctx.send(f"Successfully unmuted {member}!")

    @commands.command(name="tmute")
    @commands.has_any_role("Discord Moderator")
    async def timemute(self, ctx, member: discord.Member, duration, *, reason="No reason was given."):
        """Timemutes a user. Units are s, m, h, and d"""
        has_attch = bool(ctx.message.attachments)
        if member == ctx.message.author:
            return await ctx.send("You can't mute yourself, obviously")
        elif any(role for role in self.bot.protected_roles if role in member.roles):
            return await ctx.send("You can't mute a staff member!")
        elif self.bot.mute_role in member.roles:
            return await ctx.send("That member is already muted.")
        curr_time = discord.utils.utcnow()  # Referenced from https://github.com/chenzw95/porygon/blob/aa2454336230d7bc30a7dd715e057ee51d0e1393/cogs/mod.py#L223
        try:
            if int(duration[:-1]) == 0:
                return await ctx.send("You can't mute for a time length of 0.")
            elif duration.lower().endswith("s"):
                diff = timedelta(seconds=int(duration[:-1]))
            elif duration.lower().endswith("m"):
                diff = timedelta(minutes=int(duration[:-1]))
            elif duration.lower().endswith("h"):
                diff = timedelta(hours=int(duration[:-1]))
            elif duration.lower().endswith("d"):
                diff = timedelta(days=int(duration[:-1]))
            else:
                await ctx.send("That's not an appropriate duration value.")
                return await ctx.send_help(ctx.command)
        except ValueError:
            await ctx.send("You managed to throw a ValueError! Congrats! I guess. Use one of the correct values, and don't mix and match. Bitch.")
            return await ctx.send_help(ctx.command)
        end = curr_time + diff
        end_str = discord.utils.format_dt(end)
        await member.add_roles(self.bot.mute_role)
        embed = discord.Embed(title=f"{member} ({member.id}) timemuted")
        embed.description = f"{member} timemuted by {ctx.message.author} until {end_str} UTC for:\n\n{reason}"
        try:
            if has_attch:
                img_bytes = await ctx.message.attachments[0].read()
                mute_img = discord.File(io.BytesIO(img_bytes), 'image.png')
                log_img = discord.File(io.BytesIO(img_bytes), 'mute_image.png')
                await member.send(f"You have been muted on {ctx.guild} for\n\n`{reason}`\n\nYou will be unmuted on {end_str}.", file=mute_img)
            else:
                await member.send(f"You have been muted on {ctx.guild} for\n\n`{reason}`\n\nYou will be unmuted on {end_str}.")
        except discord.Forbidden:
            pass  # blocked DMs
        self.bot.mutes_dict[str(member.id)] = end.strftime("%Y-%m-%d %H:%M:%S")
        with open("saves/mutes.json", "w") as file:
            json.dump(self.bot.mutes_dict, file, indent=4)
        try:
            if has_attch:
                embed.set_thumbnail(url="attachment://mute_image.png")
                await self.bot.logs_channel.send(embed=embed, file=log_img)
            else:
                await self.bot.logs_channel.send(embed=embed)
        except discord.Forbidden:
            pass  # beta can't log
        await ctx.send(f"Successfully muted {member} until `{end_str}`!")

    @commands.command()
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    async def timeout(self, ctx, member: discord.Member, duration, *, reason="No reason was given"):
        """Mute a user using discord's timeout function. Units are m, h, d with an upper cap of 28 days (discord limit)"""
        has_attch = bool(ctx.message.attachments)
        cap_msg = ""
        if member == ctx.message.author:
            return await ctx.send("You can't mute yourself, obviously")
        elif any(role for role in self.bot.protected_roles if role in member.roles):
            return await ctx.send("You can't mute a staff member!")
        elif member.is_timed_out():
            return await ctx.send("That member is already timed out.")
        curr_time = discord.utils.utcnow()
        try:
            if int(duration[:-1]) == 0:
                return await ctx.send("You can't mute for a time length of 0.")
            elif duration.lower().endswith("m"):
                diff = timedelta(minutes=int(duration[:-1]))
            elif duration.lower().endswith("h"):
                diff = timedelta(hours=int(duration[:-1]))
            elif duration.lower().endswith("d"):
                diff = timedelta(days=int(duration[:-1]))
            else:
                await ctx.send("That's not an appropriate duration value.")
                return await ctx.send_help(ctx.command)
        except ValueError:
            await ctx.send("You managed to throw a ValueError! Congrats! I guess. Use one of the correct values, and don't mix and match. Bitch.")
            return await ctx.send_help(ctx.command)
        if diff.days > 28:
            diff = timedelta(hours=672)
            cap_msg = "\n\nTimeouts are limited to 28 days on Discord's side. The length of this timeout has been lowered to 28 days."
        end = curr_time + diff
        end_str = discord.utils.format_dt(end)
        try:
            if has_attch:
                img_bytes = await ctx.message.attachments[0].read()
                timeout_img = discord.File(io.BytesIO(img_bytes), 'image.png')
                await member.send(f"You have been timed out on {ctx.guild} for\n\n`{reason}`\n\nYour timeout will expire on {end_str}.", file=timeout_img)
            else:
                await member.send(f"You have been timed out on {ctx.guild} for\n\n`{reason}`\n\nYour timeout will expire on {end_str}.")
        except discord.Forbidden:
            pass  # blocked DMs
        reason += f"\n\nAction done by {ctx.author} (This is to deal with audit log scraping)"
        await member.timeout(diff - timedelta(seconds=1), reason=reason)  # Reduce diff by 1 second due to communication_disabled_until when it's *exactly* 28 days
        await ctx.send(f"Successfully timed out {member} until {end_str}!{cap_msg}")

    @commands.command()
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    async def gpssban(self, ctx, member: discord.Member, *, reason="No reason was given"):
        """Bans a user from using gpsspost"""
        has_attch = bool(ctx.message.attachments)
        if member == ctx.message.author:
            return await ctx.send("You can't ban yourself from using `gpsspost`.")
        elif any(role for role in self.bot.protected_roles if role in member.roles):
            return await ctx.send("You can't ban a staff member from using `gpsspost`.")
        elif self.bot.gpss_banned_role in member.roles:
            return await ctx.send("User is already banned from using `gpsspost`.")
        await member.add_roles(self.bot.gpss_banned_role)
        self.bot.gpss_bans_array.append(member.id)
        with open("saves/gpss-bans.json", "w") as file:
            json.dump(self.bot.gpss_bans_array, file, indent=4)
        embed = discord.Embed(title=f"{member} ({member.id}) banned from using `gpsspost`")
        embed.description = f"{member} was banned from using the `gpsspost` command by {ctx.message.author} for:\n\n{reason}"
        try:
            if has_attch:
                img_bytes = await ctx.message.attachments[0].read()
                gpss_ban_img = discord.File(io.BytesIO(img_bytes), 'image.png')
                log_img = discord.File(io.BytesIO(img_bytes), 'gpss_ban_image.png')
                await member.send(f"You were banned from using the `gpsspost` command on FlagBrew for:\n\n`{reason}`", file=gpss_ban_img)
            else:
                await member.send(f"You were banned from using the `gpsspost` command on FlagBrew for:\n\n`{reason}`")
        except discord.Forbidden:
            pass  # blocked DMs
        try:
            if has_attch:
                embed.set_thumbnail(url="attachment://gpss_ban_image.png")
                await self.bot.logs_channel.send(embed=embed, file=log_img)
            else:
                await self.bot.logs_channel.send(embed=embed)
        except discord.Forbidden:
            pass  # beta can't log
        await ctx.send(f"Successfully banned {member} from using the `gpsspost` command!")

    @commands.command()
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    async def ungpssban(self, ctx, member: discord.Member, *, reason="No reason was given."):
        """Unbans a user from using gpsspost"""
        if member == ctx.message.author or any(role for role in self.bot.protected_roles if role in member.roles):
            return await ctx.send(f"How did {member.mention} get banned from `gpsspost`...?")
        elif self.bot.gpss_banned_role not in member.roles:
            return await ctx.send("That member can already use `gpsspost`.")
        await member.remove_roles(self.bot.gpss_banned_role)
        self.bot.gpss_bans_array.remove(member.id)
        with open("saves/gpss-bans.json", "w") as file:
            json.dump(self.bot.gpss_bans_array, file, indent=4)
        embed = discord.Embed(title=f"{member} ({member.id}) unbanned from `gpsspost`")
        embed.description = f"{member} was unbanned from using the `gpsspost` command by {ctx.message.author} for:\n\n{reason}"
        try:
            await member.send(f"You can now use the `gpsspost` command on FlagBrew again.")
        except discord.Forbidden:
            pass  # blocked DMs
        try:
            await self.bot.logs_channel.send(embed=embed)
        except discord.Forbidden:
            pass  # beta can't log
        await ctx.send(f"Successfully unbanned {member} from using the `gpsspost` command!")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
