package state

import (
	"context"
	"sync/atomic"
)

type Store interface {
	Ping(ctx context.Context) error
	IncrementProcessed(ctx context.Context) (int64, error)
	Processed(ctx context.Context) (int64, error)
}

type MemoryStore struct {
	name  string
	count atomic.Int64
}

func NewMemoryStore(name string) *MemoryStore {
	return &MemoryStore{name: name}
}

func (s *MemoryStore) Ping(ctx context.Context) error {
	return ctx.Err()
}

func (s *MemoryStore) IncrementProcessed(ctx context.Context) (int64, error) {
	if err := ctx.Err(); err != nil {
		return 0, err
	}
	return s.count.Add(1), nil
}

func (s *MemoryStore) Processed(ctx context.Context) (int64, error) {
	if err := ctx.Err(); err != nil {
		return 0, err
	}
	return s.count.Load(), nil
}
