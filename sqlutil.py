import datetime
import pymysql

dbtype = 'local'

table_setting = dict()

table_setting['guild'] = []
table_setting['guild'].append('id bigint(20)')
table_setting['guild'].append('timezone int(11)')

table_setting['wait2datetime'] = []
table_setting['wait2datetime'].append('guild_id bigint(20)')
table_setting['wait2datetime'].append('key_name varchar(45)')
table_setting['wait2datetime'].append('time datetime')
table_setting['wait2datetime'].append('channel_id bigint(20)')

table_setting['memo'] = []
table_setting['memo'].append('user_id bigint(20)')
table_setting['memo'].append('key_name varchar(45)')
table_setting['memo'].append('content text')

#
def db_query(query):
    if dbtype == 'local':
        conn = pymysql.connect(host='localhost', user='root', password='localhost', db='discordbot_zanas')
    elif dbtype == 'live':
        conn = pymysql.connect(host='HOST', user='USER', password='PWD', db='DB')
    result = None
    print(f'db_query : {query}')
    if query is not None:
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        conn.commit()
    conn.close()
    return result

#
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

#
def db_table_setting():
    print('db table setting')
    for tablename, args in table_setting.items():
        argstr = None
        print(len(args))
        for arg in args:
            if argstr is None:
                argstr = arg
            else:
                argstr += ','+arg
        db_query(f'CREATE TABLE IF NOT EXISTS {tablename} ({argstr})')
        for arg in args:
            has_col = db_query(f'SHOW COLUMNS FROM {tablename} LIKE "{arg.strip().split(" ")[0]}"')
            if has_col is not None and len(has_col) > 0:
                db_query(f'ALTER TABLE {tablename} MODIFY COLUMN {arg}')
            else:
                db_query(f'ALTER TABLE {tablename} ADD COLUMN {arg}')

#
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

#
def db_get_data(table, wheres):
    where_str = None
    for key, val in wheres.items():
        if where_str is None:
            where_str = f'{key}={db_auto_str(val)}'
        else:
            where_str += f' AND {key}={db_auto_str(val)}'
    return db_query(f'SELECT * FROM {table} WHERE {where_str}')
