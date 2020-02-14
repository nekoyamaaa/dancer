import os

import discord

from my.discordmod import Client, setup_logging

class Bot(Client):
    REQUIRED_PERMISSIONS = [
        'view_channel', 'manage_channels',
        'read_message', 'send_messages', 'read_message_history',
    ]
    CHANNEL_NAME = 'member-history'

    async def on_ready(self):
        self.channels = dict()
        self.logger.info('Connected as {0.name} (ID: {0.id})'.format(self.user))
        for server in self.guilds:
            # await self.prepare(server)
            channel = discord.utils.find(lambda c: c.name == self.CHANNEL_NAME, server.channels)
            if not channel:
                channel = await server.create_text_channel(self.CHANNEL_NAME)
            self.channels[server.id]= channel
        try:
            await self.master.create_dm()
        except AttributeError:
            if self.master is None:
                self.logger.warning('Could not read dm')
        else:
            await self.cleanup(self.master.dm_channel)

        self.logger.info('Invite: %s', self.invite_url)

    async def on_guild_join(self, server):
        self.logger.info('Bot joined to %s', server)
        # await self.prepare(server)
        channel = discord.utils.find(lambda c: c.name == self.CHANNEL_NAME, server.channels)
        if not channel:
            channel = await server.create_text_channel(self.CHANNEL_NAME)
        self.channels[server.id]= channel

    async def on_guild_remove(self, server):
        del self.channels[server.id]

    async def on_member_join(self, member):
        await self.log_member(member, 'join')

    async def on_member_remove(self, member):
        await self.log_member(member, 'gone')

    async def on_member_update(self, before, after):
        if before.nick != after.nick:
            change = 'Nickname {} => {}'.format(before.nick, after.nick)
            await self.log_member(after, 'change', change)

    async def log_member(self, member, action, extra=None):
        if member == self.user:
            return
        channel = self.channels.get(member.guild.id)
        if not channel:
            self.logger.warning(
                'Server %s (member: %s) not in the list',
                member.guild, member
            )
            return

        human = '`{}`'.format(member)

        # member can be User, which does not have `nick` property
        if hasattr(member, 'nick') and member.nick:
            human = '{nick} {human}'.format(nick=member.nick, human=human)

        message = '{action}: {human}'.format(human=human, action=action.title())
        if extra:
            message += " - "
            message += extra

        try:
            await channel.send(message)
        except discord.errors.Forbidden as ex:
            # Bot has already left the guild, but still receives signal?
            self.logger.error('%s in guild: %s, member: %s', ex.__class__.__name__, channel.guild, message)

    # TODO: await/async
    def prepare(self, server):
        channel = discord.utils.find(lambda c: c.name == self.CHANNEL_NAME, server.channels)
        if not channel:
            channel = server.create_text_channel(self.CHANNEL_NAME)
        self.channels[server.id] = channel

APP_NAME = 'carlos'

opts = {
    'journal': {'SYSLOG_IDENTIFIER': 'dancer.carlos'}
}
logger = setup_logging(APP_NAME, handler_opts=opts)

debug =  os.environ.get('DEBUG', False)

client = Bot(__file__, logger=logger, debug=debug)
client.run()
