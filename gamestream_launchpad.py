# Wrap a gamestream session around a launcher program with configurable background tasks and resolution switching
import os
import sys
import time
import ctypes
import argparse
import subprocess
import configparser
from copy import copy
from time import sleep
from pathlib import Path
from contextlib import contextmanager

import psutil
import win32api
import win32gui
import pyautogui
import pywintypes
import win32.lib.win32con as win32con

DEFAULT_CONFIG = """[LAUNCHER]
# The path to your Playnite.FullscreenApp.exe
launcher_path = %%LOCALAPPDATA%%\Playnite\Playnite.FullscreenApp.exe
# Name of the window to watch to close the session when it's gone
launcher_window_name = Playnite

[BACKGROUND]
# List as many exe's or bat's as you want here. They will run at the start of the GameStream session and be killed at the end.
# background_exe_1 = C:\Program Files (x86)\JoyToKey\JoyToKey.exe
# background_exe_2 = C:\WINDOWS\system32\mspaint.exe

[SETTINGS]
# Set debug = 1 to leave a window running after gamestream to see error messages from GSLP
debug = 0
# Set sleep_on_exit to 1 to put the computer to sleep after the session
sleep_on_exit = 0
# Set close_watch_method to "process" to wait for the launcher process to totally die to exit (can be problematic if it closes to tray), or "window" to just wait the the window to close
close_watch_method = window
"""

ctypes.windll.shcore.SetProcessDpiAwareness(2)


# Window enumeration handler function per
# https://www.blog.pythonlibrary.org/2014/10/20/pywin32-how-to-bring-a-window-to-front/
def windowEnumerationHandler(hwnd, top_windows):
    top_windows.append((hwnd, win32gui.GetWindowText(hwnd)))


def get_process_name(p):
    # If there are permission errors reading a process name, it's probably not the one we want, so skip it.
    try:
        p_name = p.name()
    except (PermissionError, psutil.AccessDenied):
        p_name = ""
    return p_name


