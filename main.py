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
    elif message.content.lower() == "пинг":
        await message.channel.send(
            'понг' if random.randint(1, 5) < 5 else "в жопу себе свой пинг засунь"
        )
    elif message.content.lower() == "help":
        await message.channel.send(
            "Команды:\n" +
            "ping или пинг - отвечает pong или понг в зависимости от языка\n" +
            "trigger add - добавляет триггер\n" +
            "trigger change - изменяет одно из полей в триггере\n" +
            "trigger delete - удаляет триггер по ID\n" +
            "trigger list - генерирует файл с триггерами и присылает его в канал\n"
            "Напишите команду и help после неё, чтобы получить помощь по конкретной команде, " +
            "если по ней есть продвинутая документация.\n"
            "Например: trigger add help"
        )
    elif message.content.lower().startswith("trigger add"):
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
                "не понимаю вас без кавычек).\n" +
                "Если в тексте триггера написана подстрока \"@@\", то она будет заменять любое " +
                "упоминание @ одного человека. Обратите внимание: если не заменить комбинацию @@ " +
                "упоминанием, триггер не сработает!\n" +
                "Сочетание @sender в тексте реакции заменяется на никнейм того, кто отправил " +
                "сообщение, а @recipient - на того, чьё упоминание поставлено вместо подстроки " +
                "@@ в триггере.\n" +
                "Если триггеров на один и тот же текст несколько, я выберу любой из них на рандом."
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
    elif message.content.lower().startswith("trigger change"):
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
                        triggers[index][f"trigger{trigger_field.title()}"] = \
                            " ".join(trigger_value) if trigger_field == "reaction" else \
                            " ".join(trigger_value).lower()
                        update_triggers()
                        await message.channel.send("Триггер успешно изменен")
                except ValueError:
                    await message.channel.send("Вы написали в качестве ID триггера что угодно, " +
                                               "но не ID триггера")
    elif message.content.lower().startswith("trigger delete"):
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
                        triggerID = max(map(lambda x: int(x["id"]), triggers)) if triggers else -1
                        update_triggers()

                        await message.channel.send("Триггер успешно удален")
                except ValueError:
                    await message.channel.send("Вы написали в качестве ID триггера что угодно, " +
                                               "но не ID триггера")
    elif message.content.lower() == "trigger list":
        with open("triggers.txt", "w") as file:
            for trigger in triggers:
                file.write(
                    f"{trigger['id'].ljust(8, ' ')}{trigger['triggerType'].ljust(12, ' ')}" +
                    f"{trigger['triggerText']}\n"
                )
        await message.channel.send("Все триггеры находятся в этом файле. Реакции закрыты в " +
                                   "целях сохранения интриги",
                                   file=discord.File("triggers.txt"))
    elif message.content.lower() == "trigger list advanced":
        if str(message.channel.id) == "1033521710881841223" and \
                str(message.author.id) in ("743132856175296565", "506753799352745984"):
            await message.channel.send("Все определённые триггеры находятся в этом файле. " +
                                       "(Он доступен только разработчику и админу)",
                                       file=discord.File("triggers.csv"))
        else:
            await message.channel.send("Команда недоступна")
    else:
        reactions = []
        mention = ""
        for trigger in triggers:
            reaction = trigger["triggerReaction"]
            text = trigger["triggerText"]
            msg_text = message.content.lower().strip()
            if "@@" in trigger["triggerText"]:
                try:
                    index1 = msg_text.index("<")
                    index2 = msg_text.index(">") + 1
                    mention = msg_text[index1:index2]
                    msg_text = f"{msg_text[:index1]}@@{msg_text[index2:]}"
                except ValueError:
                    return
            if trigger["triggerType"] == "equals" and msg_text == text:
                reactions.append(reaction)
            elif trigger["triggerType"] == "startswith" and msg_text.startswith(text):
                reactions.append(reaction)
            elif trigger["triggerType"] == "endswith" and msg_text.endswith(text):
                reactions.append(reaction)
            elif trigger["triggerType"] == "contains" and text in msg_text:
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

client.run(token)
