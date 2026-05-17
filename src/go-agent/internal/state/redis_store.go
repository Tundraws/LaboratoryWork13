package state

import (
	"context"
	"fmt"

	"github.com/redis/go-redis/v9"
)

type RedisStore struct {
	client *redis.Client
	key    string
}

func NewRedisStore(addr string, name string) *RedisStore {
	return &RedisStore{
		client: redis.NewClient(&redis.Options{Addr: addr}),
		key:    fmt.Sprintf("agent:%s:processed", name),
	}
}

func (s *RedisStore) Ping(ctx context.Context) error {
	return s.client.Ping(ctx).Err()
}

func (s *RedisStore) IncrementProcessed(ctx context.Context) (int64, error) {
	return s.client.Incr(ctx, s.key).Result()
}

func (s *RedisStore) Processed(ctx context.Context) (int64, error) {
	value, err := s.client.Get(ctx, s.key).Int64()
	if err == redis.Nil {
		return 0, nil
	}
	return value, err
}

