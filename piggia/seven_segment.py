import spidev

CLEAR = 0x76
DECIMAL = 0x77

class BadNumberError(Exception):
    pass


class SevenSegment:
    def __init__(self, bus, device, mode=0, speed=50000):
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.spi.mode = mode
        self.spi.max_speed_hz = speed
        self.spi.xfer([CLEAR])

    def send_byte(self, byte):
        self.spi.xfer([byte])

    def send_int(self, int_num):
        bytes_to_send = []
        int_str = str(int_num)
        if len(int_str) > 4:
            raise(BadNumberError())
        self.spi.xfer([CLEAR])
        for c in int_str:
            bytes_to_send.append(int(c))
        self.spi.writebytes(bytes_to_send)

    def send_float(self, float_num):
        float_str = str(float_num)
        if len(float_str.split('.')[0]) > 4:
            raise(BadNumberError())
        bytes_to_send = []
        digits = 0
        self.spi.xfer([CLEAR])
        for c in float_str:
            if c == '.':
                bytes_to_send.append(DECIMAL)
                bytes_to_send.append(2**(digits-1))
            else:
                bytes_to_send.append(int(c))
                digits += 1

            if digits >= 4:
                break
        self.spi.writebytes(bytes_to_send)

