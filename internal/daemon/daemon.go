package daemon

import (
	"bufio"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/zo-ll/lkj/internal/audio"
	"github.com/zo-ll/lkj/internal/output"
	"github.com/zo-ll/lkj/internal/stt"
)

type Recording interface {
	Stop(context.Context) (string, error)
	Cancel()
}

type StartRecording func(context.Context, string) (Recording, error)
type Notify func(summary, body string)

type Response struct {
	State   string `json:"state"`
	Message string `json:"message,omitempty"`
	Text    string `json:"text,omitempty"`
	Error   string `json:"error,omitempty"`
}

type Server struct {
	Socket         string
	Device         string
	Transcriber    stt.Transcriber
	Sink           output.Sink
	StartRecording StartRecording
	Notify         Notify

	mu       sync.Mutex
	state    string
	session  Recording
	listener net.Listener
	cancel   context.CancelFunc
}

func DefaultSocket() string {
	if path := os.Getenv("LKJ_SOCKET"); path != "" {
		return path
	}
	if dir := os.Getenv("XDG_RUNTIME_DIR"); dir != "" {
		return filepath.Join(dir, "lkj.sock")
	}
	dir, err := os.UserCacheDir()
	if err != nil || dir == "" {
		dir = os.TempDir()
	}
	return filepath.Join(dir, "lkj", "lkj.sock")
}

func (s *Server) Serve(ctx context.Context) error {
	if s.Socket == "" {
		s.Socket = DefaultSocket()
	}
	if s.Transcriber == nil || s.Sink == nil {
		return errors.New("daemon requires a transcriber and sink")
	}
	if s.StartRecording == nil {
		s.StartRecording = func(ctx context.Context, device string) (Recording, error) {
			return audio.Start(ctx, device)
		}
	}
	if err := os.MkdirAll(filepath.Dir(s.Socket), 0o700); err != nil {
		return err
	}
	if err := removeStaleSocket(s.Socket); err != nil {
		return err
	}
	listener, err := net.Listen("unix", s.Socket)
	if err != nil {
		return err
	}
	if err := os.Chmod(s.Socket, 0o600); err != nil {
		listener.Close()
		return err
	}
	defer os.Remove(s.Socket)
	defer listener.Close()
	ctx, s.cancel = context.WithCancel(ctx)
	s.listener = listener
	s.state = "idle"
	s.notify("lkj ready", "Press your toggle shortcut to start recording")
	go func() {
		<-ctx.Done()
		listener.Close()
	}()

	for {
		conn, err := listener.Accept()
		if err != nil {
			if ctx.Err() != nil {
				s.cancelRecording()
				return nil
			}
			return err
		}
		go s.handle(ctx, conn)
	}
}

func (s *Server) handle(ctx context.Context, conn net.Conn) {
	defer conn.Close()
	_ = conn.SetDeadline(time.Now().Add(10 * time.Minute))
	command, err := bufio.NewReader(conn).ReadString('\n')
	if err != nil {
		writeResponse(conn, Response{State: s.currentState(), Error: err.Error()})
		return
	}
	command = strings.TrimSpace(command)
	var response Response
	switch command {
	case "toggle":
		response = s.toggle(ctx)
	case "status":
		response = Response{State: s.currentState()}
	case "stop":
		response = Response{State: "stopping", Message: "daemon stopping"}
		s.notify("lkj stopped", "Voice recording daemon stopped")
		defer s.cancel()
	case "cancel":
		response = s.cancelRecording()
	default:
		response = Response{State: s.currentState(), Error: fmt.Sprintf("unknown daemon command %q", command)}
	}
	writeResponse(conn, response)
}

func (s *Server) toggle(ctx context.Context) Response {
	s.mu.Lock()
	switch s.state {
	case "idle":
		session, err := s.StartRecording(ctx, s.Device)
		if err != nil {
			s.mu.Unlock()
			s.notify("lkj error", err.Error())
			return Response{State: "idle", Error: err.Error()}
		}
		s.session = session
		s.state = "recording"
		s.mu.Unlock()
		s.notify("Recording", "Press the toggle shortcut again to stop")
		return Response{State: "recording", Message: "recording started"}
	case "recording":
		session := s.session
		s.session = nil
		s.state = "transcribing"
		s.mu.Unlock()
		s.notify("Transcribing", "Converting speech to text")
		return s.finish(ctx, session)
	default:
		state := s.state
		s.mu.Unlock()
		return Response{State: state, Message: "busy"}
	}
}

func (s *Server) finish(ctx context.Context, session Recording) Response {
	stopCtx, cancel := context.WithTimeout(ctx, 15*time.Second)
	path, err := session.Stop(stopCtx)
	cancel()
	if err != nil {
		s.setIdle()
		s.notify("lkj error", err.Error())
		return Response{State: "idle", Error: err.Error()}
	}
	defer os.Remove(path)
	text, err := s.Transcriber.Transcribe(ctx, path)
	if err == nil {
		text = strings.TrimSpace(text)
		if text != "" {
			err = s.Sink.Send(ctx, text)
		}
	}
	s.setIdle()
	if err != nil {
		s.notify("lkj error", err.Error())
		return Response{State: "idle", Error: err.Error()}
	}
	if text == "" {
		s.notify("No speech detected", "Clipboard was not changed")
		return Response{State: "idle", Message: "no speech detected"}
	}
	s.notify("Copied to clipboard", "Your transcript is ready to paste")
	return Response{State: "idle", Message: "transcript delivered", Text: text}
}

func (s *Server) cancelRecording() Response {
	s.mu.Lock()
	if s.state != "recording" || s.session == nil {
		state := s.state
		s.mu.Unlock()
		return Response{State: state, Message: "nothing to cancel"}
	}
	session := s.session
	s.session = nil
	s.state = "idle"
	s.mu.Unlock()
	session.Cancel()
	s.notify("Recording cancelled", "Clipboard was not changed")
	return Response{State: "idle", Message: "recording cancelled"}
}

func (s *Server) notify(summary, body string) {
	if s.Notify != nil {
		s.Notify(summary, body)
	}
}

func (s *Server) setIdle() {
	s.mu.Lock()
	s.state = "idle"
	s.mu.Unlock()
}

func (s *Server) currentState() string {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.state == "" {
		return "starting"
	}
	return s.state
}

func Send(ctx context.Context, socket, command string) (Response, error) {
	if socket == "" {
		socket = DefaultSocket()
	}
	dialer := net.Dialer{}
	conn, err := dialer.DialContext(ctx, "unix", socket)
	if err != nil {
		return Response{}, fmt.Errorf("connect to lkj daemon at %s: %w", socket, err)
	}
	defer conn.Close()
	if deadline, ok := ctx.Deadline(); ok {
		_ = conn.SetDeadline(deadline)
	}
	if _, err := fmt.Fprintln(conn, command); err != nil {
		return Response{}, err
	}
	var response Response
	if err := json.NewDecoder(conn).Decode(&response); err != nil {
		return Response{}, err
	}
	return response, nil
}

func writeResponse(conn net.Conn, response Response) {
	_ = json.NewEncoder(conn).Encode(response)
}

func removeStaleSocket(path string) error {
	if _, err := os.Stat(path); errors.Is(err, os.ErrNotExist) {
		return nil
	} else if err != nil {
		return err
	}
	conn, err := net.DialTimeout("unix", path, 200*time.Millisecond)
	if err == nil {
		conn.Close()
		return fmt.Errorf("lkj daemon is already listening at %s", path)
	}
	return os.Remove(path)
}
