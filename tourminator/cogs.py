from typing import Optional

import discord
from discord import Member, TextChannel, RawReactionActionEvent, Guild, Colour
from discord.ext import commands
from discord.ext.commands import Context

from tourminator.bot import TourminatorBot
from tourminator.models import Event


class EventManagementCog(commands.Cog, name='Event Management'):
    __join_emoji = '\u2705'

    def __init__(self, bot: TourminatorBot):
        self.bot = bot

    def cog_check(self, ctx):
        return hasattr(ctx.author, 'guild')

    async def get_event_embed(self, event, add_postamble=True):
        embed = discord.Embed(title='**{0.name}**'.format(event), color=Colour.light_grey(),
                              description=event.description)
        participants = self.bot.db.get_participants_of_event(event.id)
        if len(participants) > 0:
            text = ''
            for participant in participants:
                user = await self.bot.fetch_user(participant)
                text += '{}\n'.format(user.mention)
            embed.add_field(name='Participants', value=text, inline=False)
        if add_postamble:
            embed.add_field(name='Join', value='Press {0} to join / leave this event!'.format(self.__join_emoji),
                            inline=False)
        return embed

    async def post_event_message(self, event, channel):
        message = await channel.send(embed=await self.get_event_embed(event))
        if event.message_id is not None:
            old_channel = await self.bot.fetch_channel(event.message_channel_id)
            old_message = await old_channel.fetch_message(event.message_id)
            await old_message.delete()
        self.bot.db.update_event(event.id, message_id=message.id, message_channel_id=channel.id)

        await message.add_reaction(self.__join_emoji)

    async def update_event_message(self, event):
        channel = await self.bot.fetch_channel(event.message_channel_id)
        message = await channel.fetch_message(event.message_id)
        await message.edit(embed=await self.get_event_embed(event))

    async def join_event(self, event: Event, user_id: int):
        if self.bot.db.join_event(event.id, user_id):
            guild: Guild = await self.bot.fetch_guild(event.guild_id)
            role = guild.get_role(event.event_role_id)
            user = await guild.fetch_member(user_id)
            await user.add_roles(role)
            return True
        return False

    async def leave_event(self, event: Event, user_id: int):
        if self.bot.db.leave_event(event.id, user_id):
            guild: Guild = await self.bot.fetch_guild(event.guild_id)
            role = guild.get_role(event.event_role_id)
            user = await guild.fetch_member(user_id)
            await user.remove_roles(role)
            return True
        return False

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        event = self.bot.db.get_event_by(message_id=(payload.message_id, payload.channel_id))
        if event is not None and payload.user_id != self.bot.user.id and payload.emoji.name == self.__join_emoji \
                and await self.join_event(event, payload.user_id):
            await self.update_event_message(event)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        event = self.bot.db.get_event_by(message_id=(payload.message_id, payload.channel_id))
        if event is not None and payload.user_id != self.bot.user.id and payload.emoji.name == self.__join_emoji \
                and await self.leave_event(event, payload.user_id):
            await self.update_event_message(event)

    @commands.group()
    async def event(self, ctx):
        """Commands for managing events."""
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid event command!')

    @event.command()
    @commands.has_role('Admin')
    async def create(self, ctx: Context, name: str, *, description: str = ''):
        """
        Create a new event.
        The description can be multiple lines.
        """
        name = name.strip()
        guild: Guild = ctx.guild
        event = self.bot.db.create_event(name, description, guild.id)
        if not event:
            await ctx.send('Event with the same name already exists on this server!')
        else:
            role = await guild.create_role(name=name)
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                role: discord.PermissionOverwrite(read_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True)
            }

            event_channel = await guild.create_text_channel(name=name, overwrites=overwrites)
            self.bot.db.update_event(event.id, event_channel_id=event_channel.id, event_role_id=role.id)
            await self.post_event_message(event, ctx.channel)

    @event.command()
    @commands.has_role('Admin')
    async def delete(self, ctx: Context, name: str, delete_channel: Optional[bool] = True):
        """
        Delete an existing event.
        The second parameter denotes if the event channel should be deleted or not. Defaults to true.
        """
        name = name.strip()
        guild: Guild = ctx.guild
        event = self.bot.db.get_event_by(name=(name, guild.id))
        if not event:
            await ctx.send('Event not found!')
        else:
            role = guild.get_role(event.event_role_id)
            event_channel: TextChannel = guild.get_channel(event.event_channel_id)
            if delete_channel:
                await event_channel.delete()
            else:
                await event_channel.set_permissions(guild.default_role, overwrite=None)
                await event_channel.set_permissions(guild.me, overwrite=None)
            await role.delete()

            message_channel = await self.bot.fetch_channel(event.message_channel_id)
            message = await message_channel.fetch_message(event.message_id)
            await message.delete()

            self.bot.db.delete_event(event.id)
            await ctx.send('Event deleted!')

    @event.command()
    @commands.has_role('Admin')
    async def message(self, ctx: Context, name: str, channel: TextChannel = None):
        """
        Send the event status message to a channel.
        If the second parameter is given, the message will be sent to that channel instead.
        """
        channel = channel or ctx.channel

        event = self.bot.db.get_event_by(name=(name, ctx.guild.id))
        if not event:
            await ctx.send('Event not found!')
            return
        await self.post_event_message(event, channel)

    @event.command()
    async def leave(self, ctx: Context):
        """Leave the event, if you are in a event channel."""
        event = self.bot.db.get_event_by(event_channel_id=ctx.channel.id)
        if not event:
            await ctx.send("This is not an event channel!")
        else:
            channel = await self.bot.fetch_channel(event.message_channel_id)
            message = await channel.fetch_message(event.message_id)
            await message.remove_reaction(self.__join_emoji, ctx.author)
            await ctx.message.delete()
            await self.leave_event(event, ctx.author.id)

    @event.command()
    async def list(self, ctx: Context):
        """List all events."""

        events = self.bot.db.get_all_events(ctx.guild.id)
        if len(events) > 0:
            text = ''
            for event in events:
                text += event.name + '\n'
            embed = discord.Embed(title='**Events**', description=text)
            await ctx.send(embed=embed)
        else:
            await ctx.send('No events currently!')

    @event.command(aliases=['users'])
    async def participators(self, ctx: Context, name: str):
        """List all users participating in this event."""
        event = self.bot.db.get_event_by(name=(name, ctx.guild.id))
        await ctx.send(embed=await self.get_event_embed(event, add_postamble=False))
