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
# Bare Conductive code written by Szymon Kaliski and Tom Hartley.
#
# This work is licensed under a MIT license https://opensource.org/licenses/MIT
#
# Copyright (c) 2018, Bare Conductive
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#################################################################################

from subprocess import call
import signal, argparse
import gpiozero
import threading

# app settings
button_pin          = 4    # gpiozero uses BCM pin numbering
doublepress_timeout = 0.3
longpress_timeout   = 0.75

# our state
ignoreRelease = False

# Single press: button released, and button not pressed within doublepress_timeout
# Double press: button released, and pressed again before doublepress_timeout
# Hold: Button not released until longpress_timeout

# arguments parsing
def setupargs():
  # press commands
  singlepress_cmd = "echo \"Hello World\" &"
  doublepress_cmd = "sync && reboot now &"
  longpress_cmd   = "sync && halt &"
  
  parser = argparse.ArgumentParser(description='''Maps three different PiCap button events to system calls - MUST be run as root. By default, a single press prints "Hello World" to the console, a double press reboots, and a long press triggers a shut down.''')
  parser.add_argument('-s','--single-press', nargs='?', metavar='CMD', dest = 'singlepress_cmd', type=str, default=singlepress_cmd, 
                      help='command to execute on button single press')
  parser.add_argument('-d','--double-press', nargs='?', metavar='CMD', dest = 'doublepress_cmd', type=str, default=doublepress_cmd, 
                      help='command to execute on button double press')
  parser.add_argument('-l','--long-press', nargs='?', metavar='CMD', dest = 'longpress_cmd', type=str, default=longpress_cmd, 
                      help='command to execute on button long press')
  
  return parser.parse_args()

args = setupargs()
button = gpiozero.Button(4,bounce_time=0.01,hold_time=longpress_timeout)

def release_callback(): #wait for another button press, or not
  global ignoreRelease
  doublePressed = button.wait_for_press(doublepress_timeout)
  #here, we wait for a second press. If none comes within the time, we call it a single press
  if (not doublePressed):
    call(args.singlepress_cmd, shell = True)
  else:
    ignoreRelease = True #ignore the next release trigger, as it was caused by the second press
    call(args.doublepress_cmd, shell = True)

def button_released():
  global ignoreRelease
  if (ignoreRelease):
    ignoreRelease = False
    return
  t = threading.Thread(target=release_callback) #need to call wait_for_press in a different thread
  t.start() # this is a workaround for a bug in gpiozero, it won't let you use wait_for press in a handler


def button_held():
  global ignoreRelease
  if (ignoreRelease):
    return #someone held the second press of the double press
  ignoreRelease = True #ignore the next release trigger, as it was caused by the end of the long hold
  call(args.longpress_cmd, shell = True)

button.when_held = button_held #triggered after button held for hold_time
button.when_released = button_released

#keep script active until ctrl-c etc.
signal.pause()