#!/usr/bin/env python3

import discord
from discord.ext import commands
import os
import sys
import json
import asyncio

class Moderation:
    """Bot commands for moderation."""
    def __init__(self, bot):
        self.bot = bot
        print('Addon "{}" loaded'.format(self.__class__.__name__))
        
    def find_user(self, user, ctx):
        found_member = self.bot.guild.get_member(user)
        if not found_member:
            found_member = self.bot.guild.get_member_named(user)
        if not found_member:
            try:
                found_member = ctx.message.mentions[0]
            except IndexError:
                pass
        if not found_member:
            return None
        else:
            return found_member
    
    @commands.has_permissions(kick_members=True)    
    @commands.command(pass_context=True)
    async def kick(self, ctx, member, *, reason="No reason was given."):
        """Kick a member."""
        found_member = self.find_user(member, ctx)
        if found_member == ctx.message.author:
            return await ctx.send("You can't kick yourself, obviously")
        elif not found_member:
            await ctx.send("That user could not be found.")
        else:
            embed = discord.Embed(title="{} kicked".format(found_member))
            embed.description = "{}#{} was kicked by {} for:\n\n{}".format(found_member.name, found_member.discriminator, ctx.message.author, reason)
            if ctx.guild.id == self.bot.flagbrew_id:
                await self.bot.logs_channel.send(embed=embed)
            try:
                await found_member.send("You were kicked from FlagBrew for:\n\n`{}`\n\nIf you believe this to be in error, you can rejoin here: https://discord.gg/bGKEyfY".format(reason))
            except discord.Forbidden:
                pass # bot blocked or not accepting DMs
            await found_member.kick(reason=reason)
            await ctx.send("Successfully kicked user {0.name}#{0.discriminator}!".format(found_member))
    
    @commands.has_permissions(ban_members=True)    
    @commands.command(pass_context=True)
    async def ban(self, ctx, member, *, reason="No reason was given."):
        """Ban a member."""
        found_member = self.find_user(member, ctx)
        if found_member == ctx.message.author:
            return await ctx.send("You can't ban yourself, obviously")
        elif not found_member:
            await ctx.send("That user could not be found.")
        else:
            embed = discord.Embed(title="{} banned".format(found_member))
            embed.description = "{}#{} was banned by {} for:\n\n{}".format(found_member.name, found_member.discriminator, ctx.message.author, reason)
            try:
                await found_member.send("You were banned from FlagBrew for:\n\n`{}`\n\nIf you believe this to be in error, please contact a staff member".format(reason))
            except:
                pass # bot blocked or not accepting DMs
            try:
                await ctx.guild.ban(found_member, delete_message_days=0, reason=reason)
            except discord.Forbidden: # i have no clue
                try:
                    await found_member.ban(reason=reason)
                except discord.Forbidden: # none at all
                    return await ctx.send("I don't have permission. Why don't I have permission.")
            await ctx.send("Successfully banned user {0.name}#{0.discriminator}!".format(found_member))
            
    @commands.has_permissions(ban_members=True)
    @commands.command(aliases=['p'])
    async def purge(self, ctx, amount=0):
        """Purge x amount of messages"""
        await ctx.message.delete()
        asyncio.sleep(2)
        if amount > 0:
            await ctx.channel.purge(limit=amount)
        else:
            await ctx.send("Why would you wanna purge no messages?", delete_after=10)
            
def setup(bot):
    bot.add_cog(Moderation(bot))
