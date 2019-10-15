import discord
import asyncio
import sys

token = 'token'

for argIdx, argVal in enumerate(sys.argv):
    if argVal == '-token':
        token = sys.argv[argIdx + 1]
 
client = discord.Client()
 
@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}({client.user.id})')
 
@client.event
async def on_message(message):
    if message.content.startswith('/자나스'):
        await message.channel.send('계시자.. 이 목소리가 들린다면 나를 찾아와줘..')
 
client.run(token)