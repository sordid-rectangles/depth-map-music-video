package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// ── screens ──────────────────────────────────────────────────────────────────

type screen int

const (
	screenMain screen = iota
	screenFilename
	screenDuration
	screenRecording
	screenPreset
	screenOutput
)

// ── messages ─────────────────────────────────────────────────────────────────

type tickMsg time.Time
type procDoneMsg struct{ err error }

// ── styles ───────────────────────────────────────────────────────────────────

var (
	titleStyle   = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("12"))
	labelStyle   = lipgloss.NewStyle().Foreground(lipgloss.Color("8"))
	valueStyle   = lipgloss.NewStyle().Foreground(lipgloss.Color("15"))
	cursorStyle  = lipgloss.NewStyle().Foreground(lipgloss.Color("10")).Bold(true)
	dimStyle     = lipgloss.NewStyle().Foreground(lipgloss.Color("240"))
	errorStyle   = lipgloss.NewStyle().Foreground(lipgloss.Color("9"))
	recStyle     = lipgloss.NewStyle().Foreground(lipgloss.Color("9")).Bold(true)
	successStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("10"))
)

// ── model ────────────────────────────────────────────────────────────────────

type model struct {
	screen          screen
	config          Config
	input           textinput.Model
	pendingFilename string
	isTimedRecord   bool
	cmd             *exec.Cmd
	userStopped     bool
	startTime       time.Time
	elapsed         time.Duration
	durationSecs    int
	presetCursor    int
	statusMsg       string
}

func newModel() model {
	ti := textinput.New()
	ti.CharLimit = 128
	cfg := loadConfig()
	cursor := 0
	for i, p := range Presets {
		if p.Name == cfg.Preset {
			cursor = i
			break
		}
	}
	return model{
		screen:       screenMain,
		config:       cfg,
		input:        ti,
		presetCursor: cursor,
	}
}

// ── init / update ─────────────────────────────────────────────────────────────

func (m model) Init() tea.Cmd {
	return nil
}

func tick() tea.Cmd {
	return tea.Tick(time.Second, func(t time.Time) tea.Msg { return tickMsg(t) })
}

func waitForProc(cmd *exec.Cmd) tea.Cmd {
	return func() tea.Msg {
		return procDoneMsg{err: cmd.Wait()}
	}
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		return m.handleKey(msg)

	case tickMsg:
		if m.screen == screenRecording {
			m.elapsed = time.Since(m.startTime)
			return m, tick()
		}
		return m, nil

	case procDoneMsg:
		m.cmd = nil
		m.screen = screenMain
		if !m.userStopped && msg.err != nil {
			m.statusMsg = errorStyle.Render("Recorder error: " + msg.err.Error())
		} else {
			m.statusMsg = successStyle.Render("Saved: " + m.pendingFilename + ".mkv")
		}
		m.userStopped = false
		return m, nil
	}

	// Forward other messages (e.g. blink ticks) to the active text input.
	if m.screen == screenFilename || m.screen == screenDuration || m.screen == screenOutput {
		var cmd tea.Cmd
		m.input, cmd = m.input.Update(msg)
		return m, cmd
	}

	return m, nil
}

func (m model) handleKey(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch m.screen {
	case screenMain:
		return m.handleMainKey(msg)
	case screenFilename:
		return m.handleFilenameKey(msg)
	case screenDuration:
		return m.handleDurationKey(msg)
	case screenRecording:
		return m.handleRecordingKey(msg)
	case screenPreset:
		return m.handlePresetKey(msg)
	case screenOutput:
		return m.handleOutputKey(msg)
	}
	return m, nil
}

// ── main menu ─────────────────────────────────────────────────────────────────

func (m model) handleMainKey(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "q", "ctrl+c":
		return m, tea.Quit
	case "1", "r":
		return m.openFilenameInput(false)
	case "2", "t":
		return m.openFilenameInput(true)
	case "3", "p":
		m.statusMsg = ""
		m.screen = screenPreset
	case "4", "o":
		m.statusMsg = ""
		m.input.Placeholder = `e.g. E:\CHIPPYKINECT`
		m.input.SetValue(m.config.OutputDir)
		m.input.Focus()
		m.screen = screenOutput
		return m, textinput.Blink
	}
	return m, nil
}

