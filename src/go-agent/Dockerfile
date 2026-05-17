FROM golang:1.22-alpine AS builder

WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags="-s -w" -o /out/social-agent ./cmd/agent

FROM alpine:3.20

RUN addgroup -S app && adduser -S app -G app
WORKDIR /app
COPY --from=builder /out/social-agent /app/social-agent
COPY configs /app/configs
USER app

EXPOSE 8080
ENTRYPOINT ["/app/social-agent"]

