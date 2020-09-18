# GameStream Launchpad 🚀

GameStream Launchpad orchestrates an optimized environment for NVIDIA GameStream connections through NVIDIA Shield hardware and/or [Moonlight](https://github.com/moonlight-stream) clients. It improves the GameStream experience with the following ideas:

 1. Launch the session with a controller-optimized game launcher that automatically displays all installed games from all stores (Steam, Origin, Epic, Xbox GamePass, etc).
 2. Automatically set a specific resolution on the host during the session.
 3. Automatically end the GameStream session and revert the host resolution when exiting the launcher.
 4. Enable optional global controller remappings that only exist during the GameStream session.
 
This configuration uses [Playnite](https://github.com/JosefNemec/Playnite) fullscreen mode as the launcher and [JoyToKey](https://joytokey.net/en/) as the optional controller remapper.
 
## Dependencies
 1. Install [Python 3.8](https://www.python.org/) for Windows, ensuring that you select "Add Python to PATH" during installation.
 2. Install [pipenv](https://pypi.org/project/pipenv/) via `pip install pipenv`.
 3. Install [Playnite](https://github.com/JosefNemec/Playnite) and configure it to your liking.
 4. Install [JoyToKey](https://joytokey.net/en/) if you want your controller to have additional button mapping/combo functions.

## Setup
 1. Download this repo.
 2. In the repo directory, run `pipenv install` to setup the Python environment.
 3. Ensure that things are working by running `pipenv run gamestream_launchpad.py 1280 720` and closing Playnite.
 4. Open GeForce experience > Settings > SHIELD > ADD
 5. In the file picker, select the `.bat` script with the host resolution you want to stream.
