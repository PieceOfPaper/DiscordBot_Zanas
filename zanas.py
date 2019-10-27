import discord
import asyncio
import sys
import datetime

token = 'token'

for argIdx, argVal in enumerate(sys.argv):
    if argVal == '-token':
        token = sys.argv[argIdx + 1]

class GuildData:
    id = 0
    last_channel_id = 0
    
    fieldboss_channel_id = 0
    filedboss_high_time_1 = datetime.datetime.now() #숲필보
    filedboss_high_checked_1 = True
    filedboss_high_time_2 = datetime.datetime.now() #도심필보
    filedboss_high_checked_2 = True
    filedboss_high_time_3 = datetime.datetime.now() #모링
    filedboss_high_checked_3 = True

    def __init__(self, id):
        self.id = id


class ZanasClient(discord.Client):

    guildDatas = dict()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # create the background task and run it in the background
        self.bg_task = self.loop.create_task(self.my_background_task())

    async def on_connect(self):
        print(f'on_connect: {self.user.name}({self.user.id})')
    
    async def on_ready(self):
        print(f'on_ready: {self.user.name}({self.user.id})')
        for guild in self.guilds:
            if guild.id not in self.guildDatas:
                self.guildDatas[guild.id] = GuildData(guild.id)
        print(f'guild data count: {len(self.guildDatas)}')

    # async def on_member_join(self, member):
    #     print(f'on_member_join: {member.display_name}({member.id})')

    # async def on_member_remove(self, member):
    #     print(f'on_member_remove: {member.display_name}({member.id})')

    # async def on_member_update(self, before, after):
    #     print(f'on_member_update: {before.display_name}({before.id}) -> {after.display_name}({after.id})')

    # async def on_user_update(self, before, after):
    #     print(f'on_user_update: {before.name}({before.id}) -> {after.name}({after.id})')

    async def on_guild_join(self, guild):
        print(f'on_guild_join: {guild.name}({guild.id})')
        if guild.id not in self.guildDatas:
            self.guildDatas[guild.id] = GuildData(guild.id)

    async def on_guild_remove(self, guild):
        print(f'on_guild_remove: {guild.name}({guild.id})')
        if guild.id in self.guildDatas:
            del self.guildDatas[guild.id]

    # async def on_guild_update(self, guild):
    #     print(f'on_guild_update: {guild.name}({guild.id})')
    
    async def on_message(self, message):
        if message.author == self.user:
            return
        args = message.content.split(' ')
        if len(args) > 0:
            if args[0] == './개발자나스':
                print(f'channel: {message.channel.name}({message.channel.id})')
                print(f'guild: {message.guild.name}({message.guild.id})')
                await message.channel.send('print debug.')
            elif args[0] == './필보자나스':
                del args[0]
                await self.command_fieldboss(message, args)
            elif args[0] == './숲필보':
                del args[0]
                await self.command_fieldboss_1(message, args)
            elif args[0] == './도심필보':
                del args[0]
                await self.command_fieldboss_2(message, args)
            elif args[0] == './모링' or args[0] == './모링포니아':
                del args[0]
                await self.command_fieldboss_3(message, args)
            elif args[0] == './자나스':
                if len(args) > 1 and args[1] == '도와줘':
                    help_message = '- 필보관련 명령어\n'
                    help_message += './필보자나스 [숲/도심/모링] [X/킬/취소]\n'
                    help_message += './숲필보 [X/킬/취소]\n'
                    help_message += './도심필보 [X/킬/취소]\n'
                    help_message += './모링 [X/킬/취소]\n'
                    help_message += './모링포니아 [X/킬/취소]\n'
                    await message.channel.send(help_message)
                else:
                    await message.channel.send('계시자.. 이 목소리가 들린다면 나를 찾아와줘..')

    async def command_fieldboss(self, message, args):
            if len(args) > 0:
                if args[0] == '고정':
                    self.guildDatas[message.guild.id].fieldboss_channel_id = message.channel.id
                    await message.channel.send(f'필보 알림 채널 설정 <#{message.channel.id}>')
                elif args[0] == '숲':
                    del args[0]
                    await self.command_fieldboss_1(message, args)
                elif args[0] == '도심':
                    del args[0]
                    await self.command_fieldboss_2(message, args)
                elif args[0] == '모링' or args[0] == '모링포니아':
                    del args[0]
                    await self.command_fieldboss_3(message, args)

    async def command_fieldboss_1(self, message, args):
        if len(args) > 0:
            if args[0] == '킬':
                if self.guildDatas[message.guild.id].fieldboss_channel_id == 0:
                    self.guildDatas[message.guild.id].fieldboss_channel_id = message.channel.id
                self.guildDatas[message.guild.id].filedboss_high_time_1 = datetime.datetime.now() + datetime.timedelta(hours=4, minutes=10) - datetime.timedelta(minutes=30)
                self.guildDatas[message.guild.id].filedboss_high_checked_1 = False
                await message.channel.send('숲필보 시간 등록.')
            elif args[0] == '취소':
                self.guildDatas[message.guild.id].filedboss_high_checked_1 = True
                await message.channel.send('숲필보 시간 등록취소.')
        if self.guildDatas[message.guild.id].filedboss_high_checked_1:
            await message.channel.send(f'숲필보 시간 정보없음.')
        else:
            await message.channel.send(f'숲필보 다음 젠 타임. {self.guildDatas[message.guild.id].filedboss_high_time_1}')

    async def command_fieldboss_2(self, message, args):
        if len(args) > 0:
            if args[0] == '킬':
                if self.guildDatas[message.guild.id].fieldboss_channel_id == 0:
                    self.guildDatas[message.guild.id].fieldboss_channel_id = message.channel.id
                self.guildDatas[message.guild.id].filedboss_high_time_2 = datetime.datetime.now() + datetime.timedelta(hours=4, minutes=10) - datetime.timedelta(minutes=30)
                self.guildDatas[message.guild.id].filedboss_high_checked_2 = False
                await message.channel.send('도심필보 시간 등록.')
            elif args[0] == '취소':
                self.guildDatas[message.guild.id].filedboss_high_checked_2 = True
                await message.channel.send('도심필보 시간 등록취소.')
        if self.guildDatas[message.guild.id].filedboss_high_checked_2:
            await message.channel.send(f'도심필보 시간 정보없음.')
        else:
            await message.channel.send(f'도심필보 다음 젠 타임. {self.guildDatas[message.guild.id].filedboss_high_time_2}')
    
    async def command_fieldboss_3(self, message, args):
        if len(args) > 0:
            if args[0] == '킬':
                if self.guildDatas[message.guild.id].fieldboss_channel_id == 0:
                    self.guildDatas[message.guild.id].fieldboss_channel_id = message.channel.id
                self.guildDatas[message.guild.id].filedboss_high_time_3 = datetime.datetime.now() + datetime.timedelta(hours=4, minutes=10) - datetime.timedelta(minutes=30)
                self.guildDatas[message.guild.id].filedboss_high_checked_3 = False
                await message.channel.send('모링포니아 시간 등록.')
            elif args[0] == '취소':
                self.guildDatas[message.guild.id].filedboss_high_checked_3 = True
                await message.channel.send('모링포니아 시간 등록취소.')
        if self.guildDatas[message.guild.id].filedboss_high_checked_3:
            await message.channel.send(f'모링포니아 시간 정보없음.')
        else:
            await message.channel.send(f'모링포니아 다음 젠 타임. {self.guildDatas[message.guild.id].filedboss_high_time_3}')

    async def my_background_task(self):
        await self.wait_until_ready()
        counter = 0
        while not self.is_closed():
            counter += 1
            for key in self.guildDatas:
                if self.guildDatas[key].filedboss_high_checked_1 == False:
                    if self.guildDatas[key].filedboss_high_time_1 < datetime.datetime.now():
                        self.guildDatas[key].filedboss_high_checked_1 = True
                        await client.get_channel(self.guildDatas[key].fieldboss_channel_id).send('숲필보 예상 젠 시간 30분 전!')
                if self.guildDatas[key].filedboss_high_checked_2 == False:
                    if self.guildDatas[key].filedboss_high_time_2 < datetime.datetime.now():
                        self.guildDatas[key].filedboss_high_checked_2 = True
                        await client.get_channel(self.guildDatas[key].fieldboss_channel_id).send('도심필보 예상 젠 시간 30분 전!')
                if self.guildDatas[key].filedboss_high_checked_3 == False:
                    if self.guildDatas[key].filedboss_high_time_3 < datetime.datetime.now():
                        self.guildDatas[key].filedboss_high_checked_3 = True
                        await client.get_channel(self.guildDatas[key].fieldboss_channel_id).send('모링포니아 예상 젠 시간 30분 전!')
            await asyncio.sleep(1)


client = ZanasClient()
client.run(token)