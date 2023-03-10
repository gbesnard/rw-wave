import matplotlib.pyplot as plt
import numpy as np
import copy
import logging
import struct


class Wave:
    def __init__(self):
        print("")

    def init_from_file(self, filename):
        print("read wave file %s..." % (filename))

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
            # assert ((len(data) / nchannels) % 2) == 0

            self.data_bytes = bytes(data)
            self.nchannels = nchannels
            self.samplerate = samplerate
            self.dtype = dtype
            self.samplesize = dtype // 8 * nchannels

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


    def plot_spectrum(self, filename, suptitle):
        assert self.nchannels == 1

        data_1, _ = self.get_channels_data_int()

        spectrum = np.fft.fft(data_1)
        delta_between_measure_time_s = 1 / self.samplerate
        freq = np.fft.fftfreq(len(data_1), delta_between_measure_time_s)
            
        with plt.xkcd():
            fig, axs = plt.subplots(1)
            fig.suptitle(suptitle)
                
            axs.plot(freq, np.real(spectrum))

            plt.xlabel("frequency (Hz)")
            plt.ylabel("amplitude")
            plt.savefig(filename, dpi=100)
            # plt.show()
            plt.close()

 
    def plot_signal(self, filename, suptitle, chan1_only):
        nchans = self.nchannels
        if chan1_only == True:
            nchans = 1

        data_1, data_2 = self.get_channels_data_int()

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
            # plt.show()
            plt.close()


    def print_info(self):
        print("")
        print("number of channels: %s" % (self.nchannels))
        print("       sample rate: %s Hz" % (self.samplerate))
        print("         bit depth: %s bits per sample" % (self.dtype))
        print("         data size: %s bytes" % (len(self.data_bytes)))
        print("       sample size: %s bytes" % (self.samplesize))


    def write_and_plot(self, output_folder, filename, chan1_only=False):
        filename_png = "%s.png" % (filename)
        filename_wav = "%s.wav" % (filename)

        print("\nwritting %s..." % filename_wav)
        self.save_to_file("%s/%s" % (output_folder, filename_wav), chan1_only)

        print("plotting %s..." % filename_png)
        self.plot_signal("%s/%s" % (output_folder, filename_png), filename, chan1_only)


    def get_data_foreach_channels(self):
        assert self.nchannels <= 2

        nb_samples = len(self.data_bytes) // self.samplesize
        bytes_per_sample = self.dtype // 8
        
        self.chan_1_data_bytes = b""
        self.chan_2_data_bytes = b""

        # use bytearray instead of bytestring for performance
        chan_1_data_bytes_array = bytearray() # use bytearray instead of bytestring for performance
        chan_2_data_bytes_array = bytearray() 

        for sample_idx in range(nb_samples):
            sample_offset = sample_idx * self.samplesize

            tmpbytes_1 = self.data_bytes[(sample_offset + 0):(sample_offset + bytes_per_sample)]
            chan_1_data_bytes_array.extend(tmpbytes_1)

            if self.nchannels > 1:
                tmpbytes_2 = self.data_bytes[(sample_offset + bytes_per_sample):(sample_offset + bytes_per_sample * 2)]
                chan_2_data_bytes_array.extend(tmpbytes_2)

        # convert back bytearray to bytestring
        self.chan_1_data_bytes = bytes(chan_1_data_bytes_array)
        self.chan_2_data_bytes = bytes(chan_2_data_bytes_array)


    # converts channels bytes data to int and return one array for both channels
    def get_channels_data_int(self):
        assert self.nchannels == 1 or len(self.chan_1_data_bytes) == len(self.chan_2_data_bytes)
        chan_1_data_int = []
        chan_2_data_int = []
        byte_depth = self.dtype // 8
        nb_samples = len(self.chan_1_data_bytes) // byte_depth
        for sample_idx in range(nb_samples):
            sample_offset = sample_idx * byte_depth 
            tmpbytes = self.chan_1_data_bytes[(sample_offset):(sample_offset + byte_depth)]
            chan_1_data_int.append(int.from_bytes(tmpbytes, byteorder="little", signed=True))
            tmpbytes = self.chan_2_data_bytes[(sample_offset):(sample_offset + byte_depth)]
            chan_2_data_int.append(int.from_bytes(tmpbytes, byteorder="little", signed=True))

        return chan_1_data_int, chan_2_data_int


    def set_bytes_from_data_int(self, dataint):
        assert self.nchannels == 1

        conv_msg = "setting bytes from data int... "
        print("")
        print(conv_msg, end='')

        """
        /!\ When samples are represented with 8-bits, 
            they are specified as unsigned values.
            All other sample bit-sizes are specified as signed values.
        """
        to_signed = True
        if self.dtype == 8:
            to_signed = False

        from_signed = True
        if self.dtype == 8:
            from_signed = False

        nb_samples = len(self.data_bytes) // self.samplesize
        assert abs(len(dataint) - nb_samples) <= 1

        bytes_per_sample = self.dtype // 8
        new_bytes_array = bytearray()

        # loop through data bytes and use new value

        max_val, min_val = get_max_min_from_dtype(self.dtype)

        for sample_idx in range(nb_samples):
            if (dataint[sample_idx] > max_val):
                dataint[sample_idx] = max_val
            elif (dataint[sample_idx] < min_val):
                dataint[sample_idx] = min_val

            tmpbytes = dataint[sample_idx].to_bytes(bytes_per_sample, 'little', signed=to_signed)
            new_bytes_array.extend(tmpbytes)

            if sample_idx % 100000 == 0 or sample_idx == nb_samples - 1:
                progress_bar(conv_msg, sample_idx + 1, nb_samples)

        print("")

        self.data_bytes = bytes(new_bytes_array)
        
        # update each channels buffer
        self.get_data_foreach_channels()
        
        return 0


    def filter_bandpass(self, band):
        print("\nfiltering bandpass range %d to %d Hz... " % (band[0], band[1]))

        data_1, _ = self.get_channels_data_int()

        spectre = np.fft.fft(data_1)
        delta_between_measure_time_s = 1 / self.samplerate
        freq = np.fft.fftfreq(len(data_1), delta_between_measure_time_s)
            
        # translate high frequency limit from Hz to index
        # TODO use low band
        lowfreq_filter_index = int(band[0] * len(data_1) / self.samplerate)
        highfreq_filter_index = int(band[1] * len(data_1) / self.samplerate)
    
        # inspired from https://stackoverflow.com/questions/70825086/python-lowpass-filter-with-only-numpy
        # high band
        for i in range(highfreq_filter_index + 1, len(spectre) - highfreq_filter_index):
            spectre[i] = 0

        # low band
        for i in range(0, lowfreq_filter_index):
            spectre[i] = 0

        for i in range(len(spectre) - highfreq_filter_index, len(spectre)):
            spectre[i] = 0

        signal_filtered = np.fft.ifft(spectre)
        signal_filtered_int = np.int_(signal_filtered.real)
        self.set_bytes_from_data_int(signal_filtered_int.tolist())

        return 0


    def convert_to_dtype(self, to_dtype):
        assert to_dtype == 32 or to_dtype == 24 or to_dtype == 16 or to_dtype == 8
        
        conv_msg = "converting from bit depth %d to %d... " % (self.dtype, to_dtype)
        print("")
        print(conv_msg, end='')

        if self.dtype < to_dtype:
            print("skipping, won't convert to higher bit depth")
            return -1
        elif self.dtype == to_dtype:
            print("skipping, already at the right bit depth")
            return -1
        else:
            # Scale our bits range to our new bit range.
            """
            /!\ When samples are represented with 8-bits, 
                they are specified as unsigned values.
                All other sample bit-sizes are specified as signed values.
            """
            to_signed = True
            if to_dtype == 8:
                to_signed = False

            from_signed = True
            if self.dtype == 8:
                from_signed = False


            new_max, new_min = get_max_min_from_dtype(to_dtype)
            old_max, old_min = get_max_min_from_dtype(self.dtype)

            old_range = (old_max - old_min)  
            new_range = (new_max - new_min)  
 
            nb_samples = len(self.data_bytes) // self.samplesize
            old_bytes_per_sample = self.dtype // 8
            new_bytes_per_sample = to_dtype // 8

            new_bytes_array = bytearray()

            # loop through data bytes and convert
            for sample_idx in range(nb_samples):
                sample_offset = sample_idx * self.samplesize

                tmpbytes = self.data_bytes[(sample_offset + 0):(sample_offset + old_bytes_per_sample)]
                tmpint = int.from_bytes(tmpbytes, byteorder="little", signed=from_signed)
                tmpintscaled = (((tmpint - old_min) * new_range) // old_range) + new_min
                tmpbytes_scaled = tmpintscaled.to_bytes(new_bytes_per_sample, 'little', signed=to_signed)
                new_bytes_array.extend(tmpbytes_scaled)

                if self.nchannels > 1:
                    tmpbytes = self.data_bytes[(sample_offset + old_bytes_per_sample):(sample_offset + old_bytes_per_sample * 2)]
                    tmpint = int.from_bytes(tmpbytes, byteorder="little", signed=from_signed)
                    tmpintscaled = (((tmpint - old_min) * new_range) // old_range) + new_min
                    tmpbytes_scaled = tmpintscaled.to_bytes(new_bytes_per_sample, 'little', signed=to_signed)
                    new_bytes_array.extend(tmpbytes_scaled)

                
                if sample_idx % 100000 == 0 or sample_idx == nb_samples - 1:
                    progress_bar(conv_msg, sample_idx + 1, nb_samples)

            print("")

            self.data_bytes = bytes(new_bytes_array)
            
            # data conversion done, update info
            self.dtype = to_dtype
            self.samplesize = self.dtype // 8 * self.nchannels

            # update each channels buffer
            self.get_data_foreach_channels()
            
            return 0


    def convert_to_mono(self):
        assert self.nchannels <= 2

        conv_msg = "converting from %d channels to mono..." % (self.nchannels)
        print("")
        print(conv_msg, end='')

        if self.nchannels < 2:
            print("file already has only one channel")
            return -1
        else:
            """
            /!\ When samples are represented with 8-bits, 
                they are specified as unsigned values.
                All other sample bit-sizes are specified as signed values.
            """
            signed = True
            if self.dtype == 8:
                signed = False

            bytes_per_sample = self.dtype // 8
            nb_samples = len(self.data_bytes) // self.samplesize
            new_bytes_array = bytearray()

            # loop through data bytes and convert
            for sample_idx in range(nb_samples):
                sample_offset = sample_idx * self.samplesize

                tmpbytes_c1 = self.data_bytes[(sample_offset + 0):(sample_offset + bytes_per_sample)]
                tmpint_c1 = int.from_bytes(tmpbytes_c1, byteorder="little", signed=signed)
    
                tmpbytes_c2 = self.data_bytes[(sample_offset + bytes_per_sample):(sample_offset + bytes_per_sample * 2)]
                tmpint_c2 = int.from_bytes(tmpbytes_c2, byteorder="little", signed=signed)
    
                tmpint = (tmpint_c1 + tmpint_c2) // 2
                tmpbytes = tmpint.to_bytes(bytes_per_sample, 'little', signed=signed)
                new_bytes_array.extend(tmpbytes)

                if sample_idx % 100000 == 0 or sample_idx == nb_samples - 1:
                    progress_bar(conv_msg, sample_idx + 1, nb_samples)
            
            print("")

            self.data_bytes = bytes(new_bytes_array)

            # data conversion done, update info
            self.nchannels = 1
            self.samplesize = self.dtype // 8 * self.nchannels

            # update each channels buffer
            self.chan_1_data_bytes = self.data_bytes
            self.chan_2_data_bytes = b""

            return 0


    def convert_gain(self, gain_dB):
        conv_msg = "converting with gain %ddB..." % (gain_dB)
        print("")
        print(conv_msg, end='')

        """
        /!\ When samples are represented with 8-bits, 
            they are specified as unsigned values.
            All other sample bit-sizes are specified as signed values.
        """
        signed = True
        if self.dtype == 8:
            signed = False

        max_int, min_int = get_max_min_from_dtype(self.dtype)

        bytes_per_sample = self.dtype // 8
        nb_data = len(self.data_bytes) // bytes_per_sample
        new_bytes_array = bytearray()

        # Gain_dB = 20 log_10(out/in) => out = in * 10^(Gain_dB / 20)
        ratio = pow(10, (gain_dB / 20))

        # loop through data bytes and convert
        for data_idx in range(nb_data):
            data_offset = data_idx * bytes_per_sample

            tmpbytes = self.data_bytes[(data_offset + 0):(data_offset + bytes_per_sample)]
            tmpint = int.from_bytes(tmpbytes, byteorder="little", signed=signed)
            tmpint = int(tmpint * ratio)

            if (tmpint > max_int):
                tmpint = max_int
            elif (tmpint < min_int):
                tmpint = min_int

            tmpbytes = tmpint.to_bytes(bytes_per_sample, 'little', signed=signed)
            new_bytes_array.extend(tmpbytes)

            if data_idx % 100000 == 0 or data_idx == nb_data - 1:
                progress_bar(conv_msg, data_idx + 1, nb_data)
        
        print("")

        self.data_bytes = bytes(new_bytes_array)

        # update each channels buffer
        self.get_data_foreach_channels()

        return 0


def progress_bar(txt, curr, total):
    txt_placeholder_len = 50
    bar_width = 20
    assert len(txt) < txt_placeholder_len
    ratio_done = curr/total
    nb_progress = int(ratio_done * bar_width)
    space_after_txt = txt_placeholder_len - len(txt)
    percent_str = str(int(ratio_done * 100))
    print("\r%s%s" % (txt, " " * space_after_txt), end='')
    print("[%s" % ("#" * nb_progress), end='')
    print("%s]" % (" " * (bar_width - nb_progress)), end='')
    print(" %s" % (" " * (3 - len(percent_str))), end='')
    print("%s%%" % (percent_str), end='', flush=True)


def get_max_min_from_dtype(dtype):
    """
    /!\ When samples are represented with 8-bits, 
    they are specified as unsigned values.
    All other sample bit-sizes are specified as signed values.
    """
    assert dtype == 32 or dtype == 24 or dtype == 16 or dtype == 8
    if dtype == 8:
        return 255, 0
    elif dtype == 16:
        return 32767, -32768
    elif dtype == 24:
        return 8388607, -8388608
    else:
        return 2147483647, -2147483648


def bit_depth_conversion(wave):
    filename = "signal-original-%dbits-%dchan" % (wave.dtype, wave.nchannels)
    wave.write_and_plot("output/bit-depth-conversion", filename, False) # use every channels

    res = wave.convert_to_dtype(32)
    if res != -1:
        wave.print_info() 
        filename = "signal-%dbits-%dchan" % (wave.dtype, wave.nchannels)
        wave.write_and_plot("output/bit-depth-conversion", filename, False) # use every channels
        filename = "signal-%dbits-%dchan" % (wave.dtype, 1)
        wave.write_and_plot("output/bit-depth-conversion", filename, True)  # use only channel 1

    res = wave.convert_to_dtype(24)
    if res != -1:
        wave.print_info() 
        filename = "signal-%dbits-%dchan" % (wave.dtype, wave.nchannels)
        wave.write_and_plot("output/bit-depth-conversion", filename, False) # use every channels
        filename = "signal-%dbits-%dchan" % (wave.dtype, 1)
        wave.write_and_plot("output/bit-depth-conversion", filename, True)  # use only channel 1

    res = wave.convert_to_dtype(16)
    if res != -1:
        wave.print_info() 
        filename = "signal-%dbits-%dchan" % (wave.dtype, wave.nchannels)
        wave.write_and_plot("output/bit-depth-conversion", filename, False) # use every channels
        filename = "signal-%dbits-%dchan" % (wave.dtype, 1)
        wave.write_and_plot("output/bit-depth-conversion", filename, True)  # use only channel 1

    res = wave.convert_to_dtype(8)
    if res != -1:
        wave.print_info() 
        filename = "signal-%dbits-%dchan" % (wave.dtype, wave.nchannels)
        wave.write_and_plot("output/bit-depth-conversion", filename, False) # use every channels
        filename = "signal-%dbits-%dchan" % (wave.dtype, 1)
        wave.write_and_plot("output/bit-depth-conversion", filename, True)  # use only channel 1


def mono_conversion(wave):
    filename = "signal-original-%dchan" % (wave.nchannels)
    wave.write_and_plot("output/mono-conversion", filename, False) # use every channels

    res = wave.convert_to_mono()
    if res != -1:
        wave.print_info()    
        filename = "signal-%dchan" % (wave.nchannels)
        wave.write_and_plot("output/mono-conversion", filename)


def gain_conversion(wave):
    filename = "signal-original"
    wave.write_and_plot("output/gain-conversion", filename, False) # use every channels
    
    wave_copy = copy.deepcopy(wave) # make a copy and keep the original

    gain = 10
    res = wave.convert_gain(gain)
    if res != -1:
       wave.print_info()    
       filename = "signal-gain-%ddB" % (gain)
       wave.write_and_plot("output/gain-conversion", filename)

    gain = -10
    res = wave_copy.convert_gain(gain)
    if res != -1:
        wave_copy.print_info()    
        filename = "signal-gain-minus-%ddB" % (gain * -1)
        wave_copy.write_and_plot("output/gain-conversion", filename)


def filter_conversion(wave):
    folder = "output/filter-conversion"
    
    wave_copy = copy.deepcopy(wave) # make a copy and keep the original

    # use mono file for practicity
    wave_copy.convert_to_mono()
    wave_copy2 = copy.deepcopy(wave_copy)

    filename = "signal-original"
    wave_copy.print_info()    
    wave_copy.write_and_plot(folder, filename, False) # use every channels

    filename = "spectrum-original"
    print("plotting %s.png..." % filename)
    wave_copy.plot_spectrum("%s/%s.png" % (folder, filename), filename) 

    # narrowband
    narrowband = [300, 3400]
    wave_copy.filter_bandpass(narrowband)
    filename = "signal-narrowband"
    wave_copy.print_info()    
    wave_copy.write_and_plot("output/filter-conversion", filename, False) # use every channels

    filename = "spectrum-narrowband"
    print("plotting %s.png..." % filename)
    wave_copy.plot_spectrum("%s/%s.png" % (folder, filename), filename) 

    # wideband
    wideband = [50, 7000]
    wave_copy2.filter_bandpass(wideband)
    filename = "signal-wideband"
    wave_copy2.print_info()    
    wave_copy2.write_and_plot("output/filter-conversion", filename, False) # use every channels

    filename = "spectrum-wideband"
    print("plotting %s.png..." % filename)
    wave_copy2.plot_spectrum("%s/%s.png" % (folder, filename), filename) 


def main():
    # disable font warning for matplotlib
    logging.getLogger("matplotlib.font_manager").disabled = True

    # init wave object from wave file
    wave_orig = Wave()
    wave_orig.init_from_file("signal.wav")
    wave_orig.print_info() 

    wave = copy.deepcopy(wave_orig) # make a copy and keep the original
    bit_depth_conversion(wave)

    wave = copy.deepcopy(wave_orig) # make a copy and keep the original
    mono_conversion(wave)
    
    wave = copy.deepcopy(wave_orig) # make a copy and keep the original
    gain_conversion(wave)

    wave = copy.deepcopy(wave_orig) # make a copy and keep the original
    filter_conversion(wave)


if __name__ == "__main__":
    main()

