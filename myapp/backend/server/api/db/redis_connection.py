import os
import redis
import uuid
import json

REDIS_HOST = os.getenv("REDIS_HOST", "redis-cache")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def store_id_list(id_list, expiry_seconds=3600):
    """Store a list of IDs in Redis with a unique token."""
    token = str(uuid.uuid4())
    redis_client.setex(
        f"filter_token:{token}", 
        expiry_seconds,
        json.dumps(id_list)
    )
    return token

def get_ids_from_token(token):
    """Retrieve a list of IDs from Redis using a token."""
    id_list_json = redis_client.get(f"filter_token:{token}")
    if not id_list_json:
        return None
    return json.loads(id_list_json)

