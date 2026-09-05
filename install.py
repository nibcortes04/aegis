#!/usr/bin/env python3
"""
Universal Cross-Platform Installer for AGY PowerPack
Compatible with Linux, macOS, and Windows.
Executes natively with standard Python 3.8+ (no third-party dependencies required).
"""

import sys
import os
import shutil
import json
import platform
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, "scripts"))
import env_detector

def print_banner():
    print("====================================================")
    print("   AGY PowerPack Universal Installer (Cross-Platform)  ")
    print("====================================================")
    print(f"• Detected OS      : {env_detector.get_os_type().upper()}")
    print(f"• Active Surface   : {env_detector.get_surface_type().upper()}")
    print(f"• Terminal Engine  : {env_detector.get_terminal_type().upper()}")
    print(f"• Python Runtime   : {sys.executable} (v{platform.python_version()})")
    print("----------------------------------------------------")

def setup_directories():
    home = os.path.expanduser("~")
    scripts_dir = os.path.join(home, "scripts")
    app_data_dir = env_detector.get_app_data_dir()
    config_dir = os.path.expanduser("~/.gemini/config")
    skills_dir = os.path.join(app_data_dir, "skills")

    for d in [scripts_dir, app_data_dir, config_dir, skills_dir]:
        os.makedirs(d, exist_ok=True)

    return scripts_dir, app_data_dir, config_dir, skills_dir

def copy_scripts(scripts_dir):
    print(f"▶ Installing scripts to: {scripts_dir}")
    source_scripts = os.path.join(SCRIPT_DIR, "scripts")
    files_to_copy = [
        "env_detector.py",
        "trust_levels.py",
        "agy_hook_handler.py",
        "agy-hook-dispatcher.sh",
        "statusline_formatter.py",
        "statusline.sh",
        "agy-session.sh",
        "dev-worktree.sh",
        "env_inspector.py",
    ]

    for fname in files_to_copy:
        src = os.path.join(source_scripts, fname)
        dst = os.path.join(scripts_dir, fname)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            if not fname.endswith(".py") or env_detector.get_os_type() != "windows":
                try:
                    os.chmod(dst, 0o755)
                except Exception:
                    pass

    # Enlazar o copiar CLI helper si ~/.local/bin existe
    local_bin = os.path.expanduser("~/.local/bin")
    if os.path.isdir(local_bin) and env_detector.get_os_type() != "windows":
        target_link = os.path.join(local_bin, "agy-session")
        src_script = os.path.join(scripts_dir, "agy-session.sh")
        try:
            if os.path.lexists(target_link):
                os.remove(target_link)
            os.symlink(src_script, target_link)
            print("✔ Symlink ~/.local/bin/agy-session created.")
        except Exception:
            pass

def install_skill(skills_dir):
    src_skill = os.path.join(SCRIPT_DIR, "skills", "agy-powerpack")
    dst_skill = os.path.join(skills_dir, "agy-powerpack")
    print(f"▶ Installing Skill to: {dst_skill}")

    if os.path.exists(dst_skill):
        shutil.rmtree(dst_skill)
    shutil.copytree(src_skill, dst_skill)
    print("✔ Skill agy-powerpack installed.")

