import datetime

def datetime_str(t):
    return f'{t.year}년 {t.month}월 {t.day}일 {t.hour}시 {t.minute}분 {t.second}초 (UTC+{t.utcoffset()})'

def timedelta_str(t):
    hours, remainder = divmod(t.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f'{hours}시간 {minutes}분 {seconds}초'