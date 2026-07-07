package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
)

// ── take status ──────────────────────────────────────────────────────────────

const (
	TakePending   = "pending"
	TakeExported  = "exported"
	TakeStale     = "stale"
	TakeExporting = "exporting"
)

type TakeStatus struct {
	Path    string
	Name    string
	Size    int64
	ModTime time.Time
	State   string
	Frame   int
	Total   int
}

// exportManifest mirrors the fields of manifest.json needed to detect
// whether a take has already been exported, or was re-recorded since
// (stale). Identity is filename + size, not the full source path, since
// takes come off an external drive that may mount under a different path
// each session.
type exportManifest struct {
	SourceSizeBytes int64 `json:"source_size_bytes"`
}

func dirExists(path string) bool {
	if path == "" {
		return false
	}
	info, err := os.Stat(path)
	return err == nil && info.IsDir()
}

// scanTakes lists .mkv files in inputDir and, for each, checks outputDir for
// a matching take folder's manifest.json to classify it as pending,
// exported, or stale (same filename, different size - re-recorded).
func scanTakes(inputDir, outputDir string) []TakeStatus {
	var takes []TakeStatus
	entries, err := os.ReadDir(inputDir)
	if err != nil {
		return takes
	}
	for _, e := range entries {
		if e.IsDir() || !strings.EqualFold(filepath.Ext(e.Name()), ".mkv") {
			continue
		}
		info, err := e.Info()
		if err != nil {
			continue
		}
		name := strings.TrimSuffix(e.Name(), filepath.Ext(e.Name()))
		t := TakeStatus{
			Path:    filepath.Join(inputDir, e.Name()),
			Name:    name,
			Size:    info.Size(),
			ModTime: info.ModTime(),
			State:   TakePending,
		}
		if outputDir != "" {
			manifestPath := filepath.Join(outputDir, name, "manifest.json")
			if data, err := os.ReadFile(manifestPath); err == nil {
				var man exportManifest
				if json.Unmarshal(data, &man) == nil {
					if man.SourceSizeBytes == t.Size {
						t.State = TakeExported
					} else {
						t.State = TakeStale
					}
				}
			}
		}
		takes = append(takes, t)
	}
	sort.Slice(takes, func(i, j int) bool { return takes[i].Name < takes[j].Name })
	return takes
}

// applyLiveExportState overlays the in-flight export's progress onto a
// freshly scanned (or existing) take list, so a folder rescan never
// clobbers the status of the take currently being exported.
func (m model) applyLiveExportState(takes []TakeStatus) []TakeStatus {
	if !m.exporting || m.currentTakeName == "" {
		return takes
	}
	for i := range takes {
		if takes[i].Name == m.currentTakeName {
			takes[i].State = TakeExporting
			takes[i].Frame = m.currentFrame
			takes[i].Total = m.currentTotal
		}
	}
	return takes
}

// ── messages ─────────────────────────────────────────────────────────────────

type exportTickMsg time.Time
type exportLineMsg string
type exportDoneMsg struct{ err error }

func exportTick() tea.Cmd {
	return tea.Tick(2*time.Second, func(t time.Time) tea.Msg { return exportTickMsg(t) })
}

func listenExportOutput(ch chan string) tea.Cmd {
	return func() tea.Msg {
		line, ok := <-ch
		if !ok {
			return nil
		}
		return exportLineMsg(line)
	}
}

func waitForExportProc(cmd *exec.Cmd) tea.Cmd {
	return func() tea.Msg {
		return exportDoneMsg{err: cmd.Wait()}
	}
}

// ── export setup screen ───────────────────────────────────────────────────────

func (m model) openExportSetup() (tea.Model, tea.Cmd) {
	m.statusMsg = ""
	m.exportErr = ""
	m.exportSetupStep = 0
	m.input.Placeholder = `e.g. D:\ or E:\CHIPPYKINECT`
	if dirExists(m.config.ExportInputDir) {
		m.input.SetValue(m.config.ExportInputDir)
	} else {
		m.input.SetValue("")
	}
	m.input.Focus()
	m.screen = screenExportSetup
	return m, textinput.Blink
}

