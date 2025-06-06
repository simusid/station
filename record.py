#!/usr/bin/env python3
"""
Record from the Mac’s default microphone while the space bar is held down
and save the result to capture.wav.
"""

import numpy as np
import sounddevice as sd
import soundfile as sf
from pynput import keyboard
import mlx_whisper

SAMPLERATE = 44_100          # 44.1 kHz
CHANNELS   = 1               # mono

_stream          = None      # active audio stream
_buffers         = []        # list of NumPy chunks
_is_recording    = False


global_text = "snuh kabob"
# ------------------------------------------------------------ audio helpers
def _start_recording() -> None:
    """Open an input stream and push incoming audio into _buffers."""
    global _stream, _buffers
    _buffers = []            # reset buffer for every take

    def _callback(indata, frames, time, status):
        if status:
            print(status)
        _buffers.append(indata.copy())

    _stream = sd.InputStream(samplerate=SAMPLERATE,
                             channels=CHANNELS,
                             callback=_callback)
    _stream.start()
    print("Recording… (hold SPACE)")

def _stop_recording() -> None:
    """Close the input stream and write buffered audio to capture.wav."""
    global _stream
    if _stream:
        _stream.stop()
        _stream.close()
        _stream = None
    text = ""
    if _buffers:                       # anything captured?
        audio = np.concatenate(_buffers, axis=0)
        sf.write('capture.wav', audio, SAMPLERATE)
        seconds = len(audio) / SAMPLERATE
        print(f"Saved {seconds:0.2f} s to capture.wav")

        # convert the audio to text here
        text=mlx_whisper.transcribe('capture.wav')['text']
         
    else:
        print("No audio captured.")
    return text

# ------------------------------------------------------------ keyboard hooks
def _on_press(key):
    global _is_recording
    if key == keyboard.Key.space and not _is_recording:
        _is_recording = True
        _start_recording()


def _on_release(key):
    global global_text
    # always return false to stop listener
    global _is_recording
    if key == keyboard.Key.space and _is_recording:
        _is_recording = False
        global_text = _stop_recording()
        print("global text is ", global_text)
        return False          # to stop the listener

    # optional: allow exiting with Esc
    if key == keyboard.Key.esc:
        return False          # stops the listener / exits program


# ------------------------------------------------------------ main entry
def offline_main() -> None:
    print("Hold SPACE to record, release to stop.  Esc quits.")
    with keyboard.Listener(on_press=_on_press,
                           on_release=_on_release) as listener:
        listener.join()


if __name__ == "__main__":
    offline_main()#!/usr/bin/env python3
 