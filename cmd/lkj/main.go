package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/zo-ll/lkj/internal/audio"
	"github.com/zo-ll/lkj/internal/config"
	"github.com/zo-ll/lkj/internal/desktop"
	"github.com/zo-ll/lkj/internal/output"
	"github.com/zo-ll/lkj/internal/pipeline"
	"github.com/zo-ll/lkj/internal/stt"
)

const version = "0.1.0"

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
	case "setup":
		return setup(args[1:])
	case "platform":
		return platform(args[1:])
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
  lkj doctor [--config path] [--record-test seconds]
  lkj setup [--config path]
  lkj platform
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
  --threads n          whisper.cpp worker threads
  --out name           output sink: stdout, http, file, clipboard
  --url url            HTTP sink URL
  --file-out path      file sink path
`)
}

func doctor(args []string) error {
	fs := flag.NewFlagSet("doctor", flag.ContinueOnError)
	cfgPath := fs.String("config", "", "config file path")
	recordTest := fs.Float64("record-test", 0, "record microphone test seconds")
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
	fmt.Println("threads", cfg.Threads)
	fmt.Println("record_device", cfg.RecordDevice)
	fmt.Println("output", cfg.Output)
	fmt.Println()

	issues := 0
	issues += printCommandCheck("ffmpeg", "ffmpeg")
	issues += printPathCheck("whisper_bin", cfg.WhisperBin, true)
	issues += printPathCheck("model_path", cfg.ModelPath, false)
	if strings.Contains(filepath.Base(cfg.ModelPath), "base.en") {
		fmt.Println("warn model_memory base.en previously OOM-killed this machine; prefer ggml-tiny.en.bin")
	}
	if cfg.RecordDevice != "" {
		issues += printDeviceCheck(cfg.RecordDevice)
	} else {
		fmt.Println("warn record_device not configured; run `lkj setup` or pass --device")
	}
	if *recordTest > 0 {
		issues += printRecordCheck(*recordTest, cfg.RecordDevice)
	}
	if issues > 0 {
		return fmt.Errorf("doctor found %d issue(s)", issues)
	}
	return nil
}

func platform(args []string) error {
	fs := flag.NewFlagSet("platform", flag.ContinueOnError)
	if err := fs.Parse(args); err != nil {
		return err
	}
	backend := desktop.New()
	caps := backend.Capabilities()
	fmt.Println("platform", backend.Name())
	fmt.Println("clipboard", caps.Clipboard)
	fmt.Println("type_text", caps.TypeText)
	fmt.Println("global_hotkey", caps.GlobalHotkey)
	fmt.Println("notifications", caps.Notifications)
	fmt.Println("tray", caps.Tray)
	fmt.Println("microphone_setup", caps.MicrophoneSetup)
	return nil
}

func setup(args []string) error {
	fs := flag.NewFlagSet("setup", flag.ContinueOnError)
	cfgPath := fs.String("config", "", "config file path")
	whisperBin := fs.String("whisper-bin", discoverWhisperBin(), "whisper.cpp binary")
	model := fs.String("model", discoverTinyModel(), "whisper.cpp model path")
	threads := fs.Int("threads", 0, "whisper.cpp worker threads")
	device := fs.String("device", discoverRecordDevice(), "recorder input device")
	out := fs.String("out", "stdout", "output sink")
	if err := fs.Parse(args); err != nil {
		return err
	}
	cfg := config.Default()
	cfg.WhisperBin = *whisperBin
	cfg.ModelPath = *model
	cfg.Threads = *threads
	cfg.RecordDevice = *device
	cfg.Output = *out
	path := valueOrDefault(*cfgPath, config.DefaultPath())
	if err := config.Save(path, cfg); err != nil {
		return err
	}
	fmt.Println("wrote", path)
	fmt.Println("whisper_bin", cfg.WhisperBin)
	fmt.Println("model_path", cfg.ModelPath)
	fmt.Println("threads", cfg.Threads)
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
	threads := fs.Int("threads", 0, "whisper.cpp worker threads")
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
	applyOverrides(&cfg, *backend, *whisperBin, *model, *language, *threads, *device, *out, *url, *fileOut)

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

func applyOverrides(cfg *config.Config, backend, whisperBin, model, language string, threads int, device, out, url, fileOut string) {
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
	if threads > 0 {
		cfg.Threads = threads
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
		return stt.WhisperCPP{Bin: cfg.WhisperBin, ModelPath: cfg.ModelPath, Language: cfg.Language, Threads: cfg.Threads}, nil
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

func printCommandCheck(label, name string) int {
	path, err := exec.LookPath(name)
	if err != nil {
		fmt.Println("fail", label, "not found on PATH")
		return 1
	}
	fmt.Println("ok", label, path)
	return 0
}

func printPathCheck(label, path string, executable bool) int {
	if path == "" {
		fmt.Println("fail", label, "not configured")
		return 1
	}
	if executable && !strings.ContainsRune(path, os.PathSeparator) {
		resolved, err := exec.LookPath(path)
		if err != nil {
			fmt.Println("fail", label, "not found on PATH:", path)
			return 1
		}
		fmt.Println("ok", label, resolved)
		return 0
	}
	info, err := os.Stat(path)
	if err != nil {
		fmt.Println("fail", label, err)
		return 1
	}
	if info.IsDir() {
		fmt.Println("fail", label, "is a directory")
		return 1
	}
	if executable && info.Mode()&0o111 == 0 {
		fmt.Println("fail", label, "is not executable")
		return 1
	}
	fmt.Println("ok", label, path)
	return 0
}

func printDeviceCheck(device string) int {
	if _, err := exec.LookPath("pactl"); err != nil {
		fmt.Println("warn record_device cannot verify without pactl")
		return 0
	}
	out, err := exec.Command("pactl", "list", "short", "sources").Output()
	if err != nil {
		fmt.Println("warn record_device cannot list sources:", err)
		return 0
	}
	if strings.Contains(string(out), device) {
		fmt.Println("ok", "record_device", device)
		return 0
	}
	fmt.Println("fail", "record_device", "not found:", device)
	return 1
}

func printRecordCheck(seconds float64, device string) int {
	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(seconds*float64(time.Second))+10*time.Second)
	defer cancel()
	wav, err := (audio.Recorder{Seconds: seconds, Device: device}).WAV(ctx)
	if err != nil {
		fmt.Println("fail", "record_test", err)
		return 1
	}
	defer os.Remove(wav)
	fmt.Println("ok", "record_test", wav)
	return 0
}

func discoverWhisperBin() string {
	home, _ := os.UserHomeDir()
	candidates := []string{
		filepath.Join(home, "Projects", "vendor", "whisper.cpp", "build", "bin", "whisper-cli"),
	}
	if path, err := exec.LookPath("whisper-cli"); err == nil {
		candidates = append([]string{path}, candidates...)
	}
	return firstExisting(candidates, true)
}

func discoverTinyModel() string {
	home, _ := os.UserHomeDir()
	return firstExisting([]string{
		filepath.Join(home, "Projects", "vendor", "whisper.cpp", "models", "ggml-tiny.en.bin"),
		filepath.Join(home, "Projects", "vendor", "whisper.cpp", "models", "ggml-tiny.bin"),
	}, false)
}

func discoverRecordDevice() string {
	if _, err := exec.LookPath("pactl"); err != nil {
		return "default"
	}
	out, err := exec.Command("pactl", "list", "short", "sources").Output()
	if err != nil {
		return "default"
	}
	for _, line := range strings.Split(string(out), "\n") {
		fields := strings.Fields(line)
		if len(fields) >= 2 && !strings.Contains(fields[1], ".monitor") {
			return fields[1]
		}
	}
	return "default"
}

func firstExisting(paths []string, executable bool) string {
	for _, path := range paths {
		info, err := os.Stat(path)
		if err != nil || info.IsDir() {
			continue
		}
		if executable && info.Mode()&0o111 == 0 {
			continue
		}
		return path
	}
	return ""
}

func valueOrDefault(value, fallback string) string {
	if value != "" {
		return value
	}
	return fallback
}
