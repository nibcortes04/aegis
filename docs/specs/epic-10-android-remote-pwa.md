# Technical Specification: EPIC-10 — Android Remote PWA Pairing & Session Continuity

**Epic ID:** EPIC-10  
**GitHub Issue:** [#2](https://github.com/nibcortes04/aegis/issues/2)  
**Status:** In Progress (Sprint 2)  
**Architect:** Nicolas Cortes (@nibcortes04)  
**AI Pair Engine:** Gemini 3.8 Flash (High) via Antigravity (AGY)  

---

## 1. Executive Summary & Architecture

Google Antigravity (AGY) provides native remote supervision and session continuity capabilities via the official **Google Antigravity Remote Control PWA** hosted at **[https://antigravity.google](https://antigravity.google)**. 

Unlike traditional third-party terminal apps requiring custom APK downloads or untrusted tunnels, Google Antigravity's official architecture relies on:
1. **Official PWA (Progressive Web App):** Installable natively on Android through Google Chrome, Brave, or Samsung Internet, providing a standalone fullscreen app experience with system navigation bars hidden.
2. **Google Account Authentication:** Zero need to share unencrypted passwords or raw SSH keys; pairing and access control are bound directly to the user's authenticated Google Account.
3. **Local Daemon Synchronization (`agy remote-control`):** A lightweight background daemon on the workstation or VPS exposes secure session telemetry and receives remote human approval/rejection decisions.

**EPIC-10** establishes the definitive engineering guide, interactive CLI wizard (`aegis mobile`), and automated diagnostics for pairing Android devices with active agent sessions.

---

## 2. PWA vs. Native APK Rationale

| Feature | Official Google PWA (`antigravity.google`) | Third-Party APK |
| :--- | :---: | :---: |
| **Official Support** | 🟢 Yes (Google Antigravity Team) | 🔴 No |
| **Installation Friction** | 🟢 Zero (Install from Browser in 1-tap) | 🟡 Sideloading / Play Store delays |
| **Security Model** | 🟢 Sandboxed by Chromium & Google OAuth | 🔴 App permissions & unknown binary code |
| **Push Notifications** | 🟢 Web Push API / Service Workers | 🟢 Native notifications |
| **Update Cycle** | 🟢 Instantaneous (Server-side evergreen) | 🔴 Manual APK updates |

---

## 3. End-to-End Android Setup & Pairing Flow

```
+------------------------------------+        +-----------------------------------+
| Host Workstation / VPS             |        | Android Device (Google Chrome)    |
|                                    |        |                                   |
| 1. Run: agy remote-control start   |        | 1. Navigate to antigravity.google |
| 2. Run: aegis mobile --pair        | =====> | 2. Sign in with Google Account    |
|    (Displays ASCII QR code & URL)  |        | 3. Chrome Menu (⋮) > "Install app"|
+------------------------------------+        +-----------------+-----------------+
                                                                |
                                                                v
                                              +-----------------------------------+
                                              | Aegis / AGY Remote PWA            |
                                              | • Fullscreen monitoring           |
                                              | • Remote 2FA Tool Approvals       |
                                              | • Turn completion notifications   |
                                              +-----------------------------------+
```

### Detailed Android Installation Steps:
1. **Open Google Chrome** (or Chromium-based browser) on your Android device.
2. Navigate to: **`https://antigravity.google`**.
3. Sign in using the **same Google Account** authenticated on your Antigravity CLI or IDE.
4. When prompted by the browser banner, tap **"Install Antigravity"** (or open the three-dot menu **`⋮`** and select **"Install app"** / *"Add to Home Screen"*).
5. Launch the newly created app from your home screen or app drawer. It will run in standalone mode without browser chrome or URL bars.

---

## 4. Daemon Management Commands

On your workstation or VPS:

```bash
# Start remote control synchronization daemon
agy remote-control start

# Check current connection and daemon state
agy remote-control status

# Stop daemon when finished
agy remote-control stop
```

---

## 5. Aegis Mobile CLI Wizard (`aegis mobile`)

The Aegis CLI provides an interactive helper and diagnostic tool:

```bash
# Interactive pairing guide with ASCII QR Code
aegis mobile --pair

# Quick status check of remote control daemon
aegis mobile --status

# Full technical guide in terminal
aegis mobile --guide

# Programmatic JSON report for agents and telemetry
aegis mobile --json
```

---

## 6. MCP Integration (`aegis_get_mobile_pairing_guide`)

The MCP server exposes `aegis_get_mobile_pairing_guide` enabling autonomous agents to provide human users with step-by-step guidance whenever mobile connectivity or remote approvals are requested.
