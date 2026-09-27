"""Atomic Redis Lua scripts for concurrency-safe rate limiting."""

# Token Bucket Lua Script
# KEYS[1]: rate limit key
# ARGV[1]: capacity (float/int)
# ARGV[2]: refill_rate_per_sec (float)
# ARGV[3]: cost (int)
# ARGV[4]: current_time (float seconds)
# ARGV[5]: ttl_seconds (int)
TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local cost = tonumber(ARGV[3])
local now = tonumber(ARGV[4])
local ttl = tonumber(ARGV[5])

local data = redis.call('HMGET', key, 'tokens', 'last_updated')
local tokens = tonumber(data[1])
local last_updated = tonumber(data[2])

if tokens == nil then
    tokens = capacity
    last_updated = now
else
    local elapsed = math.max(0, now - last_updated)
    tokens = math.min(capacity, tokens + (elapsed * refill_rate))
    last_updated = now
end

local allowed = 0
local remaining = math.floor(tokens)
local retry_after = 0

if tokens >= cost then
    tokens = tokens - cost
    allowed = 1
    remaining = math.floor(tokens)
else
    local deficit = cost - tokens
    retry_after = deficit / refill_rate
end

redis.call('HMSET', key, 'tokens', tokens, 'last_updated', last_updated)
redis.call('EXPIRE', key, ttl)

local reset_after = (capacity - tokens) / refill_rate
local reset_epoch = now + reset_after

return { allowed, remaining, tostring(retry_after), tostring(reset_epoch) }
"""

# Sliding Window (Sorted Set) Lua Script
# KEYS[1]: rate limit key
# ARGV[1]: capacity (int)
# ARGV[2]: window_seconds (int)
# ARGV[3]: cost (int)
# ARGV[4]: current_time (float seconds)
# ARGV[5]: request_id (unique string)
SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local cost = tonumber(ARGV[3])
local now = tonumber(ARGV[4])
local req_id = ARGV[5]

local clear_before = now - window
redis.call('ZREMRANGEBYSCORE', key, 0, clear_before)

local current_requests = redis.call('ZCARD', key)
local allowed = 0
local remaining = 0
local retry_after = 0
local reset_epoch = now + window

if (current_requests + cost) <= capacity then
    for i = 1, cost do
        redis.call('ZADD', key, now, req_id .. ':' .. i)
    end
    allowed = 1
    remaining = capacity - (current_requests + cost)
    redis.call('EXPIRE', key, window * 2)
else
    allowed = 0
    remaining = 0
    -- Find the oldest timestamp in the current window to compute retry_after
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    if #oldest >= 2 then
        local oldest_ts = tonumber(oldest[2])
        retry_after = math.max(0, (oldest_ts + window) - now)
        reset_epoch = oldest_ts + window
    else
        retry_after = window
        reset_epoch = now + window
    end
end

return { allowed, remaining, tostring(retry_after), tostring(reset_epoch) }
"""
