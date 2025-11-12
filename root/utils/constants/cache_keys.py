# Cache keys are asscreated in the format: cache-api-{user_token}-{path_key}
# where path_key is defined below for paths that need to be invalidated
# separately from others. if a request does not have a user token,
# the cache key will be: cache-api-0-{path_key} for example: meta api's cacjhe key
# will be cache-api-0-0

KEYS = {
    "/meta": 0
}