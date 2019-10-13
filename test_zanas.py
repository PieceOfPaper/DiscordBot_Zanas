import discord
import asyncio
 
client = discord.Client()
 
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
 
@client.event
async def on_message(message):
    if message.content.startswith('/자나스'):
        await message.channel.send('계시자.. 이 목소리가 들린다면 나를 찾아와줘..')
 
    # elif message.content.startswith('!say'):
    #     await message.channel.send(message.channel, 'leave message')
    #     msg = await client.wait_for_message(timeout=15.0, author=message.author)
 
    #     if msg is None:
    #         await message.channel.send(message.channel, '15초내로 입력해주세요. 다시시도: !say')
    #         return
    #     else:
    #         await message.channel.send(message.channel, msg.content)
 
client.run('NjMyODU0MjU0MDI1MDQ4MDY0.XaLfIg.SLXgX9kiD5v0Zu3kuv1atcNnSSo')