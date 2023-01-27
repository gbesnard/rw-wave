import matplotlib.pyplot as plt
import numpy as np
from rw_wave import *


def plot_data(data_1, data_2, samplerate, dtype):
    assert len(data_1) == len(data_2)
    assert dtype == 16 # only handle 16 bits depth for now

    n = len(data_1)
    t = n // samplerate

    xpoints = np.linspace(0, t, n);

    ypoints_1 = np.array(data_1).astype(np.int16)

    ypoints_2 = np.array(data_2).astype(np.int16)
    with plt.xkcd():
        fig, axs = plt.subplots(2, sharex=True, sharey=True)
        fig.suptitle('Channel 1 and 2')
        axs[0].plot(xpoints, ypoints_1, linewidth=0.5)
        axs[1].plot(xpoints, ypoints_2, linewidth=0.5)
        plt.xlabel('time(s)')
        plt.ylabel('amplitude')
        fig.canvas.manager.full_screen_toggle()
        plt.show()


def main():
    data, nchannels, samplerate, dtype = read_wave_raw("in.wav")    
    print("nchannels: %s" % (nchannels))
    print("samplerate: %s Hz" % (samplerate))
    print("dtype: %s bits per sample" % (dtype))
    print("data size: %s bytes" % (len(data)))

    # check that each channels has the same number of bytes
    assert ((len(data) / nchannels) % 2) == 0

    chan_1_data = []
    chan_2_data = []
    sample_size = dtype // 8 * nchannels
    print("sample size: %s bytes" % (sample_size))

    # build an array for each channel data
    for sample_idx in range(len(data) // sample_size):
        sample_offset = sample_idx * sample_size
        tmpbytes_1 = data[(sample_offset + 0):(sample_offset + 2)]
        chan_1_data.append(int.from_bytes(tmpbytes_1, byteorder='little'))
        tmpbytes_2 = data[(sample_offset + 2):(sample_offset + 4)]
        chan_2_data.append(int.from_bytes(tmpbytes_2, byteorder='little'))

    write_wave_raw("out.wav", data)
    plot_data(chan_1_data, chan_2_data, samplerate, dtype)

if __name__ == "__main__":
    main()

