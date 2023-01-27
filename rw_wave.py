import struct

"""
Read and write wave file

# Credit: modified code snippet from https://gist.github.com/chief7/54873e6e7009a087180902cb1f4e27be
"""

def write_wave_raw(filename, nchannels, bits_per_sample, sample_rate, data): 
    
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
    block_align = (bits_per_sample * nchannels) // 8
    bytes_per_second = (sample_rate * bits_per_sample * nchannels) // 8

    fmt_header = struct.pack("<4sIHHIIHH", fmt, header_length, fmt_tag, 
                             nchannels, sample_rate, bytes_per_second, 
                             block_align, bits_per_sample)

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


def read_wave_raw(filename):
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

        return bytes(data), nchannels, samplerate, dtype

