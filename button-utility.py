################################################################################
#
# Bare Conductive Pi Cap
# ----------------------
#
# button-utility.py - utility for reacting to single-click, long-click and
# double-click events from the Pi Cap button
#
# Written for Raspberry Pi.
#
# Bare Conductive code written by Szymon Kaliski.
#
# This work is licensed under a Creative Commons Attribution-ShareAlike 3.0
# Unported License (CC BY-SA 3.0) http://creativecommons.org/licenses/by-sa/3.0/
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#################################################################################

from time import sleep, time
from subprocess import call
import signal, sys, getopt
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)

# app settings
button_pin          = 7
doublepress_timeout = 0.30
longpress_timeout   = 0.75

# our state
last_pressed    = None
last_released   = None
is_pressed      = False

# press commands
singlepress_cmd = "echo \"Hello World\" &"
doublepress_cmd = "sync && reboot now &"
longpress_cmd   = "sync && halt &"

# handle ctrl+c gracefully
def signal_handler(signal, frame):
  GPIO.cleanup()
  sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# print help
def print_help():
  print "Maps three different PiCap button events to system calls - MUST be run as root.\n"
  print "Usage: python button-utility.py [OPTION]\n"
  print "By default single press      echoes \"Hello World!\""
  print "           double press      restarts"
  print "           long press        shuts down\n"
  print "Options:"
  print "  -s, --single-press [CMD]   executes [CMD] on button single press"
  print "  -d, --double-press [CMD]   executes [CMD] on button double press"
  print "  -l, --long-press   [CMD]   executes [CMD] on button long press"
  print "  -h, --help                 displays this message"
  sys.exit(0)

# arguments parsing
def parse_args(argv):
  # we need to tell python that those variables are global
  # we don't want to create new local copies, but change global state
  global singlepress_cmd, doublepress_cmd, longpress_cmd

  try:
    opts, args = getopt.getopt(argv, "s:d:l:h", [ "single-press=", "double-press=", "long-press=", "help" ])
  except getopt.GetoptError:
    print_help()

  for opt, arg in opts:
    if opt in ("-h", "--help"):
      print_help()
    elif opt in ("-s", "--single-press"):
      singlepress_cmd = arg
    elif opt in ("-l", "--long-press"):
      longpress_cmd = arg
    elif opt in ("-d", "--double-press"):
      doublepress_cmd = arg

# button action callback
def button_callback(button_pin):
  # we need to tell python that those variables are global
  # we don't want to create new local copies, but change global state
  global is_pressed, last_pressed, last_released

  # state 0 is pressed, 1 is released
  is_pressed = not GPIO.input(button_pin)

  if is_pressed:
    last_pressed = time()
  else:
    last_released = time()

# parse arguments on start
parse_args(sys.argv[1:])

# setup button, and add the callback
# we could do everything in while True looop, but here we get nice handling of button debouncing
GPIO.setup(button_pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.add_event_detect(button_pin, GPIO.BOTH, callback = button_callback, bouncetime = 10)

# main code loop
while True:
  now = time()

  if is_pressed:
    # if we get another press before doublepress_timeout of last_released, then it's double press
    if last_pressed is not None and last_released is not None and last_pressed < (last_released + doublepress_timeout):
      call(doublepress_cmd, shell = True)
      last_pressed = None
      last_released = None

    # otherwise if last_pressed happened before longpress_timeout from now, we have long press
    elif last_pressed is not None and last_pressed < (now - longpress_timeout):
      call(longpress_cmd, shell = True)
      last_pressed = None
      last_released = None

  else:
    # if button got released, and nothing happens in doublepress_timeout time, then we had single press
    # we could remove the timeout, but then each double press would also register single press
    if last_released is not None and last_pressed is not None and last_released < (now - doublepress_timeout):
      call(singlepress_cmd, shell = True)
      last_pressed = None

  # wait a bit
  sleep(0.1)
