package domain

import (
	"errors"
	"strings"
	"time"
)

type AgentConfig struct {
	Name           string         `json:"name"`
	Role           string         `json:"role"`
	TaskSubject    string         `json:"task_subject"`
	AuctionSubject string         `json:"auction_subject"`
	BaseCost       int            `json:"base_cost"`
	Keywords       []string       `json:"keywords"`
	Rules          map[string]int `json:"rules"`
}

func (c AgentConfig) Validate() error {
	if strings.TrimSpace(c.Name) == "" {
		return errors.New("agent name is required")
	}
	if strings.TrimSpace(c.Role) == "" {
		return errors.New("agent role is required")
	}
	if strings.TrimSpace(c.TaskSubject) == "" {
		return errors.New("task subject is required")
	}
	if strings.TrimSpace(c.AuctionSubject) == "" {
		return errors.New("auction subject is required")
	}
	if c.BaseCost < 0 {
		return errors.New("base cost must not be negative")
	}
	return nil
}

type Task struct {
	ID        string         `json:"id"`
	Type      string         `json:"type"`
	TraceID   string         `json:"trace_id"`
	Payload   map[string]any `json:"payload"`
	CreatedAt time.Time      `json:"created_at"`
}

type Result struct {
	TaskID   string         `json:"task_id"`
	Agent    string         `json:"agent"`
	Role     string         `json:"role"`
	TraceID  string         `json:"trace_id"`
	Success  bool           `json:"success"`
	Output   map[string]any `json:"output"`
	Error    string         `json:"error,omitempty"`
	Duration string         `json:"duration"`
}

type BidRequest struct {
	TaskType string         `json:"task_type"`
	Payload  map[string]any `json:"payload"`
}

type BidResponse struct {
	Agent     string `json:"agent"`
	Role      string `json:"role"`
	Cost      int    `json:"cost"`
	Available bool   `json:"available"`
	Reason    string `json:"reason"`
}
