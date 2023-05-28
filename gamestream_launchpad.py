# Wrap a gamestream session around a launcher program with configurable background tasks and resolution switching
import win32api
import win32.lib.win32con as win32con
import win32gui
import win32event
import pywintypes
import pyautogui
import configparser
import subprocess
import psutil
import os
import sys
from time import sleep

# Window enumeration handler function per https://www.blog.pythonlibrary.org/2014/10/20/pywin32-how-to-bring-a-window-to-front/
def windowEnumerationHandler(hwnd, top_windows):
    top_windows.append((hwnd, win32gui.GetWindowText(hwnd)))


def set_resolution(gamestream_width, gamestream_height,refresh_rate=None):
    if refresh_rate is None:
        print("Switching resolution to {0}x{1}".format(gamestream_width, gamestream_height))
    else:
        print("Switching resolution to {0}x{1} at {2}Hz".format(gamestream_width, gamestream_height,refresh_rate))
    devmode = pywintypes.DEVMODEType()
    devmode.PelsWidth = int(gamestream_width)
    devmode.PelsHeight = int(gamestream_height)
    devmode.Fields = win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT
    if refresh_rate is not None:
        devmode.DisplayFrequency = refresh_rate
        devmode.Fields |= win32con.DM_DISPLAYFREQUENCY
    win32api.ChangeDisplaySettings(devmode, 0)


def get_process_name(p):
    # If there are permission errors reading a process name, it's probably not the one we want, so skip it.
    try:
        p_name = p.name()
    except (PermissionError, psutil.AccessDenied):
        p_name = ""
        pass
    return p_name


def reset_launcher_resolution(gamestream_width, gamestream_height, launcher_window_name):
    # Check to ensure desired GSLP resolution is still set whenever the launcher is in focus in case it didn't reset when exiting a game
    focused_window = win32gui.GetWindowText(win32gui.GetForegroundWindow()).lstrip()
    #print("Trying to match", launcher_window_name, focused_window)
    if focused_window.startswith(launcher_window_name):
        #print("Matched")
        current_width = str(win32api.GetSystemMetrics(0))
        current_height = str(win32api.GetSystemMetrics(1))
        if current_width != gamestream_width and current_height != gamestream_height:
            print("Resolutions don't match, changing from", current_width, current_height, "to", gamestream_width, gamestream_height)
            set_resolution(gamestream_width, gamestream_height)

def handle_processes(paths, terminate):
    for path in paths:
        expanded_path = os.path.expandvars(paths[path])
        if os.path.exists(expanded_path):
            exec_name = os.path.basename(expanded_path)
            print("Terminating" if terminate else "Launching", expanded_path)
            # Terminate even if launching, so that we kill it if it's already running
            if exec_name in (get_process_name(p) for p in psutil.process_iter()):
                os.system('taskkill /f /im ' + exec_name)
            if not terminate:
                # Start the process
                subprocess.Popen(expanded_path)

def launch_processes(paths):
    handle_processes(paths, False)

def kill_processes(paths):
    handle_processes(paths, True)

# Define a default config file to write if we're missing one
config_filename = 'gamestream_playnite.ini'
default_config = """[LAUNCHER]
# The path to your Playnite.FullscreenApp.exe
launcher_path = %%LOCALAPPDATA%%\Playnite\Playnite.FullscreenApp.exe
# Name of the window to watch to close the session when it's gone
launcher_window_name = Playnite

[BACKGROUND]
# List as many exe's or bat's as you want here. They will run at the start of the GameStream session and be killed at the end.
# background_exe_1 = C:\Program Files (x86)\JoyToKey\JoyToKey.exe
# background_exe_2 = C:\WINDOWS\system32\mspaint.exe

[SESSION_START]
# List as many exe's or bat's as you want here. They will run when the GameStream session begins, but won't be killed when it ends.
# start_exe_1 = C:\Some\Path\enable_bluetooth_adapter.bat

[SESSION_END]
# List as many exe's or bat's as you want here. They will run when the GameStream session ends.
# end_exe_1 = C:\Some\Path\disable_bluetooth_adapter.bat

[SETTINGS]
# Set debug = 1 to leave a window running after gamestream to see error messages from GSLP
debug = 0
# Set sleep_on_exit to 1 to put the computer to sleep after the session
sleep_on_exit = 0
# Set close_watch_method to "process" to wait for the launcher process to totally die to exit (can be problematic if it closes to tray), or "window" to just wait the the window to close
close_watch_method = window
"""

# Write the default config
if not os.path.exists(config_filename):
    with open(config_filename, 'w') as out_file:
        out_file.write(default_config)

# Target resolution for gamestream environment
try:
    if '-r' in sys.argv:
        rind = sys.argv.index('-r')
        sys.argv.pop(rind)
        refresh_rate = int(sys.argv.pop(rind))
    else:
        refresh_rate = None    
    if '--no-nv-kill' in sys.argv:
        no_nv_kill = True
        sys.argv.remove('--no-nv-kill')
    else:
        no_nv_kill = False
    if '--skip-res-reset' in sys.argv:
        skip_res_reset = True
        sys.argv.remove('--skip-res-reset')
    else:
        skip_res_reset = False

    gamestream_width = sys.argv[1]
    gamestream_height = sys.argv[2]
    # If there's a 3rd argument after the .py/.exe, use it as a custom launcher path
    if len(sys.argv) == 4:
        config_filename = sys.argv[3]
