# Cosmos Fable

A modern **Bento Glass** cross-platform tracker built with Python and Flet for daily nutrition (macros), adaptive workout cycles, and focused study notes.

## Quick Start (Desktop)

### Linux (One-Command Auto Setup)
Automatically creates a virtual environment, installs dependencies, adds a desktop shortcut, and launches the app:
```bash
git clone https://github.comphantomclientprivat-gif/cosmos-fable.git && cd cosmos-fable && ./setup.sh
```

### Windows / macOS (Manual Setup)
```bash
git clone https://github.comphantomclientprivat-gif/cosmos-fable.git
cd cosmos-fable
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Download for Android

Download **cosmos fable.apk** directly from the [Releases](https://github.com/phantomclientprivat-gif/cosmos-fable/releases/tag/v1.0.0) page.

1. Open the link above on your Android smartphone and expand **Assets**.
2. Tap **cosmos_fable.apk** to download it.
3. Open the downloaded file and allow installation from unknown sources if prompted.

## Wi-Fi Sync Guide (Phone <-> PC)

Cosmos Fable includes a built-in local HTTP sync server (port `8765`) so you can transfer your workouts, nutrition logs, and notes between your phone and PC without cables or internet access:

1. **Connect to the same Wi-Fi:** Make sure both your PC and Android phone are connected to the same home Wi-Fi router.
2. **Open the app on both devices:** Launch **Cosmos Fable** on your PC and your smartphone.
3. **Find the host IP address:** Look at the top-left corner of the screen (or open the **Profile** tab -> **Wi-Fi Sync** card) on the device you want to connect to — you will see its local IP (for example, `192.168.1.11`).
4. **Enter IP and Sync:** On the second device, go to the **Profile** tab, enter that IP address into the **Peer device IP** field, and tap **Sync** (or tap the sync icon in the top-right corner).
5. **Automatic Two-Way Merge:** The app compares timestamps (`updated_at`) and automatically transfers the newest database in the right direction. The peer IP is saved automatically for future one-tap syncs.

> **Firewall Note:** If you are using Windows or a strict Linux firewall (`ufw`/`firewalld`), allow incoming local connections on TCP port `8765`.
