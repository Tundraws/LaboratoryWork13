package messaging

import (
	"context"
	"log/slog"
	"time"

	"github.com/nats-io/nats.go"
)

type Handler func(msg *nats.Msg)

type Client interface {
	Subscribe(subject string, handler Handler) (*nats.Subscription, error)
	Respond(msg *nats.Msg, payload []byte) error
	Close()
}

type NATSClient struct {
	conn   *nats.Conn
	logger *slog.Logger
}

func Connect(url string, logger *slog.Logger) (*NATSClient, error) {
	conn, err := nats.Connect(
		url,
		nats.Name("social-mas-go-agent"),
		nats.Timeout(5*time.Second),
		nats.ReconnectWait(time.Second),
		nats.MaxReconnects(10),
	)
	if err != nil {
		return nil, err
	}
	return &NATSClient{conn: conn, logger: logger}, nil
}

func (c *NATSClient) Subscribe(subject string, handler Handler) (*nats.Subscription, error) {
	return c.conn.QueueSubscribe(subject, "social-mas-workers", func(msg *nats.Msg) {
		handler(msg)
	})
}

func (c *NATSClient) Respond(msg *nats.Msg, payload []byte) error {
	return msg.Respond(payload)
}

func (c *NATSClient) Close() {
	c.conn.Drain()
	c.conn.Close()
}

func WaitForShutdown(ctx context.Context) {
	<-ctx.Done()
}
