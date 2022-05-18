import time
import board
import digitalio
import pulseio
import neopixel
import adafruit_irremote
from picoed import *

class RGB():
    """RGB enum"""
    left = 0x04
    right = 0x08

class Servo():
    """servo enum"""
    s1 = 0x05
    s2 = 0x06

class Unit():
    """Distance unit"""
    cm = 1
    inch = 2

class Cutebot():
    """Supports the Pico:ed cutebot by ELECFREAKS"""

    def __init__(self):
        self._address = 0x10
        self._tracking_pin_L = digitalio.DigitalInOut(board.P13)
        self._tracking_pin_L.direction = digitalio.Direction.INPUT
        self._tracking_pin_R = digitalio.DigitalInOut(board.P14)
        self._tracking_pin_R.direction = digitalio.Direction.INPUT
        self.distance = 0
        self.set_speed(0, 0)
        self.set_light(RGB.left, 0, 0, 0)
        self.set_light(RGB.right, 0, 0, 0)
        self._rainbow_leds = None

    def set_speed(self, left_speed, right_speed):
        """Set the speed of the car's left wheel and right wheel"""
        if left_speed > 100 or left_speed < -100 or right_speed > 100 or right_speed < -100:
            raise ValueError('speed error,-100~100')
        left_buffer = bytearray([0x01, 0, 0, 0])
        right_buffer = bytearray([0x02, 0, 0, 0])
        if left_speed > 0:
            left_buffer[1] = 0x02
            left_buffer[2] = left_speed
        else:
            left_buffer[1] = 0x01
            left_buffer[2] = -left_speed
        if right_speed > 0:
            right_buffer[1] = 0x02
            right_buffer[2] = right_speed
        else:
            right_buffer[1] = 0x01
            right_buffer[2] = -right_speed
        if not i2c.try_lock():
            i2c.unlock()
        else:
            i2c.writeto(self._address, left_buffer)
            i2c.writeto(self._address, right_buffer)
            i2c.unlock()

    def set_light(self, light_num:RGB, rgb_r, rgb_g, rgb_b):
        """Set the RGB light"""
        if rgb_r < 0 or rgb_r > 255 or rgb_g < 0 or rgb_g > 255 or rgb_b < 0 or rgb_b > 255:
            raise ValueError('RGB parameter error,0~255')
        if light_num == RGB.left or light_num == RGB.right:
            rgb_buffer = bytearray([light_num, rgb_r, rgb_g, rgb_b])
        else:
            raise ValueError('light select error,please select RGB.left or RGB.right.')
        if not i2c.try_lock():
            i2c.unlock()
        else:
            i2c.writeto(self._address, rgb_buffer)
            i2c.unlock()

    def get_distance(self, unit:Unit):
        """Gets the distance detected by ultrasound"""
        _ultrasonic_trig = digitalio.DigitalInOut(board.P8)
        _ultrasonic_trig.direction = digitalio.Direction.OUTPUT
        _ultrasonic_trig.value = True
        time.sleep(0.00001)
        _ultrasonic_trig.value = False
        _ultrasonic_trig.deinit()
        _ultrasonic_echo = pulseio.PulseIn(board.P12)
        while len(_ultrasonic_echo) == 0:
            pass
        _ultrasonic_echo.pause()
        distance_now = _ultrasonic_echo.popleft() * 34 / 2 / 1000 + 7
        _ultrasonic_echo.clear()
        _ultrasonic_echo.deinit()
        if distance_now >= 1121:
            if self.distance != 0:
                distance_now = self.distance
            else:
                distance_now = self.get_distance(Unit.cm)
        self.distance = distance_now
        if unit == Unit.cm:
            return distance_now
        elif unit == Unit.inch:
            return distance_now / 2.54
        else:
            raise ValueError('unit error,please select Unit.cm or Unit.inch')

    def get_tracking(self):
        """Gets the status of the patrol sensor"""
        left_value = self._tracking_pin_L.value
        right_value = self._tracking_pin_R.value
        if left_value and right_value:
            return 11
        elif not left_value and right_value:
            return 10
        elif left_value and not right_value:
            return 1
        elif not left_value and not right_value:
            return 0

    def set_servo(self, servo_num:Servo, angle):
        """Set servo angle"""
        if angle > 180 or angle < 0:
            raise ValueError('angle parameter error,0~180')
        else:
            servo_buffer = bytearray([0, angle, 0, 0])
        if servo_num == Servo.s1:
            servo_buffer[0] = Servo.s1
        elif servo_num == Servo.s2:
            servo_buffer[0] = Servo.s2
        else:
            raise ValueError('select servo error,please select Servo.s1 or Servo.s2')
        if not i2c.try_lock():
            i2c.unlock()
        else:
            i2c.writeto(self._address, servo_buffer)
            i2c.unlock()

    def get_ir_value(self):
        pulsein = pulseio.PulseIn(board.P16, maxlen=120, idle_state=True)
        decoder = adafruit_irremote.GenericDecode()
        pulses = decoder.read_pulses(pulsein)
        pulsein.clear()
        pulsein.deinit()
        try:
            code = decoder.decode_bits(pulses)
            if code[0] == 255 and code[1] == 0:
                if code[3] == 162:
                    return 11
                elif code[3] == 98:
                    return 12
                elif code[3] == 226:
                    return 13
                elif code[3] == 34:
                    return 14
                elif code[3] == 2:
                    return 15
                elif code[3] == 194:
                    return 16
                elif code[3] == 224:
                    return 17
                elif code[3] == 168:
                    return 18
                elif code[3] == 144:
                    return 19
                elif code[3] == 104:
                    return 0
                elif code[3] == 152:
                    return 100
                elif code[3] == 176:
                    return 200
                elif code[3] == 48:
                    return 1
                elif code[3] == 24:
                    return 2
                elif code[3] == 122:
                    return 3
                elif code[3] == 16:
                    return 4
                elif code[3] == 56:
                    return 5
                elif code[3] == 90:
                    return 6
                elif code[3] == 66:
                    return 7
                elif code[3] == 74:
                    return 8
                elif code[3] == 82:
                    return 9
        except:
            return self.get_ir_value()

    @property
    def rainbow_leds(self):
        """Access rainbow_leds instance"""
        if self._rainbow_leds is None:
            raise AttributeError("rainbow_leds not initialized, " +
                                 "call init_rainbow_leds to initialize.")
        return self._rainbow_leds

    def init_rainbow_leds(self, brightness=1.0, auto_write=True):
        """
        initialize rainbow_leds

        Args:
            brightness (float, optional): Brightness of the pixels between
                0.0 and 1.0 where 1.0 is full brightness. Defaults to 1.0.
            auto_write (bool, optional): True if the neopixels should
                immediately change when set. If False, `show` must be called
                explicitly.. Defaults to True.
        """
        self._rainbow_leds = neopixel.NeoPixel(
            board.P15, 2, brightness=brightness, auto_write=auto_write)
