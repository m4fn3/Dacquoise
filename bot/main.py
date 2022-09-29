import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging
import os

# logging
logging.basicConfig(level=logging.INFO)

# environment variables
load_dotenv(verbose=True)
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
TOKEN = os.getenv("TOKEN")


class Core(commands.Bot):
    """Core class of the Bot"""

    def __init__(self, prefix: str, status: discord.Status, intents: discord.Intents) -> None:
        super().__init__(prefix, status=status, intents=intents)
        self.remove_command("help")

    async def on_ready(self) -> None:
        print(f"Log-in: {self.user}")
        await self.load_extension("commands")
        await self.tree.sync()


# run
if __name__ == '__main__':
    intent = discord.Intents.default()
    intent.typing = False
    client = Core("/", status=discord.Status.idle, intents=intent)
    client.run(TOKEN)
