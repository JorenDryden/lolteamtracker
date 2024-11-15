import time
import discord
from discord.ext import commands, tasks
import asyncio
import os
from dotenv import load_dotenv
from colorama import Fore, init
import requests
import aiohttp

init(autoreset=True)

# Load environment variables from .env file
load_dotenv()

# Retrieve the Discord token and application ID from environment variables
api_token = os.getenv("DISCORD_TOKEN")
application_id = os.getenv("APPLICATION_ID")
riot_token = os.getenv("RIOT_TOKEN")

if api_token is None or application_id is None or riot_token is None:
    raise ValueError("DISCORD_TOKEN or APPLICATION_ID or RIOT_TOKEN is not set or could not be loaded.")

# Coloring
systemColor = Fore.LIGHTBLUE_EX
userInputColor = Fore.LIGHTGREEN_EX
statusColor = Fore.CYAN
neroj_color = Fore.RED

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
client = commands.Bot(command_prefix=".", intents=intents)


@client.event
async def on_ready():
    print(f'Logged in as {statusColor}{client.user} (ID:{client.user.id})')
    print(f'A discord bot by {neroj_color}NeroJ')
    print('---------------------------------------------------------')
    await client.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="league games")
    )

async def get_uuid(username):
    for i in range(len(username)):
        if username[i] == "#":
            query = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{username[0:i]}/{username[i+1:]}?api_key={riot_token}"
            async with aiohttp.ClientSession() as session:
                async with session.get(query) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['puuid']
                    else:
                        print(f"Error: {response.status}")


class LoLTeamTracker(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.matches = {}
        self.team_members = {}
        self.add_matches.start()

    @commands.command()
    async def create(self, ctx, *args):
        for username in args:
            uuid_data = await get_uuid(username)
            if uuid_data:
                self.team_members[username] = uuid_data
            else:
                self.team_members[username] = "Error: UUID not found"
        await self.add_matches()
        await self.print_team_matches(ctx)

    # add all the played matches from the team
    @tasks.loop(minutes=5)
    async def add_matches(self):
        for member in self.team_members:
            query = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{self.team_members[member]}/ids?start=0&count=20&api_key={riot_token}"
            async with aiohttp.ClientSession() as session:
                async with session.get(query) as response:
                    if response.status == 200:
                        data = await response.json()
                    else:
                        print(f"Error: {response.status}")
            for match in data:
                if match not in self.matches:
                    self.matches[match] = 1
                else:
                    self.matches[match] += 1

    async def print_team_matches(self, ctx):
        team_matches = []
        for match, value in list(self.matches.items()):
            if value == 2:
                team_matches.append(f"{match}")
                del self.matches[match]
        await ctx.send("\n".join(team_matches) if team_matches else "No matches to show.")

    @commands.command()
    async def list(self, ctx):
        command_list = """ 
            ## __**LolTeamTracker Commands**__📋
        - **.create** <player1#NA1> <player2#NA1> ... - create a new team to track containing given players
        - **.about** - display information about LoLTeamTracker
        - **.list** - list LoLTeamTracker's commands
        """
        await ctx.send(f"{command_list}")


# Run the bot
async def main():
    await client.add_cog(LoLTeamTracker(client))
    await client.start(api_token)

asyncio.run(main())