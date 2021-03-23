class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def timestamp_to_snowflake(ts) :
    return ts - 1420070400000 << 22


def timestamp_from_snowflake(snowflake):
    return (snowflake >> 22) + 1420070400000
