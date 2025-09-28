# Github_FA

A lightweight **Python 3.8+** script that automatically fetches trending GitHub repositories, generates short Farsi captions using **DeepSeek API**, and posts them to a **Telegram channel**.

---

## Features

* 📡 Fetches trending GitHub repositories (daily).
* 🧠 Uses DeepSeek API for short Farsi introductions.
* 📢 Sends message/photo to Telegram channel via Bot API.
* 🕒 Fully cron-job friendly (every hour).
* 🔑 Loads secrets from `.env` file (no hard-coded tokens).
* 🪶 Pure Python standard libraries (no `pip install` required).

---

## Requirements

* Python **3.8+** (tested on cPanel ALT Python 3.8.20).
* A **Telegram Bot Token** (via [@BotFather](https://t.me/BotFather)).
* Your **Telegram Channel ID** (e.g. `@mychannel`).
* A **DeepSeek API Key**.

---

## Installation on cPanel Hosting

1. **Create a new Python project in cPanel**  
   - Go to **cPanel → Setup Python App** (sometimes called *Python Selector*).  
   - Choose **Python 3.8+** (recommended: ALT Python 3.8).  
   - Set an application root, e.g.:  
     ```
     /home/<username>/trending_bot
     ```  
   - Save the project.

2. **Upload the project files** into that directory.

3. **Create `.env` file** inside the same directory:

   ```env
   TG_BOT_TOKEN=123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   TG_CHANNEL_ID=@MyChannel
   DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
   ```

4. **Set up cron job (cPanel):**  
   - Open **cPanel → Cron Jobs**.  
   - Add a new cron job with the following settings:  

     * **Minute:** `0`  
     * **Hour:** `*`  
     * **Day:** `*`  
     * **Month:** `*`  
     * **Weekday:** `*`  
     * **Command:**  
       ```bash
       /opt/alt/python38/bin/python3.8 /home/<username>/trending_bot/trending_bot.py >> /home/<username>/trending_bot/trending_bot.log 2>&1
       ```

   This will run the bot **once every hour at minute 0** and save logs in `trending_bot.log`.

---

## Installation on VPS (SSH)

1. **Clone the repository:**  
   ```bash
   git clone https://github.com/TBmohammad/Github_FA.git
   cd Github_FA
   ```

2. **Create `.env` file:**  
   ```bash
   nano .env
   ```

   ```env
   TG_BOT_TOKEN=123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   TG_CHANNEL_ID=@MyChannel
   DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
   ```

3. **Make the script executable:**  
   ```bash
   chmod +x trending_bot.py
   ```

4. **Run manually:**  
   ```bash
   python3 trending_bot.py
   ```

5. **Set up cron job (Linux crontab):**  
   ```bash
   crontab -e
   ```

   Add this line:  
   ```cron
   0 * * * * /usr/bin/python3 /home/<username>/Github_FA/trending_bot.py >> /home/<username>/Github_FA/trending_bot.log 2>&1
   ```

---

## Logs

* All output and errors are appended to:  
  ```
  /home/<username>/trending_bot/trending_bot.log
  ```

* View logs:  
  ```bash
  cat /home/<username>/trending_bot/trending_bot.log
  ```

---

## Notes

* On **cPanel shared hosting**, always use `/opt/alt/python38/bin/python3.8`.  
* On **VPS/SSH**, you can use `/usr/bin/python3`.  
* For security, keep `.env` outside `public_html` on cPanel.  