class GameStreamLauncher:
    def __init__(self, launch_startup_timeout=30, watch_sleep_time=5):
        self.displays = {}
        self.launch_startup_timeout = launch_startup_timeout
        self.watch_sleep_time = watch_sleep_time

        i = 0
        while True:
            try:
                d = win32api.EnumDisplayDevices(None, i)
                self.displays[d.DeviceName] = {
                    'device': d,
                    'settings': win32api.EnumDisplaySettings(d.DeviceName, win32con.ENUM_CURRENT_SETTINGS)
                }
                i += 1
            except pywintypes.error:
                break
        self.primary_display = next(iter(k for k, v in self.displays.items()
                                         if v['settings'].Position_x == 0 and v['settings'].Position_y == 0))
        self._active_display = ''

    def _change_display_settings(self, display, devmode, resolution, pos=None, primary=False):
        if pos is None:
            pos = (self.displays[display]['settings'].Position_x, self.displays[display]['settings'].Position_y)
        print(f"Setting display to {display} {resolution[0]}x{resolution[1]}+{pos[0]},{pos[1]}")
        devmode.PelsWidth = int(resolution[0])
        devmode.PelsHeight = int(resolution[1])
        devmode.Position_x = int(pos[0])
        devmode.Position_y = int(pos[1])
        devmode.Fields = win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT | win32con.DM_POSITION
        win32api.ChangeDisplaySettingsEx(display, devmode, win32con.CDS_SET_PRIMARY if primary else 0)

    @contextmanager
    def display_resolution(self, resolution, target_display=None):
        target_display = target_display or self.primary_display
        if target_display.lower() == 'primary':
            target_display = self.primary_display
        try:
            devmode = win32api.EnumDisplaySettings(target_display, win32con.ENUM_CURRENT_SETTINGS)
            self._change_display_settings(target_display, devmode, resolution, (0, 0), False)
            self._active_display = target_display
            yield
        finally:
            # Restore original layout
            win32api.ChangeDisplaySettings(None, 0)

    def is_process_running(self, name):
        return name in (get_process_name(p) for p in psutil.process_iter() if p)

    def get_window_handle(self, name):
        top_windows = []
        win32gui.EnumWindows(windowEnumerationHandler, top_windows)
        try:
            return next(iter(_[0] for _ in top_windows if _[1] == name))
        except StopIteration:
            return None

    def run_launcher(self, resolution, config_file=None, target_display='primary'):
        # Define a default config file to write if we're missing one
        config_file = Path(config_file or 'gamestream_playnite.ini')
        if not config_file.is_file():
            with config_file.open('w') as out_file:
                out_file.write(DEFAULT_CONFIG)

        # Parse the config file and assume defaults otherwise
        config = configparser.ConfigParser()
        config.read(config_file.as_posix())
        cfg_launcher_path = config['LAUNCHER'].get('launcher_path',
                                                   r'%LOCALAPPDATA%\Playnite\Playnite.FullscreenApp.exe')
        cfg_launcher_window_name = config['LAUNCHER'].get('launcher_window_name', 'Playnite')
        cfg_bg_paths = config['BACKGROUND']
        debug = config['SETTINGS'].get('debug', '0')
        sleep_on_exit = config['SETTINGS'].get('sleep_on_exit', '0')
        close_watch_method = config['SETTINGS'].get('close_watch_method', 'window')

        launcher_exec_name = os.path.basename(cfg_launcher_path)

        # Set resolution to target
        with self.display_resolution(resolution, target_display):

            # Start background programs, if they're available
            for path in cfg_bg_paths:
                expanded_path = os.path.expandvars(cfg_bg_paths[path])
                if os.path.exists(expanded_path):
                    print("Launching", expanded_path)
                    exec_name = os.path.basename(expanded_path)
                    # Kill the process first if it's already running
                    if exec_name in (get_process_name(p) for p in psutil.process_iter()):
                        os.system('taskkill /f /im ' + exec_name)
                    # Start the process
                    subprocess.Popen(expanded_path)

            # A launcher value of false will create a wait inside of the console instead watching a program
            if cfg_launcher_path.lower() == "false":
                input('Press enter to end the GameStream session.')
                return
            else:
                # Minimize all windows
                # print("Minimizing windows")
                # pyautogui.hotkey('winleft', 'd')

                # Playnite has to be killed before it will start in fullscreen mode
                if "Playnite" in launcher_exec_name:
                    if "Playnite.FullscreenApp.exe" in (get_process_name(p) for p in psutil.process_iter()):
                        os.system('taskkill /f /im ' + "Playnite.FullscreenApp.exe")
                    if "Playnite.DesktopApp.exe" in (get_process_name(p) for p in psutil.process_iter()):
                        os.system('taskkill /f /im ' + "Playnite.DesktopApp.exe")

                    # Move mouse cursor into the lower-right corner to pseudo-hide it because sticks out in playnite
                    # fullscreen
                    pyautogui.FAILSAFE = False
                    pyautogui.moveTo(9999, 9999, duration=0)

                # Start game launcher
                print("Starting game launcher")
                launcher_exe = os.path.expandvars(cfg_launcher_path)
                subprocess.Popen(launcher_exe)

                # Focus launcher in the foreground and maximize
                launch_timeout = self.launch_startup_timeout
                while launch_timeout > 0:
                    if (launcher_window_handle := self.get_window_handle(cfg_launcher_window_name)) is not None:
                        if 'fullscreen' not in cfg_launcher_path.lower():
                            print("Maximizing", cfg_launcher_window_name)
                            win32gui.ShowWindow(launcher_window_handle, 3)
                        print("Focusing", cfg_launcher_window_name)
                        win32gui.SetForegroundWindow(launcher_window_handle)
                        break
                    sleep(1)
                    launch_timeout -= 1
                else:
                    raise TimeoutError(f'Timeout waiting for launcher to start')

                # Watch for closing the launcher window to return to the system's original configuration
                if close_watch_method == "window":
                    print("Watching for launcher window to close")
                    while self.get_window_handle(cfg_launcher_window_name) is not None:
                        # print("Visible:", launcher_window_handle)
                        sleep(self.watch_sleep_time)
                        # self.reset_launcher_resolution(resolution, cfg_launcher_window_name)

                # Alternative method that waits for the process to die (can be problematic if it minimizes to system tray)
                elif close_watch_method == "process":
                    print("Watching for launcher process to die")
                    while True:
                        if launcher_exec_name in (get_process_name(p) for p in psutil.process_iter()):
                            sleep(self.watch_sleep_time)
                            # self.reset_launcher_resolution(resolution, cfg_launcher_window_name)
                        else:
                            break
                else:
                    print("No valid close_watch_method in the config. Press Enter when you're done.")
                    input()

            # Terminate background programs, if they're available
            for path in cfg_bg_paths:
                expanded_path = os.path.expandvars(cfg_bg_paths[path])
                if os.path.exists(expanded_path):
                    exec_name = os.path.basename(expanded_path)
                    print("Terminating", exec_name)
                    if exec_name in (get_process_name(p) for p in psutil.process_iter()):
                        os.system('taskkill /f /im ' + exec_name)

            # Kill gamestream
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

    def reset_launcher_resolution(self, resolution, launcher_window_name):
        # Check to ensure desired GSLP resolution is still set whenever the launcher is in focus in case it didn't reset
        # when exiting a game
        focused_window = win32gui.GetWindowText(win32gui.GetForegroundWindow()).lstrip()
        # print("Trying to match", launcher_window_name, focused_window)
        if focused_window.startswith(launcher_window_name):
            # print("Matched")
            current_width = int(win32api.GetSystemMetrics(0))
            current_height = int(win32api.GetSystemMetrics(1))
            if current_width != resolution[0] and current_height != resolution[1]:
                print(f"Resolutions don't match, changing from {current_width}x{current_height} "
                      f"to {resolution[0]}x{resolution[1]}")
                self._change_display_settings(self._active_display, resolution)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--list-displays', default=False, action="store_true",
                        help='List current displays and exit')
    parser.add_argument('width', type=int, help='Resolution Width')
    parser.add_argument('height', type=int, help='Resolution Height')
    parser.add_argument('-d', '--display', default='primary', type=str, required=False,
                        help='Which display to use (defaults to current primary)')
    parser.add_argument('-c', '--config_file', default='', type=str, required=False,
                        help='Configuration file to use (defaults to gamestream_playnite.ini which will be created if '
                             'it does not exist')
    launcher = GameStreamLauncher()
    if '-l' in sys.argv:
        for name, display in launcher.displays.items():
            print(f'{name:<14} {"primary" if name == launcher.primary_display else "":<9}'
                  f'{display["settings"].PelsWidth}x{display["settings"].PelsHeight}'
                  f'+{display["settings"].Position_x},{display["settings"].Position_y}')
        sys.exit(0)

    args = parser.parse_args()
    launcher.run_launcher((args.width, args.height), args.config_file, args.display)
