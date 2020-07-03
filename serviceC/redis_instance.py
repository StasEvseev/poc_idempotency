import redis
from redlock import RedLockFactory

r = redis.Redis()
redlock_factory = RedLockFactory(connection_details=[r])
