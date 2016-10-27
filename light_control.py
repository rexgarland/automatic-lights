import RPi.GPIO as GPIO
import time

def setup():
	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
	GPIO.setup(4,GPIO.OUT)
	GPIO.setup(18,GPIO.OUT)

def turn_light_on():
	GPIO.output(18,GPIO.HIGH)
	time.sleep(0.5)
	GPIO.output(18,GPIO.LOW)

def turn_light_off():
	GPIO.output(4,GPIO.HIGH)
	time.sleep(0.5)
	GPIO.output(4,GPIO.LOW)