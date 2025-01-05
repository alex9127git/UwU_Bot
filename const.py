from datetime import datetime, timezone
import discord


GUILD_ID = 1030498911586091019
GUILD_BOT_TEST_CHANNEL = 1033521710881841223
GUILD_ADMIN = 506753799352745984
GUILD_DEV = 743132856175296565
MEMBER_ROLE_ID = 1030598327059886170
GUEST_ROLE_ID = 1030600917839532092
TEXT_CATEGORY_ID = 1030498911586091020
VOICE_CATEGORY_ID = 1030793767738953828
WAITING_ROOM_ID = 1032379895118049342
BOT_USER = 1031095399521472522


TRIGGERS_FILE = 'triggers.csv'
CONFIG_FILE = 'config.env'
TRIGGER_TYPES = ['equals', 'startswith', 'endswith', 'contains', 'regex']
TRIGGER_FIELDS = ['type', 'text', 'reaction']


BOT_HELP = {
    'help': 'https://discord.com/channels/1030498911586091019/1056296643349200966/1056299068395110410',
    'trigger help': 'https://discord.com/channels/1030498911586091019/1056299068395110410/1305191749227905044',
    'trigger add help': 'https://discord.com/channels/1030498911586091019/1056299068395110410/1305191872792100896',
    'trigger change help': 'https://discord.com/channels/1030498911586091019/1056299068395110410/1305191902353690644',
    'trigger delete help': 'https://discord.com/channels/1030498911586091019/1056299068395110410/1305191926080999435',
    'trigger list help': 'https://discord.com/channels/1030498911586091019/1056299068395110410/1305191816395751604',
    'vc help': 'https://discord.com/channels/1030498911586091019/1056299068395110410/1307440864607604766',
    'vc private help': 'https://discord.com/channels/1030498911586091019/1056299068395110410/1307440864607604766',
    'vc permit help': 'https://discord.com/channels/1030498911586091019/1056299068395110410/1307440864607604766',
    'vc kick help': 'https://discord.com/channels/1030498911586091019/1056299068395110410/1307440864607604766'
}


def is_superuser(user_id):
    return user_id in (GUILD_ADMIN, GUILD_DEV)


async def is_channel_generated(channel: discord.VoiceChannel):
    first_message = [message async for message in channel.history(limit=10, oldest_first=True)][0]
    return first_message and first_message.author.id == BOT_USER
