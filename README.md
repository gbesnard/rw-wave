# Introduction

Learning project to get a feeling about how audio is digitized, stored, and manipulated.

Simple python script which:

- Import a .wav file and instantiate a Python object with it
- Convert .wav file to different bit depths
- Convert stereo .wav to mono
- Change dB gain of a .wav
- Bandpass filter using FFT (narrowband and wideband)
- Display audio signal to useless xkcd style plots

# Usage

```
python rw_wave.py
```

Python dependencies in `requirements.txt` files

The script take a file named signal.wav in entry. It must be a .wav in PCM format, with 1 or 2 channels maximum, a bit depth of 8, 16, 24 or 32 and any sample rate should do

# Tools

## Soxi

Give info about .wav file (sampling rate, precision, ...)

    soxi signal.wav

## Play

Play sound from CLI

    play signal.wav

# Audacity

Swiss army knife tool for audio files (view, manipulation, conversion)

# Todo

- Add some filtering using a "real" filter such as Butterworth
- Read more than two channels using FMT WAVEFORMATEXTENSIBLE format

# Resources

http://soundfile.sapp.org/doc/WaveFormat/

https://gist.github.com/chief7/54873e6e7009a087180902cb1f4e27be

https://www.nasa.gov/mission_pages/apollo/apollo11_audio.html

https://www.nasa.gov/connect/sounds/index.html

https://www2.cs.uic.edu/~i101/SoundFiles/

https://www.mmsp.ece.mcgill.ca/Documents/AudioFormats/WAVE/Samples.html

https://stackoverflow.com/questions/1149092/how-do-i-attenuate-a-wav-file-by-a-given-decibel-value

https://stackoverflow.com/questions/70825086/python-lowpass-filter-with-only-numpy

https://bigsoundbank.com
