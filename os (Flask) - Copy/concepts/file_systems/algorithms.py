from typing import List, Dict, Any, Optional

# ================= FILE =================
class File:
    def __init__(self, name: str, size: int, content: str = ""):
        self.name = name
        self.size = size
        self.content = content
        self.blocks: List[int] = []


# ================= DIRECTORY =================
class Directory:
    def __init__(self, name: str, parent: Optional['Directory'] = None):
        self.name = name
        self.parent = parent
        self.files: List[File] = []
        self.subdirectories: List['Directory'] = []

    def add_file(self, file: File):
        self.files.append(file)

    def add_subdirectory(self, directory: 'Directory'):
        self.subdirectories.append(directory)

    def get_path(self) -> str:
        if self.parent is None:
            return "/"
        return self.parent.get_path() + self.name + "/"


# ================= DISK BLOCK =================
class DiskBlock:
    def __init__(self, index: int):
        self.index = index
        self.allocated = False
        self.file: Optional[File] = None
        self.next_block: Optional[int] = None


# ================= FILE SYSTEM =================
class FileSystem:
    def __init__(self, total_blocks: int = 100, block_size: int = 1024):
        self.total_blocks = total_blocks
        self.block_size = block_size
        self.disk: List[DiskBlock] = [DiskBlock(i) for i in range(total_blocks)]
        self.root = Directory("")
        self.allocation_method = "contiguous"  # contiguous, linked, indexed

    # ---------- ALLOCATION METHODS ----------
    def allocate_contiguous(self, file: File) -> bool:
        required = (file.size + self.block_size - 1) // self.block_size
        start = -1
        count = 0

        for i, block in enumerate(self.disk):
            if not block.allocated:
                if start == -1:
                    start = i
                count += 1
                if count == required:
                    for j in range(start, start + required):
                        self.disk[j].allocated = True
                        self.disk[j].file = file
                        file.blocks.append(j)
                    return True
            else:
                start = -1
                count = 0
        return False

    def allocate_linked(self, file: File) -> bool:
        required = (file.size + self.block_size - 1) // self.block_size
        prev = None

        for block in self.disk:
            if not block.allocated:
                block.allocated = True
                block.file = file
                if prev is not None:
                    prev.next_block = block.index
                file.blocks.append(block.index)
                prev = block
                if len(file.blocks) == required:
                    return True

        # rollback
        for i in file.blocks:
            self.disk[i].allocated = False
            self.disk[i].file = None
            self.disk[i].next_block = None
        file.blocks.clear()
        return False

    def allocate_indexed(self, file: File) -> bool:
        required = (file.size + self.block_size - 1) // self.block_size
        free_blocks = [b for b in self.disk if not b.allocated]

        if len(free_blocks) < required + 1:
            return False

        index_block = free_blocks[0]
        index_block.allocated = True
        index_block.file = file
        file.blocks.append(index_block.index)

        for b in free_blocks[1:required + 1]:
            b.allocated = True
            b.file = file
            file.blocks.append(b.index)

        return True

    # ---------- FILE OPERATIONS ----------
    def create_file(self, path: str, name: str, size: int) -> bool:
        directory = self.navigate_to_directory(path)
        if not directory:
            return False

        if any(f.name == name for f in directory.files):
            return False

        file = File(name, size)

        if self.allocation_method == "contiguous":
            ok = self.allocate_contiguous(file)
        elif self.allocation_method == "linked":
            ok = self.allocate_linked(file)
        elif self.allocation_method == "indexed":
            ok = self.allocate_indexed(file)
        else:
            return False

        if ok:
            directory.add_file(file)
            return True
        return False

    def delete_file(self, path: str, name: str) -> bool:
        directory = self.navigate_to_directory(path)
        if not directory:
            return False

        file = next((f for f in directory.files if f.name == name), None)
        if not file:
            return False

        for i in file.blocks:
            self.disk[i].allocated = False
            self.disk[i].file = None
            self.disk[i].next_block = None

        directory.files.remove(file)
        return True

    # ---------- DIRECTORY ----------
    def create_directory(self, path: str, name: str) -> bool:
        directory = self.navigate_to_directory(path)
        if not directory:
            return False

        if any(d.name == name for d in directory.subdirectories):
            return False

        directory.add_subdirectory(Directory(name, directory))
        return True

    def navigate_to_directory(self, path: str) -> Optional[Directory]:
        if path in ("", "/"):
            return self.root

        parts = [p for p in path.split("/") if p]
        current = self.root

        for p in parts:
            found = next((d for d in current.subdirectories if d.name == p), None)
            if not found:
                return None
            current = found
        return current

    # ---------- 🔥 FIXED METHOD ----------
    def list_files(self) -> List[Dict[str, Any]]:
        result = []

        def traverse(directory: Directory, path="/"):
            for f in directory.files:
                result.append({
                    "path": path,
                    "name": f.name,
                    "size": f.size,
                    "blocks": f.blocks
                })
            for d in directory.subdirectories:
                traverse(d, path + d.name + "/")

        traverse(self.root)
        return result

    # ---------- DISK USAGE ----------
    def get_disk_usage(self) -> Dict[str, Any]:
        used = sum(1 for b in self.disk if b.allocated)
        return {
            "total_blocks": self.total_blocks,
            "allocated_blocks": used,
            "free_blocks": self.total_blocks - used,
            "usage_percentage": (used / self.total_blocks) * 100
        }
