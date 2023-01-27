import matplotlib.pyplot as plt
import numpy as np
from read_wave import read_wave_raw

def plot_data(data_1, data_2):
    xpoints_1 = np.arange(len(data_1))
    ypoints_1 = np.array(data_1).astype(np.int16)

    xpoints_2 = np.arange(len(data_2))
    ypoints_2 = data_2

    fig, axs = plt.subplots(2)
    fig.suptitle('Channel 1 and 2')
    axs[0].plot(xpoints_1, ypoints_1)
    axs[1].plot(xpoints_2, ypoints_2)
    plt.show()


def main():
    databytes, nchannels, samplerate, dtype = read_wave_raw("2023-01-27-11-02-50.wav")    
    print("nchannels: %s" % (nchannels))
    print("samplerate: %s Hz" % (samplerate))
    print("dtype: %s bits per sample" % (dtype))

#    data = list(databytes)
    data = databytes
    print("data size: %s bytes" % (len(data)))

    # Check that each channels has the same number of bytes
    assert ((len(data) / nchannels) % 2) == 0

    chan_1_data = []
    chan_2_data = []
    # chans_data = np.zeros(((len(data) // nchannels), nchannels))
    sample_size = dtype // 8 * nchannels
    print("sample size: %s bytes" % (sample_size))

    for sample_idx in range(len(data) // sample_size):
        # np.append(chans_data[0], [data[sample_idx * 4 + 0], data[sample_idx * 4 + 1]])
        tmpbytes = [data[sample_idx * 4 + 0], data[sample_idx * 4 + 1]]
        chan_1_data.append(int.from_bytes(tmpbytes, byteorder='little'))
        tmpbytes = [data[sample_idx * 4 + 2], data[sample_idx * 4 + 3]]
        chan_2_data.append(int.from_bytes(tmpbytes, byteorder='little'))
        # chan_1_data.append(data[sample_idx * 4 + 0])
        # chan_1_data.append(data[sample_idx * 4 + 1])
        # chan_2_data.append(data[sample_idx * 4 + 2])
        # chan_2_data.append(data[sample_idx * 4 + 3])

    print(len(chan_1_data))
    print(len(chan_2_data))
        # (bad, good)[x in goodvals].append(x)
    # print("sample 1, chan 1, data: %d", data[0], data[1])
    # print("sample 1, chan 2, data: %d", data[2], data[4])

    plot_data(chan_1_data, chan_2_data)

if __name__ == "__main__":
    main()
