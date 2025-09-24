"""
Optimized File I/O Utilities for PvZModTool
Consolidated file operations with improved performance and reduced code duplication
"""
import os
import shutil
import struct
import ctypes
from typing import Optional, Union, Tuple, Dict, Any
import psutil


class FileIOManager:
    """Unified file I/O manager with optimized operations"""

    def __init__(self):
        self._process_handle = None
        self._current_process_id = None
        self._file_cache = {}  # Cache for frequently accessed files
        self._memory_cache = {}  # Cache for memory reads

    def _get_process_handle(self) -> Optional[int]:
        """Get or create process handle with caching"""
        try:
            # Find PVZ process
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] == 'PlantsVsZombies.exe':
                    process_id = proc.info['pid']
                    break
            else:
                return None

            # Return cached handle if process hasn't changed
            if self._current_process_id == process_id and self._process_handle:
                return self._process_handle

            # Close old handle if exists
            if self._process_handle:
                try:
                    ctypes.windll.kernel32.CloseHandle(self._process_handle)
                except:
                    pass

            # Open new handle
            self._process_handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, process_id)
            self._current_process_id = process_id

            return self._process_handle if self._process_handle else None

        except Exception as e:
            print(f"Error getting process handle: {e}")
            return None

    def read_file_data(self, file_path: str, address: int, size: int = 4) -> Optional[Union[int, bytes]]:
        """Unified file reading with caching and optimization"""
        try:
            # Check cache first
            cache_key = f"{file_path}_{address}_{size}"
            if cache_key in self._file_cache:
                return self._file_cache[cache_key]

            with open(file_path, 'rb') as f:
                f.seek(address)
                data = f.read(size)

                if len(data) != size:
                    return None

                # Cache the result
                self._file_cache[cache_key] = data
                return data

        except Exception as e:
            print(f"Error reading file {file_path} at {hex(address)}: {e}")
            return None

    def write_file_data(self, file_path: str, address: int, data: Union[int, bytes], size: int = 4) -> bool:
        """Unified file writing with backup creation"""
        try:
            # Create backup
            backup_path = file_path + '.backup'
            shutil.copy2(file_path, backup_path)

            with open(file_path, 'r+b') as f:
                f.seek(address)

                if isinstance(data, int):
                    if size == 4:
                        data_bytes = struct.pack('<I', data)
                    elif size == 2:
                        data_bytes = struct.pack('<H', data)
                    elif size == 1:
                        data_bytes = struct.pack('<B', data)
                    else:
                        raise ValueError(f"Unsupported size: {size}")
                else:
                    data_bytes = data

                f.write(data_bytes)
                # Clear cache after successful write
                cache_key = f"{file_path}_{address}_{len(data_bytes)}"
                if cache_key in self._file_cache:
                    del self._file_cache[cache_key]
                return True

        except Exception as e:
            print(f"Error writing to file {file_path} at {hex(address)}: {e}")
            return False

    def read_memory_data(self, address: int, size: int = 4) -> Optional[Union[int, bytes]]:
        """Unified memory reading with caching"""
        try:
            # Check cache first
            cache_key = f"mem_{address}_{size}"
            if cache_key in self._memory_cache:
                return self._memory_cache[cache_key]

            process_handle = self._get_process_handle()
            if not process_handle:
                return None

            buffer = ctypes.create_string_buffer(size)
            bytes_read = ctypes.c_size_t()

            process_address = address + 0x400000

            if ctypes.windll.kernel32.ReadProcessMemory(
                process_handle, ctypes.c_void_p(process_address),
                buffer, size, ctypes.byref(bytes_read)
            ):
                result = buffer.raw[:bytes_read.value]

                # Cache the result
                self._memory_cache[cache_key] = result
                return result

            return None

        except Exception as e:
            print(f"Error reading memory at {hex(address)}: {e}")
            return None

    def write_memory_data(self, address: int, data: Union[int, bytes], size: int = 4) -> bool:
        """Unified memory writing"""
        try:
            process_handle = self._get_process_handle()
            if not process_handle:
                return False

            if isinstance(data, int):
                if size == 4:
                    data_bytes = struct.pack('<I', data)
                elif size == 2:
                    data_bytes = struct.pack('<H', data)
                elif size == 1:
                    data_bytes = struct.pack('<B', data)
                else:
                    raise ValueError(f"Unsupported size: {size}")
            else:
                data_bytes = data

            bytes_written = ctypes.c_size_t()
            process_address = address + 0x400000

            if ctypes.windll.kernel32.WriteProcessMemory(
                process_handle, ctypes.c_void_p(process_address),
                data_bytes, len(data_bytes), ctypes.byref(bytes_written)
            ):
                # Clear cache after successful write
                cache_key = f"mem_{address}_{len(data_bytes)}"
                if cache_key in self._memory_cache:
                    del self._memory_cache[cache_key]
                return bytes_written.value == len(data_bytes)

            return False

        except Exception as e:
            print(f"Error writing memory at {hex(address)}: {e}")
            return False

    def batch_file_backup(self, source_path: str, dest_path: str, progress_callback=None) -> bool:
        """Optimized batch file backup with progress tracking"""
        try:
            total_files = self._count_files_excluding_backups(source_path)
            if total_files == 0:
                return True

            os.makedirs(dest_path, exist_ok=True)
            copied_files = 0

            for item in os.listdir(source_path):
                if item.startswith("backup_"):
                    continue

                src_path = os.path.join(source_path, item)
                dst_path = os.path.join(dest_path, item)

                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                    copied_files += self._count_files_in_directory(dst_path)
                else:
                    shutil.copy2(src_path, dst_path)
                    copied_files += 1

                # Update progress
                if progress_callback:
                    progress = (copied_files / total_files) * 100
                    progress_callback(progress)

            return True

        except Exception as e:
            print(f"Error in batch backup: {e}")
            return False

    def _count_files_excluding_backups(self, path: str) -> int:
        """Count files excluding backup directories"""
        count = 0
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith("backup_")]
            count += len(files)
        return count

    def _count_files_in_directory(self, path: str) -> int:
        """Count files in a directory"""
        count = 0
        for root, dirs, files in os.walk(path):
            count += len(files)
        return count

    def clear_cache(self):
        """Clear all caches"""
        self._file_cache.clear()
        self._memory_cache.clear()

    def close_process_handle(self):
        """Close process handle"""
        if self._process_handle:
            try:
                ctypes.windll.kernel32.CloseHandle(self._process_handle)
                self._process_handle = None
                self._current_process_id = None
            except:
                pass

    def find_pvz_process(self) -> Optional[int]:
        """Find PVZ process ID"""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] == 'PlantsVsZombies.exe':
                    return proc.info['pid']
            return None
        except Exception as e:
            print(f"Error finding PVZ process: {e}")
            return None


