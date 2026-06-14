package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"os"
	"time"

	"github.com/zo-ll/lkj/internal/audio"
	"github.com/zo-ll/lkj/internal/config"
	"github.com/zo-ll/lkj/internal/output"
	"github.com/zo-ll/lkj/internal/pipeline"
	"github.com/zo-ll/lkj/internal/stt"
)

const version = "0.1.0-go-rewrite"

func main() {
	if err := run(os.Args[1:]); err != nil {
		fmt.Fprintln(os.Stderr, "error:", err)
		os.Exit(1)
	}
}

func run(args []string) error {
	if len(args) == 0 {
		usage()
		return nil
	}

	switch args[0] {
	case "version":
		fmt.Println(version)
		return nil
	case "doctor":
		return doctor(args[1:])
	case "once":
		return once(args[1:])
	case "help", "-h", "--help":
		usage()
		return nil
	default:
		return fmt.Errorf("unknown command %q", args[0])
	}
}

func usage() {
	fmt.Print(`lkj - tiny local voice input bridge for agents

Usage:
  lkj version
  lkj doctor [--config path]
  lkj once --file input.wav --model model.bin [options]
  lkj once --seconds 5 --model model.bin [options]

Options for once:
  --config path        config file path
  --file path          input wav file
  --seconds n          record microphone for n seconds
  --device name        recorder input device
  --backend name       stt backend (whispercpp)
  --whisper-bin path   whisper.cpp CLI binary
  --model path         whisper.cpp ggml model path
  --language code      optional language code
  --out name           output sink: stdout, http, file, clipboard
  --url url            HTTP sink URL
  --file-out path      file sink path
`)
}

func doctor(args []string) error {
	fs := flag.NewFlagSet("doctor", flag.ContinueOnError)
	cfgPath := fs.String("config", "", "config file path")
	if err := fs.Parse(args); err != nil {
		return err
	}
	cfg, err := config.Load(*cfgPath)
	if err != nil {
		return err
	}
	fmt.Println("lkj", version)
	fmt.Println("config_path", valueOrDefault(*cfgPath, config.DefaultPath()))
	fmt.Println("stt_backend", cfg.STTBackend)
	fmt.Println("whisper_bin", cfg.WhisperBin)
	fmt.Println("model_path", cfg.ModelPath)
	fmt.Println("record_device", cfg.RecordDevice)
	fmt.Println("output", cfg.Output)
	return nil
}

func once(args []string) error {
	fs := flag.NewFlagSet("once", flag.ContinueOnError)
	cfgPath := fs.String("config", "", "config file path")
	inputFile := fs.String("file", "", "input wav file")
	seconds := fs.Float64("seconds", 0, "record microphone seconds")
	device := fs.String("device", "", "recorder input device")
	backend := fs.String("backend", "", "stt backend")
	whisperBin := fs.String("whisper-bin", "", "whisper.cpp binary")
	model := fs.String("model", "", "model path")
	language := fs.String("language", "", "language code")
	out := fs.String("out", "", "output sink")
	url := fs.String("url", "", "http output url")
	fileOut := fs.String("file-out", "", "file output path")
	if err := fs.Parse(args); err != nil {
		return err
	}

	cfg, err := config.Load(*cfgPath)
	if err != nil {
		return err
	}
	applyOverrides(&cfg, *backend, *whisperBin, *model, *language, *device, *out, *url, *fileOut)

	source, err := buildSource(*inputFile, *seconds, cfg.RecordDevice)
	if err != nil {
		return err
	}
	transcriber, err := buildTranscriber(cfg)
	if err != nil {
		return err
	}
	sink, err := buildSink(cfg)
	if err != nil {
		return err
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()

	_, err = pipeline.Pipeline{Source: source, Transcriber: transcriber, Sink: sink}.Run(ctx)
	return err
}

func applyOverrides(cfg *config.Config, backend, whisperBin, model, language, device, out, url, fileOut string) {
	if backend != "" {
		cfg.STTBackend = backend
	}
	if whisperBin != "" {
		cfg.WhisperBin = whisperBin
	}
	if model != "" {
		cfg.ModelPath = model
	}
	if language != "" {
		cfg.Language = language
	}
	if device != "" {
		cfg.RecordDevice = device
	}
	if out != "" {
		cfg.Output = out
	}
	if url != "" {
		cfg.HTTPURL = url
	}
	if fileOut != "" {
		cfg.FilePath = fileOut
	}
}

func buildSource(inputFile string, seconds float64, device string) (audio.Source, error) {
	if inputFile != "" {
		return audio.ExistingWAV{Path: inputFile}, nil
	}
	if seconds > 0 {
		return audio.Recorder{Seconds: seconds, Device: device}, nil
	}
	return nil, errors.New("missing audio source: pass --file input.wav or --seconds N")
}

func buildTranscriber(cfg config.Config) (stt.Transcriber, error) {
	switch cfg.STTBackend {
	case "", "whispercpp":
		return stt.WhisperCPP{Bin: cfg.WhisperBin, ModelPath: cfg.ModelPath, Language: cfg.Language}, nil
	default:
		return nil, fmt.Errorf("unsupported stt backend %q", cfg.STTBackend)
	}
}

func buildSink(cfg config.Config) (output.Sink, error) {
	switch cfg.Output {
	case "", "stdout":
		return output.Stdout{Writer: os.Stdout}, nil
	case "http":
		if cfg.HTTPURL == "" {
			return nil, errors.New("http output requires --url or http_url config")
		}
		return output.HTTP{URL: cfg.HTTPURL}, nil
	case "file":
		if cfg.FilePath == "" {
			return nil, errors.New("file output requires --file-out or file_path config")
		}
		return output.File{Path: cfg.FilePath}, nil
	case "clipboard":
		return output.Clipboard{}, nil
	default:
		return nil, fmt.Errorf("unsupported output sink %q", cfg.Output)
	}
}

func valueOrDefault(value, fallback string) string {
	if value != "" {
		return value
	}
	return fallback
}
