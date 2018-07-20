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
            if ctx.guild.id == 278222834633801728:
                await self.bot.logs_channel.send(embed=embed)
            try:
                await found_member.kick("You were kicked from {} for:\n\n`{}`\n\nIf you believe this to be in error, you can rejoin here: {}".format(ctx.guild.name, reason, "https://discord.gg/bGKEyfY" if ctx.guild.id == 278222834633801728 else "https://discord.gg/5Wg4AEb"))
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
            if ctx.guild.id == 278222834633801728:
                await self.bot.get_guild(418291144850669569).get_channel(430164418345566208).send("On the PKSM server, the following action occurred: ", embed=embed) # Appeals logging
                await self.bot.logs_channel.send(embed=embed)
            elif ctx.guild.id == 418291144850669569:
                await self.bot.get_channel(430164418345566208).send(embed=embed)
                await found_member.ban(reason=reason)
                return await ctx.send("Successfully banned user {0.name}#{0.discriminator}!".format(found_member))
            try:
                await found_member.send("You were banned from {} for:\n\n`{}`{}".format(ctx.guild.name, reason, "\n\nIf you believe this to be in error, please join the appeals server here: https://discord.gg/5Wg4AEb" if ctx.guild == 278222834633801728 else ""))
            except:
                pass # bot blocked or not accepting DMs
            try:
                await found_member.ban(reason=reason)
            except discord.Forbidden: # i have no clue
                try:
                    await self.bot.get_guild(278222834633801728).ban(found_member, delete_message_days=0, reason=reason)
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
            
    @commands.has_permissions(ban_members=True)
    @commands.command()
    async def unban(self, ctx, member):
        """Unban command, only works on the appeals server"""
        if not ctx.guild.id == 418291144850669569:
            return await ctx.send("This command is for the appeals server only.", delete_after(10))
        found_member = self.find_user(member, ctx)
        if found_member == ctx.message.author:
            return await found_member.send("How did you possibly ban yourself? Go ask someone else to unban you.")
        elif not found_member:
            return await ctx.send("That user could not be found.", delete_after(10))
        else:
            try:
                await found_member.send("You were unbanned from PKSM! Thank you for appealing. Here's an invite to rejoin: https://discord.gg/bGKEyfY")
            except discord.Forbidden:
                pass # bot blocked or not accepting DMs
            try:
                await self.bot.get_guild(278222834633801728).unban(found_member)
            except discord.NotFound:
                return await ctx.send("{} is not banned!".format(found_member.mention))
            embed = discord.Embed(title="{}#{} unbanned".format(found_member.name, found_member.discriminator))
            embed.description = "{}#{} was unbanned from PKSM by {}".format(found_member.name, found_member.discriminator, ctx.message.author)
            await ctx.guild.get_channel(430164418345566208).send(embed=embed)
            await found_member.kick()
            await ctx.send("Unbanned {}#{}!".format(found_member.name, found_member.discriminator))
            
def setup(bot):
    bot.add_cog(Moderation(bot))
