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
SEQUENCE_LENGTH = 8 

#Timeout to play again
PLAY_AGAIN_TIMEOUT = 10


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
    lines = message.split("\n")
    LCD.cursor_pos = (0, 0)
    LCD.write_strings(lines[0][:16])
    if len(lines) > 1:
        LCD.cursor_pos = (1, 0)
        LCD.write_strings(lines[1][:16])

def run_with_timeout(handler_fn, timeout: int) -> bool:
    """
    Run a blocking input handler in a background thread with a timeout.
    Returns True if the handler completed in time, False if it timed out.
 
    How it works:
      - The handler runs in a daemon thread so it doesn't block the main thread.
      - A threading.Event is set when the handler finishes.
      - The main thread waits up to `timeout` seconds for the event to be set.
      - If the event isn't set in time, we return False (timeout = failed step).
 
    Note: the background thread may still be alive after a timeout since
    GPIO.wait_for_edge() can't be forcibly cancelled -- it will simply be
    ignored once the round moves on (daemon=True ensures it won't block exit).
    """
    completed = threading.Event()
 
    def run():
        handler_fn()
        completed.set()
 
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return completed.wait(timeout=timeout)
    

def magstripe_reader() -> bool:
    print("Waiting for Card Start")
    input()
    return True
    #Wait until player swipes a card to begin the game

def read_keyboard_switch() -> bool:
    #Wait until keyboard switch is pressed
    print("Waiting for Keyboard")
    GPIO.wait_for_edge(PIN_KEYBOARD_SWITCH, GPIO.FALLING)
    time.sleep(0.05)
    return True

def read_toggle_switch() -> bool:
    #Wait until toggle switch is flipped
    print("Waiting for Toggle Switch")
    GPIO.wait_for_edge(PIN_TOGGLE_SWITCH, GPIO.FALLING)
    time.sleep(0.05)
    return True

def read_push_button() -> bool:
    #Wait until button is pushed
    print("Waiting for button press")
    GPIO.wait_for_edge(PIN_PUSH_BUTTON, GPIO.FALLING)
    return True

def get_rotary_direction():
    #Read the inputted direction
    last_clk = GPIO.inpt(PIN_ROTARY_CLK)
    while True:
        current_clk = GPIO.input(PIN_ROTARY_CLK)
        if current_clk != last_clk:
            dt_state = GPIO.input(PIN_ROTARY_DT)
            direction = 'right' if dt_state != current_clk else "left"
            time.sleep(0.05) 
            return direction
        last_clk == current_clk
        time_sleep(0.001)


def read_rotary_encoder(expected_direction: str, timeout: int = STEP_TIMEOUT) -> bool:
    """
    Wait for the player to turn the rotary encoder in the expected direction.
    Returns True if correct turn in time, False if wrong direction or timed out.
    """
    print(f"Waiting for rotary encoder turn ({expected_direction})...")
 
    # Use a container to pass the result out of the thread
    result = {"direction": None}
 
    def detect():
        result["direction"] = detect_rotary_direction()
 
    completed = threading.Event()
 
    def run():
        detect()
        completed.set()
 
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
 
    if not completed.wait(timeout=timeout):
        print(f"Rotary encoder timed out after {timeout}s.")
        return False
 
    if result["direction"] == expected_direction:
        return True
    print(f"Wrong direction! Expected {expected_direction}, got {result['direction']}.")
    return False

def wait_for_swipe_or_timeout(timeout: int) -> bool:
    """
    Show a countdown on the LCD and simultaneously listen for a magstripe swipe.
    Returns True if the player swiped in time, False if the countdown expired.
 
    How it works:
      - A background thread watches for the swipe via input().
      - The main thread counts down second by second, updating the LCD.
      - A threading.Event acts as a flag -- the swipe thread sets it when
        a swipe is detected, and the countdown checks it each second.
      - If the event is set before the countdown hits zero, the player continues.
      - If the countdown hits zero first, the game stops.
    """
    swipe_detected = threading.Event()
 
    def swipe_listener():
        """Background thread: blocks on input() until a swipe comes in."""
        input()  # Magstripe reader sends a line + Enter on swipe
        swipe_detected.set()
 
    # Start the swipe listener in the background
    listener = threading.Thread(target=swipe_listener, daemon=True)
    listener.start()
 
    # Count down, checking each second if a swipe came in
    for remaining in range(timeout, 0, -1):
        if swipe_detected.is_set():
            return True  # Swiped in time
        lcd_show(f"Swipe to play!\n{remaining} seconds left")
        print(f"Play again countdown: {remaining}s")
        time.sleep(1)
 
    # One final check right as the timer hits zero
    if swipe_detected.is_set():
        return True
 
    return False  # Timed out -- no swipe detected
 



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

