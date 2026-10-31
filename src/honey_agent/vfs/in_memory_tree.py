"""
src/honey_agent/vfs/in_memory_tree.py
Dueño: Programador 1 (P1).
Responsabilidad: Árbol de inodos en RAM (Zero-Disk) y operaciones atómicas de archivos.
"""

from __future__ import annotations
import copy
import time
from typing import Dict, List, Optional, Tuple

class VFSNode:
    """Representación en memoria de un inodo (archivo o directorio)."""

    def __init__(
        self,
        name: str,
        is_dir: bool = False,
        owner: str = "root",
        group: str = "root",
        permissions: int = 0o755,
        content: bytes = b"",
    ):
        self.name = name
        self.is_dir = is_dir
        self.owner = owner
        self.group = group
        self.permissions = permissions
        self.content = content
        self.mtime = time.time()
        self.ctime = self.mtime
        self.children: Dict[str, VFSNode] = {} if is_dir else {}

    @property
    def size(self) -> int:
        return 4096 if self.is_dir else len(self.content)

class VirtualFileSystem:
    """Sistema de Archivos Virtual que opera exclusivamente en memoria RAM."""

    def __init__(self):
        self.root = VFSNode(name="", is_dir=True)

    def normalize_path(self, path: str, cwd: str = "/") -> str:
        """Convierte cualquier ruta relativa o con . / .. en ruta canónica absoluta."""
        if not path:
            return cwd

        if not path.startswith("/"):
            path = f"{cwd.rstrip('/')}/{path}"

        segments = path.split("/")
        resolved: List[str] = []
        for seg in segments:
            if not seg or seg == ".":
                continue
            if seg == "..":
                if resolved:
                    resolved.pop()
            else:
                resolved.append(seg)
        return "/" + "/".join(resolved)

    def get_node(self, canonical_path: str) -> Optional[VFSNode]:
        """Recupera el nodo asociado a una ruta canónica."""
        if canonical_path == "/":
            return self.root

        parts = [p for p in canonical_path.split("/") if p]
        curr = self.root
        for part in parts:
            if not curr.is_dir or part not in curr.children:
                return None
            curr = curr.children[part]
        return curr

    def mkdir(self, canonical_path: str, permissions: int = 0o755) -> bool:
        """Crea un directorio y sus ancestros de forma recursiva."""
        parts = [p for p in canonical_path.split("/") if p]
        curr = self.root
        for part in parts:
            if part not in curr.children:
                new_dir = VFSNode(name=part, is_dir=True, permissions=permissions)
                curr.children[part] = new_dir
                curr = new_dir
            else:
                curr = curr.children[part]
                if not curr.is_dir:
                    return False
        return True

    def write_file(self, canonical_path: str, content: bytes, permissions: int = 0o644) -> bool:
        """Escribe datos en un archivo en RAM (crea directorios padres si no existen)."""
        parts = [p for p in canonical_path.split("/") if p]
        if not parts:
            return False

        parent_path = "/" + "/".join(parts[:-1]) if len(parts) > 1 else "/"
        filename = parts[-1]

        parent_node = self.get_node(parent_path)
        if not parent_node or not parent_node.is_dir:
            if not self.mkdir(parent_path):
                return False
            parent_node = self.get_node(parent_path)

        if filename in parent_node.children:
            existing = parent_node.children[filename]
            if existing.is_dir:
                return False
            existing.content = content
            existing.mtime = time.time()
        else:
            parent_node.children[filename] = VFSNode(
                name=filename, is_dir=False, permissions=permissions, content=content
            )
        return True

    def read_file(self, canonical_path: str) -> Optional[bytes]:
        """Retorna el contenido de un archivo o None si no existe o es directorio."""
        node = self.get_node(canonical_path)
        if not node or node.is_dir:
            return None
        return node.content

    def listdir(self, canonical_path: str) -> Optional[List[Tuple[str, VFSNode]]]:
        """Retorna las entradas hijas de un directorio ordenadas alfabéticamente."""
        node = self.get_node(canonical_path)
        if not node or not node.is_dir:
            return None
        return sorted(node.children.items(), key=lambda x: x[0])

    def unlink(self, canonical_path: str) -> bool:
        """Elimina un archivo o directorio vacío."""
        if canonical_path == "/":
            return False
        parts = [p for p in canonical_path.split("/") if p]
        parent_path = "/" + "/".join(parts[:-1]) if len(parts) > 1 else "/"
        filename = parts[-1]

        parent = self.get_node(parent_path)
        if parent and parent.is_dir and filename in parent.children:
            del parent.children[filename]
            return True
        return False

    def clone(self) -> "VirtualFileSystem":
        """Clona el VFS completo para dotar a una nueva sesión de aislamiento absoluto."""
        return copy.deepcopy(self)
