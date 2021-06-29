#!/usr/bin/env python3

import discord
from discord.ext import commands
import os
import sys
import json
import asyncio
import random
import io
from datetime import datetime, timedelta
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
        guild = self.bot.get_guild(278222834633801728)
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
                with open("saves/mutes.json", "w") as f:
                    json.dump(self.bot.mutes_dict, f, indent=4)
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
            if any(r for r in self.bot.protected_roles if r in member_guild.roles):
                return await ctx.send("That user is protected!")
        except AttributeError:
            pass  # Happens when banning via id, as they have no roles if not on guild
        try:
            if has_attch:
                img_bytes = await ctx.message.attachments[0].read()
                img = discord.File(io.BytesIO(img_bytes))
                await member.send(f"You were banned from FlagBrew for:\n\n`{reason}`\n\nIf you believe this to be in error, please contact a staff member.", file=img)
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
                img = discord.File(self.ban_attch_dict.pop(str(user.id)), 'ban_image.png')
                embed.set_thumbnail(url="attachment://ban_image.png")
                await self.bot.logs_channel.send(embed=embed, file=img)
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
        elif any(r for r in self.bot.protected_roles if r in member.roles):
            return await ctx.send("You can't kick a staff member!")
        else:
            embed = discord.Embed(title=f"{member} kicked")
            embed.description = f"{member} was kicked by {ctx.message.author} for:\n\n{reason}"
            try:
                if has_attch:
                    img_bytes = await ctx.message.attachments[0].read()
                    img = discord.File(io.BytesIO(img_bytes), 'kick_image.png')
                    await member.send(f"You were kicked from FlagBrew for:\n\n`{reason}`\n\nIf you believe this to be in error, you can rejoin here: https://discord.gg/bGKEyfY", file=img)
                else:
                    await member.send(f"You were kicked from FlagBrew for:\n\n`{reason}`\n\nIf you believe this to be in error, you can rejoin here: https://discord.gg/bGKEyfY")
            except discord.Forbidden:
                pass  # bot blocked or not accepting DMs
            try:
                if has_attch:
                    embed.set_thumbnail(url="attachment://kick_image.png")
                    await self.bot.logs_channel.send(embed=embed, file=img)
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
    @commands.has_any_role("Discord Moderator")
    async def purge(self, ctx, amount=0, user: discord.User = None):
        """Purge x amount of messages"""
        await ctx.message.delete()
        await asyncio.sleep(2)
        if amount > 0:
            if not user:
                await ctx.channel.purge(limit=amount)
            else:
                def purge_specific_user(m):
                    return m.author == user
                purged = await ctx.channel.purge(limit=amount, check=purge_specific_user)
                if len(purged) == 0:
                    return await ctx.send(f"Could not find any messages by {user} ({user.id}) to purge.")
                await ctx.send(f"Purged {len(purged)} messages by {user} ({user.id}).")
        else:
            await ctx.send("Why would you wanna purge no messages?", delete_after=10)

    @commands.command()
    @commands.has_any_role("Discord Moderator")
    async def mute(self, ctx, member: discord.Member, *, reason="No reason was given."):
        """Mutes a user"""
        has_attch = bool(ctx.message.attachments)
        if member == ctx.message.author:
            return await ctx.send("You can't mute yourself, obviously")
        elif any(r for r in self.bot.protected_roles if r in member.roles):
            return await ctx.send("You can't mute a staff member!")
        elif self.bot.mute_role in member.roles:
            return await ctx.send("That member is already muted.")
        await member.add_roles(self.bot.mute_role)
        self.bot.mutes_dict[str(member.id)] = "Indefinite"
        with open("saves/mutes.json", "w") as f:
            json.dump(self.bot.mutes_dict, f, indent=4)
        embed = discord.Embed(title=f"{member} ({member.id}) muted")
        embed.description = f"{member} was muted by {ctx.message.author} for:\n\n{reason}"
        try:
            if has_attch:
                img_bytes = await ctx.message.attachments[0].read()
                img = discord.File(io.BytesIO(img_bytes), 'mute_image.png')
                await member.send(f"You were muted on FlagBrew for:\n\n`{reason}`", file=img)
            else:
                await member.send(f"You were muted on FlagBrew for:\n\n`{reason}`")
        except discord.Forbidden:
            pass  # blocked DMs
        try:
            if has_attch:
                embed.set_thumbnail(url="attachment://mute_image.png")
                await self.bot.logs_channel.send(embed=embed, file=img)
            else:
                await self.bot.logs_channel.send(embed=embed)
        except discord.Forbidden:
            pass  # beta can't log
        await ctx.send(f"Successfully muted {member}!")

    @commands.command()
    @commands.has_any_role("Discord Moderator")
    async def unmute(self, ctx, member: discord.Member, *, reason="No reason was given."):
        """Unmutes a user"""
        if member == ctx.message.author or any(r for r in self.bot.protected_roles if r in member.roles):
            return await ctx.send(f"How did {member.mention} get muted...?")
        elif self.bot.mute_role not in member.roles:
            return await ctx.send("That member isn't muted.")
        await member.remove_roles(self.bot.mute_role)
        self.bot.mutes_dict[str(member.id)] = ""
        with open("saves/mutes.json", "w") as f:
            json.dump(self.bot.mutes_dict, f, indent=4)
        embed = discord.Embed(title=f"{member} ({member.id}) unmuted")
        embed.description = f"{member} was unmuted by {ctx.message.author} for:\n\n{reason}"
        await member.send(f"You were unmuted on FlagBrew.")
        try:
            await self.bot.logs_channel.send(embed=embed)
        except discord.Forbidden:
            pass  # beta can't log
        await ctx.send(f"Successfully unmuted {member}!")

    @commands.command(name="tmute")
    @commands.has_any_role("Discord Moderator")
    async def timemute(self, ctx, member: discord.Member, duration, reason="No reason was given."):
        """Timemutes a user. Units are s, m, h, and d"""
        has_attch = bool(ctx.message.attachments)
        if member == ctx.message.author:
            return await ctx.send("You can't mute yourself, obviously")
        elif any(r for r in self.bot.protected_roles if r in member.roles):
            return await ctx.send("You can't mute a staff member!")
        elif self.bot.mute_role in member.roles:
            return await ctx.send("That member is already muted.")
        curr_time = datetime.utcnow()  # Referenced from https://github.com/chenzw95/porygon/blob/aa2454336230d7bc30a7dd715e057ee51d0e1393/cogs/mod.py#L223
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
        end_str = end.strftime("%Y-%m-%d %H:%M:%S")
        await member.add_roles(self.bot.mute_role)
        embed = discord.Embed(title=f"{member} ({member.id}) timemuted")
        embed.description = f"{member} timemuted by {ctx.message.author} until {end_str} UTC for:\n\n{reason}"
        try:
            if has_attch:
                img_bytes = await ctx.message.attachments[0].read()
                img = discord.File(io.BytesIO(img_bytes), 'mute_image.png')
                await member.send(f"You have been muted on {ctx.guild} for\n\n`{reason}`\n\nYou will be unmuted on {end_str}.", file=img)
            else:
                await member.send(f"You have been muted on {ctx.guild} for\n\n`{reason}`\n\nYou will be unmuted on {end_str}.")
        except discord.Forbidden:
            pass  # blocked DMs
        self.bot.mutes_dict[str(member.id)] = end_str
        with open("saves/mutes.json", "w") as f:
            json.dump(self.bot.mutes_dict, f, indent=4)
        try:
            if has_attch:
                embed.set_thumbnail(url="attachment://mute_image.png")
                await self.bot.logs_channel.send(embed=embed, file=img)
            else:
                await self.bot.logs_channel.send(embed=embed)
        except discord.Forbidden:
            pass  # beta can't log
        await ctx.send(f"Successfully muted {member} until `{end_str}` UTC!")

def setup(bot):
    bot.add_cog(Moderation(bot))
