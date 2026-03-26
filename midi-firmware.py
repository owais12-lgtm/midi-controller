import board
import busio
import digitalio
import rotaryio
import analogio
import usb_midi
import adafruit_midi
import time
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange
from adafruit_midi.program_change import ProgramChange

midi = adafruit_midi.MIDI(
    midi_in=usb_midi.ports[0],
    midi_out=usb_midi.ports[1],
    out_channel=0,
    in_channel=0,
)

MIDI_CHANNEL = 0

ROW_PINS = [board.GP4, board.GP3, board.GP2, board.GP1, board.GP0]
COL_PINS = [board.GP9, board.GP8, board.GP7, board.GP6, board.GP5]

rows = []
for pin in ROW_PINS:
    p = digitalio.DigitalInOut(pin)
    p.direction = digitalio.Direction.OUTPUT
    p.value = True
    rows.append(p)

cols = []
for pin in COL_PINS:
    p = digitalio.DigitalInOut(pin)
    p.direction = digitalio.Direction.INPUT
    p.pull = digitalio.Pull.UP
    cols.append(p)

BASE_NOTE = 48

def key_note(row, col):
    return BASE_NOTE + row * 5 + col

VELOCITY = 100
key_state = [[False] * 5 for _ in range(5)]

def scan_matrix():
    for r, row_pin in enumerate(rows):
        row_pin.value = False
        for c, col_pin in enumerate(cols):
            pressed = not col_pin.value
            if pressed and not key_state[r][c]:
                note = key_note(r, c)
                midi.send(NoteOn(note, VELOCITY))
                key_state[r][c] = True
            elif not pressed and key_state[r][c]:
                note = key_note(r, c)
                midi.send(NoteOff(note, 0))
                key_state[r][c] = False
        row_pin.value = True

ENCODER_AB_PINS = [
    (board.GP14, board.GP15),
    (board.GP16, board.GP17),
    (board.GP18, board.GP19),
    (board.GP20, board.GP21),
    (board.GP22, board.GP23),
    (board.GP26, board.GP27),
]

encoders = []
for a, b in ENCODER_AB_PINS:
    encoders.append(rotaryio.IncrementalEncoder(a, b))

encoder_positions = [enc.position for enc in encoders]
encoder_programs = [0] * 6

def scan_encoders():
    for i, enc in enumerate(encoders):
        pos = enc.position
        delta = pos - encoder_positions[i]
        if delta != 0:
            encoder_programs[i] = max(0, min(127, encoder_programs[i] + delta))
            midi.send(ProgramChange(encoder_programs[i]))
            encoder_positions[i] = pos

SLIDER_PINS = [board.GP10, board.GP11, board.GP12, board.GP13]
SLIDER_CC = 7
SLIDER_CHANNELS = [0, 1, 2, 3]
SLIDER_DEADBAND = 200

sliders = [analogio.AnalogIn(pin) for pin in SLIDER_PINS]
slider_last = [None] * 4

def scan_sliders():
    for i, slider in enumerate(sliders):
        raw = slider.value
        cc_val = raw >> 9
        if slider_last[i] is None or abs(raw - slider_last[i]) > SLIDER_DEADBAND:
            midi.send(ControlChange(SLIDER_CC, cc_val), channel=SLIDER_CHANNELS[i])
            slider_last[i] = raw

print("MIDI Controller ready.")

while True:
    scan_matrix()
    scan_encoders()
    scan_sliders()
    time.sleep(0.001)
