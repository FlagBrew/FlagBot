#!/usr/bin/env python3

import discord
from discord.ext import commands
import os
import sys
import json
import asyncio
import random
from datetime import datetime, timedelta
import addons.helper as helper


class Moderation(commands.Cog):
    """Bot commands for moderation."""
    def __init__(self, bot):
        self.bot = bot
        self.mute_loop = bot.loop.create_task(self.check_mute_loop())  # loops referenced from https://github.com/chenzw95/porygon/blob/aa2454336230d7bc30a7dd715e057ee51d0e1393/cogs/mod.py#L23
        print('Addon "{}" loaded'.format(self.__class__.__name__))
        
    def __unload(self):
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
                await member.send("Your mute on {} has expired!".format(self.bot.guild))
            await asyncio.sleep(1)

    async def generic_ban_things(self, ctx, member, reason):
        """Generic stuff that is used by both ban commands.

        ctx -> Commands.Context object.
        member -> discord.User object, can be limited.
        reason -> reason to ban
        """

        if member.id == ctx.message.author.id:
            return await ctx.send("You can't ban yourself, obviously")
        try:
            member_guild = ctx.guild.get_member(member.id)
            if any(r for r in self.bot.protected_roles if r in member_guild.roles):
                return await ctx.send("That user is protected!")
        except AttributeError:
            pass  # Happens when banning via id, as they have no roles if not on guild
        try:
            await member.send("You were banned from FlagBrew for:\n\n`{}`\n\nIf you believe this to be in error, please contact a staff member".format(reason))
        except discord.Forbidden:
            pass  # bot blocked or not accepting DMs
        reason += "\n\nAction done by {} (This is to deal with audit log scraping)".format(ctx.author)
        try:
            if len(reason) > 512:
                await ctx.guild.ban(member, delete_message_days=0, reason="Failed to log reason as length was {}. Please check bot logs.".format(len(reason)))
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
        await ctx.send("Successfully banned user {}!".format(member), embed=embed)

    @commands.command(pass_context=True)
    @commands.has_any_role("Discord Moderator")
    async def kick(self, ctx, member: discord.Member, *, reason="No reason was given."):
        """Kick a member."""
        if member == ctx.message.author:
            return await ctx.send("You can't kick yourself, obviously")
        elif any(r for r in self.bot.protected_roles if r in member.roles):
            return await ctx.send("You can't kick a staff member!")
        else:
            embed = discord.Embed(title="{} kicked".format(member))
            embed.description = "{} was kicked by {} for:\n\n{}".format(member, ctx.message.author, reason)
            try:
                await self.bot.logs_channel.send(embed=embed)
            except discord.Forbidden:
                pass  # beta bot can't log
            try:
                await member.send("You were kicked from FlagBrew for:\n\n`{}`\n\nIf you believe this to be in error, you can rejoin here: https://discord.gg/bGKEyfY".format(reason))
            except discord.Forbidden:
                pass  # bot blocked or not accepting DMs
            if len(reason) > 512:
                await member.kick(reason="Failed to log reason, as reason length was {}. Please check bot logs.".format(len(reason)))
            else:
                await member.kick(reason=reason)
            await ctx.send("Successfully kicked user {}!".format(member))

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
    async def purge(self, ctx, amount=0):
        """Purge x amount of messages"""
        await ctx.message.delete()
        await asyncio.sleep(2)
        if amount > 0:
            await ctx.channel.purge(limit=amount)
        else:
            await ctx.send("Why would you wanna purge no messages?", delete_after=10)


def setup(bot):
    bot.add_cog(Moderation(bot))
