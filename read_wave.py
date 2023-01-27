import struct


def read_wave_raw(filename):
    """
    Just pass in a filename and get bytes representation of
    audio data as result
    :param filename: a wave file
    :param rate:
    :return: tuple -> data, #channels, samplerate, datatype (in bits)
    """
    with open(filename, "rb") as wav:
        # RIFF-Header: "RIFF<size as uint32_t>WAVE" (12 bytes)
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
        _, header_len, fmt_tag, nchannels, samplerate, _, _, dtype = fmt_header_data
        assert fmt_tag == 1 # only PCM supported

        """
        Data part
        'data' - 4 bytes, header
        len of data - 4 bytes
        """
        data_header = wav.read(8)
        head, data_len = struct.unpack("<4sI", data_header)

        assert head.decode("utf-8") == "data"

        data = b""

        while True:
            chunk = wav.read(samplerate)
            data += chunk

            if len(chunk) < samplerate or len(data) >= data_len:
                # it's possible to encounter another data section you should handle it
                break

        return data, nchannels, samplerate, dtype

