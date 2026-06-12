.PHONY: build test fmt vet run

build:
	go build -o bin/lkj ./cmd/lkj

test:
	go test ./...

fmt:
	gofmt -w .

vet:
	go vet ./...

run:
	go run ./cmd/lkj
