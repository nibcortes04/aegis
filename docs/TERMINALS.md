# 🖥️ Terminal Emulators Setup & Bell Configuration Guide

This guide provides step-by-step configuration instructions for popular terminal emulators on Linux, macOS, and Windows to ensure tab notification bells (🔔) and visual alerts render properly without disruptive audio beeps.

---

## 🐧 Linux Terminals

### 1. KDE Konsole (Primary Reference Setup)
*Tested on KDE Plasma 6.3 / Fedora Linux*
- **Tab Bell Icon:** Konsole automatically intercepts the ASCII BEL (`\a`) emitted by `Aegis` and displays a bell icon 🔔 directly on the active tab header.
- **Visual Bell Configuration:**
  1. Open **Settings > Edit Current Profile > Advanced**.
  2. Under **Terminal features**, set **Bell Mode** to **"System Notifications"** or **"Visual Bell"**.
  3. Ensure **"No Bell"** is NOT selected if you want desktop integration.

### 2. Orca Terminal
- Orca directly receives agent lifecycle events via its local agent hook daemon (`endpoint.env`).
- `Aegis` synchronizes hook payloads over HTTP/JSON to the Orca server, triggering tab status updates and panel indicators natively.

### 3. Kitty
Add to your `~/.config/kitty/kitty.conf`:
```conf
# Disable intrusive audio chime
enable_audio_bell no

# Enable visual window alert on tab bar
window_alert_on_bell yes

# Visual bell flash duration (ms)
visual_bell_duration 0.1
```

### 4. Alacritty
Add to your `~/.config/alacritty/alacritty.toml`:
```toml
[bell]
animation = "EaseOut"
duration = 150
color = "#38bdf8"
command = { program = "notify-send", args = ["AGY", "Task finished"] }
```

### 5. GNOME Terminal / Ptyxis
- Go to **Preferences > Profiles > [Active Profile] > General**.
- Toggle **"Terminal bell"** ON.
- Set desktop notification permissions in GNOME Settings > Notifications > Terminal.

---

## 🍏 macOS Terminals

### 1. iTerm2 (Recommended for macOS)
1. Open **Preferences (⌘+,) > Profiles > Terminal**.
2. Under **Notifications**:
   - Check **"Silence bell"** (to prevent audio chimes).
   - Check **"Show bell icon in tabs"** (displays 🔔 in the tab title).
   - Check **"Send notification when session ends / bell rings"**.

### 2. Terminal.app (macOS Built-in)
1. Open **Settings > Profiles > Advanced**.
2. Under **Bell**:
   - Check **"Visual bell"** (flashes screen softly).
   - Check **"Bounce icon in Dock"**.
   - Uncheck **"Audible bell"**.

---

## 🪟 Windows Terminals

### 1. Windows Terminal (Windows 10/11 Default)
Add to your `settings.json` profile configuration:
```json
{
  "profiles": {
    "defaults": {
      "bellStyle": ["taskbar", "window"]
    }
  }
}
```
- `"taskbar"`: Flashes the Windows taskbar icon when AGY requires approval or finishes a turn.
- `"window"`: Subtle in-window visual flash.

### 2. Mintty (Git Bash / MSYS2)
1. Right-click the title bar > **Options...**
2. Go to **Window**.
3. Under **Bell**, select **"Taskbar flash"** or **"Visual"** and uncheck **"Sound"**.
