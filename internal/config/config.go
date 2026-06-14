package config

import (
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
)

type Config struct {
	STTBackend   string `json:"stt_backend"`
	WhisperBin   string `json:"whisper_bin"`
	ModelPath    string `json:"model_path"`
	Language     string `json:"language"`
	RecordDevice string `json:"record_device"`
	Output       string `json:"output"`
	HTTPURL      string `json:"http_url"`
	FilePath     string `json:"file_path"`
}

func Default() Config {
	return Config{
		STTBackend: "whispercpp",
		WhisperBin: "whisper-cli",
		Output:     "stdout",
	}
}

func DefaultPath() string {
	if dir, err := os.UserConfigDir(); err == nil && dir != "" {
		return filepath.Join(dir, "lkj", "config.json")
	}
	return filepath.Join(".", "config.json")
}

func Load(path string) (Config, error) {
	cfg := Default()
	if path == "" {
		path = DefaultPath()
	}
	data, err := os.ReadFile(path)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return cfg, nil
		}
		return cfg, err
	}
	if err := json.Unmarshal(data, &cfg); err != nil {
		return cfg, err
	}
	return cfg, nil
}