func (m model) openFilenameInput(timed bool) (tea.Model, tea.Cmd) {
	m.statusMsg = ""
	m.isTimedRecord = timed
	m.input.Placeholder = "e.g. 1"
	m.input.SetValue("")
	m.input.Focus()
	m.screen = screenFilename
	return m, textinput.Blink
}

// ── filename input ────────────────────────────────────────────────────────────

func (m model) handleFilenameKey(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.Type {
	case tea.KeyEsc:
		m.screen = screenMain
		return m, nil
	case tea.KeyEnter:
		take := strings.TrimSpace(m.input.Value())
		if take == "" {
			return m, nil
		}
		if n, err := strconv.Atoi(take); err == nil {
			m.pendingFilename = fmt.Sprintf("take-%02d-%s", n, time.Now().Format("20060102-150405"))
		} else {
			m.pendingFilename = fmt.Sprintf("take-%s-%s", take, time.Now().Format("20060102-150405"))
		}
		if m.isTimedRecord {
			m.input.Placeholder = "seconds, e.g. 30"
			m.input.SetValue("")
			m.screen = screenDuration
			return m, textinput.Blink
		}
		return m.startRecording(0)
	}
	var cmd tea.Cmd
	m.input, cmd = m.input.Update(msg)
	return m, cmd
}

// ── duration input ────────────────────────────────────────────────────────────

func (m model) handleDurationKey(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.Type {
	case tea.KeyEsc:
		m.input.Placeholder = "e.g. scene-01-take-01"
		m.input.SetValue(m.pendingFilename)
		m.input.Focus()
		m.screen = screenFilename
		return m, textinput.Blink
	case tea.KeyEnter:
		secs, err := strconv.Atoi(strings.TrimSpace(m.input.Value()))
		if err != nil || secs <= 0 {
			return m, nil
		}
		return m.startRecording(secs)
	}
	var cmd tea.Cmd
	m.input, cmd = m.input.Update(msg)
	return m, cmd
}

// ── recording ─────────────────────────────────────────────────────────────────

func (m model) startRecording(durationSecs int) (tea.Model, tea.Cmd) {
	preset := presetByName(m.config.Preset)
	outputPath := filepath.Join(m.config.OutputDir, m.pendingFilename+".mkv")

	args := []string{
		"-c", preset.ColorMode,
		"-d", preset.DepthMode,
		"-r", preset.FrameRate,
		"--imu", preset.IMU,
	}
	if durationSecs > 0 {
		args = append(args, "-l", strconv.Itoa(durationSecs))
	}
	args = append(args, outputPath)

	if _, err := os.Stat(outputPath); err == nil {
		m.statusMsg = errorStyle.Render("File already exists: " + m.pendingFilename + ".mkv — rename and try again")
		m.input.SetValue(m.pendingFilename)
		m.input.Focus()
		m.screen = screenFilename
		return m, textinput.Blink
	}

	cmd := exec.Command(m.config.RecorderPath, args...)
	setCmdAttrs(cmd)
	if err := cmd.Start(); err != nil {
		m.statusMsg = errorStyle.Render("Failed to start recorder: " + err.Error())
		m.screen = screenMain
		return m, nil
	}

	m.cmd = cmd
	m.startTime = time.Now()
	m.elapsed = 0
	m.durationSecs = durationSecs
	m.userStopped = false
	m.screen = screenRecording
	return m, tea.Batch(tick(), waitForProc(cmd))
}

func (m model) handleRecordingKey(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "q", "Q", "ctrl+c":
		if m.cmd != nil && m.cmd.Process != nil && !m.userStopped {
			m.userStopped = true
			gracefulStop(m.cmd)
		}
	}
	return m, nil
}

// ── preset selection ──────────────────────────────────────────────────────────

