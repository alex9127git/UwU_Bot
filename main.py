import csv

import discord
import random
from os import environ
from dotenv import load_dotenv

load_dotenv(dotenv_path="config.env")
token = environ["TOKEN"]

intents = discord.Intents.all()
client = discord.Client(intents=intents)
triggers = []
triggerID = 0


def get_triggers():
    global triggers
    with open("triggers.csv", "r", encoding="utf8") as file:
        reader = csv.DictReader(file, delimiter=';', quotechar='"')
        triggers = list(reader)


def update_triggers():
    with open("triggers.csv", "w", newline='', encoding="utf8") as file:
        writer = csv.DictWriter(file, fieldnames=["id", "triggerType", "triggerText",
                                                  "triggerReaction"],
                                delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(triggers)


@client.event
async def on_ready():
    global triggers, triggerID
    print("Loading triggers...")
    get_triggers()
    print("Triggers loaded")
    triggerID = max(map(lambda x: int(x["id"]), triggers)) if triggers else -1
    print(f'Logged in: {client.user}')


@client.event
async def on_message(message):
    global triggers, triggerID
    if message.author == client.user:
        return

    if message.content.lower() == "ping":
        await message.channel.send(
            'pong' if random.randint(1, 5) < 5 else "в жопу себе свой ping засунь"
        )

    if message.content.lower() == "пинг":
        await message.channel.send(
            'понг' if random.randint(1, 5) < 5 else "в жопу себе свой пинг засунь"
        )

    if message.content.lower() == "help":
        await message.channel.send(
            "Команды:\n" +
            "ping или пинг - отвечает pong или понг в зависимости от языка\n" +
            "trigger add - добавляет триггер\n" +
            "trigger change - изменяет одно из полей в триггере\n" +
            "trigger delete - удаляет триггер по ID\n" +
            "triggers list - генерирует файл с триггерами и присылает его в канал\n"
            "Напишите команду и help после неё, чтобы получить помощь по конкретной команде, " +
            "если по ней есть продвинутая документация.\n"
            "Например: trigger add help"
        )

    if message.content.lower().startswith("trigger add"):
        message_words = message.content.lower().split()
        if message_words[2] == "help":
            await message.channel.send(
                "Введите trigger add <тип триггера> <текст триггера> <ответ на триггер>, чтобы " +
                "добавить триггер бота. Бот будет реагировать на текст триггера и отвечать на " +
                "него.\n"
                "Типы триггеров:\n" +
                "equals - проверка на полное совпадение текста сообщения с триггером\n" +
                "startswith - проверка на совпадение начала сообщения с триггером\n" +
                "endswith - проверка на совпадение конца сообщения с триггером\n" +
                "contains - проверка на наличие триггера в сообщении где угодно.\n" +
                "После создания триггера ему присваивается уникальный ID, по которому его можно " +
                "будет изменить или удалить. ID триггеров можно посмотреть в списке триггеров.\n" +
                "Текст триггера и ответ на триггер нужно заключать в кавычки (так как я еблан и " +
                "не понимаю вас без кавычек)."
            )
        else:
            try:
                _, _, trigger_type, *_ = message.content.split()
                _, trigger_text, _, trigger_reaction, _ = message.content.split("\"")
            except ValueError:
                await message.channel.send("Ошибка при добавлении триггера: Не забывайте, " +
                                           "что триггер нужно заключить в кавычки!")
            else:
                if trigger_type.lower() in ["equals", "startswith", "endswith", "contains"]:

                    trigger = {"id": str(triggerID + 1),
                               "triggerType": trigger_type.lower(),
                               "triggerText": trigger_text.lower(),
                               "triggerReaction": trigger_reaction}
                    triggers.append(trigger)
                    triggerID = max(map(lambda x: int(x["id"]), triggers)) if triggers else -1
                    update_triggers()
                    await message.channel.send("Триггер успешно создан")
                else:
                    await message.channel.send("Ошибка при добавлении триггера: " +
                                               f"Типа {trigger_type.lower()} не существует")

    if message.content.lower().startswith("trigger change"):
        message_words = message.content.lower().split()
        if message_words[2] == "help":
            await message.channel.send(
                "Введите trigger add <ID триггера> <тип поля> <новое значение>, чтобы " +
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
                _, _, trigger_ID, trigger_field, *trigger_value = message.content.split()
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
                        triggers[index][f"trigger{trigger_field.title()}"] = " ".join(trigger_value)
                        update_triggers()
                        await message.channel.send("Триггер успешно изменен")
                except ValueError:
                    await message.channel.send("Вы написали в качестве ID триггера что угодно, " +
                                               "но не ID триггера")

    if message.content.lower().startswith("trigger delete"):
        message_words = message.content.lower().split()
        if message_words[2] == "help":
            await message.channel.send(
                "Введите trigger delete <ID триггера>, чтобы удалить триггер с этим ID.\n" +
                "Кроме ID, ничего больше писать не нужно."
            )
        else:
            try:
                _, _, trigger_ID = message.content.split()
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
                        update_triggers()
                        await message.channel.send("Триггер успешно удален")
                except ValueError:
                    await message.channel.send("Вы написали в качестве ID триггера что угодно, " +
                                               "но не ID триггера")

    if message.content.lower() == "trigger list":
        await message.channel.send("Все определённые триггеры находятся в этом файле. " +
                                   "Если вы скинете это @Alex9127, он должен понять этот файл.",
                                   file=discord.File("triggers.csv"))

    for trigger in triggers:
        if trigger["triggerType"] == "equals" and message.content.lower() == trigger["triggerText"]:
            await message.channel.send(trigger["triggerReaction"])
        elif trigger["triggerType"] == "startswith" and message.content.lower().startswith(trigger[
                "triggerText"]):
            await message.channel.send(trigger["triggerReaction"])
        elif trigger["triggerType"] == "endswith" and message.content.lower().endswith(trigger[
                "triggerText"]):
            await message.channel.send(trigger["triggerReaction"])
        elif trigger["triggerType"] == "contains" and trigger["triggerText"] in \
                message.content.lower():
            await message.channel.send(trigger["triggerReaction"])

client.run(token)
