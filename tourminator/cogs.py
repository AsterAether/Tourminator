import discord
from discord import Member, TextChannel, Reaction, RawReactionActionEvent
from discord.ext import commands
from discord.ext.commands import Context, CommandError

from tourminator.bot import TourminatorBot


class NotRegisteredError(CommandError):
    def __init__(self, ctx: Context):
        super().__init__('{0.name}, you are not registered!\n'
                         'Please use `{1}register` to register on this bot.'.format(ctx.author,
                                                                                    ctx.cog.bot.command_prefix))


async def is_registered(ctx: Context):
    if not ctx.cog.bot.db.is_registered(ctx.author.id, ctx.author.guild.id):
        raise NotRegisteredError(ctx)
    return True


class UserManagementCog(commands.Cog, name='User Management'):
    def __init__(self, bot: TourminatorBot):
        self.bot = bot

    def cog_check(self, ctx):
        return hasattr(ctx.author, 'guild')

    @commands.command()
    async def register(self, ctx: Context):
        """Register to the bot on this server, to be able to participate in events"""
        member: Member = ctx.author

        self.bot.db.register_guild(member.guild.id)
        message = '{0.name}, you are registered now!'.format(member) \
            if self.bot.db.register_user(member.id, member.guild.id) \
            else '{0.name}, you are already registered.'.format(member)

        await ctx.send(message)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, NotRegisteredError):
            await ctx.send(str(error))


class EventManagementCog(commands.Cog, name='Event Management'):
    __join_emoji = '\u2705'
    __leave_emoji = '\u274C'

    def __init__(self, bot: TourminatorBot):
        self.bot = bot

    def cog_check(self, ctx):
        return hasattr(ctx.author, 'guild')

    async def post_event_message(self, event, channel):
        message = await channel.send('Event {0.name}'.format(event))
        self.bot.db.update_event(event.id, message.id)

        await message.add_reaction(self.__join_emoji)
        await message.add_reaction(self.__leave_emoji)

    @commands.group()
    @commands.check(is_registered)
    async def event(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid event command!')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        channel = await self.bot.fetch_channel(payload.channel_id)
        user = await self.bot.fetch_user(payload.user_id)
        event = self.bot.db.get_event_by_message_id(payload.message_id)

        if event is not None and self.bot.db.is_registered(payload.user_id, payload.guild_id):
            if payload.emoji.name == self.__join_emoji:
                if self.bot.db.join_event(event.id, payload.user_id):
                    await channel.send('{0.name} joined event {1.name}!'.format(user, event))
            elif payload.emoji.name == self.__leave_emoji:
                if self.bot.db.leave_event(event.id, user.id):
                    await channel.send('{0.name} left event {1.name}!'.format(user, event))

    @event.command()
    async def create(self, ctx: Context, name: str):
        """Create a new event."""
        name = name.strip()
        event = self.bot.db.create_event(name, ctx.guild.id)
        message = 'Event created!' \
            if event \
            else 'Event with the same name already exists on this server!'
        await ctx.send(message)
        if event:
            await self.post_event_message(event, ctx.channel)

    @event.command()
    async def list(self, ctx):
        """List all events."""
        message = "Events:\n"
        events = self.bot.db.get_all_events()
        for event in events:
            message += '\t' + event.name + '\n'
        await ctx.send(message)

    @event.command()
    async def message(self, ctx: Context, name: str, channel: TextChannel = None):
        channel = channel or ctx.channel

        event = self.bot.db.get_event_by_name(name, ctx.guild.id)
        if not event:
            await ctx.send('Event not found!')
            return
        await self.post_event_message(event, channel)

    @event.command()
    async def users(self, ctx: Context, name: str):
        event = self.bot.db.get_event_by_name(name, ctx.guild.id)
        participators = self.bot.db.get_participators_of_event(event.id)
        message = '{0.name}:\n'.format(event)
        for participator in participators:
            user = await self.bot.fetch_user(participator)
            message += '\t{0.name}\n'.format(user)
        await ctx.send(message)
