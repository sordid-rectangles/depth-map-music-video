//go:build windows

package main

import (
	"os/exec"
	"syscall"
)

// setCmdAttrs puts the recorder in its own process group so we can target it
// specifically with GenerateConsoleCtrlEvent.
func setCmdAttrs(cmd *exec.Cmd) {
	cmd.SysProcAttr = &syscall.SysProcAttr{
		CreationFlags: syscall.CREATE_NEW_PROCESS_GROUP,
	}
}

// gracefulStop sends CTRL_BREAK_EVENT to the recorder's process group, which
// k4arecorder handles by flushing and closing the MKV file before exiting.
func gracefulStop(cmd *exec.Cmd) {
	dll := syscall.MustLoadDLL("kernel32.dll")
	proc := dll.MustFindProc("GenerateConsoleCtrlEvent")
	proc.Call(uintptr(syscall.CTRL_BREAK_EVENT), uintptr(cmd.Process.Pid))
}
