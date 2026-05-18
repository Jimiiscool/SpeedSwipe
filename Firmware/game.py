import random
import time
import os
import csv
import shutil
from datetime import datetime
import requests
import RPi.GPIO as GPIO
from RPLCD.i2c import CharLCD

#Leaderboard Computer IP
COMPUTER_IP =  "YOUR COMPUTER IP"
LEADERBOARD_URL = "LEADERBOARD URL"

#Can be changed
SEQUENCE_LENGTH = 6 


#If true, game resets player to beginning of combination if mistake is made while time still runs
RESTART_ON_FAIL = True


#GPIO pin numbers, placeholders for now
PIN_KEYBOARD_SWITCH = -1
PIN_TOGGLE_SWITCH = -1
PIN_PUSH_BUTTON = -1
PIN_ROTARY_CLK = -1
PIN_ROTARY_DT = -1

#LCD Initializer. Placeholder values for now
LCD = CharLCD(i2c_expander='PCF8574', address = 0x27, port=1, cols=16, rows=2)

#GPIO Setup
def setup_gpio():
    gpio.setmode(GPIO.BCM)
    gpio.setup(PIN_KEYBOARD_SWITCH, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    gpio.setup(PIN_TOGGLE_SWITCH, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    gpio.setup(PIN_PUSH_BUTTON, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    gpio.setup(PIN_ROTARY_CLK, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    gpio.setup(PIN_ROTARY_DT, GPIO.IN, pull_up_down = GPIO.PUD_UP)


def cleanup_gpio():
    GPIO.cleanup()

#LCD dispplay main code
def lcd_show(message):
    LCD.clear
    lines = message.split


def magstripe_reader() -> bool:
    #Wait until player swipes a card to begin the game
    return True


def read_keyboard_switch() -> bool:
    #Wait until keyboard switch is pressed
    return True

def read_toggle_switch() -> bool:
    return True

def read_push_button() -> bool:
    return True

def get_rotary_direction():


def read_rotary_encoder():

'''Sequence Generation, Generate random sequence of inputs user must input to win'''

SIMPLE_INPUTS = ['keyboard_switch', 'toggle_switch', 'push_button']

SIMPLE_HANDLES = {"keyboard_switch" : read_keyboard_switch,
                  "toggle_switch" : read_toggle_switch,
                  "push_button" : read_push_button}

SIMPLE_LABELS = {"keyboard_switch" : "CLICK!",
                 "toggle_switch" : "FLIP!",
                 "push_button" : "PUSH!"}

ROTARY_LABELS = {"left" : "LEFT!",
                 "right" : "RIGHT!"}

def generate_sequence(length: int = sequence_length) -> list:
    t_list = []
    return t_list


def send_score(elapsed: float):
    return

def play_game() -> float


