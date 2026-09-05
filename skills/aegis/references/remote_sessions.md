# Session Continuity and Android PWA Guide

Google Antigravity allows you to manage, resume, and supervise agent coding sessions across terminals, desktop IDEs, and mobile devices.

---

## 1. Local Session Resumption (CLI)

- **Resume Most Recent Workspace Session:**
  ```bash
  agy -c
  # or
  agy --continue
  ```
- **Resume Specific Session by ID:**
  ```bash
  agy --conversation <conversation_id>
  ```
- **Interactive Session Picker (`/resume` in TUI):**
  - Type `/resume` inside any active session.
  - Press `Ctrl+F` to toggle between flat list and workspace-grouped view.
  - Press `F2` to rename a conversation.
  - Press `F4` to delete outdated conversations.

---

## 2. Google Antigravity Remote Control

Remote Control lets you monitor and control sessions running on your workstation or VPS from any web browser or smartphone.

### Starting the Daemon
On your host or VPS:
```bash
agy remote-control start
```
Verify the daemon status:
```bash
agy remote-control status
```
To stop the daemon:
```bash
agy remote-control stop
```

---

## 3. Connecting on Android (Official PWA)

Google Antigravity Remote Control is designed as an official Progressive Web App (PWA). There is no native `.apk` on Google Play Store.

### Setup Instructions for Android:
1. Open **Google Chrome** on your Android device.
2. Navigate to: **[https://antigravity.google](https://antigravity.google)** (or scan the QR code from Antigravity 2.0 desktop app: Settings > App > Enable Remote Control).
3. Sign in with the **same Google Account** used in your CLI or IDE.
4. Tap the three-dot menu (**`⋮`**) in the top right corner of Chrome.
5. Tap **"Install app"** (or *"Add to Home Screen"*).
6. The app is now installed on your Android device:
   - Fullscreen immersive UI without browser URL bars.
   - Real-time task inspection.
   - Remote tool approvals/denials from your phone.
   - Native push notifications when tasks complete.
