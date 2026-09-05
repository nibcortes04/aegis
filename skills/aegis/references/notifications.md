# Terminal Bell and Notifications Reference

This guide details how `Aegis` communicates with terminal emulators and desktop notification daemons.

---

## 1. Terminal Tab Bell (🔔)

Modern terminal emulators (KDE Konsole, Orca, iTerm2, Kitty, WezTerm, Alacritty) listen for the standard ASCII BEL character:
- Byte: `\a` or `\007` (Hex `0x07`).
- Target: `/dev/tty` (the controlling terminal of the process).

When `agy` finishes answering (`Stop` hook) or is waiting for user confirmation (`PreToolUse` hook with `ask`), the handler writes directly to `/dev/tty`:
```python
with open("/dev/tty", "w") as tty:
    tty.write("\a")
    tty.write("\033]9;AGY: Notificación\007")
    tty.write("\033]777;notify;AGY;Notificación\007")
    tty.flush()
```
This triggers:
1. **The Bell icon in the terminal tab:** Indicates that the background agent is ready or waiting.
2. **KDE Konsole / Desktop Audio/Visual Bell:** Configurable in Konsole settings.

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
