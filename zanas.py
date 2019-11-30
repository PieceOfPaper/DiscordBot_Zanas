import discord
import asyncio
import sys
import datetime
import random
import pymysql

import myutil
import sqlutil

token = 'token'

for argIdx, argVal in enumerate(sys.argv):
    if argVal == '-token':
        token = sys.argv[argIdx + 1]
    elif argVal == '-db':
        sqlutil.dbtype = sys.argv[argIdx + 1]




class WaitToDatetimeForm:
    guild_id = 0
    key_name = ''
    name = ''
    channel_id = 0
    time = None
    checked_30min = True
    checked_10min = True

    #
    def __init__(self, guild_id, key_name, name):
        self.guild_id = guild_id
        self.key_name = key_name
        self.name = name
        results = sqlutil.db_get_data('wait2datetime', {'guild_id':self.guild_id, 'key_name':self.key_name})
        if len(results) == 0:
            sqlutil.db_set_data('wait2datetime', {'guild_id':self.guild_id, 'key_name':self.key_name}, {})
            results = sqlutil.db_get_data('wait2datetime', {'guild_id':self.guild_id, 'key_name':self.key_name})
        for result in results:
            if result[2] is not None:
                self.time = result[2]
            if result[3] is not None:
                self.channel_id = int(result[3])

        self.update_checked()

    #
    def set_channel_id(self, ch_id):
        self.channel_id = ch_id
        sqlutil.db_set_data('wait2datetime', {'guild_id':self.guild_id, 'key_name':self.key_name}, {'channel_id':self.channel_id})

    #
    def get_remain_time(self):
        if self.time is None:
            return None
        return self.time - datetime.datetime.utcnow()

    #
    def can_check_time(self):
        return (not self.checked_30min) or (not self.checked_10min)

    #
    def update_checked(self):
        remain_time = self.get_remain_time()
        if remain_time is None:
            minutes = 0
        else:
            minutes, seconds = divmod(self.get_remain_time().seconds, 60)
        if minutes >= 30:
            self.checked_30min = False
        else:
            self.checked_30min = True
        if minutes >= 10:
            self.checked_10min = False
        else:
            self.checked_10min = True

    #
    def set_time(self, time):
        self.time = time
        self.update_checked()
        sqlutil.db_set_data('wait2datetime', {'guild_id':self.guild_id, 'key_name':self.key_name}, {'time':self.time})

    #
    def cancel_time(self):
        self.set_time(None)
        
    #
    def check_time(self):
        minutes, seconds = divmod(self.get_remain_time().seconds, 60)
        if (not self.checked_30min) and minutes < 30:
            return 30
        elif (not self.checked_10min) and minutes < 10:
            return 10
        else:
            return -1