func (m model) handleExportSetupKey(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.Type {
	case tea.KeyEsc:
		m.screen = screenMain
		return m, nil
	case tea.KeyEnter:
		path := strings.TrimSpace(m.input.Value())
		if path == "" {
			return m, nil
		}
		if m.exportSetupStep == 0 {
			m.config.ExportInputDir = path
			m.exportSetupStep = 1
			m.input.Placeholder = `e.g. E:\EXPORTS`
			if dirExists(m.config.ExportOutputDir) {
				m.input.SetValue(m.config.ExportOutputDir)
			} else {
				m.input.SetValue("")
			}
			m.input.Focus()
			return m, textinput.Blink
		}
		m.config.ExportOutputDir = path
		_ = saveConfig(m.config)
		m.takes = m.applyLiveExportState(scanTakes(m.config.ExportInputDir, m.config.ExportOutputDir))
		m.takeCursor = 0
		m.selected = map[string]bool{}
		m.screen = screenExportSession
		return m, exportTick()
	}
	var cmd tea.Cmd
	m.input, cmd = m.input.Update(msg)
	return m, cmd
}

func (m model) viewExportSetup() string {
	var b strings.Builder
	b.WriteString("\n")
	b.WriteString(titleStyle.Render("  EXPORT SESSION") + "\n\n")
	if m.exportSetupStep == 0 {
		b.WriteString("  Input folder (external drive with .mkv takes):\n\n")
	} else {
		b.WriteString(fmt.Sprintf("  %s  %s\n\n", labelStyle.Render("Input:"), valueStyle.Render(m.config.ExportInputDir)))
		b.WriteString("  Output folder (where exports are written):\n\n")
	}
	b.WriteString("  " + m.input.View() + "\n\n")
	b.WriteString(dimStyle.Render("  [Enter] Continue   [Esc] Cancel") + "\n")
	return b.String()
}

// ── export session screen ─────────────────────────────────────────────────────

func (m model) handleExportSessionKey(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	if m.exporting {
		return m, nil
	}
	switch msg.String() {
	case "esc", "q":
		m.screen = screenMain
		m.statusMsg = ""
		return m, nil
	case "up", "k":
		if m.takeCursor > 0 {
			m.takeCursor--
		}
	case "down", "j":
		if m.takeCursor < len(m.takes)-1 {
			m.takeCursor++
		}
	case " ":
		if len(m.takes) > 0 {
			name := m.takes[m.takeCursor].Name
			m.selected[name] = !m.selected[name]
		}
	case "a":
		for _, t := range m.takes {
			if t.State == TakePending || t.State == TakeStale {
				m.selected[t.Name] = true
			}
		}
	case "r":
		m.takes = m.applyLiveExportState(scanTakes(m.config.ExportInputDir, m.config.ExportOutputDir))
	case "x":
		var toExport []TakeStatus
		for _, t := range m.takes {
			if m.selected[t.Name] {
				toExport = append(toExport, t)
			}
		}
		if len(toExport) == 0 && len(m.takes) > 0 {
			toExport = []TakeStatus{m.takes[m.takeCursor]}
		}
		return m.startExport(toExport)
	}
	return m, nil
}

func (m model) startExport(selected []TakeStatus) (tea.Model, tea.Cmd) {
	if len(selected) == 0 {
		return m, nil
	}

	args := []string{"run", m.config.ExportScriptPath}
	for _, t := range selected {
		args = append(args, t.Path)
	}
	args = append(args, "--out", m.config.ExportOutputDir)

	cmd := exec.Command("uv", args...)
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		m.exportErr = "failed to start export: " + err.Error()
		return m, nil
	}
	if err := cmd.Start(); err != nil {
		m.exportErr = "failed to start export: " + err.Error()
		return m, nil
	}

	ch := make(chan string, 32)
	go func() {
		scanner := bufio.NewScanner(stdout)
		for scanner.Scan() {
			ch <- scanner.Text()
		}
		close(ch)
	}()

	m.exportCmd = cmd
	m.exportChan = ch
	m.exporting = true
	m.currentTakeName = ""
	m.currentFrame = 0
	m.currentTotal = 0
	m.exportErr = ""
	m.selected = map[string]bool{}
	return m, tea.Batch(listenExportOutput(ch), waitForExportProc(cmd))
}

