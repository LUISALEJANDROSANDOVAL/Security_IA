"""
tests/fakes/filesystem.py
Dueño: Programador 1 (P1).
Responsabilidad: Fixtures y fakes del sistema de archivos en RAM para pruebas de todos los módulos.
"""

from honey_agent.vfs.in_memory_tree import VirtualFileSystem
from honey_agent.vfs.skeleton import populate_ubuntu_skeleton
from honey_agent.vfs.session_state import SessionState

def create_fake_vfs() -> VirtualFileSystem:
    """Crea una instancia de VFS aislada con el esqueleto canónico de Ubuntu."""
    vfs = VirtualFileSystem()
    populate_ubuntu_skeleton(vfs)
    return vfs

def create_fake_session(username: str = "root") -> SessionState:
    """Crea una sesión de prueba en memoria con su propio VFS clonado."""
    vfs = create_fake_vfs()
    return SessionState(vfs=vfs, username=username)
