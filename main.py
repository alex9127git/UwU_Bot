import csv
import sys

import discord
import random
from os import environ, path
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(dotenv_path="config.env")
token = environ["TOKEN"]

intents = discord.Intents.all()
client = discord.Client(intents=intents)

triggers = []
triggerID = 0
stats_total = []
members_list = []


def load_triggers():
    global triggers
    try:
        with open("triggers.csv", "r", encoding="utf8") as file:
            reader = csv.DictReader(file, delimiter=';', quotechar='"')
            triggers = list(reader)
    except FileNotFoundError:
        print("Error: Triggers file not found")
        sys.exit(1)


def update_triggers():
    with open("triggers.csv", "w", newline='', encoding="utf8") as file:
        writer = csv.DictWriter(file, fieldnames=["id", "triggerType", "triggerText",
                                                  "triggerReaction"],
                                delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(triggers)


def regenerate_stats_file():
    with open("stats_total.csv", "w", newline='', encoding="utf8") as file:
        writer = csv.DictWriter(file, fieldnames=["uid", "totalMessages", "totalSymbols",
                                                  "dailyMessages", "dailySymbols", "lastUpdate",
                                                  "lastActive", "description", "awards"],
                                delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(
            list(map(
                lambda member: {"uid": member.id, "totalMessages": 0, "totalSymbols": 0,
                                "dailyMessages": 0, "dailySymbols": 0,
                                "lastUpdate": datetime.now(),
                                "lastActive": datetime.now(),
                                "description": "", "awards": ""},
                members_list
            ))
        )


def load_stats():
    global stats_total, members_list
    if not path.isfile("stats_total.csv"):
        print("Stats file doesn't exist, regenerating...")
        regenerate_stats_file()
    with open("stats_total.csv", "r", encoding="utf8") as file:
        reader = csv.DictReader(file, delimiter=';', quotechar='"')
        stats_total = list(reader)
        records = list(map(lambda record: int(record["uid"]), stats_total))
        ids = list(map(lambda member: member.id, members_list))
        if records != ids:
            print("Stats file is corrupted, regenerating...")
            regenerate_stats_file()


def update_stats():
    with open("stats_total.csv", "w", newline='', encoding="utf8") as file:
        writer = csv.DictWriter(file, fieldnames=["uid", "totalMessages", "totalSymbols",
                                                  "dailyMessages", "dailySymbols", "lastUpdate",
                                                  "lastActive", "description", "awards"],
                                delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(stats_total)


def getRecordIndex(uid):
    for i in range(len(stats_total)):
        if stats_total[i]["uid"] == str(uid):
            return i
    return -1


async def send_bio(channel, member):
    role_names = map(lambda role: role.name, member.roles)
    description = stats_total[getRecordIndex(member.id)]['description']
    rewards = stats_total[getRecordIndex(member.id)]['awards']
    await channel.send(
        f"Ник: {member.nick if member.nick else member.name}\n" +
        f"Роли: {', '.join(list(filter(lambda name: name != '@everyone', role_names))[::-1])}\n"
        f"Описание:\n{description.strip() if description.strip() else '<Пусто>'}\n" +
        f"Награды:\n{rewards if rewards else 'Наград нет'}"
    )


async def send_stats(channel, member):
    index = getRecordIndex(member.id)
    total_messages = stats_total[index]["totalMessages"]
    total_symbols = stats_total[index]["totalSymbols"]
    daily_messages = stats_total[index]["dailyMessages"]
    daily_symbols = stats_total[index]["dailySymbols"]
    lastActive = datetime.strptime(
        str(stats_total[index]["lastActive"]), "%Y-%m-%d %H:%M:%S.%f")
    await channel.send(
        f"Ник: {member.nick if member.nick else member.name}\n" +
        f"Всего сообщений: {total_messages}\n" +
        f"Всего символов: {total_symbols}\n" +
        f"Сообщений за сегодня: {daily_messages}\n"
        f"Символов за сегодня: {daily_symbols}\n"
        f"Последнее сообщение было отправлено {lastActive.date()} в {lastActive.time()}\n"
    )


@client.event
async def on_ready():
    global triggers, triggerID, members_list
    guild = client.get_guild(1030498911586091019)
    members_list = sorted(filter(
        lambda member: member.bot is False, guild.members
    ), key=lambda member: member.id)
    print("Loading triggers...")
    load_triggers()
    print("Loading stats...")
    load_stats()
    triggerID = max(map(lambda x: int(x["id"]), triggers)) if triggers else -1
    print(f'Logged in: {client.user}')


@client.event
async def on_message(message):
    global triggers, triggerID
    guild = client.get_guild(1030498911586091019)
    if message.author == client.user:
        return

    msg_text = str(message.content)
    symbols = len(msg_text)
    user_index = getRecordIndex(message.author.id)
    totalSymbols = int(stats_total[user_index]["totalSymbols"])
    stats_total[user_index]["totalSymbols"] = totalSymbols + symbols
    totalMessages = int(stats_total[user_index]["totalMessages"])
    stats_total[user_index]["totalMessages"] = totalMessages + 1
    moment = datetime.now()
    stats_total[user_index]["lastActive"] = moment
    for record in range(len(stats_total)):
        stats_total[record]["lastUpdate"] = moment
        lastActive = datetime.strptime(
            str(stats_total[record]["lastActive"]), "%Y-%m-%d %H:%M:%S.%f")
        member = members_list[getRecordIndex(stats_total[record]["uid"])]
        if (moment - lastActive).days >= 3:
            await member.add_roles(guild.get_role(1030600650792382527))
            await member.remove_roles(guild.get_role(1030600493069766678))
        if lastActive.date() != moment.date():
            stats_total[record]["dailyMessages"] = 0
            stats_total[record]["dailySymbols"] = 0
    dailySymbols = int(stats_total[user_index]["dailySymbols"])
    stats_total[user_index]["dailySymbols"] = dailySymbols + symbols
    dailyMessages = int(stats_total[user_index]["dailyMessages"])
    stats_total[user_index]["dailyMessages"] = dailyMessages + 1
    update_stats()

    if msg_text.lower() == "ping":
        await message.channel.send(
            'pong' if random.randint(1, 5) < 5 else "в жопу себе свой ping засунь"
        )
    elif msg_text.lower() == "пинг":
        await message.channel.send(
            'понг' if random.randint(1, 5) < 5 else "в жопу себе свой пинг засунь"
        )
    elif msg_text.lower() == "help":
        await message.channel.send(
            "Технические команды:\n" +
            "ping или пинг - отвечает pong или понг в зависимости от языка\n\n" +
            "Команды триггеров:\n" +
            "trigger add - добавляет триггер\n" +
            "trigger change - изменяет одно из полей в триггере\n" +
            "trigger delete - удаляет триггер по ID\n" +
            "trigger list - генерирует файл с триггерами и присылает его в канал\n\n" +
            "Команды биографии:\n" +
            "bio - выводит свою биографию\n" +
            "bio @пользователь - выводит биографию другого человека\n" +
            "bio edit - редактировать описание в биографии\n" +
            "bio award - наградить человека\n" +
            "bio revoke - отозвать награду\n\n" +
            "Команды статистики:\n" +
            "stats - выводит детальную статистику для вызвавшего команду человека\n" +
            "stats @пользователь - выводит детальную статистику другого человека\n" +
            "stats all - выводит краткую статистику всех людей в сервере\n" +
            "Напишите команду и help после неё, чтобы получить помощь по конкретной команде, " +
            "если по ней есть продвинутая документация.\n"
            "Например: trigger add help"
        )
    elif msg_text.lower().startswith("trigger add"):
        message_words = msg_text.lower().split()
        if message_words[2] == "help":
            await message.channel.send(
                "Введите\ntrigger add <тип триггера>\n<текст триггера>\n<ответ на триггер>\n " +
                "чтобы добавить триггер бота. Бот будет реагировать на текст триггера и отвечать " +
                "на него.\nТипы триггеров:\n" +
                "equals - проверка на полное совпадение текста сообщения с триггером\n" +
                "startswith - проверка на совпадение начала сообщения с триггером\n" +
                "endswith - проверка на совпадение конца сообщения с триггером\n" +
                "contains - проверка на наличие триггера в сообщении где угодно.\n" +
                "После создания триггера ему присваивается уникальный ID, по которому его можно " +
                "будет изменить или удалить. ID триггеров можно посмотреть в списке триггеров.\n" +
                "Если в тексте триггера написана подстрока \"@@\", то она будет заменять любое " +
                "упоминание @ одного человека. Обратите внимание: если не заменить комбинацию @@ " +
                "упоминанием, триггер не сработает!\n" +
                "Сочетание @sender в тексте реакции заменяется на никнейм того, кто отправил " +
                "сообщение, а @recipient - на того, чьё упоминание поставлено вместо подстроки " +
                "@@ в триггере.\n" +
                "\\n заменяется на новую строку.\n"
                "Если триггеров на один и тот же текст несколько, я выберу любой из них на рандом."
            )
        else:
            try:
                _, _, trigger_type, *_ = msg_text.split()
                _, trigger_text, trigger_reaction = msg_text.split("\n")
            except ValueError:
                await message.channel.send(
                    "Ошибка при добавлении триггера: Неверный синтаксис команды")
            else:
                if trigger_type.lower() in ["equals", "startswith", "endswith", "contains"]:
                    trigger = {"id": str(triggerID + 1),
                               "triggerType": trigger_type.lower(),
                               "triggerText": trigger_text.lower().replace("\\n", "\n"),
                               "triggerReaction": trigger_reaction.replace("\\n", "\n")}
                    triggers.append(trigger)
                    triggerID = max(map(lambda x: int(x["id"]), triggers)) if triggers else -1
                    update_triggers()
                    await message.channel.send("Триггер успешно создан")
                else:
                    await message.channel.send("Ошибка при добавлении триггера: " +
                                               f"Типа {trigger_type.lower()} не существует")
    elif msg_text.lower().startswith("trigger change"):
        message_words = msg_text.lower().split()
        if message_words[2] == "help":
            await message.channel.send(
                "Введите trigger change <ID триггера> <тип поля> <новое значение>, чтобы " +
                "изменить один из параметров триггера.\n"
                "Типы полей:\n" +
                "type - тип триггера по характеру его срабатывания\n" +
                "text - текст триггера\n" +
                "reaction - ответ на триггер\n" +
                "ID триггера изменить невозможно, так как моему создателю легче убрать эту "
                "функциональность, чем программировать случаи, когда ID триггеров совпадают.\n" +
                "Значение в этой команде в кавычки не вписывайте, одно значение я всё-таки пойму."
            )
        else:
            try:
                _, _, trigger_ID, trigger_field, *trigger_value = msg_text.split()
            except ValueError:
                await message.channel.send("Ошибка при изменении триггера: слишком мало значений")
            else:
                try:
                    if int(trigger_ID) not in list(map(lambda x: int(x["id"]), triggers)):
                        await message.channel.send("Ошибка при изменении триггера: " +
                                                   f"Триггера с ID {trigger_ID} не существует")
                    elif trigger_field.lower() not in ["type", "text", "reaction"]:
                        await message.channel.send("Ошибка при изменении триггера: " +
                                                   f"Поля {trigger_field.lower()} не существует")
                    else:
                        trigger = list(filter(
                            lambda x: int(x["id"]) == int(trigger_ID), triggers))[0]
                        index = triggers.index(trigger)
                        triggers[index][f"trigger{trigger_field.title()}"] = \
                            " ".join(trigger_value).replace('\\n', '\n') \
                            if trigger_field == "reaction" else \
                            " ".join(trigger_value).lower().replace('\\n', '\n')
                        update_triggers()
                        await message.channel.send("Триггер успешно изменен")
                except ValueError:
                    await message.channel.send("Вы написали в качестве ID триггера что угодно, " +
                                               "но не ID триггера")
    elif msg_text.lower().startswith("trigger delete"):
        message_words = msg_text.lower().split()
        if message_words[2] == "help":
            await message.channel.send(
                "Введите trigger delete <ID триггера>, чтобы удалить триггер с этим ID.\n" +
                "Кроме ID, ничего больше писать не нужно."
            )
        else:
            try:
                _, _, trigger_ID = msg_text.split()
            except ValueError:
                await message.channel.send("Ошибка при удалении триггера: слишком много значений")
            else:
                try:
                    if int(trigger_ID) not in list(map(lambda x: int(x["id"]), triggers)):
                        await message.channel.send("Ошибка при изменении триггера: " +
                                                   f"Триггера с ID {trigger_ID} не существует")
                    else:
                        trigger = list(filter(
                            lambda x: int(x["id"]) == int(trigger_ID), triggers))[0]
                        triggers.remove(trigger)
                        triggerID = max(map(lambda x: int(x["id"]), triggers)) if triggers else -1
                        update_triggers()

                        await message.channel.send("Триггер успешно удален")
                except ValueError:
                    await message.channel.send("Вы написали в качестве ID триггера что угодно, " +
                                               "но не ID триггера")
    elif msg_text.lower() == "trigger list":
        with open("triggers.txt", "w") as file:
            for trigger in triggers:
                file.write(
                    f"{trigger['id'].ljust(8, ' ')}{trigger['triggerType'].ljust(12, ' ')}" +
                    f"{trigger['triggerText']}\n"
                )
        await message.channel.send("Все триггеры находятся в этом файле. Реакции закрыты в " +
                                   "целях сохранения интриги",
                                   file=discord.File("triggers.txt"))
    elif msg_text.lower() == "trigger list advanced":
        if str(message.channel.id) == "1033521710881841223" and \
                str(message.author.id) in ("743132856175296565", "506753799352745984"):
            await message.channel.send("Все определённые триггеры находятся в этом файле. " +
                                       "(Он доступен только разработчику и админу)",
                                       file=discord.File("triggers.csv"))
        else:
            await message.channel.send("Команда недоступна")
    elif msg_text.lower().startswith("bio"):
        if msg_text.lower() == "bio":
            await send_bio(message.channel, message.author)
        elif len(msg_text.split()) == 2:
            mention = msg_text.split()[1]
            if mention.startswith("<@") and mention.endswith(">"):
                user_id = mention[2:-1]
                index = getRecordIndex(user_id)
                if index != -1:
                    member = members_list[index]
                    await send_bio(message.channel, member)
                else:
                    await message.channel.send("Такого пользователя не существует")
            else:
                await message.channel.send("Неправильный синтакис команды")
        elif msg_text.lower().startswith("bio edit"):
            if msg_text.lower() == "bio edit help":
                await message.channel.send(
                    "Введите\nbio edit\n<описание>\nчтобы изменить себе описание в биографии.")
            else:
                _, *desc = msg_text.split("\n")
                if desc:
                    description = "\n".join(desc)
                    stats_total[getRecordIndex(message.author.id)]["description"] = description
                    update_stats()
                    await message.channel.send("Описание успешно изменено")
                else:
                    await message.channel.send("Отсутсвует описание")
        elif msg_text.lower().startswith("bio award"):
            if msg_text.lower() == "bio award help":
                await message.channel.send(
                    "Введите bio award <упоминание> <награда>, чтобы наградить пользователя.\n" +
                    "Награды будут отображаться в биографии у пользователя."
                )
            else:
                _, _, mention, *reward_name = msg_text.split()
                if mention.startswith("<@") and mention.endswith(">"):
                    user_id = mention[2:-1]
                    index = getRecordIndex(user_id)
                    member = members_list[index]
                    if member == message.author:
                        await message.channel.send("Нельзя награждать самого себя")
                    elif index != -1:
                        rewards = stats_total[index]["awards"]
                        if rewards:
                            rewards += "\n"
                        reward = f':star: {" ".join(reward_name)}'
                        rewards += reward
                        stats_total[index]["awards"] = rewards
                        await message.channel.send(f"<@{user_id}> получает награду:\n{reward}")
                    else:
                        await message.channel.send("Такого пользователя не существует")
                else:
                    await message.channel.send("Неправильный синтакис команды")
        elif msg_text.lower().startswith("bio revoke"):
            if msg_text.lower() == "bio revoke help":
                await message.channel.send(
                    "Введите bio revoke <упоминание> <ID награды>, чтобы отозвать награду у " +
                    "пользователя.\n" +
                    "Награды нумеруются с нуля, сверху вниз."
                )
            else:
                _, _, mention, reward_id = msg_text.split()
                if mention.startswith("<@") and mention.endswith(">"):
                    user_id = mention[2:-1]
                    index = getRecordIndex(user_id)
                    member = members_list[index]
                    if member == message.author:
                        await message.channel.send("Нельзя отбирать награды у самого себя")
                    elif index != -1:
                        try:
                            rewards = stats_total[index]["awards"]
                            r = rewards.split("\n")
                            reward = r[int(reward_id)]
                            del r[int(reward_id)]
                            stats_total[index]["awards"] = "\n".join(r)
                            await message.channel.send(f"Награда {reward} отозвана у <@{user_id}>")
                        except ValueError:
                            await message.channel.send("Ошибка при чтении ID награды")
                    else:
                        await message.channel.send("Такого пользователя не существует")
                else:
                    await message.channel.send("Неправильный синтакис команды")
    elif msg_text.lower().startswith("stats"):
        if msg_text.lower() == "stats":
            await send_stats(message.channel, message.author)
        elif msg_text.lower() == "stats all":
            stats_width1 = 40
            stats_width2 = 20
            stats_width3 = 20
            stats_width4 = 30
            stats_string = "```" + "Пользователь".ljust(stats_width1, " ") + \
                           "Сообщений за день".ljust(stats_width2, " ") + \
                           "Символов за день".ljust(stats_width3, " ") + \
                           "Последняя активность".ljust(stats_width4, " ") + "\n"
            for i, stats in enumerate(stats_total):
                member = members_list[i]
                stats_string += (
                    member.nick if member.nick else member.name).ljust(stats_width1, " ")
                stats_string += str(stats["dailyMessages"]).ljust(stats_width2, " ")
                stats_string += str(stats["dailySymbols"]).ljust(stats_width3, " ")
                stats_string += str(stats["lastActive"]).ljust(stats_width4, " ")
                stats_string += "\n"
            stats_string += "```"
            await message.channel.send(stats_string)
        elif len(msg_text.split()) == 2:
            mention = msg_text.split()[1]
            if mention.startswith("<@") and mention.endswith(">"):
                user_id = mention[2:-1]
                index = getRecordIndex(user_id)
                if index != -1:
                    member = members_list[index]
                    await send_stats(message.channel, member)
                else:
                    await message.channel.send("Такого пользователя не существует")
            else:
                await message.channel.send("Неправильный синтакис команды")
    else:
        try:
            reactions = []
            mention = ""
            for trigger in triggers:
                reaction = trigger["triggerReaction"]
                text = trigger["triggerText"]
                msg = msg_text.lower()
                if "@@" in trigger["triggerText"]:
                    try:
                        index1 = msg.index("<")
                        index2 = msg.index(">") + 1
                        mention = msg[index1:index2]
                        msg = f"{msg[:index1]}@@{msg[index2:]}"
                    except ValueError:
                        continue
                if trigger["triggerType"] == "equals" and msg == text:
                    reactions.append(reaction)
                elif trigger["triggerType"] == "startswith" and msg.startswith(text):
                    reactions.append(reaction)
                elif trigger["triggerType"] == "endswith" and msg.endswith(text):
                    reactions.append(reaction)
                elif trigger["triggerType"] == "contains" and text in msg.lower():
                    reactions.append(reaction)
            reactions = list(map(
                lambda x: x.replace("@sender", f"<@{message.author.id}>"), reactions
            ))
            if mention:
                reactions = list(map(
                    lambda x: x.replace("@recipient", mention), reactions
                ))
            if reactions:
                await message.channel.send(random.choice(reactions))
        except discord.Forbidden:
            pass


client.run(token)
