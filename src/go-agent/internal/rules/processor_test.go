package rules

import (
	"testing"

	"github.com/tundraws/laboratorywork13/src/go-agent/internal/domain"
)

func TestProcessorCollectPosts(t *testing.T) {
	processor := NewProcessor(domain.AgentConfig{Name: "collector", Role: "collector"})
	output, err := processor.Process(domain.Task{Payload: map[string]any{"query": "новый сервис", "limit": float64(3)}})
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
	if output["count"] != 3 {
		t.Fatalf("expected 3 posts, got %v", output["count"])
	}
}

func TestProcessorCollectPostsValidation(t *testing.T) {
	processor := NewProcessor(domain.AgentConfig{Name: "collector", Role: "collector"})
	_, err := processor.Process(domain.Task{Payload: map[string]any{"query": "", "limit": float64(3)}})
	if err == nil {
		t.Fatal("expected validation error")
	}
}

func TestProcessorAnalyzeSentiment(t *testing.T) {
	processor := NewProcessor(domain.AgentConfig{
		Name:  "sentiment",
		Role:  "sentiment",
		Rules: map[string]int{"хороший": 2, "ошибка": -3},
	})
	output, err := processor.Process(domain.Task{Payload: map[string]any{
		"posts": []any{
			map[string]any{"id": "1", "text": "хороший запуск"},
			map[string]any{"id": "2", "text": "ошибка сервиса"},
		},
	}})
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
	items, ok := output["items"].([]map[string]any)
	if !ok {
		t.Fatalf("expected sentiment items, got %#v", output["items"])
	}
	if len(items) != 2 {
		t.Fatalf("expected 2 items, got %d", len(items))
	}
}

func TestProcessorBidUsesLoadAndRelevance(t *testing.T) {
	processor := NewProcessor(domain.AgentConfig{
		Name:     "reports",
		Role:     "reports",
		BaseCost: 5,
		Keywords: []string{"отчёт"},
	})
	bid := processor.Bid(domain.BidRequest{Payload: map[string]any{"text": "нужен отчёт"}}, 7)
	if !bid.Available {
		t.Fatal("expected available bid")
	}
	if bid.Cost != 5 {
		t.Fatalf("expected cost 5, got %d", bid.Cost)
	}
}
