🚀 CoinvidBot Setup Guide
Welcome to the setup guide for CoinvidBot! This document walks you through the process of setting up the bot on a Linux system (Ubuntu/Debian) with clear, concise steps. Let's get started! 🎉

📋 Prerequisites

🖥️ A Linux-based system (e.g., Ubuntu/Debian).
🔑 Root or sudo privileges.
🌐 Internet connection for downloading packages and cloning the repository.


🛠️ Setup Instructions
Follow these steps in order to configure the environment and run CoinvidBot:



Step
Command
Description



1
sudo apt update
🔄 Refresh package repository lists.


2
apt update && apt upgrade -y
🔝 Update all installed packages to the latest versions.


3
apt install python3 python3-pip libssl-dev libffi-dev -y
🐍 Install Python 3, pip, and SSL/FFI development libraries.


4
pip install python-socks
🧦 Install python-socks for SOCKS proxy support.


5
sudo apt install git
📦 Install Git for version control.


6
sudo apt install -y tmux
🖥️ Install tmux for terminal session management.


7
git --version  python3 --version  pip3 --version  tmux -V
✅ Verify versions of installed tools.


8
pip3 install python-telegram-bot dotenv stem requests
📚 Install Python libraries for Telegram bot, environment variables, Tor, and HTTP requests.


9
apt install tor -y
🕵️ Install Tor for anonymous networking.


10
systemctl start tor
▶️ Start the Tor service.


11
systemctl enable tor
🔄 Enable Tor to run on system boot.


12
sudo service tor status
🔔 Check the status of the Tor service.


13
curl --socks5 localhost:9050 https://api.ipify.org
🌐 Verify Tor connectivity by checking public IP.


14
sudo service tor restart
🔄 Restart the Tor service to apply changes.


15
git clone https://github.com/Daicool/CoinvidBot.git
📥 Clone the CoinvidBot repository.


16
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
⏰ Set system timezone to Asia/Ho_Chi_Minh.


17
tmux new -s CoinvidSession
🖼️ Create a new tmux session named "CoinvidSession".


18
tmux split-window -h
➗ Split the tmux window horizontally.


19
tmux attach-session -t CoinvidSession
🔗 Reattach to the "CoinvidSession" tmux session.



🚀 Next Steps

Navigate to the project directory:cd CoinvidBot


Configure environment variables (e.g., Telegram bot token) in a .env file.
Run the bot (refer to the project's documentation for specific commands).


⚠️ Troubleshooting

Tor not working? Check the service status with:sudo service tor status

Ensure port 9050 is open.
Missing Python libraries? Verify installed packages with:pip3 list


tmux issues? List active sessions with:tmux list-sessions




💡 Pro Tip: Keep your terminal organized with tmux to manage multiple tasks efficiently!


🌟 Happy Coding!
Thank you for using CoinvidBot! If you have questions, check the GitHub Issues page or contact the maintainers. 🎉
