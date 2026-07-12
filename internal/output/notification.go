package output

import (
	"os/exec"
	"runtime"
)

// Notify displays a best-effort desktop notification. Notification failures
// never interrupt recording or transcription.
func Notify(summary, body string) {
	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "linux":
		cmd = exec.Command("notify-send", "--app-name=lkj", "--icon=audio-input-microphone", summary, body)
	case "darwin":
		script := `on run argv
display notification (item 2 of argv) with title (item 1 of argv)
end run`
		cmd = exec.Command("osascript", "-e", script, summary, body)
	case "windows":
		return
	default:
		return
	}
	_ = cmd.Run()
}

func CheckNotifications() error {
	switch runtime.GOOS {
	case "linux":
		_, err := exec.LookPath("notify-send")
		return err
	case "darwin":
		_, err := exec.LookPath("osascript")
		return err
	default:
		return nil
	}
}
