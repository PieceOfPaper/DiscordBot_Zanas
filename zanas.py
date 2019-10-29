import discord
import asyncio
import sys
import datetime

token = 'token'

for argIdx, argVal in enumerate(sys.argv):
    if argVal == '-token':
        token = sys.argv[argIdx + 1]


def datetime_str(t):
    return f'{t.year}년 {t.month}월 {t.day}일 {t.hour}시 {t.minute}분 {t.second}초'

def timedelta_str(t):
    hours, remainder = divmod(t.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f'{hours}시간 {minutes}분 {seconds}초'


class WaitToDatetimeForm:
    name = ''
    channel_id = 0
    time = datetime.datetime.now()
    check_30min = True
    check_10min = True

    def __init__(self, name):
        self.name = name

    def get_remain_time(self):
        return self.time - datetime.datetime.now()

    def can_check_time(self):
        return (not self.check_30min) or (not self.check_10min)

    def reset_time(self, time):
        self.time = time
        self.check_30min = False
        self.check_10min = False

    def cancel_time(self):
        self.time = datetime.datetime.now()
        self.check_30min = True
        self.check_10min = True
        
    def check_time(self):
        minutes, seconds = divmod(self.time - datetime.datetime.now(), 60)
        if not self.check_30min and minutes < 30:
            return 30
        elif not self.check_10min and minutes < 10:
            return 10
        else:
            return -1

class GuildData:
    id = 0
    last_channel_id = 0
    
    waitToDatetime = dict()

    def __init__(self, id):
        self.id = id
        self.waitToDatetime['fb_1'] = WaitToDatetimeForm('숲필보 젠')
        self.waitToDatetime['fb_2'] = WaitToDatetimeForm('도심필보 젠')
        self.waitToDatetime['fb_m'] = WaitToDatetimeForm('모링포니아 젠')


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
            if args[0].startswith('./'):
                if args[0] == './개발자나스':
                    print(f'channel: {message.channel.name}({message.channel.id})')
                    print(f'guild: {message.guild.name}({message.guild.id})')
                    await message.channel.send('print debug.')
                elif args[0] == './필보자나스':
                    del args[0]
                    await self.command_fieldboss(message, args)
                elif args[0] == './숲필보':
                    args[0] = '숲'
                    await self.command_fieldboss(message, args)
                elif args[0] == './도심필보':
                    args[0] = '도심'
                    await self.command_fieldboss(message, args)
                elif args[0] == './모링' or args[0] == './모링포니아':
                    args[0] = '모링'
                    await self.command_fieldboss(message, args)
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
                else:
                    waitTimeKey = ''
                    if args[0] == '숲':
                        waitTimeKey = 'fb_1'
                    elif args[0] == '도심':
                        waitTimeKey = 'fb_2'
                    elif args[0] == '모링' or args[0] == '모링포니아':
                        waitTimeKey = 'fb_m'
                    waitToDatetime = self.guildDatas[message.guild.id].waitToDatetime[waitTimeKey]
                    if len(args) > 1:
                        if args[1] == '킬':
                            if waitToDatetime.channel_id == 0:
                                waitToDatetime.channel_id = message.channel.id
                            waitToDatetime.reset_time(datetime.datetime.now() + datetime.timedelta(hours=4, minutes=10))
                            await message.channel.send(f'{waitToDatetime.name} 시간 등록.')
                        elif args[1] == '취소':
                            waitToDatetime.cancel_time()
                            await message.channel.send(f'{waitToDatetime.name} 시간 등록취소.')
                    if not waitToDatetime.can_check_time():
                        await message.channel.send(f'{waitToDatetime.name} 시간 정보없음.')
                    else:
                        await message.channel.send(f'{waitToDatetime.name} 시간 {timedelta_str(waitToDatetime.get_remain_time())} 남음.')

    async def my_background_task(self):
        await self.wait_until_ready()
        counter = 0
        while not self.is_closed():
            counter += 1
            for guildKey in self.guildDatas:
                for waitTimeKey in self.guildDatas[guildKey].waitToDatetime:
                    currentWaitTime = self.guildDatas[guildKey].waitToDatetime[waitTimeKey]
                    if currentWaitTime.can_check_time():
                        checkSignal = currentWaitTime.check_time()
                        if checkSignal == 30:
                            currentWaitTime.check_30min = True
                            await client.get_channel(currentWaitTime.channel_id).send(f'{currentWaitTime.name} 30분 전!')
                        elif checkSignal == 10:
                            currentWaitTime.check_10min = True
                            await client.get_channel(currentWaitTime.channel_id).send(f'{currentWaitTime.name} 10분 전!')
            await asyncio.sleep(1)


client = ZanasClient()
client.run(token)