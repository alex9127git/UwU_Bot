import logging
import random
import re
import discord
import csv
import sys
from typing import Any
from const import GUILD_ID, GUILD_BOT_TEST_CHANNEL, GUILD_ADMIN, GUILD_DEV, MEMBER_ROLE_ID, GUEST_ROLE_ID
from const import TEXT_CATEGORY_ID, VOICE_CATEGORY_ID, TRIGGERS_FILE, TRIGGER_TYPES, TRIGGER_FIELDS, WAITING_ROOM_ID
from const import is_superuser, is_channel_generated, BOT_HELP


class UwuBotClient(discord.Client):
    def __init__(self, intents: discord.Intents, **options: Any):
        super().__init__(intents=intents, **options)
        self.voice_ctg = None
        self.text_ctg = None
        self.wguild = None
        self.triggers = None
        self.triggerID = 0
        self.logger = logging.getLogger('discord')

    def load_triggers(self):
        try:
            with open(TRIGGERS_FILE, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file, delimiter=';', quotechar='"')
                self.triggers = list(reader)
        except FileNotFoundError:
            self.logger.critical('Triggers file not found')
            sys.exit(1)

    def update_triggers(self):
        self.triggerID = max(map(lambda x: int(x['id']), self.triggers)) if self.triggers else -1
        with open(TRIGGERS_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['id', 'triggerType', 'triggerText',
                                                      'triggerReaction'],
                                    delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(self.triggers)
            self.logger.info('Triggers file successfully updated')

    async def on_ready(self):
        self.wguild = self.get_guild(GUILD_ID)
        self.text_ctg = discord.utils.get(self.wguild.categories, id=TEXT_CATEGORY_ID)
        self.voice_ctg = discord.utils.get(self.wguild.categories, id=VOICE_CATEGORY_ID)
        self.logger.info('Loading triggers...')
        self.load_triggers()
        self.triggerID = max(map(lambda x: int(x['id']), self.triggers)) if self.triggers else -1
        self.logger.info(f'Logged in: {self.user}')

    async def on_message(self, message):
        if message.author == self.user:
            return

        msg_text = str(message.content)

        if msg_text.startswith('send') and is_superuser(message.author.id):
            separator = msg_text[5:].index(' ')
            channel_id = int(msg_text[5:separator + 5])
            sent_msg = msg_text[separator + 6:]
            channel = discord.utils.get(self.wguild.channels, id=channel_id)
            if channel:
                await channel.send(sent_msg)

        if msg_text.startswith('debug'):
            if message.channel.id == GUILD_BOT_TEST_CHANNEL and is_superuser(message.author.id):
                command = msg_text[6:]
                try:
                    await message.channel.send(eval(command))
                except Exception as e:
                    await message.channel.send(f'{e.__class__.__name__}: {str(e)}')

        if msg_text.startswith('customdebug'):
            if message.channel.id == GUILD_BOT_TEST_CHANNEL and is_superuser(message.author.id):
                for channel in self.voice_ctg.channels:
                    print(channel.id)
                    if await is_channel_generated(channel):
                        await channel.send('Этот канал создан мной')

        if msg_text.lower() == 'ping':
            await message.channel.send(
                'pong' if random.randint(1, 5) < 5 else 'в жопу себе свой ping засунь'
            )
        elif msg_text.lower() == 'пинг':
            await message.channel.send(
                'понг' if random.randint(1, 5) < 5 else 'в жопу себе свой пинг засунь'
            )
        elif 'help' in msg_text.lower():
            if msg_text.lower() not in BOT_HELP.keys():
                return
            await message.channel.send(BOT_HELP[msg_text.lower()])
        elif msg_text.lower().startswith('trigger add'):
            if not discord.utils.get(message.author.roles, id=MEMBER_ROLE_ID):
                await message.channel.send('Вы не можете создавать, менять и удалять триггеры')
                return
            try:
                _, _, trigger_type, *_ = msg_text.split()
                _, trigger_text, trigger_reaction = msg_text.split('\n')
            except ValueError:
                await message.channel.send(
                    'Ошибка при добавлении триггера: Неверный синтаксис команды')
            else:
                if trigger_type.lower() not in TRIGGER_TYPES:
                    await message.channel.send('Ошибка при добавлении триггера: ' +
                                               f'Типа {trigger_type.lower()} не существует')
                    return
                trigger = {'id': str(self.triggerID + 1),
                           'triggerType': trigger_type.lower().strip(),
                           'triggerText': trigger_text.lower().replace('\\n', '\n').strip(),
                           'triggerReaction': trigger_reaction.replace('\\n', '\n').strip()}
                self.triggers.append(trigger)
                self.update_triggers()
                await message.channel.send('Триггер успешно создан')
        elif msg_text.lower().startswith('trigger change'):
            if not discord.utils.get(message.author.roles, id=MEMBER_ROLE_ID):
                await message.channel.send('Вы не можете создавать, менять и удалять триггеры')
                return
            try:
                _, _, tid, trigger_field, *trigger_value = msg_text.split()
            except ValueError:
                await message.channel.send('Ошибка при изменении триггера: слишком мало значений')
            else:
                try:
                    trigger_value = ' '.join(trigger_value)
                    if int(tid) not in list(map(lambda x: int(x['id']), self.triggers)):
                        await message.channel.send('Ошибка при изменении триггера: ' +
                                                   f'Триггера с ID {tid} не существует')
                        return
                    if trigger_field.lower() not in TRIGGER_FIELDS:
                        await message.channel.send('Ошибка при изменении триггера: ' +
                                                   f'Поля {trigger_field.lower()} не существует')
                        return
                    if trigger_field == 'type' and trigger_value.lower() not in TRIGGER_TYPES:
                        await message.channel.send('Ошибка при изменении триггера: ' +
                                                   f'Типа {trigger_value.lower()} не существует')
                        return
                    trigger = list(filter(
                        lambda x: int(x['id']) == int(tid), self.triggers))[0]
                    index = self.triggers.index(trigger)
                    self.triggers[index][f'trigger{trigger_field.title()}'] = \
                        trigger_value.replace('\\n', '\n').strip() if trigger_field == 'reaction' else \
                        trigger_value.lower().replace('\\n', '\n').strip()
                    update_triggers()
                    await message.channel.send('Триггер успешно изменен')
                except ValueError:
                    await message.channel.send('Вы написали в качестве ID триггера что угодно, но не ID триггера')
        elif msg_text.lower().startswith('trigger delete'):
            if not discord.utils.get(message.author.roles, id=MEMBER_ROLE_ID):
                await message.channel.send('Вы не можете создавать, менять и удалять триггеры')
                return
            try:
                _, _, tid = msg_text.split()
            except ValueError:
                await message.channel.send('Ошибка при удалении триггера: слишком много значений')
            else:
                try:
                    if int(tid) not in list(map(lambda x: int(x['id']), self.triggers)):
                        await message.channel.send('Ошибка при изменении триггера: ' +
                                                   f'Триггера с ID {tid} не существует')
                        return
                    trigger = list(filter(lambda x: int(x['id']) == int(tid), self.triggers))[0]
                    self.triggers.remove(trigger)
                    update_triggers()
                    await message.channel.send('Триггер успешно удален')
                except ValueError:
                    await message.channel.send('Вы написали в качестве ID триггера что угодно, но не ID триггера')
        elif msg_text.lower() == 'trigger list':
            with open('triggers.txt', 'w', encoding='utf-8') as file:
                for trigger in self.triggers:
                    file.write(
                        f'{trigger["id"].ljust(8, " ")}{trigger["triggerType"].ljust(12, " ")}' +
                        f'{trigger["triggerText"]}\n'
                    )
            await message.channel.send('Все триггеры находятся в этом файле. Реакции закрыты в ' +
                                       'целях сохранения интриги',
                                       file=discord.File('triggers.txt'))
        elif msg_text.lower() == 'trigger list advanced':
            if message.channel.id == GUILD_BOT_TEST_CHANNEL and is_superuser(message.author.id):
                await message.channel.send('Все определённые триггеры находятся в этом файле. ' +
                                           '(Он доступен только разработчику и админу)',
                                           file=discord.File(TRIGGERS_FILE))
        elif msg_text.lower() == 'vc private':
            if not is_channel_generated(message.channel):
                return
            try:
                role1 = discord.utils.get(self.wguild.roles, id=MEMBER_ROLE_ID)
                role2 = discord.utils.get(self.wguild.roles, id=GUEST_ROLE_ID)
                await message.channel.set_permissions(role1, read_messages=False, send_messages=False)
                await message.channel.set_permissions(role2, read_messages=False, send_messages=False)
                await message.channel.set_permissions(message.author, read_messages=True, send_messages=True,
                                                      manage_channels=True)
                await message.channel.set_permissions(
                    discord.utils.get(self.wguild.members, id=self.user.id),
                    read_messages=True, send_messages=True
                )
                await message.channel.send(
                    f'<@{message.author.id}>, теперь этот канал приватный.\n' +
                    'Чтобы пригласить людей, напишите vc permit <никнейм на сервере или юзернейм дискорда>.\n' +
                    'Канал удалится автоматически при неактивности.')
            except ValueError:
                await message.channel.send('Неправильный синтакис команды')
        elif msg_text.lower().startswith('vc permit') or msg_text.lower().startswith('vc kick'):
            if not is_channel_generated(message.channel):
                return
            _, action, *words = msg_text.split()
            name = ' '.join(words)
            member = discord.utils.get(self.wguild.members, nick=name)
            if not member:
                member = discord.utils.get(self.wguild.members, name=name)
            if not member:
                await message.channel.send('Такого пользователя не существует')
                return
            perms = action.lower() == 'permit'
            await message.channel.set_permissions(member, read_messages=perms, send_messages=perms)
            await message.channel.send(f'<@{member.id}> теперь имеет доступ в канал'
                                       if perms else
                                       f'<@{member.id}> теперь изгнан из канала')
        else:
            try:
                reactions = []
                mention = ''
                for trigger in self.triggers:
                    reaction = trigger['triggerReaction']
                    text = trigger['triggerText']
                    msg = msg_text.lower()
                    if '@@' in trigger['triggerText']:
                        try:
                            index1 = msg.index('<')
                            index2 = msg.index('>') + 1
                            mention = msg[index1:index2]
                            msg = f'{msg[:index1]}@@{msg[index2:]}'
                        except ValueError:
                            continue
                    if trigger['triggerType'] == TRIGGER_TYPES[0] and msg == text:
                        reactions.append(reaction)
                    elif trigger['triggerType'] == TRIGGER_TYPES[1] and msg.startswith(text):
                        reactions.append(reaction)
                    elif trigger['triggerType'] == TRIGGER_TYPES[2] and msg.endswith(text):
                        reactions.append(reaction)
                    elif trigger['triggerType'] == TRIGGER_TYPES[3] and text in msg:
                        reactions.append(reaction)
                    elif trigger['triggerType'] == TRIGGER_TYPES[4] and bool(re.search(text, msg_text)):
                        reactions.append(reaction)
                reactions = list(map(
                    lambda x: x.replace('@sender', f'<@{message.author.id}>'), reactions
                ))
                if mention:
                    reactions = list(map(
                        lambda x: x.replace('@recipient', mention), reactions
                    ))
                if reactions:
                    await message.channel.send(random.choice(reactions))
            except discord.Forbidden:
                pass

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        waiting_room: discord.VoiceChannel = discord.utils.get(self.voice_ctg.channels, id=WAITING_ROOM_ID)
        for channel in self.voice_ctg.channels:
            if await is_channel_generated(channel) and len(channel.members) == 0:
                await channel.delete()
        if waiting_room.members:
            channel = await self.wguild.create_voice_channel(name=f'🛑┃Приватка {member.nick}',
                                                             category=self.voice_ctg)
            await channel.set_permissions(member, manage_channels=True)
            await channel.send(
                f'<@{member.id}>, вы создали приватный канал.\n' +
                'Сюда можно пригласить людей и общаться с ними вдали от мирской суеты сервера.\n' +
                f'Когда вам надоест, выйдите из канала, и он автоматически удалится.')
            for m in waiting_room.members:
                await m.move_to(channel)
