import matplotlib.pyplot as plt
import numpy as np
import logging
from rw_wave import *

class Wave:
    def __init__(self):
        print("")

    def init_from_file(self, filename):
        with open(filename, "rb") as wav:
            """ RIFF-Header: 
            'RIFF' - 4 bytes
            file size - 4 bytes
            'WAVE' - 4 bytes
            """
            riff_header = wav.read(12)
            riff, filesize, wave = struct.unpack("<4sI4s", riff_header)

            assert riff.decode("utf-8") == "RIFF"
            assert wave.decode("utf-8") == "WAVE"

            """
            Format header:
            'fmt ' - 4 bytes
            header length - 4 bytes
            format tag - 2 bytes (only PCM supported here)
            channels - 2 bytes
            sample rate - 4 bytes
            bytes per second - 4 bytes
            block align - 2 bytes
            bits per sample - 2 bytes
            """
            fmt_header = wav.read(24)
            fmt_header_data = struct.unpack("<4sIHHIIHH", fmt_header)
            _, _, fmt_tag, nchannels, samplerate, _, block_align, dtype = fmt_header_data
            assert fmt_tag == 1 # only PCM supported

            """
            Data part
            'data' - 4 bytes, header
            len of data - 4 bytes
            """
            data_header = wav.read(8)
            head, data_len = struct.unpack("<4sI", data_header)

            assert head.decode("utf-8") == "data"

            data = bytearray()

            while True:
                chunk = wav.read(samplerate)
                data.extend(chunk)

                if len(chunk) < samplerate or len(data) >= data_len:
                    # it's possible to encounter another data section you should handle it
                    break

            # check that each channels has the same number of bytes
            assert ((len(data) / nchannels) % 2) == 0

            self.data_bytes = bytes(data)
            self.nchannels = nchannels
            self.samplerate = samplerate
            self.dtype = dtype
            self.samplesize = dtype // 8 * nchannels

            print("\nbuild an array for each channel data...")
            self.get_data_foreach_channels()


    """
    Credit: method is modified code snippet from 
    https://gist.github.com/chief7/54873e6e7009a087180902cb1f4e27be
    """
    def save_to_file(self, filename, chan1_only): 
        data = self.data_bytes
        nchans = self.nchannels

        if chan1_only == True:
            data = self.chan_1_data_bytes
            nchans = 1

        """
        Data part
        'data' - 4 bytes, header
        len of data - 4 bytes
        """
        data_header = struct.pack("<4sI", bytes("data", "utf-8"), len(data))

        """
        Format header:
        'fmt ' - 4 bytes
        header length - 4 bytes
        format tag - 2 bytes (only PCM supported here)
        channels - 2 bytes
        sample rate - 4 bytes
        bytes per second - 4 bytes
        block align - 2 bytes
        bits per sample - 2 bytes
        """
        fmt = bytes("fmt ", "utf-8")
        header_length = 16
        fmt_tag = 1
        block_align = (self.dtype * nchans) // 8
        bytes_per_second = (self.samplerate * self.dtype * nchans) // 8

        fmt_header = struct.pack("<4sIHHIIHH", fmt, header_length, fmt_tag, 
                                 nchans, self.samplerate, bytes_per_second, 
                                 block_align, self.dtype)

        """ RIFF-Header: 
        'RIFF' - 4 bytes
        'file size' - 4 bytes
        'WAVE' - 4 bytes
        """
        filesize = 4 + len(fmt_header) + len(data_header) + len(data) 
        riff_header = struct.pack("<4sI4s", bytes("RIFF", "utf-8"), filesize, bytes("WAVE", "utf-8"))

        with open(filename, "wb") as wav:
            wav.write(riff_header)
            wav.write(fmt_header)
            wav.write(data_header)
            wav.write(data)


    def plot_signal(self, filename, suptitle, chan1_only):
        nchans = self.nchannels
        if chan1_only == True:
            nchans = 1
        data_1 = self.chan_1_data_int
        data_2 = self.chan_2_data_int

        assert nchans <= 2
        assert self.dtype == 32 or self.dtype == 24 or self.dtype == 16 or self.dtype == 8
        assert nchans == 1 or len(data_1) == len(data_2)

        n = len(data_1)
        t = n // self.samplerate

        xpoints = np.linspace(0, t, n);

        with plt.xkcd():
            fig, axs = plt.subplots(nchans, sharex=True, sharey=True)
            fig.suptitle(suptitle)
            """
            /!\ When samples are represented with 8-bits, 
                they are specified as unsigned values. 
                All other sample bit-sizes are specified as signed values.
            """
            if (self.dtype == 8):
                ypoints_1 = np.array(data_1).astype(np.uint8)
                ypoints_2 = np.array(data_2).astype(np.uint8)
            else: 
                ypoints_1 = np.array(data_1).astype(np.int32)
                ypoints_2 = np.array(data_2).astype(np.int32)

            if nchans == 1:
                axs.plot(xpoints, ypoints_1, "b", linewidth=0.2)
            else:
                axs[0].plot(xpoints, ypoints_1, "b", linewidth=0.2)
                axs[1].plot(xpoints, ypoints_2, "g", linewidth=0.2)

            plt.xlabel("time(s)")
            plt.ylabel("amplitude")
            plt.savefig("%s" % (filename), dpi=100)
            plt.show()
            plt.close()


    def print_info(self):
        print("number of channels: %s" % (self.nchannels))
        print("       sample rate: %s Hz" % (self.samplerate))
        print("         bit depth: %s bits per sample" % (self.dtype))
        print("         data size: %s bytes" % (len(self.data_bytes)))
        print("       sample size: %s bytes" % (self.samplesize))


    def write_and_plot(self, chan1_only=False):
        nchans = 2
        chan_1_data_int = self.chan_1_data_int
        chan_2_data_int = self.chan_2_data_int
        data_bytes = self.data_bytes

        if chan1_only == True:
            nchans = 1
            chan_2_data_int = []
            data_bytes = self.chan_1_data_bytes

        output_folder = "output"
        filename = "signal-%dbits-%dchan" % (self.dtype, nchans)
        filename_png = "%s.png" % (filename)
        filename_wav = "%s.wav" % (filename)

        print("\nwrite %s..." % filename_wav)
        self.save_to_file("%s/%s" % (output_folder, filename_wav), chan1_only)

        print("plot %s..." % filename_png)
        self.plot_signal("%s/%s" % (output_folder, filename_png), filename, chan1_only)


    def get_data_foreach_channels(self):
        assert self.nchannels <= 2
        nb_samples = len(self.data_bytes) // self.samplesize
        bytes_per_sample = self.dtype // 8
        
        self.chan_1_data_int = []
        self.chan_2_data_int = []
        self.chan_1_data_bytes = b""
        self.chan_2_data_bytes = b""

        # use bytearray instead of bytestring for performance
        chan_1_data_bytes_array = bytearray() # use bytearray instead of bytestring for performance
        chan_2_data_bytes_array = bytearray() 

        for sample_idx in range(nb_samples):
            sample_offset = sample_idx * self.samplesize

            tmpbytes_1 = self.data_bytes[(sample_offset + 0):(sample_offset + bytes_per_sample)]
            chan_1_data_bytes_array.extend(tmpbytes_1)
            self.chan_1_data_int.append(int.from_bytes(tmpbytes_1, byteorder="little", signed=True))

            if self.nchannels > 1:
                tmpbytes_2 = self.data_bytes[(sample_offset + bytes_per_sample):(sample_offset + bytes_per_sample * 2)]
                chan_2_data_bytes_array.extend(tmpbytes_2)
                self.chan_2_data_int.append(int.from_bytes(tmpbytes_2, byteorder="little", signed=True))

            if sample_idx % 100000 == 0 or sample_idx == nb_samples - 1:
                print("%d/%d samples" % (sample_idx, nb_samples - 1))

        print("")

        # convert back bytearray to bytestring
        self.chan_1_data_bytes = bytes(chan_1_data_bytes_array)
        self.chan_2_data_bytes = bytes(chan_2_data_bytes_array)



