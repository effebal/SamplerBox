import time
import rtmidi_python as rtmidi

midiout = rtmidi.MidiOut()
#available_ports = midiout.get_ports()

#if available_ports:
#midiout.open_port(1)
#else:
midiout.open_virtual_port("My virtual output")

note_on = [0x90, 60, 112] # channel 1, middle C, velocity 112
note_off = [0x80, 60, 0]
midiout.send_message(note_on)
time.sleep(0.5)

#midiout.send_message(note_off)

midiout.send_message([0x90, 63, 112])
midiout.send_message([0x90, 64, 90])
midiout.send_message([0x90, 65, 127])
midiout.send_message([0x90, 66, 112])
midiout.send_message([0x90, 67, 112])
midiout.send_message([0x90, 68, 112])
midiout.send_message([0x90, 69, 90])
midiout.send_message([0x90, 70, 127])
midiout.send_message([0x90, 71, 112])
midiout.send_message([0x90, 72, 112])
midiout.send_message([0x90, 73, 112])
midiout.send_message([0x90, 74, 90])
midiout.send_message([0x90, 75, 127])
midiout.send_message([0x90, 76, 112])
midiout.send_message([0x90, 77, 112])

time.sleep(2)
midiout.send_message(note_off)

del midiout
