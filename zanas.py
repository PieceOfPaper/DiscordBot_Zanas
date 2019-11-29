import discord
import asyncio
import sys
import datetime
import random
import pymysql

import myutil

token = 'token'
dbtype = 'local'

for argIdx, argVal in enumerate(sys.argv):
    if argVal == '-token':
        token = sys.argv[argIdx + 1]
    elif argVal == '-db':
        dbtype = sys.argv[argIdx + 1]
        
def db_query(query):
    if dbtype == 'local':
        conn = pymysql.connect(host='localhost', user='root', password='localhost', db='discordbot_zanas', charset='utf8')
    result = None
    if query is not None:
        cursor = conn.cursor()
        print(f'db_query : {query}')
        cursor.execute(query)
        result = cursor.fetchall()
        conn.commit()
    conn.close()
    return result

def db_auto_str(value):
    if value is None:
        return 'NULL'
    if type(value) is str:
        return f'"{value}"'
    elif type(value) is bool:
        if value:
            return 1
        else:
            return 0
    elif type(value) is datetime.datetime:
        datetime_str = value.strftime('%Y-%m-%d %H:%M:%S')
        return f'"{datetime_str}"'
    else:
        return value

def db_set_data(table, wheres, values):
    select_result = db_get_data(table, wheres)
    if len(select_result) > 0:
        where_str = None
        for key, val in wheres.items():
            if where_str is None:
                where_str = f'{key}={db_auto_str(val)}'
            else:
                where_str += f' AND {key}={db_auto_str(val)}'
        set_str = None
        for key, val in values.items():
            if set_str is None:
                set_str = f'{key}={db_auto_str(val)}'
            else:
                set_str += f',{key}={db_auto_str(val)}'
        if where_str is None or set_str is None:
            return
        db_query(f'UPDATE {table} SET {set_str} WHERE {where_str}')
    else:
        cols = None
        vals = None
        for key, val in values.items():
            if cols is None:
                cols = f'{key}'
                vals = f'{db_auto_str(val)}'
            else:
                cols += f',{key}'
                vals += f',{db_auto_str(val)}'
        for key, val in wheres.items():
            if key in values:
                continue
            if cols is None:
                cols = f'{key}'
                vals = f'{db_auto_str(val)}'
            else:
                cols += f',{key}'
                vals += f',{db_auto_str(val)}'
        if cols is None or vals is None:
            return
        db_query(f'INSERT INTO {table}({cols}) VALUES ({vals})')

def db_get_data(table, wheres):
    where_str = None
    for key, val in wheres.items():
        if where_str is None:
            where_str = f'{key}={db_auto_str(val)}'
        else:
            where_str += f' AND {key}={db_auto_str(val)}'
    return db_query(f'SELECT * FROM {table} WHERE {where_str}')



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
        results = db_get_data('wait2datetime', {'guild_id':self.guild_id, 'key_name':self.key_name})
        if len(results) == 0:
            db_set_data('wait2datetime', {'guild_id':self.guild_id, 'key_name':self.key_name}, {})
            results = db_get_data('wait2datetime', {'guild_id':self.guild_id, 'key_name':self.key_name})
        for result in results:
            if result[2] is not None:
                self.time = result[2]
            if result[3] is not None:
                self.channel_id = int(result[3])

        self.update_checked()

    #
    def set_channel_id(self, ch_id):
        self.channel_id = ch_id
        db_set_data('wait2datetime', {'guild_id':self.guild_id, 'key_name':self.key_name}, {'channel_id':self.channel_id})

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
        db_set_data('wait2datetime', {'guild_id':self.guild_id, 'key_name':self.key_name}, {'time':self.time})

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

        results = db_get_data('guild', {'id':self.id})
        if len(results) == 0:
            db_set_data('guild', {'id':self.id}, {})
            results = db_get_data('guild', {'id':self.id})
        for result in results:
            if result[1] is not None:
                self.tzinfo = datetime.timezone(datetime.timedelta(hours=int(result[1])))
            
        self.waitToDatetime['fb_1'] = WaitToDatetimeForm(self.id, 'fb_1', '숲필보 젠')
        self.waitToDatetime['fb_2'] = WaitToDatetimeForm(self.id, 'fb_2', '도심필보 젠')
        self.waitToDatetime['fb_moring'] = WaitToDatetimeForm(self.id, 'fb_moring', '모링포니아 젠')
    
    def set_timezone(self, hour):
        self.tzinfo = datetime.timezone(datetime.timedelta(hours=hour))
        db_set_data('guild', {'id':self.id}, {'timezone':hour})



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
                elif args[0] == './크로노마법':
                    del args[0]
                    await self.command_time(message, args)
                elif args[0] == './오미쿠지':
                    del args[0]
                    await self.command_random(message, args)
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
                            # await message.channel.send(f'{waitToDatetime.name} 시간 등록.')
                        elif args[1] == '취소':
                            waitToDatetime.cancel_time()
                            # await message.channel.send(f'{waitToDatetime.name} 시간 등록취소.')
                    if waitToDatetime.time is None:
                        await message.channel.send(f'{waitToDatetime.name} 시간 정보없음.')
                    else:
                        await message.channel.send(f'마지막으로 등록된 {waitToDatetime.name} 시간 {myutil.datetime_str(waitToDatetime.time.astimezone(self.guildDatas[message.guild.id].tzinfo))}')


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
            await message.channel.send('형식이 올바르지 않습니다.')


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


db_query(None) #test connect
client = ZanasClient()
client.run(token)