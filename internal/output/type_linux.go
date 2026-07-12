//go:build linux

package output

import (
	"context"
	"encoding/binary"
	"fmt"
	"os"
	"syscall"
	"time"
)

const (
	evKey        = 1
	evSyn        = 0
	synReport    = 0
	uiSetEvbit   = 0x40045564
	uiSetKeybit  = 0x40045565
	uiDevCreate  = 0x5501
	uiDevDestroy = 0x5502
	keyLeftCtrl  = 29
	keyLeftShift = 42
	keyU         = 22
	keyEnter     = 28
)

type uinputUserDev struct {
	Name         [80]byte
	ID           [4]uint16
	FFEffectsMax uint32
	AbsMax       [64]int32
	AbsMin       [64]int32
	AbsFuzz      [64]int32
	AbsFlat      [64]int32
}

type inputEvent struct {
	Time  syscall.Timeval
	Type  uint16
	Code  uint16
	Value int32
}

func typeLinux(ctx context.Context, text string) error {
	device, err := os.OpenFile("/dev/uinput", os.O_WRONLY|syscall.O_NONBLOCK, 0)
	if err != nil {
		return err
	}
	defer device.Close()
	if err := ioctl(device.Fd(), uiSetEvbit, evKey); err != nil {
		return err
	}
	for code := 1; code <= 255; code++ {
		if err := ioctl(device.Fd(), uiSetKeybit, uintptr(code)); err != nil {
			return err
		}
	}
	var definition uinputUserDev
	copy(definition.Name[:], "lkj virtual keyboard")
	definition.ID = [4]uint16{3, 0x1, 0x1, 1}
	if err := binary.Write(device, binary.LittleEndian, &definition); err != nil {
		return err
	}
	if err := ioctl(device.Fd(), uiDevCreate, 0); err != nil {
		return err
	}
	defer ioctl(device.Fd(), uiDevDestroy, 0)
	time.Sleep(100 * time.Millisecond)

	for _, r := range text {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
		}
		code, shift, ok := linuxKey(r)
		if !ok {
			if err := typeUnicode(device, r); err != nil {
				return err
			}
			continue
		}
		if shift {
			if err := keyEvent(device, keyLeftShift, 1); err != nil {
				return err
			}
		}
		if err := keyPress(device, code); err != nil {
			return err
		}
		if shift {
			if err := keyEvent(device, keyLeftShift, 0); err != nil {
				return err
			}
		}
	}
	return nil
}

func typeUnicode(device *os.File, r rune) error {
	for _, event := range []struct{ code, value int }{{keyLeftCtrl, 1}, {keyLeftShift, 1}, {keyU, 1}, {keyU, 0}, {keyLeftShift, 0}, {keyLeftCtrl, 0}} {
		if err := keyEvent(device, event.code, event.value); err != nil {
			return err
		}
	}
	for _, digit := range fmt.Sprintf("%x", r) {
		code, shift, _ := linuxKey(digit)
		if shift {
			return fmt.Errorf("unexpected shifted unicode digit %q", digit)
		}
		if err := keyPress(device, code); err != nil {
			return err
		}
	}
	return keyPress(device, keyEnter)
}

func keyPress(device *os.File, code int) error {
	if err := keyEvent(device, code, 1); err != nil {
		return err
	}
	return keyEvent(device, code, 0)
}

func keyEvent(device *os.File, code, value int) error {
	if err := binary.Write(device, binary.LittleEndian, inputEvent{Type: evKey, Code: uint16(code), Value: int32(value)}); err != nil {
		return err
	}
	return binary.Write(device, binary.LittleEndian, inputEvent{Type: evSyn, Code: synReport})
}

func ioctl(fd uintptr, request uintptr, value uintptr) error {
	_, _, errno := syscall.Syscall(syscall.SYS_IOCTL, fd, request, value)
	if errno != 0 {
		return errno
	}
	return nil
}

func linuxKey(r rune) (code int, shift bool, ok bool) {
	if r >= 'A' && r <= 'Z' {
		r += 'a' - 'A'
		shift = true
	}
	if r >= 'a' && r <= 'z' {
		codes := [...]int{30, 48, 46, 32, 18, 33, 34, 35, 23, 36, 37, 38, 50, 49, 24, 25, 16, 19, 31, 20, 22, 47, 17, 45, 21, 44}
		return codes[r-'a'], shift, true
	}
	digits := map[rune]int{'1': 2, '2': 3, '3': 4, '4': 5, '5': 6, '6': 7, '7': 8, '8': 9, '9': 10, '0': 11}
	if code, ok := digits[r]; ok {
		return code, false, true
	}
	keys := map[rune]struct {
		code  int
		shift bool
	}{
		' ': {57, false}, '\n': {28, false}, '\t': {15, false},
		'-': {12, false}, '_': {12, true}, '=': {13, false}, '+': {13, true},
		'[': {26, false}, '{': {26, true}, ']': {27, false}, '}': {27, true},
		';': {39, false}, ':': {39, true}, '\'': {40, false}, '"': {40, true},
		'`': {41, false}, '~': {41, true}, '\\': {43, false}, '|': {43, true},
		',': {51, false}, '<': {51, true}, '.': {52, false}, '>': {52, true},
		'/': {53, false}, '?': {53, true}, '!': {2, true}, '@': {3, true},
		'#': {4, true}, '$': {5, true}, '%': {6, true}, '^': {7, true},
		'&': {8, true}, '*': {9, true}, '(': {10, true}, ')': {11, true},
	}
	key, ok := keys[r]
	return key.code, key.shift, ok
}