class GuildData:
    id = 0
    tzinfo = None
    
    waitToDatetime = dict()

    def __init__(self, id):
        self.id = id
        self.tzinfo = datetime.timezone(datetime.timedelta(hours=0))

        results = sqlutil.db_get_data('guild', {'id':self.id})
        if len(results) == 0:
            sqlutil.db_set_data('guild', {'id':self.id}, {})
            results = sqlutil.db_get_data('guild', {'id':self.id})
        for result in results:
            if result[1] is not None:
                self.tzinfo = datetime.timezone(datetime.timedelta(hours=int(result[1])))
            
        self.waitToDatetime['fb_1'] = WaitToDatetimeForm(self.id, 'fb_1', '숲필보 젠')
        self.waitToDatetime['fb_2'] = WaitToDatetimeForm(self.id, 'fb_2', '도심필보 젠')
        self.waitToDatetime['fb_moring'] = WaitToDatetimeForm(self.id, 'fb_moring', '모링포니아 젠')
    
    def set_timezone(self, hour):
        self.tzinfo = datetime.timezone(datetime.timedelta(hours=hour))
        sqlutil.db_set_data('guild', {'id':self.id}, {'timezone':hour})



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
                elif args[0] == './필보':
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
                elif args[0] == './크로노마법':
                    del args[0]
                    await self.command_time(message, args)
                elif args[0] == './오미쿠지':
                    del args[0]
                    await self.command_random(message, args)
                elif args[0] == './메모':
                    del args[0]
                    await self.command_memo(message, args)
                elif args[0] == './메모쓰기':
                    args[0] = '쓰기'
                    await self.command_memo(message, args)
                elif args[0] == './강화':
                    del args[0]
                    await self.command_reinforce_simulate(message, args)
                elif args[0] == './모루강화':
                    args[0] = '모루'
                    await self.command_reinforce_simulate(message, args)
                elif args[0] == './다모강화':
                    args[0] = '다이아모루'
                    await self.command_reinforce_simulate(message, args)
                elif args[0] == './황모강화':
                    args[0] = '황금모루'
                    await self.command_reinforce_simulate(message, args)
                elif args[0] == './루모강화':
                    args[0] = '루비모루'
                    await self.command_reinforce_simulate(message, args)
                elif args[0] == './자나스':
                    await message.channel.send('계시자.. 이 목소리가 들린다면 나를 찾아와줘..')

    async def command_fieldboss(self, message, args):
            if len(args) > 0:
                if args[0] == '고정':
                    self.guildDatas[message.guild.id].waitToDatetime['fb_1'].set_channel_id(message.channel.id)
                    self.guildDatas[message.guild.id].waitToDatetime['fb_2'].set_channel_id(message.channel.id)
                    self.guildDatas[message.guild.id].waitToDatetime['fb_moring'].set_channel_id(message.channel.id)
                    await message.channel.send(f'필보 알림 채널 설정 <#{message.channel.id}>')
                else:
                    waitTimeKey = ''
                    if args[0] == '숲':
                        waitTimeKey = 'fb_1'
                    elif args[0] == '도심':
                        waitTimeKey = 'fb_2'
                    elif args[0] == '모링' or args[0] == '모링포니아':
                        waitTimeKey = 'fb_moring'
                    waitToDatetime = self.guildDatas[message.guild.id].waitToDatetime[waitTimeKey]
                    if len(args) > 1:
                        if args[1] == '킬':
                            if waitToDatetime.channel_id == 0:
                                waitToDatetime.set_channel_id(message.channel.id)
                            waitToDatetime.set_time(datetime.datetime.utcnow() + datetime.timedelta(hours=4, minutes=10))
                        elif args[1] == '취소':
                            waitToDatetime.cancel_time()
                    if waitToDatetime.time is None:
                        await message.channel.send(f'{waitToDatetime.name} 시간 정보없음.')
                    else:
                        await message.channel.send(f'마지막으로 등록된 {waitToDatetime.name} 시간 {myutil.datetime_str(waitToDatetime.time.astimezone(self.guildDatas[message.guild.id].tzinfo))}')
            else:
                help_message = '**- 필보 시간 보기**\n'
                help_message += '```'
                help_message += './숲필보\n'
                help_message += './도심필보\n'
                help_message += './모링\n'
                help_message += '```'
                help_message += '**- 필보 시간 기록**\n'
                help_message += '```'
                help_message += './숲필보 킬\n'
                help_message += './도심필보 킬\n'
                help_message += './모링 킬\n'
                help_message += '```'
                help_message += '**- 필보 시간 취소**\n'
                help_message += '```'
                help_message += './숲필보 취소\n'
                help_message += './도심필보 취소\n'
                help_message += './모링 취소\n'
                help_message += '```'
                await message.channel.send(help_message)


    async def command_time(self, message, args):
        if len(args) > 0:
            if args[0] == '초기화':
                if len(args) > 1:
                    self.guildDatas[message.guild.id].set_timezone(int(args[1]))
                    await message.channel.send(f'현재시간 {myutil.datetime_str(datetime.datetime.now(self.guildDatas[message.guild.id].tzinfo))}')
                else:
                    await message.channel.send('기준이 될 시간이 없습니다. ex)"./크로노마법 초기화 9"')
        else:
            await message.channel.send(f'현재시간 {myutil.datetime_str(datetime.datetime.now(self.guildDatas[message.guild.id].tzinfo))}')


    async def command_random(self, message, args):
        if len(args) > 1:
            player = []
            for arg in args:
                if arg != args[0]:
                    player.append(arg)

            rand_len = int(args[0])
            player_len = len(player)
            result = ''
            for idx in range(player_len):
                if len(player) == 0:
                    break
                if idx > 0:
                    result += '\n'
                randidx = random.randrange(0,len(player))
                if idx < rand_len:
                    result += f'{idx+1}. :white_flower: **{player[randidx]}** :white_flower:'
                elif idx >= player_len - rand_len:
                    result += f'{idx+1}. :skull: *{player[randidx]}* :skull:'
                else:
                    result += f'{idx+1}. ~~{player[randidx]}~~'
                del player[randidx]
            await message.channel.send(result)
        else:
            help_message = '**- 사용법**\n'
            help_message += '```./오미쿠지 [당첨자수] [대상1] [대상2] [대상3] ... [대상n]```\n'
            await message.channel.send(help_message)

    async def command_memo(self, message, args):
        if len(args) > 0:
            if args[0] == '쓰기':
                key_name = None
                content = None
                lines = message.content.split('\n')
                if len(lines) > 1:
                    content = message.content.replace(lines[0]+'\n', '')
                    if len(args) > 1:
                        key_name = args[1].split('\n')[0]
                if key_name is None:
                    await message.channel.send('형식이 올바르지 않습니다.')
                else:
                    sqlutil.db_set_data('memo', {'user_id':message.author.id, 'key_name':key_name}, {'content':content})
                    await message.channel.send(f'**[{key_name}]**메모 저장 완료.')
            # elif args[0] == '삭제':
            #     key_name = None
            #     if len(args) > 1:
            #         key_name = args[1].replace('\n','')
            #     if key_name is None:
            #         await message.channel.send('형식이 올바르지 않습니다.')
            #     else:
            #         print('query')
            #         print('succes chat')
            else:
                key_name = args[0].replace('\n','')
                results = sqlutil.db_get_data('memo', {'user_id':message.author.id, 'key_name':key_name})
                if results is not None and len(results) > 0:
                    await message.channel.send(f'<@{message.author.id}>님의 **[{key_name}]**메모.\n```{results[0][2]}```')
                else:
                    await message.channel.send(f'[{key_name}]메모에 내용이 없습니다.')
        else:
            help_message = '**- 메모 보기**\n'
            help_message += '```./메모 [메모이름]```\n'
            help_message += '**- 메모 쓰기**\n'
            help_message += '```./메모쓰기 [메모이름]\n[메모내용]```\n'
            await message.channel.send(help_message)


    async def command_reinforce_simulate(self, message, args):
        if len(args) > 2:
            if args[0] == '모루' or args[0] == '다이아모루':
                safe_reinforce = 3
                if args[1] == '무기':
                    safe_reinforce = 5
                potential = int(args[2])
                reinforce = 0
                count = 0
                log = ''
                while potential > 0:
                    if reinforce < safe_reinforce:
                        reinforce += 1
                    else:
                        if random.randrange(0,10000) < 5100:
                            reinforce += 1
                        else:
                            if args[0] != '다이아모루':
                                reinforce -= 1
                            potential -= 1
                    count += 1
                    log += f'+{reinforce} '
                
                result_message = f'**:crossed_swords: +{reinforce}**\n'
                result_message += '```'
                result_message += f'강화횟수: {count}\n'
                result_message += log
                result_message += '```'
                await message.channel.send(result_message)
            elif args[0] == '황금모루' or args[0] == '루비모루':
                safe_reinforce = 3
                if args[1] == '무기':
                    safe_reinforce = 5
                count_max = 1
                if len(args) > 3:
                    count_max = int(args[3])
                reinforce = int(args[2].replace('+',''))
                count = 0
                log = ''
                while count < count_max:
                    if reinforce < safe_reinforce:
                        reinforce += 1
                    else:
                        if random.randrange(0,10000) < 5100:
                            reinforce += 1
                        else:
                            if args[0] == '황금모루' and reinforce > 10:
                                reinforce = 10
                            elif args[0] == '루비모루' and reinforce > 15:
                                reinforce = 15
                            else:
                                reinforce -= 1
                    count += 1
                    log += f'+{reinforce} '
                
                result_message = f'**:crossed_swords: +{reinforce}**\n'
                result_message += '```'
                result_message += f'강화횟수: {count}\n'
                result_message += log
                result_message += '```'
                await message.channel.send(result_message)
        else:
            help_message = '**- 사용법**\n'
            # help_message += '```./오미쿠지 [당첨자수] [대상1] [대상2] [대상3] ... [대상n]```\n'
            await message.channel.send(help_message)


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
                            currentWaitTime.checked_30min = True
                            await client.get_channel(currentWaitTime.channel_id).send(f'{currentWaitTime.name} 30분 전!')
                        elif checkSignal == 10:
                            currentWaitTime.checked_10min = True
                            await client.get_channel(currentWaitTime.channel_id).send(f'{currentWaitTime.name} 10분 전!')
            await asyncio.sleep(1)


sqlutil.db_table_setting()
client = ZanasClient()
client.run(token)