def generate_sequence(length: int = SEQUENCE_LENGTH) -> list:
    all_types = SIMPLE_INPUTS + ["rotary encoder"]
    sequence = []
    for i in range(length):
        chosen  = random.choice(all_types)
        if chosen == "rotary_encoder":
            sequence.append({
                "type": "rotary_encoder",
                "direction" : random.choice(["left", "right"])
            })
        else:
            sequence.append({"type" : chosen})
    return sequence


'''Score Sending'''


def send_score(elapsed: float):
    #Replace with actual leaderboard computer IP
    if COMPUTER_IP == "Your Computer IP":
        print("[Sync] Computer IP not set, skipping Sync")
        return
    try:
        response = requests.post(
            LEADERBOARD_URL,
            json = {"time" : elapsed}
            timeout = 5
        )
        if response.status_code == 200:
            print(f"[Sync] score sent succesfully ({elapsed:.3f}).")
        else:
            print(f"[Sync] Server returned {response.status_code}.")
    except Exception as e:
        print(f"[Sync] failed to reach computer: {e}")
    
'''Main Game Loop'''
def play_game() -> float | None:
    #Step 1: Generate Sequence
    sequence = generate_sequence()
    print(f"\nSequence: {sequence}")

    #Countdown
    for i in [3, 2, 1]:
        lcd_show(str(i))
        time.sleep(1)
    lcd_show("GO!")

    #Start Timer
    start_time = time.time()


    #Walk through sequence
    attempt = 1
    while True:
        if attempt > 1:
            print(f"Attempt {attempt} -- restarting sequence")
            lcd_show("RESTART!")
            time.sleep(0.8)
        
        completed = True
        for i, step in enumerate(sequence):
            input_type = step["type"]


            if input_type == "rotary_encoder":
                direction = step["direction"]
                lcd_show(ROTARY_LABELS[direction])
                print(f"Step {i + 1}/{ len(sequence)}: rotary encoder -- {direction}")
                success = read_rotary_encoder(direction)

            else:
                lcd_show(SIMPLE_LABELS[input_type])
                success = SIMPLE_HANDLES[input_type]()

            if not success:
                if RESTART_ON_FAIL:
                    completed = False
                    attempt += 1
                    break
                else:
                    lcd_show("FAIL!")
                    print("Wrong input, game over")
                    return None
        if completed:
            break
    elapsed = time.time() - start_time
    lcd_show(f"{elapsed:.2f}s!")
    print(f"\nCompleted in {elapsed:.3f}s over {attempt} attempt(s)!")
    return elapsed


def main():
    setup_gpio()
    lcd_show("SpeedSwipe!")

    try:
        while True:
            lcd_show("Swipe to Start!")
            print("\nWaiting for card swipe to begin...")
            magstripe_reader()

            while True:
                elapsed = play_game()

                if elapsed is not None:
                    send_score(elapsed)
                lcd_show("Swipe in 10 seconds if you want to play again")
                
                swiped = wait_for_swipe_or_timeout(PLAY_AGAIN_TIMEOUT)
                
                if swiped:
                    print("Swipe detected -- starting new round!")
                    lcd_show("Get Ready!")
                    time.sleep(1)
                else:
                    # Countdown expired -- end the game
                    lcd_show("Game Over!\nThanks!")
                    print("No swipe detected -- game over.")
                    time.sleep(2)
                    break
 
    finally:
        # Always clean up on exit, even if the program crashes
        cleanup_gpio()
        LCD.clear()
 
 
if __name__ == "__main__":
    main() 