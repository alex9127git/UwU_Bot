import discord
import random
from os import environ
from dotenv import load_dotenv

load_dotenv(dotenv_path="config.env")
token = environ["TOKEN"]

intents = discord.Intents.all()
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f'Logged in: {client.user}')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content == "ping":
        await message.channel.send(
            'pong' if random.randint(1, 5) < 5 else "в жопу себе свой пинг засунь"
        )

client.run(token)
