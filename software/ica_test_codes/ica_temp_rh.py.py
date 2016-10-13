# ica_ip_disp.py
# Reading temperature & humidity from SHT20 sensor
# and display them on segment LED.

#!/usr/bin/env python

import pigpio
import wiringpi2 as wpi
import time

# Import font lib: English 7-bit Segment
import font_en_seg7

# Soft CS# of MAX7219
SPI_CS_PIN = 26
BUZ_PIN = 4
LED_PIN = [27, 23, 22, 24]
KEY_PIN = [13, 12, 5, 25, 6]

# Using SPI1
AUX_SPI=(1<<8)

# Initialize MAX7219
def max7219Init():
    max7219WriteReg(0x09, 0x00)
    max7219WriteReg(0x0A, 0x03)
    max7219WriteReg(0x0B, 0x07)
    max7219WriteReg(0x0C, 0x01)
    max7219WriteReg(0x0F, 0x00)
    max7219DisplayClear()

# Wirte MAX7219 register
def max7219WriteReg(addr, data):
    pi.write(SPI_CS_PIN, pigpio.LOW)
    #print("[ICA] <max7219WriteReg> addr = 0x%02X, data = 0x%02X" %(addr, data))
    pi.spi_xfer(spi1, [addr & 0xFF, data & 0xFF])
    pi.write(SPI_CS_PIN, pigpio.HIGH)

# Display char of font lib on MAX7219
def max7219DiplayChar(digit, char, dp):
    if not char in font_en_seg7.data.keys():
        print("[ICA] <max7219Diplaychar> Error: Char (%d) can't be displayed!" %ord(char))
        return -1;
    
    if dp != 0:
        max7219WriteReg(digit + 1, font_en_seg7.data[char] + (1<<font_en_seg7.segDP))
    else:
        max7219WriteReg(digit + 1, font_en_seg7.data[char])
    return 0

def max7219DiplayString(string):
    index = 0
    for digit in range(0, 8):
        if index > (len(string) - 1):
            char = " "
        else:
            char = string[index]
                       
        if (index + 1 <= (len(string) - 1)) and (string[index + 1] == "."):
            dp = 1
            index = index + 2
        else:
            dp = 0
            index = index + 1
        max7219DiplayChar(digit, char, dp)

def max7219DisplayClear():
    for dig in range(1, 9):
        max7219WriteReg(dig, 0x00)  


def SHT20_Init():
    _i2c = wpi.wiringPiI2CSetup(0x40)
    return _i2c

def SHT20_ReadTemp(_i2c):
    wpi.wiringPiI2CWrite(_i2c, 0xF3)
    time.sleep(0.1)
    ret = wpi.wiringPiI2CRead(_i2c)
    ret = (ret<<8) + wpi.wiringPiI2CRead(_i2c)
    ret = ret * 175.72 / 65536.0 - 46.85
    #print("%3.1f" %ret)
    return ret

def SHT20_ReadRh(_i2c):
    wpi.wiringPiI2CWrite(_i2c, 0xF5)
    time.sleep(0.1)
    ret = wpi.wiringPiI2CRead(_i2c)
    ret = (ret<<8) + wpi.wiringPiI2CRead(_i2c)
    ret = ret * 125.0 / 65536.0 - 6.0
    #print("%3.1f" %ret)
    return ret

def ICA_ReadKey(num):
    key = pi.read(KEY_PIN[num])
    if key == pigpio.LOW:
        time.sleep(0.01)
        if key == pigpio.LOW:
            return 1
    return 0


##########################################
#             Main Process               #
##########################################
pi = pigpio.pi() # Connect to local Pi.

# Init Software CS# of MAX7219
pi.set_mode(SPI_CS_PIN, pigpio.OUTPUT)
pi.write(SPI_CS_PIN, pigpio.HIGH)

# Init LEDs
for i in range(0, len(LED_PIN)):
    pi.set_mode(LED_PIN[i], pigpio.OUTPUT)
    pi.write(LED_PIN[i], pigpio.LOW)

# Init Keys
for i in range(0, len(KEY_PIN)):
    pi.set_mode(KEY_PIN[i], pigpio.INPUT) 

# Init Buzzer
pi.set_mode(BUZ_PIN, pigpio.OUTPUT)
pi.write(BUZ_PIN, pigpio.HIGH)
time.sleep(0.1)
pi.write(BUZ_PIN, pigpio.LOW)

# Get handle to aux SPI channel 1.
spi1 = pi.spi_open(1, 8000000, AUX_SPI)
if spi1 < 0:
    print("[ICA] SPI1 init error!")
    exit(1)
else:
    print("[ICA] SPI1 init OK!")

io = wpi.GPIO(wpi.GPIO.WPI_MODE_PINS)
i2c_sht20 = SHT20_Init()
if i2c_sht20 < 0:
    print("[ICA]I2C init error")
    exit(2)

# Init MAX7219 Seg LED driver
max7219Init()
print("[ICA] MAX7219 init OK!")

# Second beep after display system init
pi.write(BUZ_PIN, pigpio.HIGH)
time.sleep(0.1)
pi.write(BUZ_PIN, pigpio.LOW)

# Turn off all LEDs after display system init
for i in range(0, len(LED_PIN)):
    pi.write(LED_PIN[i], pigpio.HIGH)

# Display temp & rh on seg7 LED, untill the central key is pressed
while not ICA_ReadKey(1):
    max7219DiplayString(" %2.01f %2.10f" %(SHT20_ReadTemp(i2c_sht20), SHT20_ReadRh(i2c_sht20)))
    time.sleep(1)

# Thrid beep after display done
pi.write(BUZ_PIN, pigpio.HIGH)
time.sleep(0.1)
pi.write(BUZ_PIN, pigpio.LOW)

# Clear resources after display
max7219DisplayClear()
pi.spi_close(spi1)
pi.stop()









