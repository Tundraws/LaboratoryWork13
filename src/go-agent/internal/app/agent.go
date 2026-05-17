package app

import (
	"context"
	"encoding/json"
	"log/slog"
	"time"

	"github.com/nats-io/nats.go"
	"go.opentelemetry.io/otel"

	"github.com/tundraws/laboratorywork13/src/go-agent/internal/domain"
	"github.com/tundraws/laboratorywork13/src/go-agent/internal/messaging"
	"github.com/tundraws/laboratorywork13/src/go-agent/internal/rules"
	"github.com/tundraws/laboratorywork13/src/go-agent/internal/state"
)

type Agent struct {
	config    domain.AgentConfig
	processor *rules.Processor
	store     state.Store
	client    messaging.Client
	logger    *slog.Logger
}

func NewAgent(config domain.AgentConfig, processor *rules.Processor, store state.Store, client messaging.Client, logger *slog.Logger) *Agent {
	return &Agent{config: config, processor: processor, store: store, client: client, logger: logger}
}

func (a *Agent) Run(ctx context.Context) error {
	if _, err := a.client.Subscribe(a.config.TaskSubject, a.handleTask(ctx)); err != nil {
		return err
	}
	if _, err := a.client.Subscribe(a.config.AuctionSubject, a.handleBid(ctx)); err != nil {
		return err
	}
	a.logger.Info("agent subscribed", "task_subject", a.config.TaskSubject, "auction_subject", a.config.AuctionSubject)
	<-ctx.Done()
	return ctx.Err()
}

func (a *Agent) handleTask(parent context.Context) messaging.Handler {
	return func(msg *nats.Msg) {
		start := time.Now()
		ctx, span := otel.Tracer("social-mas-go-agent").Start(parent, "agent.process."+a.config.Role)
		defer span.End()

		var task domain.Task
		if err := json.Unmarshal(msg.Data, &task); err != nil {
			a.respondError(msg, domain.Task{TraceID: "unknown"}, "invalid task payload", start)
			return
		}

		a.logger.Info("task received", "task_id", task.ID, "role", a.config.Role, "trace_id", task.TraceID)
		output, err := a.processor.Process(task)
		if err != nil {
			a.respondError(msg, task, err.Error(), start)
			return
		}
		count, err := a.store.IncrementProcessed(ctx)
		if err != nil {
			a.logger.Warn("state increment failed", "error", err)
		}
		output["processed_total"] = count

		result := domain.Result{
			TaskID:   task.ID,
			Agent:    a.config.Name,
			Role:     a.config.Role,
			TraceID:  task.TraceID,
			Success:  true,
			Output:   output,
			Duration: time.Since(start).String(),
		}
		a.respond(msg, result)
		a.logger.Info("task completed", "task_id", task.ID, "duration", result.Duration, "processed_total", count)
	}
}

func (a *Agent) handleBid(parent context.Context) messaging.Handler {
	return func(msg *nats.Msg) {
		ctx, cancel := context.WithTimeout(parent, 2*time.Second)
		defer cancel()

		var request domain.BidRequest
		if err := json.Unmarshal(msg.Data, &request); err != nil {
			a.respond(msg, domain.BidResponse{Agent: a.config.Name, Role: a.config.Role, Available: false, Cost: 999, Reason: "invalid bid request"})
			return
		}
		count, err := a.store.Processed(ctx)
		if err != nil {
			count = 0
		}
		a.respond(msg, a.processor.Bid(request, count))
	}
}

func (a *Agent) respondError(msg *nats.Msg, task domain.Task, message string, start time.Time) {
	a.respond(msg, domain.Result{
		TaskID:   task.ID,
		Agent:    a.config.Name,
		Role:     a.config.Role,
		TraceID:  task.TraceID,
		Success:  false,
		Error:    message,
		Output:   map[string]any{},
		Duration: time.Since(start).String(),
	})
}

func (a *Agent) respond(msg *nats.Msg, payload any) {
	encoded, err := json.Marshal(payload)
	if err != nil {
		a.logger.Error("encode response failed", "error", err)
		return
	}
	if err := a.client.Respond(msg, encoded); err != nil {
		a.logger.Error("respond failed", "error", err)
	}
}

