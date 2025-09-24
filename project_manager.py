import os
import shutil
from tkinter import filedialog, simpledialog, messagebox, ttk
from file_io_utils import file_io_manager


class ProjectManager():
    """Optimized project manager using unified file I/O utilities"""

    def __init__(self):
        self.projects_dir = os.path.join(os.getcwd(), "projects")
        self.template_dir = os.path.join(os.getcwd(), "example", "template")
        self.project_path = ""

    def open_project(self):
        """Open existing project directory"""
        self.project_path = filedialog.askdirectory(initialdir=self.projects_dir)
        return self.project_path

    def create_project(self):
        """Create new project from template"""
        name = simpledialog.askstring("Project name?", "enter name")
        if name and name != "":
            try:
                # Use optimized batch file backup for template copying
                temp_path = os.path.join(self.projects_dir, "template")
                target_path = os.path.join(self.projects_dir, name)

                # Copy template to temporary location first
                success = file_io_manager.batch_file_backup(
                    self.template_dir,
                    temp_path
                )

                if success:
                    # Rename temporary directory to final name
                    os.rename(temp_path, target_path)
                else:
                    messagebox.showerror("Error", "Failed to create project template")

            except FileExistsError:
                # Template already exists, just rename it
                temp_path = os.path.join(self.projects_dir, "template")
                target_path = os.path.join(self.projects_dir, name)
                os.rename(temp_path, target_path)

    def rename_project(self):
        """Rename current project"""
        name = simpledialog.askstring("New Project Name?", "Enter name.")
        if name and name != "":
            old_path = os.path.join(self.projects_dir, self.project_path)
            new_path = os.path.join(self.projects_dir, name)
            os.rename(old_path, new_path)

    def delete_project(self):
        """Delete current project"""
        if messagebox.askyesno("DELETE PROJECT?", "This action cannot be undone."):
            project_path = os.path.join(self.projects_dir, self.project_path)
            shutil.rmtree(project_path)
