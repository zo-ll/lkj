.PHONY: build install install-shortcut uninstall test fmt vet run

LKJ_INSTALL_DIR ?= $(HOME)/.local/bin
LKJ_APPLICATION_DIR ?= $(HOME)/.local/share/applications

build:
	go build -o bin/lkj ./cmd/lkj

install: build
	mkdir -p $(LKJ_INSTALL_DIR)
	install -m 0755 bin/lkj $(LKJ_INSTALL_DIR)/lkj

install-shortcut: install
	mkdir -p $(LKJ_APPLICATION_DIR)
	install -m 0644 share/applications/lkj-toggle.desktop $(LKJ_APPLICATION_DIR)/lkj-toggle.desktop
	@if command -v kbuildsycoca6 >/dev/null 2>&1; then kbuildsycoca6; fi

uninstall:
	rm -f $(LKJ_INSTALL_DIR)/lkj
	rm -f $(LKJ_APPLICATION_DIR)/lkj-toggle.desktop

test:
	go test ./...

fmt:
	gofmt -w .

vet:
	go vet ./...

run:
	go run ./cmd/lkj