def convert_bit_and_write_and_plot(from_dtype, to_dtype, nchannels, samplerate, data_old,
                                   chan_1_data_int_old, chan_2_data_int_old, 
                                   chan_1_data_bytes_old, chan_2_data_bytes_old):
    assert from_dtype >= to_dtype
    assert from_dtype == 32 or from_dtype == 24 or from_dtype == 16 or from_dtype == 8
    assert to_dtype   == 32 or to_dtype   == 24 or to_dtype   == 16 or to_dtype   == 8

    if from_dtype < to_dtype:
        print("cannot convert from %d to %d bits, nothing to do" % (from_dtype, to_dtype))
        return
    elif from_dtype == to_dtype:
        print("already at the right bit depth of %d" % (from_dtype))            
        data = data_old
        chan_1_data_int = chan_1_data_int_old
        chan_2_data_int = chan_2_data_int_old
        chan_1_data_bytes = chan_1_data_bytes_old
        chan_2_data_bytes = chan_2_data_bytes_old
    else:
        print("converting from %d to %d bits" % (from_dtype, to_dtype))
        print("TODO")

    write_and_plot(to_dtype, nchannels, chan_1_data_int, chan_2_data_int, data, samplerate)
    if nchannels == 2:
        write_and_plot(to_dtype, 1, chan_1_data_int, [], chan_1_data_bytes, samplerate)


def main():
    # disable font warning for matplotlib
    logging.getLogger("matplotlib.font_manager").disabled = True

    print("\nread wave file signal.wav...\n")

    # data, nchannels, samplerate, dtype = read_wave_raw("signal.wav")
    wave = Wave()
    wave.init_from_file("signal.wav")
    wave.print_info() 
    wave.write_and_plot(2)
    wave.write_and_plot(1)
       
#    conv_results = convert_bit_depth(dtype, 32, chan_1_data_int, chan_2_data_int, data)
#    if conv_results[0] != -1:
#        write_and_plot(dtype, nchannels, conv_results[1], conv_results[2], conv_results[3], samplerate)
              #    if nchannels == 2:
              #write_and_plot(dtype, 1, conv_results[0], [], chan_1_data_bytes, chan_2_data_bytes, samplerate)
#    convert_bit_and_write_and_plot(wave.dtype, 32, wave.nchannels, wave.samplerate, wave.data_bytes, 
#                                   chan_1_data_int, chan_2_data_int, 
#                                   chan_1_data_bytes, chan_2_data_bytes)

#    write_and_plot(wave.dtype, wave.nchannels, wave.chan_1_data_int, wave.chan_2_data_int, wave.data_bytes, wave.samplerate)
#    if wave.nchannels == 2:
#        write_and_plot(wave.dtype, 1, wave.chan_1_data_int, [], wave.chan_1_data_bytes, wave.samplerate)
    return

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