def configure_hooks(config_dir, scripts_dir):
    hooks_file = os.path.join(config_dir, "hooks.json")
    print(f"▶ Verifying Lifecycle Hooks in: {hooks_file}")

    data = {}
    if os.path.isfile(hooks_file):
        try:
            with open(hooks_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    py_exe = sys.executable
    hook_script = os.path.join(scripts_dir, "agy_hook_handler.py")

    # En Windows usamos directamente python executable con comillas
    if env_detector.get_os_type() == "windows":
        pre_tool_cmd = f'"{py_exe}" "{hook_script}" PreToolUse'
        stop_cmd = f'"{py_exe}" "{hook_script}" Stop'
    else:
        dispatcher = os.path.join(scripts_dir, "agy-hook-dispatcher.sh")
        if os.path.isfile(dispatcher):
            pre_tool_cmd = f"{dispatcher} PreToolUse"
            stop_cmd = f"{dispatcher} Stop"
        else:
            pre_tool_cmd = f'python3 "{hook_script}" PreToolUse'
            stop_cmd = f'python3 "{hook_script}" Stop'

    expected_entry = {
        "PreToolUse": [
            {
                "matcher": "*",
                "hooks": [
                    {
                        "type": "command",
                        "command": pre_tool_cmd,
                        "timeout": 10
                    }
                ]
            }
        ],
        "Stop": [
            {
                "type": "command",
                "command": stop_cmd,
                "timeout": 10
            }
        ]
    }

    # Idempotencia: Verificar si ya está exactamente configurado
    if data.get("agy-powerpack") == expected_entry:
        print("✔ Hooks already active and correctly configured (idempotent, no rewrite needed).")
        return

    if os.path.isfile(hooks_file):
        shutil.copy2(hooks_file, f"{hooks_file}.bak.{int(time.time())}")

    data["agy-powerpack"] = expected_entry

    with open(hooks_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("✔ Hooks registered successfully.")

def configure_settings(app_data_dir, scripts_dir):
    settings_file = os.path.join(app_data_dir, "settings.json")
    print(f"▶ Configuring settings in: {settings_file}")

    data = {}
    if os.path.isfile(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    # Configuración de statusline
    if env_detector.get_os_type() == "windows":
        status_script = os.path.join(scripts_dir, "statusline_formatter.py")
        status_cmd = f'"{sys.executable}" "{status_script}"'
    else:
        status_script = os.path.join(scripts_dir, "statusline.sh")
        status_cmd = status_script

    expected_statusline = {
        "type": "command",
        "command": status_cmd,
        "enabled": True
    }

    # Comandos seguros estándar para el allowlist
    standard_cmds = [
        "command(git)", "command(pnpm)", "command(npm)", "command(yarn)",
        "command(cargo)", "command(python3)", "command(python)", "command(pytest)",
        "command(node)", "command(npx)", "command(which)", "command(pwd)",
        "command(docker ps)", "command(docker logs)", "command(cat)", "command(tail)",
        "command(head)", "command(cp)", "command(echo)", "command(grep)", "command(cut)",
        "command(ls)", "command(find)", "command(mkdir)", "command(touch)", "command(wc)"
    ]

    current_allow = data.get("permissions", {}).get("allow", [])
    has_all_cmds = all(cmd in current_allow for cmd in standard_cmds)
    is_mode_set = data.get("mode") == "accept-edits"
    is_statusline_set = data.get("statusLine") == expected_statusline
    is_trust_level_set = data.get("autoModeLevel") in ["audit", "workspace-safe", "full-developer", "subagent-worker"]

    if is_mode_set and is_statusline_set and has_all_cmds and is_trust_level_set:
        print("✔ settings.json already configured (idempotent, no rewrite needed).")
        return

    if os.path.isfile(settings_file):
        shutil.copy2(settings_file, f"{settings_file}.bak.{int(time.time())}")

    data["mode"] = "accept-edits"
    data["statusLine"] = expected_statusline
    if "autoModeLevel" not in data:
        data["autoModeLevel"] = "workspace-safe"

    allowlist = data.setdefault("permissions", {}).setdefault("allow", [])
    for cmd in standard_cmds:
        if cmd not in allowlist:
            allowlist.append(cmd)

    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("✔ settings.json configured successfully.")

def main():
    print_banner()
    scripts_dir, app_data_dir, config_dir, skills_dir = setup_directories()
    copy_scripts(scripts_dir)
    install_skill(skills_dir)
    configure_hooks(config_dir, scripts_dir)
    configure_settings(app_data_dir, scripts_dir)

    # 5. Ejecutar escaneo autónomo del entorno e incorporar herramientas locales
    print("\n▶ Running Autonomous Environment Inspector...")
    try:
        sys.path.insert(0, scripts_dir)
        import env_inspector
        profile = env_inspector.inspect_environment()
        _, added = env_inspector.apply_profile(profile)
        print(f"✔ Environment profile: {profile['total_tools_found']} developer tools detected.")
        if added > 0:
            print(f"✔ Personalized Auto Mode allowlist populated with {added} new safe commands.")
    except Exception as e:
        print(f"⚠️ Inspector note: {e}")

    print("\n🎉 Installation completed successfully on all platforms!")
    print("----------------------------------------------------")
    print("• Auto Mode    : Active (accept-edits) with graduated Trust Levels")
    print("• Safety Gate  : Two-Factor Double Confirmation enabled for destructive commands")
    print("• Statusline   : 3-line Claude Code format with local quota reset")
    print("• Notifications: Single-card replacement & test silence active")
    print("====================================================")

if __name__ == "__main__":
    main()