func (m model) handleExportLine(line string) (tea.Model, tea.Cmd) {
	fields := strings.Fields(line)
	if len(fields) > 0 {
		switch fields[0] {
		case "TAKE":
			if len(fields) > 1 {
				m.currentTakeName = strings.TrimSuffix(fields[1], filepath.Ext(fields[1]))
				m.currentFrame = 0
				m.currentTotal = 0
			}
		case "TOTAL":
			if len(fields) > 1 {
				if n, err := strconv.Atoi(fields[1]); err == nil {
					m.currentTotal = n
				}
			}
		case "FRAME":
			if len(fields) > 1 {
				if n, err := strconv.Atoi(fields[1]); err == nil {
					m.currentFrame = n
				}
			}
		case "ERROR":
			m.exportErr = strings.TrimSpace(strings.TrimPrefix(line, "ERROR"))
		}
	}
	m.takes = m.applyLiveExportState(m.takes)
	return m, listenExportOutput(m.exportChan)
}

func (m model) handleExportDone(err error) (tea.Model, tea.Cmd) {
	m.exporting = false
	m.exportCmd = nil
	m.exportChan = nil
	m.currentTakeName = ""
	if err != nil && m.exportErr == "" {
		m.exportErr = err.Error()
	}
	m.takes = scanTakes(m.config.ExportInputDir, m.config.ExportOutputDir)
	return m, nil
}

func formatTakeState(t TakeStatus) string {
	switch t.State {
	case TakeExported:
		return successStyle.Render("exported")
	case TakeStale:
		return errorStyle.Render("stale (re-recorded)")
	case TakeExporting:
		if t.Total > 0 {
			return recStyle.Render(fmt.Sprintf("exporting %d/%d", t.Frame, t.Total))
		}
		return recStyle.Render(fmt.Sprintf("exporting (%d frames)", t.Frame))
	default:
		return dimStyle.Render("pending")
	}
}

func (m model) viewExportSession() string {
	var b strings.Builder
	b.WriteString("\n")
	b.WriteString(titleStyle.Render("  EXPORT SESSION") + "\n")
	b.WriteString(dimStyle.Render("  ────────────────────────────────") + "\n")
	b.WriteString(fmt.Sprintf("  %s  %s\n", labelStyle.Render("Input: "), valueStyle.Render(m.config.ExportInputDir)))
	b.WriteString(fmt.Sprintf("  %s  %s\n\n", labelStyle.Render("Output:"), valueStyle.Render(m.config.ExportOutputDir)))

	if len(m.takes) == 0 {
		b.WriteString(dimStyle.Render("  No .mkv files found in input folder.") + "\n\n")
	}
	for i, t := range m.takes {
		cursor := "  "
		if i == m.takeCursor {
			cursor = cursorStyle.Render("▸ ")
		}
		check := "[ ]"
		if m.selected[t.Name] {
			check = "[x]"
		}
		b.WriteString(fmt.Sprintf("  %s%s %-40s %s\n", cursor, check, t.Name, formatTakeState(t)))
	}
	b.WriteString("\n")
	if m.exportErr != "" {
		b.WriteString("  " + errorStyle.Render("Error: "+m.exportErr) + "\n\n")
	}
	if m.exporting {
		b.WriteString(dimStyle.Render("  Exporting - please wait...") + "\n")
	} else {
		b.WriteString(dimStyle.Render("  [↑↓/jk] Move  [Space] Select  [a] Select pending  [x] Export  [r] Refresh  [Esc] Back") + "\n")
	}
	return b.String()
}
