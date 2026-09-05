#!/usr/bin/env python3
"""
Official Antigravity Plugin Packaging Utility for Aegis
Empaqueta y valida la distribución oficial del plugin para:
- Instalaciones manuales o por URL (tar.gz / zip).
- Futuro registro en Google Antigravity Plugin Registry (agy plugin publish).
- Garantía criptográfica de integridad SHA-256 y cero artefactos de desarrollo.
"""

import os
import sys
import json
import re
import shutil
import tarfile
import zipfile
import hashlib
import tempfile
import argparse

# Constantes de empaquetado
REQUIRED_MANIFEST_FIELDS = ["name", "version", "description", "author", "license"]
SEMVER_REGEX = re.compile(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$")

ESSENTIAL_RUNTIME_FILES = [
    "plugin.json",
    "hooks.json",
    "README.md",
    "LICENSE",
    "rules/AGENTS.md",
    "skills/aegis/SKILL.md",
    "mcp/mcp_server.py",
    "scripts/agy_hook_handler.py",
    "scripts/statusline_formatter.py",
    "scripts/env_detector.py",
    "scripts/trust_levels.py",
    "scripts/env_inspector.py",
    "scripts/dev-worktree.sh",
    "scripts/agy-hook-dispatcher.sh",
]

EXCLUDE_DIR_PATTERNS = {
    ".git",
    ".github",
    "tests",
    "docs",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".user_uploaded",
    ".tempmediaStorage",
    "scratch",
}

EXCLUDE_FILE_PATTERNS = [
    r"\.py[co]$",
    r"\.DS_Store$",
    r"\.log$",
    r"^\.env.*",
    r"\.sw[po]$",
    r"\.tmp$",
]

def validate_manifest(repo_root):
    """Valida que plugin.json exista y cumpla el esquema oficial."""
    manifest_path = os.path.join(repo_root, "plugin.json")
    if not os.path.isfile(manifest_path):
        raise ValueError(f"No se encontró el manifiesto obligatorio: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            raise ValueError(f"Error parseando plugin.json: {e}")

    for field in REQUIRED_MANIFEST_FIELDS:
        if field not in data or not data[field]:
            raise ValueError(f"Campo obligatorio '{field}' ausente o vacío en plugin.json")

    version = str(data["version"]).strip()
    if not SEMVER_REGEX.match(version):
        raise ValueError(f"La versión '{version}' no sigue el formato SemVer (ej. 1.5.0)")

    return data

def validate_essential_files(repo_root):
    """Verifica que todos los archivos esenciales del runtime existan."""
    missing = []
    for rel_path in ESSENTIAL_RUNTIME_FILES:
        full_path = os.path.join(repo_root, rel_path)
        if not os.path.isfile(full_path):
            missing.append(rel_path)
    if missing:
        raise FileNotFoundError(f"Faltan archivos esenciales del runtime: {', '.join(missing)}")
    return True

def should_exclude(rel_path):
    """Determina si un archivo o ruta debe excluirse del bundle."""
    parts = rel_path.split(os.sep)
    for part in parts:
        if part in EXCLUDE_DIR_PATTERNS:
            return True

    filename = parts[-1]
    for pattern in EXCLUDE_FILE_PATTERNS:
        if re.search(pattern, filename, re.IGNORECASE):
            return True

    return False

def collect_files_to_package(repo_root):
    """Recolecta todos los archivos válidos para el bundle respetando exclusiones."""
    collected = []
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIR_PATTERNS]

        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, repo_root)
            if not should_exclude(rel_path):
                collected.append(rel_path)

    collected.sort()
    return collected

