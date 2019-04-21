import RPi.GPIO as GPIO
import time


class Notes:
    """
    Structure describing notes with frequencies
    """
    c = 261.0
    d = 294.0
    e = 329.0
    f = 349.0
    g = 392.0
    a = 440.0
    b = 493.0
    C = 523.0
    r = 1.0

    major_scale = [c, d, e, f, g, a, b, C]


class Buzzer:
    """
    Simple class for controlling piezo buzzer.
    """

    def __init__(self, pin_number: int = 12):
        """
        Initialize proper pin and PWM module.
        :param pin_number: pin number on which is buzzer connected. Optional, default is pin 12(GPIO18).
        """
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(pin_number, GPIO.OUT)
        self.__pin_number = pin_number
        self.__pwm = GPIO.PWM(self.__pin_number, 2)

    def start_alarm(self):
        """
        Starts buzzer with frequency 10Hz and duty cycle 50% (1:1).
        :return: None
        """
        GPIO.output(self.__pin_number, True)
        self.__pwm.start(10)  # start the PWM on 100  percent duty cycle
        self.__pwm.ChangeDutyCycle(50)  # change the duty cycle to 90%

    def stop_alarm(self):
        """
        Stops alarm.
        :return: None
        """
        self.__pwm.stop()

    def play_major_scale(self, speed):
        """
        Plays major scale using class Notes.
        :param speed: Length of each note.
        :return: None
        """
        GPIO.output(self.__pin_number, True)
        time.sleep(speed)
        self.__pwm.start(0)
        self.__pwm.ChangeDutyCycle(90)

        for frequency in Notes.major_scale:
            self.__pwm.ChangeFrequency(frequency)  # change the frequency to 261 Hz (floats also work)
            time.sleep(speed)

    def __del__(self):
        """
        Cleans GPIO
        :return: None
        """
        GPIO.cleanup()

