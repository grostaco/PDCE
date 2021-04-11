from discord import DiscordCustomContext, Query
import json

conf = json.load(open('.env', encoding='utf8'))

dcc = DiscordCustomContext(conf['token'])
r = dcc.query_time_split(conf['guild_id'],
                         query_filters=Query.Has('image') &
                                       Query.Before('528980587315200000') &
                                       Query.After('397433792102400000')
                         )
