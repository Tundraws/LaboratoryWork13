package rules

import (
	"errors"
	"fmt"
	"sort"
	"strings"

	"github.com/tundraws/laboratorywork13/src/go-agent/internal/domain"
)

type Processor struct {
	config domain.AgentConfig
}

func NewProcessor(config domain.AgentConfig) *Processor {
	return &Processor{config: config}
}

func (p *Processor) Process(task domain.Task) (map[string]any, error) {
	switch p.config.Role {
	case "collector":
		return p.collectPosts(task)
	case "sentiment":
		return p.analyzeSentiment(task)
	case "trends":
		return p.detectTrends(task)
	case "reports":
		return p.generateReport(task)
	default:
		return nil, fmt.Errorf("unsupported role %q", p.config.Role)
	}
}

func (p *Processor) Bid(req domain.BidRequest, processedCount int64) domain.BidResponse {
	relevance := p.keywordRelevance(req.Payload)
	cost := p.config.BaseCost + int(processedCount%5) - relevance
	if cost < 1 {
		cost = 1
	}
	return domain.BidResponse{
		Agent:     p.config.Name,
		Role:      p.config.Role,
		Cost:      cost,
		Available: true,
		Reason:    fmt.Sprintf("base=%d relevance=%d load=%d", p.config.BaseCost, relevance, processedCount%5),
	}
}

func (p *Processor) collectPosts(task domain.Task) (map[string]any, error) {
	query := stringValue(task.Payload, "query")
	if strings.TrimSpace(query) == "" {
		return nil, errors.New("query is required")
	}
	limit := intValue(task.Payload, "limit", 5)
	if limit < 1 || limit > 50 {
		return nil, errors.New("limit must be between 1 and 50")
	}

	posts := make([]map[string]any, 0, limit)
	templates := []string{
		"%s получил много обсуждений после обновления сервиса",
		"Пользователи спорят о качестве %s и скорости поддержки",
		"Эксперты считают, что %s становится заметным трендом недели",
		"Негативные отзывы о %s связаны с задержками и ошибками",
		"Положительная реакция на %s растёт после публикации отчёта",
	}
	for i := 0; i < limit; i++ {
		posts = append(posts, map[string]any{
			"id":      fmt.Sprintf("post-%03d", i+1),
			"network": []string{"telegram", "vk", "x", "reddit"}[i%4],
			"text":    fmt.Sprintf(templates[i%len(templates)], query),
			"likes":   20 + i*7,
			"shares":  5 + i*3,
		})
	}
	return map[string]any{"query": query, "posts": posts, "count": len(posts)}, nil
}

func (p *Processor) analyzeSentiment(task domain.Task) (map[string]any, error) {
	posts, err := postsFromPayload(task.Payload)
	if err != nil {
		return nil, err
	}
	results := make([]map[string]any, 0, len(posts))
	total := 0
	for _, post := range posts {
		text := strings.ToLower(stringValue(post, "text"))
		score := p.scoreText(text)
		total += score
		results = append(results, map[string]any{
			"id":        stringValue(post, "id"),
			"text":      stringValue(post, "text"),
			"sentiment": label(score),
			"score":     score,
		})
	}
	average := 0.0
	if len(results) > 0 {
		average = float64(total) / float64(len(results))
	}
	return map[string]any{"items": results, "average_score": average, "summary": label(int(average))}, nil
}

func (p *Processor) detectTrends(task domain.Task) (map[string]any, error) {
	items, ok := task.Payload["items"].([]any)
	if !ok || len(items) == 0 {
		return nil, errors.New("sentiment items are required")
	}
	frequencies := map[string]int{}
	for _, item := range items {
		post, ok := item.(map[string]any)
		if !ok {
			continue
		}
		for _, word := range tokenize(stringValue(post, "text")) {
			if len([]rune(word)) >= 5 {
				frequencies[word]++
			}
		}
	}
	trends := rankWords(frequencies, 5)
	return map[string]any{"trends": trends, "source_items": len(items)}, nil
}

func (p *Processor) generateReport(task domain.Task) (map[string]any, error) {
	trends, ok := task.Payload["trends"].([]any)
	if !ok {
		return nil, errors.New("trends are required")
	}
	lines := []string{"Отчёт по анализу социальных сетей", "Ключевые тренды:"}
	for _, trend := range trends {
		item, ok := trend.(map[string]any)
		if !ok {
			continue
		}
		lines = append(lines, fmt.Sprintf("- %s: %v упоминаний", stringValue(item, "term"), item["count"]))
	}
	lines = append(lines, "Рекомендация: отслеживать негативные всплески и усиливать коммуникацию по главным темам.")
	return map[string]any{"title": "Social media intelligence report", "markdown": strings.Join(lines, "\n"), "trend_count": len(trends)}, nil
}

func (p *Processor) keywordRelevance(payload map[string]any) int {
	text := strings.ToLower(fmt.Sprint(payload))
	score := 0
	for _, keyword := range p.config.Keywords {
		if strings.Contains(text, strings.ToLower(keyword)) {
			score += 2
		}
	}
	return score
}

func (p *Processor) scoreText(text string) int {
	score := 0
	for word, weight := range p.config.Rules {
		if strings.Contains(text, strings.ToLower(word)) {
			score += weight
		}
	}
	return score
}

func postsFromPayload(payload map[string]any) ([]map[string]any, error) {
	rawPosts, ok := payload["posts"].([]any)
	if !ok || len(rawPosts) == 0 {
		return nil, errors.New("posts are required")
	}
	posts := make([]map[string]any, 0, len(rawPosts))
	for _, item := range rawPosts {
		post, ok := item.(map[string]any)
		if ok {
			posts = append(posts, post)
		}
	}
	if len(posts) == 0 {
		return nil, errors.New("posts must contain objects")
	}
	return posts, nil
}

func stringValue(payload map[string]any, key string) string {
	value, ok := payload[key]
	if !ok || value == nil {
		return ""
	}
	return strings.TrimSpace(fmt.Sprint(value))
}

func intValue(payload map[string]any, key string, fallback int) int {
	value, ok := payload[key]
	if !ok {
		return fallback
	}
	switch typed := value.(type) {
	case int:
		return typed
	case float64:
		return int(typed)
	default:
		return fallback
	}
}

func label(score int) string {
	switch {
	case score > 0:
		return "positive"
	case score < 0:
		return "negative"
	default:
		return "neutral"
	}
}

func tokenize(text string) []string {
	replacer := strings.NewReplacer(".", " ", ",", " ", ":", " ", ";", " ", "!", " ", "?", " ", "\n", " ")
	return strings.Fields(strings.ToLower(replacer.Replace(text)))
}

func rankWords(frequencies map[string]int, limit int) []map[string]any {
	type pair struct {
		term  string
		count int
	}
	pairs := make([]pair, 0, len(frequencies))
	for term, count := range frequencies {
		pairs = append(pairs, pair{term: term, count: count})
	}
	sort.Slice(pairs, func(i, j int) bool {
		if pairs[i].count == pairs[j].count {
			return pairs[i].term < pairs[j].term
		}
		return pairs[i].count > pairs[j].count
	})
	if len(pairs) > limit {
		pairs = pairs[:limit]
	}
	result := make([]map[string]any, 0, len(pairs))
	for _, item := range pairs {
		result = append(result, map[string]any{"term": item.term, "count": item.count})
	}
	return result
}
