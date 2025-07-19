#!/usr/bin/env python3
"""
Script para sincronizar y verificar dependencias entre requirements.txt y el entorno actual.
Ayuda a identificar dependencias instaladas que no están en requirements.txt.
"""

import subprocess
import sys
from pathlib import Path

def get_installed_packages():
    """Obtiene la lista de paquetes instalados usando uv pip list."""
    try:
        result = subprocess.run(['uv', 'pip', 'list', '--format=freeze'], 
                              capture_output=True, text=True, check=True)
        packages = {}
        for line in result.stdout.strip().split('\n'):
            if '==' in line:
                name, version = line.split('==')
                packages[name.lower()] = version
        return packages
    except subprocess.CalledProcessError as e:
        print(f"Error al obtener paquetes instalados: {e}")
        return {}

def get_requirements_packages(requirements_file):
    """Lee los paquetes del archivo requirements.txt."""
    packages = set()
    if requirements_file.exists():
        with open(requirements_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Extraer solo el nombre del paquete (sin versión ni extras)
                    package_name = line.split('==')[0].split('>=')[0].split('[')[0].strip()
                    if package_name:
                        packages.add(package_name.lower())
    return packages

def get_top_level_dependencies():
    """
    Identifica las dependencias de nivel superior (las que instalaste directamente).
    Estas son las que deberían estar en requirements.txt.
    """
    # Dependencias principales que normalmente instalas directamente
    main_deps = {
        'fastapi', 'uvicorn', 'sqlalchemy', 'asyncpg', 'psycopg2-binary',
        'passlib', 'python-jose', 'alembic', 'pydantic', 'pydantic-settings',
        'python-dotenv', 'email-validator', 'python-multipart', 'fastapi-limiter',
        'redis'
    }
    
    # Dependencias de desarrollo/testing
    dev_deps = {
        'pytest', 'pytest-asyncio', 'pytest-cov', 'httpx'
    }
    
    return main_deps, dev_deps

def main():
    project_root = Path(__file__).parent.parent
    requirements_file = project_root / 'requirements.txt'
    
    print("🔍 Analizando dependencias...")
    print("=" * 50)
    
    # Obtener paquetes instalados
    installed = get_installed_packages()
    if not installed:
        print("❌ No se pudieron obtener los paquetes instalados.")
        return 1
    
    # Obtener paquetes en requirements.txt
    requirements_packages = get_requirements_packages(requirements_file)
    
    # Obtener dependencias esperadas
    main_deps, dev_deps = get_top_level_dependencies()
    expected_deps = main_deps | dev_deps
    
    print(f"📦 Paquetes instalados: {len(installed)}")
    print(f"📝 Paquetes en requirements.txt: {len(requirements_packages)}")
    print()
    
    # Verificar dependencias principales que faltan en requirements.txt
    missing_in_requirements = []
    for dep in expected_deps:
        if dep.lower() not in requirements_packages and dep.lower() in installed:
            missing_in_requirements.append(dep)
    
    if missing_in_requirements:
        print("⚠️  Dependencias principales que faltan en requirements.txt:")
        for dep in sorted(missing_in_requirements):
            version = installed.get(dep.lower(), 'unknown')
            print(f"   - {dep}=={version}")
        print()
    
    # Verificar dependencias en requirements.txt que no están instaladas
    not_installed = []
    for dep in requirements_packages:
        if dep not in installed:
            not_installed.append(dep)
    
    if not_installed:
        print("❌ Dependencias en requirements.txt que NO están instaladas:")
        for dep in sorted(not_installed):
            print(f"   - {dep}")
        print()
    
    # Mostrar dependencias que son sub-dependencias (instaladas automáticamente)
    sub_dependencies = []
    for package in installed:
        if package not in expected_deps and package not in requirements_packages:
            sub_dependencies.append(package)
    
    if sub_dependencies:
        print("ℹ️  Sub-dependencias (instaladas automáticamente):")
        print("   (Estas NO necesitan estar en requirements.txt)")
        for dep in sorted(sub_dependencies)[:10]:  # Mostrar solo las primeras 10
            version = installed[dep]
            print(f"   - {dep}=={version}")
        if len(sub_dependencies) > 10:
            print(f"   ... y {len(sub_dependencies) - 10} más")
        print()
    
    # Resumen
    print("📊 RESUMEN:")
    if not missing_in_requirements and not not_installed:
        print("✅ Tu requirements.txt está completo y sincronizado!")
    else:
        if missing_in_requirements:
            print(f"⚠️  {len(missing_in_requirements)} dependencias faltan en requirements.txt")
        if not_installed:
            print(f"❌ {len(not_installed)} dependencias en requirements.txt no están instaladas")
    
    print(f"📄 Total de paquetes instalados: {len(installed)}")
    print(f"🎯 Dependencias principales esperadas: {len(expected_deps)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
