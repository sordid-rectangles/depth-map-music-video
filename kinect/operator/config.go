package main

import (
	"encoding/json"
	"os"
	"path/filepath"
)

type Config struct {
	RecorderPath string `json:"recorder_path"`
	Preset       string `json:"preset"`
	OutputDir    string `json:"output_dir"`
}

type PresetDef struct {
	Name      string
	ColorMode string
	DepthMode string
	FrameRate string
	IMU       string
}

var Presets = []PresetDef{
	{Name: "Primary",   ColorMode: "1440p", DepthMode: "WFOV_2X2BINNED", FrameRate: "30", IMU: "OFF"},
	{Name: "Hero Shot", ColorMode: "2160p", DepthMode: "WFOV_2X2BINNED", FrameRate: "30", IMU: "OFF"},
	{Name: "Long Take", ColorMode: "1080p", DepthMode: "WFOV_2X2BINNED", FrameRate: "30", IMU: "OFF"},
	{Name: "Depth Ref", ColorMode: "OFF",   DepthMode: "WFOV_2X2BINNED", FrameRate: "30", IMU: "OFF"},
}

var defaultConfig = Config{
	RecorderPath: `C:\Program Files\Azure Kinect SDK v1.4.2\tools\k4arecorder.exe`,
	Preset:       "Long Take",
	OutputDir:    `E:\CHIPPYKINECT`,
}

func configFilePath() string {
	exe, err := os.Executable()
	if err != nil {
		return "operator-config.json"
	}
	return filepath.Join(filepath.Dir(exe), "operator-config.json")
}

func loadConfig() Config {
	data, err := os.ReadFile(configFilePath())
	if err != nil {
		return defaultConfig
	}
	var cfg Config
	if err := json.Unmarshal(data, &cfg); err != nil {
		return defaultConfig
	}
	return cfg
}

func saveConfig(cfg Config) error {
	data, err := json.MarshalIndent(cfg, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(configFilePath(), data, 0644)
}

func presetByName(name string) PresetDef {
	for _, p := range Presets {
		if p.Name == name {
			return p
		}
	}
	return Presets[2] // Long Take default
}