func (m model) handlePresetKey(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "esc", "q":
		m.screen = screenMain
	case "up", "k":
		if m.presetCursor > 0 {
			m.presetCursor--
		}
	case "down", "j":
		if m.presetCursor < len(Presets)-1 {
			m.presetCursor++
		}
	case "enter", " ":
		m.config.Preset = Presets[m.presetCursor].Name
		_ = saveConfig(m.config)
		m.statusMsg = successStyle.Render("Preset: " + m.config.Preset)
		m.screen = screenMain
	}
	return m, nil
}

// ── output folder ─────────────────────────────────────────────────────────────

func (m model) handleOutputKey(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.Type {
	case tea.KeyEsc:
		m.screen = screenMain
		return m, nil
	case tea.KeyEnter:
		path := strings.TrimSpace(m.input.Value())
		if path != "" {
			m.config.OutputDir = path
			_ = saveConfig(m.config)
			m.statusMsg = successStyle.Render("Output: " + path)
		}
		m.screen = screenMain
		return m, nil
	}
	var cmd tea.Cmd
	m.input, cmd = m.input.Update(msg)
	return m, cmd
}

// ── views ─────────────────────────────────────────────────────────────────────

func (m model) View() string {
	switch m.screen {
	case screenMain:
		return m.viewMain()
	case screenFilename:
		return m.viewFilename()
	case screenDuration:
		return m.viewDuration()
	case screenRecording:
		return m.viewRecording()
	case screenPreset:
		return m.viewPreset()
	case screenOutput:
		return m.viewOutput()
	}
	return ""
}

func (m model) viewMain() string {
	preset := presetByName(m.config.Preset)
	presetDesc := fmt.Sprintf("%s  (%s / %sfps)", preset.Name, preset.ColorMode, preset.FrameRate)

	var b strings.Builder
	b.WriteString("\n")
	b.WriteString(titleStyle.Render("  KINECT CAMERA OPERATOR") + "\n")
	b.WriteString(dimStyle.Render("  ────────────────────────────────") + "\n\n")
	b.WriteString(fmt.Sprintf("  %s  %s\n", labelStyle.Render("Preset:"), valueStyle.Render(presetDesc)))
	b.WriteString(fmt.Sprintf("  %s  %s\n", labelStyle.Render("Output:"), valueStyle.Render(m.config.OutputDir)))
	b.WriteString("\n")
	b.WriteString(dimStyle.Render("  ────────────────────────────────") + "\n\n")
	b.WriteString(fmt.Sprintf("  %s  Record\n", cursorStyle.Render("[1]")))
	b.WriteString(fmt.Sprintf("  %s  Timed record\n", cursorStyle.Render("[2]")))
	b.WriteString(fmt.Sprintf("  %s  Change preset\n", cursorStyle.Render("[3]")))
	b.WriteString(fmt.Sprintf("  %s  Set output folder\n", cursorStyle.Render("[4]")))
	b.WriteString("\n")
	b.WriteString(dimStyle.Render("  [q] Quit") + "\n")
	if m.statusMsg != "" {
		b.WriteString("\n  " + m.statusMsg + "\n")
	}
	return b.String()
}

func (m model) viewFilename() string {
	heading := "  RECORD"
	if m.isTimedRecord {
		heading = "  TIMED RECORD"
	}
	var b strings.Builder
	b.WriteString("\n")
	b.WriteString(titleStyle.Render(heading) + "\n\n")
	b.WriteString("  Take number:\n\n")
	b.WriteString("  " + m.input.View() + "\n\n")
	if m.statusMsg != "" {
		b.WriteString("  " + m.statusMsg + "\n\n")
	}
	b.WriteString(dimStyle.Render("  [Enter] Continue   [Esc] Cancel") + "\n")
	return b.String()
}

func (m model) viewDuration() string {
	var b strings.Builder
	b.WriteString("\n")
	b.WriteString(titleStyle.Render("  TIMED RECORD") + "\n\n")
	b.WriteString(fmt.Sprintf("  %s  %s\n\n", labelStyle.Render("File:"), valueStyle.Render(m.pendingFilename+".mkv")))
	b.WriteString("  Duration in seconds:\n\n")
	b.WriteString("  " + m.input.View() + "\n\n")
	b.WriteString(dimStyle.Render("  [Enter] Start   [Esc] Back") + "\n")
	return b.String()
}

