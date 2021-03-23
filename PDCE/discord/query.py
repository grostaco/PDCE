import requests
import time
import tqdm

from . import DISCORD_ENDPOINT


def discord_message_query(token, guild_id, query_filters=None, offset=0, is_channel=False):
    while True:
        res = requests.get(discord_message_query_str(guild_id, query_filters=query_filters, offset=0,
                                                     is_channel=is_channel),
                           headers={'Authorization': str(token),
                                    'accept': '*/*',
                                    'accept-encoding': 'gzip, deflate, br',
                                    'accept-language': 'en-US',
                                    'sec-fetch-dest': 'empty',
                                    'sec-fetch-mode': 'cors',
                                    'sec-fetch-site': 'same-origin',
                                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, '
                                                  'like Gecko) discord/0.0.309 Chrome/83.0.4103.122 Electron/9.3.5 '
                                                  'Safari/537.36 ',
                                    },
                           )
        if res.status_code == 429:
            retry_after = res.json()['retry_after']
            for x in tqdm.tqdm(range(int(retry_after * 10)), desc='Rate limited: Waiting:', position=0,
                               leave=True):
                time.sleep(0.1)
        elif res.status_code == 200:
            return res
        else:
            raise RuntimeError("Got unexpected status code {} with content {}".format(res.status_code, res.json()))


def discord_message_query_str(guild_id, query_filters=None, offset=0, is_channel=False):
    if query_filters is None:
        query_filters = []

    qoffset_filters = tuple(i for i, x in enumerate(query_filters) if isinstance(x, Query.Offset))
    if len(qoffset_filters) > 1:
        raise RuntimeError("Expected 1 Query.Offset, got {}".format(len(qoffset_filters)))
    elif len(qoffset_filters) == 0:
        query_filters.append(Query.Offset(offset))
    else:
        query_filters[qoffset_filters[0]].offset += offset

    qstr = ('{}/channels/{}/messages/search?{}' if is_channel else '{}/guilds/{}/messages/search?{}') \
        .format(DISCORD_ENDPOINT, guild_id, "&".join(map(str, query_filters)))
    if len(qoffset_filters) == 0:
        query_filters.pop(-1)
    return qstr


class Query:
    class Author:
        def __init__(self, author_id):
            self.author_id = author_id

        def __str__(self):
            return self.query_str

        @property
        def query_str(self):
            return 'author_id={}'.format(self.author_id)

    class Mention:
        def __init__(self, user_id):
            self.user_id = user_id

        def __str__(self):
            return self.query_str

        @property
        def query_str(self):
            return 'mentions={}'.format(self.user_id)

    class Before:
        def __init__(self, timestamp):
            self.timestamp = timestamp

        def __str__(self):
            return self.query_str

        @property
        def query_str(self):
            return 'max_id={}'.format(self.timestamp)

    class After:
        def __init__(self, timestamp):
            self.timestamp = timestamp

        def __str__(self):
            return self.query_str

        @property
        def query_str(self):
            return 'min_id={}'.format(self.timestamp)

    class Has:
        def __init__(self, *contains):
            self.contains = contains

        def __str__(self):
            return self.query_str

        @property
        def query_str(self):
            return '&'.join(['has={}'.format(x) for x in self.contains])

    class Channel:
        def __init__(self, channel_id):
            self.channel_id = channel_id

        def __str__(self):
            return self.query_str

        @property
        def query_str(self):
            return 'channel_id={}'.format(self.channel_id)

    class IncludeNSFW:
        def __init__(self, include_nsfw):
            self.include_nsfw = include_nsfw

        def __str__(self):
            return self.query_str

        @property
        def query_str(self):
            return 'include_nsfw={}'.format(self.include_nsfw)

    class Offset:
        def __init__(self, offset):
            self.offset = offset

        def __str__(self):
            return self.query_str

        @property
        def query_str(self):
            return 'offset={}'.format(self.offset)

    # not useful in query functions
    class Limit:
        def __init__(self, limit):
            self.limit = limit

        def __str__(self):
            return self.query_str

        @property
        def query_str(self):
            return 'limit={}'.format(self.limit)

    class During:
        def __init__(self, before, after):
            self.before = before
            self.after = after

        def __str__(self):
            return self.query_str

        @property
        def query_str(self):
            return 'min_id={}&max_id={}'.format(self.after, self.before)