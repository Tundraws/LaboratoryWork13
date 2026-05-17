package config

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"time"

	"github.com/tundraws/laboratorywork13/src/go-agent/internal/domain"
)

const (
	defaultNATSURL    = "nats://localhost:4222"
	defaultRedisAddr  = "localhost:6379"
	defaultHealthAddr = ":8080"
)

type Config struct {
	Agent      domain.AgentConfig
	NATSURL    string
	RedisAddr  string
	HealthAddr string
}

func Load() (Config, error) {
	configPath := os.Getenv("AGENT_CONFIG_PATH")
	if configPath == "" {
		return Config{}, errors.New("AGENT_CONFIG_PATH is required")
	}

	data, err := os.ReadFile(configPath)
	if err != nil {
		return Config{}, fmt.Errorf("read agent config: %w", err)
	}

	var agent domain.AgentConfig
	if err := json.Unmarshal(data, &agent); err != nil {
		return Config{}, fmt.Errorf("decode agent config: %w", err)
	}
	if err := agent.Validate(); err != nil {
		return Config{}, err
	}

	return Config{
		Agent:      agent,
		NATSURL:    envOrDefault("NATS_URL", defaultNATSURL),
		RedisAddr:  envOrDefault("REDIS_ADDR", defaultRedisAddr),
		HealthAddr: envOrDefault("HEALTH_ADDR", defaultHealthAddr),
	}, nil
}

func envOrDefault(key string, fallback string) string {
	value := os.Getenv(key)
	if value == "" {
		return fallback
	}
	return value
}

func RequestTimeout() time.Duration {
	return 10 * time.Second
}
