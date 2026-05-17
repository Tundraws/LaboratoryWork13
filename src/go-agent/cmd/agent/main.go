package main

import (
	"context"
	"errors"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"github.com/tundraws/laboratorywork13/src/go-agent/internal/app"
	"github.com/tundraws/laboratorywork13/src/go-agent/internal/config"
	"github.com/tundraws/laboratorywork13/src/go-agent/internal/health"
	"github.com/tundraws/laboratorywork13/src/go-agent/internal/logging"
	"github.com/tundraws/laboratorywork13/src/go-agent/internal/messaging"
	"github.com/tundraws/laboratorywork13/src/go-agent/internal/rules"
	"github.com/tundraws/laboratorywork13/src/go-agent/internal/state"
	"github.com/tundraws/laboratorywork13/src/go-agent/internal/telemetry"
)

func main() {
	if err := run(); err != nil {
		slog.Error("agent stopped with error", "error", err)
		os.Exit(1)
	}
}

func run() error {
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	cfg, err := config.Load()
	if err != nil {
		return err
	}
	logger := logging.New(cfg.Agent.Name)

	shutdownTelemetry, err := telemetry.Configure(ctx, cfg.Agent.Name)
	if err != nil {
		logger.Warn("telemetry disabled", "error", err)
	}
	defer func() {
		if shutdownTelemetry != nil {
			_ = shutdownTelemetry(context.Background())
		}
	}()

	var store state.Store = state.NewRedisStore(cfg.RedisAddr, cfg.Agent.Name)
	if err := store.Ping(ctx); err != nil {
		logger.Warn("redis unavailable, falling back to in-memory state", "error", err)
		store = state.NewMemoryStore(cfg.Agent.Name)
	}

	processor := rules.NewProcessor(cfg.Agent)
	client, err := messaging.Connect(cfg.NATSURL, logger)
	if err != nil {
		return err
	}
	defer client.Close()

	agent := app.NewAgent(cfg.Agent, processor, store, client, logger)
	healthServer := health.NewServer(cfg.HealthAddr, store, logger)

	errCh := make(chan error, 2)
	go func() { errCh <- healthServer.Start(ctx) }()
	go func() { errCh <- agent.Run(ctx) }()

	select {
	case <-ctx.Done():
		logger.Info("shutdown signal received")
		return nil
	case err := <-errCh:
		if errors.Is(err, context.Canceled) {
			return nil
		}
		return err
	}
}
