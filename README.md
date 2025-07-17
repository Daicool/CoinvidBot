CoinvidBot Setup Guide
This guide provides step-by-step instructions to set up the CoinvidBot project on a Linux system (Ubuntu/Debian). Follow the commands in order to configure the environment, install dependencies, and run the bot.
Prerequisites

A Linux-based system (e.g., Ubuntu/Debian).
Root or sudo privileges.
Internet connection for downloading packages and cloning the repository.

Setup Instructions

Update Package ListsRefresh the system's package repository to ensure you have the latest package information.
sudo apt update


Upgrade System PackagesUpdate all installed packages to their latest versions.
apt update && apt upgrade -y


Install Python and Development LibrariesInstall Python 3, pip, and required development libraries for SSL and FFI.
apt install python3 python3-pip libssl-dev libffi-dev -y


Install python-socksInstall the python-socks library to enable SOCKS proxy support.
pip install python-socks


Install GitInstall Git for version control and cloning the repository.
sudo apt install git


Install tmuxInstall tmux for managing terminal sessions.
sudo apt install -y tmux


Verify Installed VersionsCheck the versions of installed tools to ensure successful installation.
git --version
python3 --version
pip3 --version
tmux -V


Install Python DependenciesInstall Python libraries required for the bot: python-telegram-bot, dotenv, stem, and requests.
pip3 install python-telegram-bot dotenv stem requests


Install TorInstall Tor for anonymous network communication.
apt install tor -y


Start Tor ServiceLaunch the Tor service.
systemctl start tor


Enable Tor on BootConfigure Tor to start automatically on system boot.
systemctl enable tor


Check Tor StatusVerify that the Tor service is running.
sudo service tor status


Test Tor ConnectivityCheck your public IP through Tor's SOCKS5 proxy to confirm it’s working.
curl --socks5 localhost:9050 https://api.ipify.org


Restart Tor ServiceRestart Tor to apply any changes.
sudo service tor restart


Clone CoinvidBot RepositoryDownload the CoinvidBot source code from GitHub.
git clone https://github.com/Daicool/CoinvidBot.git


Set TimezoneConfigure the system timezone to Asia/Ho_Chi_Minh.
sudo timedatectl set-timezone Asia/Ho_Chi_Minh


Create a tmux SessionStart a new tmux session named "CoinvidSession" for running the bot.
tmux new -s CoinvidSession


Split tmux WindowSplit the tmux window horizontally for multitasking.
tmux split-window -h


Reattach to tmux SessionReconnect to the "CoinvidSession" if disconnected.
tmux attach-session -t CoinvidSession



Next Steps

Navigate to the CoinvidBot directory (cd CoinvidBot).
Configure any required environment variables (e.g., Telegram bot token) in a .env file.
Run the bot using the appropriate command (refer to the project's documentation).

Troubleshooting

If Tor fails to connect, check the service status with sudo service tor status and ensure port 9050 is open.
Verify Python dependencies are installed correctly using pip3 list.
For tmux issues, ensure the session name is correct or list active sessions with tmux list-sessions.

Happy coding with CoinvidBot!
