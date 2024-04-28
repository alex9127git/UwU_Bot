import discord
from os import environ
from dotenv import load_dotenv
from client import UwuBotClient


load_dotenv(dotenv_path='config.env')
token = environ['TOKEN']


if __name__ == '__main__':
    intents = discord.Intents.all()
    client = UwuBotClient(intents=intents)
    client.run(token)
