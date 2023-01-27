import matplotlib.pyplot as plt
import numpy as np
import logging
from rw_wave import *

def plot_signal_2_channels(data_1, data_2, 
                           dtype_1, dtype_2, 
                           samplerate, sharey,
                           filename, suptitle):

    assert dtype_1 == 32 or dtype_1 == 24 or dtype_1 == 16 or dtype_1 == 8
    assert dtype_2 == 32 or dtype_2 == 24 or dtype_2 == 16 or dtype_2 == 8

    assert(len(data_1), len(data_2))
    n = len(data_1)
    t = n // samplerate

    xpoints = np.linspace(0, t, n);

    """
    /!\ When samples are represented with 8-bits, 
        they are specified as unsigned values. 
        All other sample bit-sizes are specified as signed values.
    """
    if (dtype_1 == 8):
        ypoints_1 = np.array(data_1).astype(np.uint8)
    else: 
        ypoints_1 = np.array(data_1).astype(np.int32)

    if (dtype_2 == 8):
        ypoints_2 = np.array(data_2).astype(np.uint8)
    else:
        ypoints_2 = np.array(data_2).astype(np.int32)

    with plt.xkcd():
        fig, axs = plt.subplots(2, sharex=True, sharey=sharey)
        fig.suptitle(suptitle)
        axs[0].plot(xpoints, ypoints_1, "b", linewidth=0.2)
        axs[1].plot(xpoints, ypoints_2, "g", linewidth=0.2)
        plt.xlabel("time(s)")
        plt.ylabel("amplitude")
        plt.savefig(filename, dpi=100)
        plt.show()
        plt.close()


def main():
    # disable font warning for matplotlib
    logging.getLogger("matplotlib.font_manager").disabled = True

    print("\nread wave file signal.wav...\n")

    data, nchannels, samplerate, dtype = read_wave_raw("signal.wav")

    # check that each channels has the same number of bytes
    # assert ((len(data) / nchannels) % 2) == 0

    chan_1_data_int = []
    chan_2_data_int = []
    chan_1_data_bytes_array = bytearray() # use bytearray instead of bytestring for performance
    sample_size = dtype // 8 * nchannels

    print("number of channels: %s" % (nchannels))
    print("       sample rate: %s Hz" % (samplerate))
    print("         bit depth: %s bits per sample" % (dtype))
    print("         data size: %s bytes" % (len(data)))
    print("       sample size: %s bytes" % (sample_size))

    print("\nbuild an array for each channel data...")
    assert nchannels <= 2
    nb_samples = len(data) // sample_size
    bytes_per_sample = dtype // 8

    for sample_idx in range(nb_samples):
        sample_offset = sample_idx * sample_size

        tmpbytes_1 = data[(sample_offset + 0):(sample_offset + bytes_per_sample)]
        chan_1_data_bytes_array.extend(tmpbytes_1)
        chan_1_data_int.append(int.from_bytes(tmpbytes_1, byteorder="little", signed=True))

        if nchannels > 1:
            tmpbytes_2 = data[(sample_offset + bytes_per_sample):(sample_offset + bytes_per_sample * 2)]
            chan_2_data_int.append(int.from_bytes(tmpbytes_2, byteorder="little", signed=True))

        if sample_idx % 100000 == 0 or sample_idx == nb_samples - 1:
            print("%d/%d samples" % (sample_idx, nb_samples - 1))

    # convert back bytearray to bytestring
    chan_1_data_bytes = bytes(chan_1_data_bytes_array)

    if nchannels > 1:
        plot_signal_2_channels(chan_1_data_int, chan_2_data_int, 
                               dtype, dtype, 
                               samplerate, True,
                               "signal-channels.png", "Channels 1 and 2")

    print("\ncopy signal.wav into signal-copy.wav...")
    write_wave_raw("signal-copy.wav", nchannels, dtype, samplerate, data)

    print("\nexport signal.wav channel 1 to signal-chan1.wav...")
    write_wave_raw("signal-chan1.wav", 1, dtype, samplerate, chan_1_data_bytes)

    if dtype != 16:
        print("cannot yet convert from 24 or 32 to 8 bits, exiting...")
        exit(1)

    print("\ndecrease signal-chan1.wav bit depth from 16 to 8")
    print("and export it in signal-8bits.wav...")

    """
    Scale our 16 bits range to our new 8 bit range.
    /!\ When samples are represented with 8-bits, 
        they are specified as unsigned values.
        All other sample bit-sizes are specified as signed values.
    """
    OldMax = 32767
    OldMin = -32768
    NewMin = 0
    NewMax = 255
    OldRange = (OldMax - OldMin)  
    NewRange = (NewMax - NewMin)  
    eightbits_data_bytes = b""
    eightbits_data_int = []
    for sample in chan_1_data_int:
        sample_scaled = (((sample - OldMin) * NewRange) // OldRange) + NewMin
        eightbits_data_int.append(sample_scaled)
        eightbits_data_bytes += sample_scaled.to_bytes(1, "little")

    write_wave_raw("signal-8bits.wav", 1, 8, samplerate, eightbits_data_bytes)
    plot_signal_2_channels(chan_1_data_int, eightbits_data_int, 
                           dtype, 8, 
                           samplerate, False,
                           "signal-16-8bits.png", "Signal 16 and 8 bits")

if __name__ == "__main__":
    main()

