import requests
import time
import tqdm
from urllib.parse import urljoin
from .util import tqdm_ratelimit_sleep

DISCORD_ENDPOINT = "https://discord.com/api/v8/"


def discord_request(path, headers=None, data=None, sleep_callback=time.sleep):
    while True:
        r = requests.get(urljoin(DISCORD_ENDPOINT, path), headers=headers, data=data)
        if r.status_code == 429:
            sleep_callback(r.json()['retry_after'])
            continue
        elif r.status_code == 200:
            return r
        raise ValueError("Unexpected response status code {}".format(r.status_code))


def discord_message_query(token, guild_id, query_filters=None, offset=0, is_channel=False):
    r = discord_request(
        discord_message_query_str(guild_id, query_filters=query_filters, offset=0, is_channel=is_channel),
        headers={'Authorization': str(token),
                 'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                'discord/0.0.309 Chrome/83.0.4103.122 Electron/9.3.5 Safari/537.36'
                 },
        sleep_callback=tqdm_ratelimit_sleep)
    return r


def discord_message_query_str(guild_id, query_filters=None, offset=0, is_channel=False):
    if query_filters is None:
        query_filters = []

    query_filters = Query.QueryCollection(query_filters)

    qoffset_filters = tuple(i for i, x in enumerate(query_filters) if isinstance(x, Query.Offset))
    if len(qoffset_filters) > 1:
        raise RuntimeError("Expected 1 Query.Offset, got {}".format(len(qoffset_filters)))
    elif len(qoffset_filters) == 0:
        query_filters &= Query.Offset(offset)
    else:
        query_filters[qoffset_filters[0]].offset += offset

    qstr = ('channels/{}/messages/search?{}' if is_channel else 'guilds/{}/messages/search?{}') \
        .format(guild_id, "&".join(map(str, query_filters)))
    if len(qoffset_filters) == 0:
        query_filters.pop(-1)
    return qstr


# TODO: implement inverted queries
class Query:
    # Template query for inheritance, DO NOT use as a filter.
    class Template:
        inverted = False

        def __invert__(self):
            self.inverted = not self.inverted
            return self

        def __str__(self):
            return self.query_str

        def __and__(self, other):
            return Query.QueryCollection((self, other))

        @property
        def query_str(self):
            return None

    class QueryCollection:
        def __init__(self, queries):
            if isinstance(queries, Query.Template):
                self.queries = [queries]
            elif not isinstance(queries, type(self)):
                self.queries = list(queries)
            else:
                self.queries = queries.queries

        def __and__(self, other):
            if not isinstance(other, type(self)):
                self.queries.append(other)
            else:
                self.queries += other.queries

            return Query.QueryCollection(self.queries)

        def pop(self, index):
            tmp = self.queries[index]
            del self.queries[index]
            return tmp

        def __getitem__(self, item):
            return self.queries[item]

        def __iter__(self):
            return iter(self.queries)

        def compile(self, token=None):
            if token is None:
                assert not any(x.inverted for x in self.queries), "Inverted queries cannot be completed without token"
                return self

    class Author(Template):
        def __init__(self, author_id):
            self.author_id = author_id

        @property
        def query_str(self):
            return 'author_id={}'.format(self.author_id)

    class Mention(Template):
        def __init__(self, user_id):
            self.user_id = user_id

        @property
        def query_str(self):
            return 'mentions={}'.format(self.user_id)

    class Before(Template):
        def __init__(self, timestamp):
            self.timestamp = timestamp

        @property
        def query_str(self):
            return 'max_id={}'.format(self.timestamp)

    class After(Template):
        def __init__(self, timestamp):
            self.timestamp = timestamp

        @property
        def query_str(self):
            return 'min_id={}'.format(self.timestamp)

    class Has(Template):
        def __init__(self, *contains):
            self.contains = contains

        @property
        def query_str(self):
            return '&'.join(['has={}'.format(x) for x in self.contains])

    class Channel(Template):
        def __init__(self, channel_id):
            self.channel_id = channel_id

        @property
        def query_str(self):
            return 'channel_id={}'.format(self.channel_id)

    class IncludeNSFW(Template):
        def __init__(self, include_nsfw):
            self.include_nsfw = include_nsfw

        @property
        def query_str(self):
            return 'include_nsfw={}'.format(self.include_nsfw)

    class Offset(Template):
        def __init__(self, offset):
            self.offset = offset

        @property
        def query_str(self):
            return 'offset={}'.format(self.offset)

    # not useful in query functions
    class Limit(Template):
        def __init__(self, limit):
            self.limit = limit

        @property
        def query_str(self):
            return 'limit={}'.format(self.limit)

    class During(Template):
        def __init__(self, before, after):
            self.before = before
            self.after = after

        @property
        def query_str(self):
            return 'min_id={}&max_id={}'.format(self.after, self.before)