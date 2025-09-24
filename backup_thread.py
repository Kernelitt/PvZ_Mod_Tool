import threading
from file_io_utils import file_io_manager


class BackupThread(threading.Thread):
    """Optimized backup thread using unified file I/O utilities"""

    def __init__(self, source_path, backup_path, progress_callback):
        super().__init__()
        self.source_path = source_path
        self.backup_path = backup_path
        self.progress_callback = progress_callback

    def run(self):
        """Main thread method using optimized batch operations"""
        try:
            # Use optimized batch file backup with progress tracking
            success = file_io_manager.batch_file_backup(
                self.source_path,
                self.backup_path,
                self.progress_callback
            )

            if success:
                # Set final progress to 100%
                if self.progress_callback:
                    self.progress_callback(100)
            else:
                print("Backup failed")

        except Exception as e:
            print(f"Backup failed: {e}")
