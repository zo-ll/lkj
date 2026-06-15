.PHONY: build install uninstall test fmt vet run

LKJ_INSTALL_DIR ?= $(HOME)/.local/bin

build:
	go build -o bin/lkj ./cmd/lkj

install: build
	mkdir -p $(LKJ_INSTALL_DIR)
	install -m 0755 bin/lkj $(LKJ_INSTALL_DIR)/lkj

uninstall:
	rm -f $(LKJ_INSTALL_DIR)/lkj

test:
	go test ./...

fmt:
	gofmt -w .

vet:
	go vet ./...

run:
	go run ./cmd/lkj
