import time
import board
import busio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus
ads = ADS.ADS1015(i2c)

# Create single-ended input on channel 0
chan = AnalogIn(ads, ADS.P0)
chan2 = AnalogIn(ads, ADS.P1)
# Create differential input between channel 0 and 1
#chan = AnalogIn(ads, ADS.P0, ADS.P1)

print("{:>5}\t{:>5}".format('raw', 'v'))

# while True:
#     print("{:>5}\t{:>5.5f}".format(chan.value, chan.voltage, chan2.voltage))
#     time.sleep(0.001)
    

while True:
    print(chan.voltage, chan2.voltage)

def volt(chan):
    return chan.value, chan.voltage, chan2.voltage