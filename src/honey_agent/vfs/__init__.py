"""
Módulo VFS: Sistema de Archivos Virtual en Memoria (Zero-Disk).
"""

from honey_agent.vfs.in_memory_tree import VFSNode, VirtualFileSystem
from honey_agent.vfs.skeleton import populate_ubuntu_skeleton
from honey_agent.vfs.session_state import SessionState

__all__ = ["VFSNode", "VirtualFileSystem", "populate_ubuntu_skeleton", "SessionState"]
