# pylint: disable=no-value-for-parameter
import asyncio
import typing
import json
import weakref
import discord
from discord.ext import commands


class Starboard(commands.Cog):
    """
    Adds stuff to the starboard
    """

    def __init__(self, bot):
        self.bot = bot
        self._message_cache = {}
        self._star_queue = weakref.WeakValueDictionary()
        if self.bot.is_mongodb:
            self.db = bot.db

    def star_gradient_colour(self, stars):
        percent = stars / 13
        if percent > 1.0:
            percent = 1.0

        red = 255
        green = int((194 * percent) + (253 * (1 - percent)))
        blue = int((12 * percent) + (247 * (1 - percent)))
        return (red << 16) + (green << 8) + blue

    def star_emoji(self, stars):
        if 5 > stars >= 0:
            return '\N{WHITE MEDIUM STAR}'
        elif 10 > stars >= 5:
            return '\N{GLOWING STAR}'
        elif 25 > stars >= 10:
            return '\N{DIZZY SYMBOL}'
        else:
            return '\N{SPARKLES}'

    def get_emoji_message(self, message, count):
        emoji = self.star_emoji(count)
        content = '{0} **{1}** {2} ID: {3}'.format(emoji, count, message.channel.mention, message.id)
        embed = discord.Embed(description=message.content)
        if message.embeds:
            data = message.embeds[0]
            if data.type == 'image':
                embed.set_image(url=data.url)

        if message.attachments:
            file = message.attachments[0]
            if file.url.lower().endswith(('png', 'jpeg', 'jpg', 'gif', 'webp')):
                embed.set_image(url=file.url)
            else:
                embed.add_field(name='Attachment', value='[{0}]({1})'.format(file.filename, file.url), inline=False)

        embed.add_field(name='Context', value='[Jump!]({0})'.format(message.jump_url), inline=False)
        embed.set_author(name=message.author.display_name, icon_url=str(message.author.display_avatar))
        embed.timestamp = message.created_at
        embed.colour = self.star_gradient_colour(count)
        return content, embed

    async def get_message(self, channel, message_id):
        try:
            return self._message_cache[message_id]
        except KeyError:
            try:
                obj = discord.Object(id=message_id + 1)
                # don't wanna use get_message due to poor rate limit (1/1s) vs (50/1s)
                msg = await channel.history(limit=1, before=obj).next()

                if msg.id != message_id:
                    return None

                self._message_cache[message_id] = msg
                return msg
            except discord.HTTPException:
                return None

    async def update_db(self, message, add_value):
        starboard_db = self.db['starboard']
        existing = starboard_db.find_one({'$or': [{'message_id': message.id}, {'starboard_id': message.id}]})
        if existing:
            starboard_message = await self.get_message(self.bot.starboard_channel, existing['starboard_id'])
            if existing['star_count'] + add_value >= self.bot.star_count:
                if existing['starboard_id'] == message.id:
                    message = await self.get_message(self.bot.get_guild(self.bot.flagbrew_id).get_channel(existing['channel_id']), existing['message_id'])
                content, embed = self.get_emoji_message(message, add_value + existing['star_count'])
                await starboard_message.edit(content=content, embed=embed)
                starboard_db.update_one({'message_id': message.id}, {'$inc': {'star_count': add_value}})
            elif existing['star_count'] + add_value < self.bot.star_count:
                starboard_db.delete_one({'message_id': message.id})
                await starboard_message.delete()
        else:
            star_reactions = self.get_star_reaction_count(message)
            if star_reactions >= self.bot.star_count:
                content, embed = self.get_emoji_message(message, star_reactions)
                sent_message = await self.bot.starboard_channel.send(content=content, embed=embed)
                entry = {
                    'message_id': message.id,
                    'star_count': star_reactions,
                    'author_id': message.author.id,
                    'channel_id': message.channel.id,
                    'starboard_id': sent_message.id
                }
                starboard_db.insert_one(entry)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.type != discord.MessageType.default:
            return
        if str(reaction.emoji) != '⭐':
            return
        star_lock = self._star_queue.get(reaction.message.id)
        if star_lock is None:
            star_lock = asyncio.Lock()
            self._star_queue[reaction.message.id] = star_lock
        async with star_lock:
            await self.update_db(reaction.message, 1)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if reaction.message.type != discord.MessageType.default:
            return
        if str(reaction.emoji) != '⭐':
            return
        star_lock = self._star_queue.get(reaction.message.id)
        if star_lock is None:
            star_lock = asyncio.Lock()
            self._star_queue[reaction.message.id] = star_lock
        async with star_lock:
            await self.update_db(reaction.message, -1)

    def get_star_reaction_count(self, message):
        reactions = message.reactions
        for react in reactions:
            if str(react.emoji) == '⭐':
                return react.count
        return 0

    @commands.command(name='deletestar', aliases=['delstar'])
    @commands.has_any_role("Discord Moderator", "Bot Dev")
    async def deletestar(self, ctx, message_id: int):
        starboard_db = self.db['starboard']
        existing = starboard_db.find_one({'$or': [{'message_id': message_id}, {'starboard_id': message_id}]})
        if existing:
            starboard_message = await self.bot.starboard_channel.fetch_message(existing['starboard_id'])
            embed = discord.Embed(color=discord.Color.orange(), timestamp=ctx.message.created_at)
            embed.title = "<:nostar:723763060321550407> Message un-starred"
            embed.add_field(name="Un-starred by", value=ctx.author.name)
            try:
                await self.bot.logs_channel.send(embed=embed)
            except discord.Forbidden:  # beta can't log
                pass
            starboard_db.delete_one({'message_id': message_id})
            await starboard_message.delete()
            return await ctx.send("✅ Message `{}` removed from starboard.".format(existing['message_id']))
        else:
            return await ctx.send("❌ Message not found in starboard.")


async def setup(bot):
    await bot.add_cog(Starboard(bot))
