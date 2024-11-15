import discord
from os import environ
from dotenv import load_dotenv
from client import UwuBotClient
from const import CONFIG_FILE


load_dotenv(dotenv_path=CONFIG_FILE)
token = environ['TOKEN']


if __name__ == '__main__':
    intents = discord.Intents.all()
    client = UwuBotClient(intents=intents)
    client.run(token)