def compute_sha256(file_path):
    """Calcula el hash SHA-256 de un archivo."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def create_tarball(repo_root, file_list, output_path, root_prefix="aegis"):
    """Crea archivo tar.gz con permisos normalizados y prefijo de directorio."""
    with tarfile.open(output_path, "w:gz") as tar:
        for rel_path in file_list:
            full_path = os.path.join(repo_root, rel_path)
            arcname = os.path.join(root_prefix, rel_path)
            
            tarinfo = tar.gettarinfo(full_path, arcname=arcname)
            tarinfo.uid = 0
            tarinfo.gid = 0
            tarinfo.uname = "aegis"
            tarinfo.gname = "aegis"
            if rel_path.endswith((".sh", ".py")) or os.access(full_path, os.X_OK):
                tarinfo.mode = 0o755
            else:
                tarinfo.mode = 0o644
            
            if os.path.islink(full_path):
                tar.addfile(tarinfo)
            else:
                with open(full_path, "rb") as f:
                    tar.addfile(tarinfo, f)

def create_zip(repo_root, file_list, output_path, root_prefix="aegis"):
    """Crea archivo .zip con compresión deflate y prefijo de directorio."""
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel_path in file_list:
            full_path = os.path.join(repo_root, rel_path)
            arcname = os.path.join(root_prefix, rel_path)
            zf.write(full_path, arcname)

def verify_bundle_integrity(archive_path, expected_files, root_prefix="aegis"):
    """Extrae el archivo generado en un directorio temporal y valida su integridad."""
    temp_extract = tempfile.mkdtemp(prefix="aegis_verify_")
    try:
        if archive_path.endswith(".tar.gz"):
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(temp_extract)
        elif archive_path.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(temp_extract)
        else:
            raise ValueError(f"Formato no soportado para verificación: {archive_path}")

        extracted_root = os.path.join(temp_extract, root_prefix)
        if not os.path.isdir(extracted_root):
            raise AssertionError(f"El prefijo raíz '{root_prefix}' no existe en el archivo extraído")

        for req in expected_files:
            target = os.path.join(extracted_root, req)
            if not os.path.exists(target):
                raise AssertionError(f"Archivo requerido ausente tras extracción: {req}")

        for root, dirs, files in os.walk(extracted_root):
            for d in dirs:
                if d in EXCLUDE_DIR_PATTERNS:
                    raise AssertionError(f"Directorio prohibido detectado en bundle: {d}")
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), extracted_root)
                if should_exclude(rel):
                    raise AssertionError(f"Archivo prohibido detectado en bundle: {rel}")

        return True, "Integridad 100% verificada"
    finally:
        shutil.rmtree(temp_extract, ignore_errors=True)

def package_plugin(repo_root, output_dir, verify=True, dry_run=False):
    """Orquesta la validación, construcción y verificación del paquete."""
    manifest = validate_manifest(repo_root)
    validate_essential_files(repo_root)
    
    pkg_name = manifest["name"]
    version = manifest["version"]
    
    files_to_pkg = collect_files_to_package(repo_root)
    
    print(f"📦 Empaquetador Oficial de Plugins Antigravity — Aegis v{version}")
    print(f"✔ Manifiesto validado: {pkg_name} v{version} ({manifest.get('license', 'MIT')})")
    print(f"✔ Archivos esenciales verificados: {len(ESSENTIAL_RUNTIME_FILES)} requeridos presentes")
    print(f"✔ Total de archivos incluidos: {len(files_to_pkg)}")

    if dry_run:
        print("\n🔍 Modo DRY-RUN (simulación activa):")
        for f in files_to_pkg:
            print(f"  + {f}")
        return {"version": version, "files_count": len(files_to_pkg), "dry_run": True}

    os.makedirs(output_dir, exist_ok=True)
    
    tar_name = f"{pkg_name}-v{version}.tar.gz"
    zip_name = f"{pkg_name}-v{version}.zip"
    tar_path = os.path.join(output_dir, tar_name)
    zip_path = os.path.join(output_dir, zip_name)
    checksum_path = os.path.join(output_dir, "checksums.sha256")

    print(f"\nGenerando archivos de distribución en '{output_dir}'...")
    create_tarball(repo_root, files_to_pkg, tar_path, root_prefix=pkg_name)
    create_zip(repo_root, files_to_pkg, zip_path, root_prefix=pkg_name)

    tar_hash = compute_sha256(tar_path)
    zip_hash = compute_sha256(zip_path)

    with open(checksum_path, "w", encoding="utf-8") as f:
        f.write(f"{tar_hash}  {tar_name}\n")
        f.write(f"{zip_hash}  {zip_name}\n")

    print(f"✔ Tarball: {tar_name} ({os.path.getsize(tar_path):,} bytes)")
    print(f"✔ Zip:     {zip_name} ({os.path.getsize(zip_path):,} bytes)")
    print(f"✔ Hashes:  checksums.sha256")

    if verify:
        print("\nEjecutando prueba de auto-integridad post-empaquetado...")
        ok_tar, msg_tar = verify_bundle_integrity(tar_path, ESSENTIAL_RUNTIME_FILES, root_prefix=pkg_name)
        ok_zip, msg_zip = verify_bundle_integrity(zip_path, ESSENTIAL_RUNTIME_FILES, root_prefix=pkg_name)
        if not ok_tar or not ok_zip:
            raise RuntimeError(f"Fallo en la prueba de integridad: tar={msg_tar}, zip={msg_zip}")
        print("✔ Prueba de auto-integridad superada con éxito (tar.gz y zip)")

    return {
        "name": pkg_name,
        "version": version,
        "tarball": tar_path,
        "zip": zip_path,
        "checksums": checksum_path,
        "tar_hash": tar_hash,
        "zip_hash": zip_hash,
        "files_count": len(files_to_pkg),
    }

def main():
    parser = argparse.ArgumentParser(description="Antigravity Plugin Packaging Utility")
    parser.add_argument("-o", "--output-dir", default="dist", help="Directorio de salida (default: dist/)")
    parser.add_argument("--repo-root", default=".", help="Ruta al repositorio raíz de Aegis")
    parser.add_argument("--dry-run", action="store_true", help="Simula el empaquetado y lista archivos")
    parser.add_argument("--no-verify", action="store_true", help="Omite la prueba de auto-integridad")
    parser.add_argument("--version", action="store_true", help="Muestra la versión del plugin y sale")

    args = parser.parse_args()

    repo_root = os.path.abspath(args.repo_root)

    if args.version:
        manifest = validate_manifest(repo_root)
        print(f"v{manifest['version']}")
        return

    try:
        package_plugin(
            repo_root=repo_root,
            output_dir=os.path.abspath(args.output_dir),
            verify=not args.no_verify,
            dry_run=args.dry_run
        )
        print("\n✨ Empaquetado completado satisfactoriamente.")
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