func (m model) viewRecording() string {
	var b strings.Builder
	b.WriteString("\n")
	b.WriteString(recStyle.Render("  ● RECORDING") + "\n")
	b.WriteString(dimStyle.Render("  ────────────────────────────────") + "\n\n")
	b.WriteString(fmt.Sprintf("  %s  %s\n", labelStyle.Render("File:  "), valueStyle.Render(m.pendingFilename+".mkv")))
	b.WriteString(fmt.Sprintf("  %s  %s\n", labelStyle.Render("Output:"), valueStyle.Render(m.config.OutputDir)))
	b.WriteString("\n")
	if m.durationSecs > 0 {
		remaining := time.Duration(m.durationSecs)*time.Second - m.elapsed
		if remaining < 0 {
			remaining = 0
		}
		b.WriteString(fmt.Sprintf("  %s  %s\n", labelStyle.Render("Remaining:"), titleStyle.Render(fmtDuration(remaining))))
		b.WriteString(fmt.Sprintf("  %s  %s\n", labelStyle.Render("Elapsed:  "), dimStyle.Render(fmtDuration(m.elapsed))))
	} else {
		b.WriteString(fmt.Sprintf("  %s  %s\n", labelStyle.Render("Elapsed:"), titleStyle.Render(fmtDuration(m.elapsed))))
	}
	b.WriteString("\n")
	if m.userStopped {
		b.WriteString(dimStyle.Render("  Stopping — finalizing file...") + "\n")
	} else {
		b.WriteString(dimStyle.Render("  [Q] or [Ctrl+C] to stop") + "\n")
	}
	return b.String()
}

func (m model) viewPreset() string {
	var b strings.Builder
	b.WriteString("\n")
	b.WriteString(titleStyle.Render("  CHANGE PRESET") + "\n\n")
	for i, p := range Presets {
		desc := fmt.Sprintf("%-10s  %s / %sfps", p.Name, p.ColorMode, p.FrameRate)
		isCurrent := p.Name == m.config.Preset
		if isCurrent && i != m.presetCursor {
			desc += "  ✓"
		}
		if i == m.presetCursor {
			b.WriteString(cursorStyle.Render("  ▸ "+desc) + "\n")
		} else if isCurrent {
			b.WriteString(valueStyle.Render("    "+desc) + "\n")
		} else {
			b.WriteString(dimStyle.Render("    "+desc) + "\n")
		}
	}
	b.WriteString("\n")
	b.WriteString(dimStyle.Render("  [↑↓ / jk] Move   [Enter] Select   [Esc] Cancel") + "\n")
	return b.String()
}

func (m model) viewOutput() string {
	var b strings.Builder
	b.WriteString("\n")
	b.WriteString(titleStyle.Render("  SET OUTPUT FOLDER") + "\n\n")
	b.WriteString(fmt.Sprintf("  %s  %s\n\n", labelStyle.Render("Current:"), valueStyle.Render(m.config.OutputDir)))
	b.WriteString("  New path:\n\n")
	b.WriteString("  " + m.input.View() + "\n\n")
	b.WriteString(dimStyle.Render("  [Enter] Save   [Esc] Cancel") + "\n")
	return b.String()
}

// ── helpers ───────────────────────────────────────────────────────────────────

func fmtDuration(d time.Duration) string {
	d = d.Round(time.Second)
	h := d / time.Hour
	d -= h * time.Hour
	m := d / time.Minute
	d -= m * time.Minute
	s := d / time.Second
	if h > 0 {
		return fmt.Sprintf("%02d:%02d:%02d", h, m, s)
	}
	return fmt.Sprintf("%02d:%02d", m, s)
}

// ── entry point ───────────────────────────────────────────────────────────────

func main() {
	p := tea.NewProgram(newModel(), tea.WithAltScreen())
	if _, err := p.Run(); err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		os.Exit(1)
	}
}