except IndexError:
    print("Error parsing arguments. Did you mean to run one of the .bat launcher scripts?")
    print("Usage: gamestream_launchpad.exe 1920 1080 [config.ini] [-r refresh_rate_hz]")
    input("Press Enter to exit.")
    sys.exit(1)

# Parse the config file and assume defaults otherwise
config = configparser.ConfigParser()
config.read(config_filename)
cfg_launcher_path = config['LAUNCHER'].get('launcher_path', r'%LOCALAPPDATA%\Playnite\Playnite.FullscreenApp.exe')
cfg_launcher_window_name = config['LAUNCHER'].get('launcher_window_name', 'Playnite')
cfg_bg_paths = config['BACKGROUND']
try:
    cfg_start_paths = config['SESSION_START']
except KeyError:
    cfg_start_paths = ""
try:
    cfg_end_paths = config['SESSION_END']
except KeyError:
    cfg_end_paths = ""
debug = config['SETTINGS'].get('debug', '0')
sleep_on_exit = config['SETTINGS'].get('sleep_on_exit', '0')
close_watch_method = config['SETTINGS'].get('close_watch_method', 'window')

launcher_exec_name = os.path.basename(cfg_launcher_path)

# Set resolution to target
set_resolution(gamestream_width, gamestream_height,refresh_rate)

# Start background and session_start programs, if they're available
launch_processes(cfg_bg_paths)
launch_processes(cfg_start_paths)

# A launcher value of false will create a wait inside of the console instead watching a program
if cfg_launcher_path.lower() == "false":
    input('Press enter to end the GameStream session.')
else:
    # Minimize all windows
    print("Minimizing windows")
    pyautogui.hotkey('winleft', 'd')
    sleep(3)

    # Playnite has to be killed before it will start in fullscreen mode
    if "Playnite" in launcher_exec_name:
        if "Playnite.FullscreenApp.exe" in (get_process_name(p) for p in psutil.process_iter()):
            os.system('taskkill /f /im ' + "Playnite.FullscreenApp.exe")
        if "Playnite.DesktopApp.exe" in (get_process_name(p) for p in psutil.process_iter()):
            os.system('taskkill /f /im ' + "Playnite.DesktopApp.exe")

        # Move mouse cursor into the lower-right corner to pseudo-hide it because sticks out in playnite fullscreen
        pyautogui.FAILSAFE = False
        pyautogui.moveTo(9999, 9999, duration = 0)

    # Start game launcher
    print("Starting game launcher")
    launcher_exe = os.path.expandvars(cfg_launcher_path)
    subprocess.Popen(launcher_exe)

    # Focus launcher in the foreground and maximize
    results = []
    top_windows = []
    launcher_focused = False
    while not launcher_focused:
        win32gui.EnumWindows(windowEnumerationHandler, top_windows)
        for i in top_windows:
            if cfg_launcher_window_name in i[1]:
                if not 'Fullscreen' in cfg_launcher_path:
                    print("Maximizing", cfg_launcher_window_name)
                    win32gui.ShowWindow(i[0], 3)
                print("Focusing", cfg_launcher_window_name)
                win32gui.SetForegroundWindow(i[0])
                launcher_focused = True
                launcher_window_handle = i[0]
                break
        sleep(1)

    # Watch for closing the launcher window to return to the system's original configuration
    if close_watch_method == "window":
        print("Watching for launcher window to close")
        while win32gui.IsWindowVisible(launcher_window_handle):
            #print("Visible:", launcher_window_handle)
            sleep(2)
            reset_launcher_resolution(gamestream_width, gamestream_height, cfg_launcher_window_name)
    # Alternative method that waits for the process to die (can be problematic if it minimizes to system tray)
    elif close_watch_method == "process":
        print("Watching for launcher process to die")
        while True:
            if launcher_exec_name in (get_process_name(p) for p in psutil.process_iter()):
                sleep(2)
                reset_launcher_resolution(gamestream_width, gamestream_height, cfg_launcher_window_name)
            else:
                break
    elif close_watch_method == "playnite_mutex":
        while True:
            try:
                #Instance is spelled wrong in the Playnite source code, this may need to be fixed someday
                #for now it must be spelled Instace
                playnite_mutex_handle = win32event.OpenMutex(win32event.SYNCHRONIZE, False, "PlayniteInstaceMutex")
                break
            except Exception as e:
                print(f"Exception attempting to open Playnite mutex:{e}")
                sleep(0.1)
        #Playnite creates and locks a mutex so if we can lock the mutex it means Playnite has quit
        win32event.WaitForSingleObject(playnite_mutex_handle,0xffffffff)
        #We need to tear down the mutex or Playnite won't start again
        win32event.ReleaseMutex(playnite_mutex_handle)
        win32api.CloseHandle(playnite_mutex_handle)
        
    else:
        print("No valid close_watch_method in the config. Press Enter when you're done.")
        input()

# Terminate background and launch session_end programs, if they're available
kill_processes(cfg_bg_paths)
launch_processes(cfg_end_paths)

# Restore original resolution
if skip_res_reset == False:
    print('Restoring original resolution.')
    win32api.ChangeDisplaySettings(None, 0)

# Kill gamestream
if no_nv_kill == False:
    print("Terminating GameStream session.")
    if "nvstreamer.exe" in (get_process_name(p) for p in psutil.process_iter()):
        os.system('taskkill /f /im nvstreamer.exe')


if sleep_on_exit == '1':
# Put computer to sleep
    print("Going to sleep")
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

if debug == '1':
    # Leave window open for debugging
    input("Paused for debug review. Press Enter key to close.")
