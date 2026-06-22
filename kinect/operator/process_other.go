//go:build !windows

package main

import "os/exec"

func setCmdAttrs(cmd *exec.Cmd) {}

func gracefulStop(cmd *exec.Cmd) {
	cmd.Process.Kill()
}