# Global instance
file_io_manager = FileIOManager()


# Legacy function wrappers for backward compatibility
def read_exe_file(exe_path: str, address: int, size: int = 4) -> Optional[int]:
    """Legacy wrapper for file reading"""
    data = file_io_manager.read_file_data(exe_path, address, size)
    if data is None:
        return None

    if size == 4:
        return struct.unpack('<I', data)[0]
    elif size == 2:
        return struct.unpack('<H', data)[0]
    elif size == 1:
        return struct.unpack('<B', data)[0]
    return None


def write_exe_file(exe_path: str, address: int, value: int, size: int = 4) -> bool:
    """Legacy wrapper for file writing"""
    return file_io_manager.write_file_data(exe_path, address, value, size)


def read_exe_bytes(exe_path: str, address: int, size: int) -> Optional[bytes]:
    """Legacy wrapper for reading bytes"""
    return file_io_manager.read_file_data(exe_path, address, size)


def write_exe_bytes(exe_path: str, address: int, data: bytes) -> bool:
    """Legacy wrapper for writing bytes"""
    return file_io_manager.write_file_data(exe_path, address, data)


def read_memory(process_handle: int, address: int, size: int = 4) -> Optional[int]:
    """Legacy wrapper for memory reading"""
    data = file_io_manager.read_memory_data(address, size)
    if data is None:
        return None

    if size == 4:
        return struct.unpack('<I', data)[0]
    elif size == 2:
        return struct.unpack('<H', data)[0]
    elif size == 1:
        return struct.unpack('<B', data)[0]
    return None


def write_memory(process_handle: int, address: int, value: int, size: int = 4) -> bool:
    """Legacy wrapper for memory writing"""
    return file_io_manager.write_memory_data(address, value, size)


def read_memory_bytes(process_handle: int, address: int, size: int) -> Optional[bytes]:
    """Legacy wrapper for reading memory bytes"""
    return file_io_manager.read_memory_data(address, size)


def write_memory_bytes(process_handle: int, address: int, data: bytes) -> bool:
    """Legacy wrapper for writing memory bytes"""
    return file_io_manager.write_memory_data(address, data)


def find_pvz_process() -> Optional[int]:
    """Find PVZ process ID"""
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == 'PlantsVsZombies.exe':
                return proc.info['pid']
        return None
    except Exception as e:
        print(f"Error finding PVZ process: {e}")
        return None
