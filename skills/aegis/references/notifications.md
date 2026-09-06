# Terminal Bell and Notifications Reference

This guide details how `Aegis` communicates with terminal emulators and desktop notification daemons.

---

## 1. Terminal Tab Bell (🔔)

Modern terminal emulators (KDE Konsole, Orca, iTerm2, Kitty, WezTerm, Alacritty) listen for the standard ASCII BEL character:
- Byte: `\a` or `\007` (Hex `0x07`).
- Target: `/dev/tty` (the controlling terminal of the process).

### Strict Policy: Interactive/Blocking Only
To avoid intrusive "Timbre en <sesión>" popups in terminal emulators (e.g. KDE Konsole) whenever routine commands or responses finish:
- **Terminal Bell is ONLY emitted when human intervention is required to advance**:
  1. `ask_question`: Agent is blocked waiting for interactive user response.
  2. `PreToolUse` with `decision: "ask"`: Tool execution requires interactive user approval (plan mode mutation, dangerous command confirmation, or untrusted action).
- **Terminal Bell is NEVER emitted on routine turn completions (`Stop`)**: Normal response completion sends a non-intrusive desktop notification (`notify-send`) without triggering terminal emulator bells.

```python
with open("/dev/tty", "w") as tty:
    tty.write("\a")
    tty.flush()
```
This triggers:
1. **The Bell icon in the terminal tab:** Indicates that the background agent is actively blocked waiting for user input.
2. **KDE Konsole / Desktop Alert:** Alerting the user that their decision is required to proceed.

---

## 2. Desktop Notifications (notify-send)

Desktop notifications use the FreeDesktop D-Bus notification specification.

### Preventing Sticky Notifications in KDE Plasma:
In KDE Plasma and several Linux environments:
- Setting `urgency=critical` forces the notification to remain on screen until manually clicked or dismissed with the close button.
- Setting `urgency=normal` combined with `-t 4000` (timeout of 4000ms) and `-h int:transient:1` ensures the notification appears and automatically fades away after 4 seconds:

```bash
notify-send -a "AGY" -u normal -t 4000 -h int:transient:1 -i utilities-terminal "AGY: [Sesión]" "Respuesta completada"
```
