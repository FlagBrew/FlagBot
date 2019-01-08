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
    
    @commands.has_permissions(kick_members=True)    
    @commands.command(pass_context=True)
    async def kick(self, ctx, member:discord.Member, *, reason="No reason was given."):
        """Kick a member."""
        if member == ctx.message.author:
            return await ctx.send("You can't kick yourself, obviously")
        else:
            embed = discord.Embed(title="{} kicked".format(member))
            embed.description = "{}#{} was kicked by {} for:\n\n{}".format(member.name, member.discriminator, ctx.message.author, reason)
            await self.bot.logs_channel.send(embed=embed)
            try:
                await member.send("You were kicked from FlagBrew for:\n\n`{}`\n\nIf you believe this to be in error, you can rejoin here: https://discord.gg/bGKEyfY".format(reason))
            except discord.Forbidden:
                pass # bot blocked or not accepting DMs
            await member.kick(reason=reason)
            await ctx.send("Successfully kicked user {0.name}#{0.discriminator}!".format(member))
    
    @commands.has_permissions(ban_members=True)    
    @commands.command(pass_context=True)
    async def ban(self, ctx, member:discord.Member, *, reason="No reason was given."):
        """Ban a member."""
        if member == ctx.message.author:
            return await ctx.send("You can't ban yourself, obviously")
        else:
            try:
                await member.send("You were banned from FlagBrew for:\n\n`{}`\n\nIf you believe this to be in error, please contact a staff member".format(reason))
            except:
                pass # bot blocked or not accepting DMs
            try:
                await ctx.guild.ban(member, delete_message_days=0, reason=reason)
            except discord.Forbidden: # i have no clue
                try:
                    reason += "\n\nAction done by {} (This is to deal with audit log scraping".format(ctx.author)
                    await member.ban(reason=reason)
                except discord.Forbidden: # none at all
                    return await ctx.send("I don't have permission. Why don't I have permission.")
            embed = discord.Embed()
            embed.set_image(url="https://i.imgur.com/tEBrxUF.jpg")
            await ctx.send("Successfully banned user {0.name}#{0.discriminator}!".format(member), embed=embed)
            
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
