from tkinter import *
from tkinter import filedialog, messagebox, ttk
import os, subprocess, threading, sys
from project_manager import ProjectManager
from backup_thread import BackupThread
from adventure_spawn import AdventureSpawnEditor
from file_io_utils import file_io_manager
import addresses

# Increase the limit for integer string conversion to handle large memory values
sys.set_int_max_str_digits(0)  # 0 means no limit

class StartMenu():
    def __init__(self, project_manager):
        self.project_manager = project_manager
        self.root = Tk()
        self.root.title("PvZ Modding Tool - Start Menu")
        self.root.geometry("600x400")

        Button(self.root, text="New Project", command=self.create_project).pack(pady=10)
        Button(self.root, text="Open Project", command=self.open_project).pack(pady=10)

    def create_project(self):
        self.project_manager.create_project()

    def open_project(self):
        global main_menu
        project_path = self.project_manager.open_project()
        if project_path:
            self.root.destroy()
            main_menu = MainMenu(self.project_manager, project_path)

class MainMenu():
    def __init__(self, project_manager, project_path):
        self.project_manager = project_manager
        self.project_path = project_path

        self.root = Tk()
        self.root.title("PvZ Modding Tool - Main Menu")
        self.root.geometry("900x600")

        # Frame to hold Listbox and Notebook side by side
        main_frame = Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True)

        # Listbox on the left
        self.listbox = Listbox(main_frame)
        self.listbox.pack(side=LEFT, fill=BOTH, expand=True)

        # Notebook on the right
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(side=RIGHT, fill=BOTH, expand=True)

        # First tab with general actions
        tab1 = Frame(self.notebook)
        self.notebook.add(tab1, text="General Actions")

        # Second tab with address editor
        tab2 = Frame(self.notebook)
        self.notebook.add(tab2, text="Address Editor")

        # Create address editor in tab2
        self.address_editor = AddressEditor(tab2, self)

        # Third tab with spawn rate presets
        tab3 = Frame(self.notebook)
        self.notebook.add(tab3, text="Adventure Spawn")

        # Create spawn rate presets editor in tab3
        self.spawn_rate_editor = AdventureSpawnEditor(tab3, self.project_path, self)

        # Global edit mode selection (moved to first tab)
        self.global_edit_mode_var = StringVar(value="process")

        # Add global mode selection to first tab
        mode_frame = Frame(tab1)
        mode_frame.pack(pady=10, padx=10, fill=X)

        Label(mode_frame, text="Глобальный режим редактирования:").pack(side=LEFT, padx=5)
        self.process_radio = Radiobutton(mode_frame, text="Процесс",
                                        variable=self.global_edit_mode_var, value="process",
                                        command=self.on_global_mode_changed)
        self.process_radio.pack(side=LEFT, padx=5)

        self.exe_radio = Radiobutton(mode_frame, text="EXE файл",
                                    variable=self.global_edit_mode_var, value="exe",
                                    command=self.on_global_mode_changed)
        self.exe_radio.pack(side=LEFT, padx=5)

        # Кнопка выбора exe файла
        self.select_exe_button = Button(mode_frame, text="Выбрать EXE", command=self.select_exe_file)
        self.select_exe_button.pack(side=LEFT, padx=5)

        # Add buttons for general actions in tab1
        Button(tab1, text="Launch PlantsVsZombies.exe", command=lambda: self.launch_tool(os.path.join(self.project_path, "PlantsVsZombies.exe"), "PlantsVsZombies.exe")).pack(pady=5, fill=X)
        Button(tab1, text="Launch PvZ_Tools_v2.3.4.exe", command=lambda: self.launch_tool(os.path.join(os.getcwd(), "tools", "PvZ_Tools_v2.3.4.exe"), "PvZ_Tools_v2.3.4.exe")).pack(pady=5, fill=X)
        Button(tab1, text="Open CFF_Explorer", command=lambda: self.launch_tool(os.path.join(os.getcwd(), "CFF_Explorer", "CFF Explorer.exe"), "CFF Explorer.exe")).pack(pady=5, fill=X)
        Button(tab1, text="Launch HxD", command=lambda: self.launch_tool(os.path.join(os.getcwd(), "tools", "HxD.exe"), "HxD.exe")).pack(pady=5, fill=X)
        Button(tab1, text="Create Backup", command=self.create_backup).pack(pady=5, fill=X)

        self.populate_listbox()

        # Progress bar at the bottom
        self.progress_frame = Frame(self.root)
        self.progress_frame.pack(side=BOTTOM, fill=X, padx=10, pady=10)

        self.progress_label = Label(self.progress_frame, text="Готов к работе")
        self.progress_label.pack()

        self.progress_bar = ttk.Progressbar(self.progress_frame, orient=HORIZONTAL, length=300, mode='determinate')
        self.progress_bar.pack(fill=X)


        self.root.mainloop()

    def populate_listbox(self):
        self.listbox.delete(0, END)
        if os.path.isdir(self.project_path):
            for item in os.listdir(self.project_path):
                self.listbox.insert(END, item)

    def launch_tool(self, default_path, friendly_name):
        def launch_in_thread():
            path_to_launch = default_path
            if not os.path.isfile(path_to_launch):
                path_to_launch = filedialog.askopenfilename(title=f"Select {friendly_name}")
                if not path_to_launch:
                    messagebox.showerror("Error", f"{friendly_name} executable not selected.")
                    return

            try:
                cwd = None
                if friendly_name == "PlantsVsZombies.exe":
                    cwd = os.path.dirname(path_to_launch)

                # Запустить процесс в отдельном потоке
                process = subprocess.Popen([path_to_launch], cwd=cwd)
                self.progress_label.config(text=f"{friendly_name} запущен (PID: {process.pid})")

                # Ожидать завершения процесса в фоне
                process.wait()

                # Обновить статус после завершения
                self.root.after(0, lambda: self.progress_label.config(text="Готов к работе"))

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to launch {friendly_name}: {e}"))

        # Запустить в отдельном потоке
        launch_thread = threading.Thread(target=launch_in_thread, daemon=True)
        launch_thread.start()


    def update_progress(self, progress):
        """Обновить прогрессбар (вызывается из потока)"""
        self.root.after(0, self._update_progress_ui, progress)

    def _update_progress_ui(self, progress):
        """Обновить интерфейс прогрессбара"""
        self.progress_bar.pack()  # Show progress bar
        self.progress_bar['value'] = progress
        self.progress_label.config(text=f"Создание бэкапа... {progress:.1f}%")
        self.root.update_idletasks()

        if progress >= 100:
            self.progress_label.config(text="Бэкап завершен!")
            # Показать сообщение только один раз при завершении
            if not hasattr(self, 'backup_completed_shown'):
                self.backup_completed_shown = True
                messagebox.showinfo("Backup Created", f"Backup created at {self.backup_path}")
            # Hide progress bar after 2 seconds
            self.root.after(2000, lambda: self.progress_bar.pack_forget())
            self.progress_label.config(text="Готов к работе")

    def create_backup(self):
        import datetime
        self.backup_path = os.path.join(self.project_path, "backup_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))

        # Reset progress bar
        self.progress_bar['value'] = 0
        self.progress_label.config(text="Подготовка к созданию бэкапа...")

        try:
            # Start backup in separate thread
            backup_thread = BackupThread(self.project_path, self.backup_path, self.update_progress)
            backup_thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create backup: {e}")
            self.progress_label.config(text="Ошибка создания бэкапа")
            self.root.after(2000, lambda: self.progress_label.config(text="Готов к работе"))

    def on_global_mode_changed(self):
        """Обработчик изменения глобального режима редактирования"""
        # Update status in all editors
        if hasattr(self, 'address_editor'):
            self.address_editor.on_global_mode_changed()
        if hasattr(self, 'spawn_rate_editor'):
            self.spawn_rate_editor.on_global_mode_changed()

    def select_exe_file(self):
        """Выбрать exe файл для редактирования"""
        file_path = filedialog.askopenfilename(
            title="Выберите PlantsVsZombies.exe",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if file_path:
            self.exe_file_path = file_path
            # Update status in all editors
            if hasattr(self, 'address_editor'):
                self.address_editor.exe_file_path = file_path
            if hasattr(self, 'spawn_rate_editor'):
                self.spawn_rate_editor.exe_file_path = file_path
        else:
            # Если файл не выбран, вернуться в режим процесса
            self.global_edit_mode_var.set("process")

class AddressEditor:
    def __init__(self, parent_frame, main_menu):
        self.parent = parent_frame
        self.main_menu = main_menu
        self.process_handle = None
        self.current_process_id = None
        self.exe_file_path = None
        self.edit_mode = "exe"  # "process" или "exe"

        # Словарь категорий и их адресов
        self.categories = {
            "Sun Cost": addresses.sun_cost,
            "Recharge": addresses.recharge,
            "Action Rates": addresses.action_rates,
            "Health & Armor": addresses.health_and_armor,
            "Projectiles": addresses.projectiles,
            "Damage": addresses.damage,
            "First Zombie Arrival": addresses.first_zombie_arrival,
            "Currency Prices": addresses.currency_prices,
            "Prize Bags": addresses.prize_bags,
            "Shop Prices": addresses.shop_prices,
            "Minigame Flags": addresses.minigame_flags,
        }

        self.create_widgets()

    def create_widgets(self):
        """Создать элементы интерфейса"""
        # Frame для категории
        category_frame = Frame(self.parent)
        category_frame.pack(pady=10, padx=10, fill=X)

        Label(category_frame, text="Category:").pack(side=LEFT, padx=5)
        self.category_combo = ttk.Combobox(category_frame, values=list(self.categories.keys()), state="readonly")
        self.category_combo.pack(side=LEFT, padx=5, fill=X, expand=True)
        self.category_combo.bind("<<ComboboxSelected>>", self.on_category_changed)

        # Frame для выбора адреса
        address_frame = Frame(self.parent)
        address_frame.pack(pady=10, padx=10, fill=X)

        Label(address_frame, text="Address:").pack(side=LEFT, padx=5)
        self.address_combo = ttk.Combobox(address_frame, state="readonly")
        self.address_combo.pack(side=LEFT, padx=5, fill=X, expand=True)
        self.address_combo.bind("<<ComboboxSelected>>", self.on_address_changed)

        # Frame для текущего значения
        current_frame = Frame(self.parent)
        current_frame.pack(pady=10, padx=10, fill=X)

        Label(current_frame, text="Current value:").pack(side=LEFT, padx=5)
        self.current_value_label = Label(current_frame, text="Не выбрано", relief=SUNKEN)
        self.current_value_label.pack(side=LEFT,fill=X)

        # Frame для ввода нового значения
        input_frame = Frame(self.parent)
        input_frame.pack(pady=10, padx=10, fill=X)

        Label(input_frame, text="New value:").pack(side=LEFT, padx=5)
        self.value_entry = Entry(input_frame)
        self.value_entry.pack(side=LEFT, padx=5, fill=X, expand=True)

        # Frame для кнопок
        button_frame = Frame(self.parent)
        button_frame.pack(pady=10, padx=10, fill=X)

        self.apply_button = Button(button_frame, text="Apply", command=lambda: self.apply_value())
        self.apply_button.pack(side=LEFT, padx=5)

        self.refresh_button = Button(button_frame, text="Refresh", command=lambda: self.refresh_current_value())
        self.refresh_button.pack(side=LEFT, padx=5)

        # Frame для предустановок spawn rate
        preset_frame = Frame(self.parent)
        preset_frame.pack(pady=10, padx=10, fill=X)

        Label(preset_frame, text="Spawn Rate Presets:").pack(side=LEFT, padx=5)
        self.preset_combo = ttk.Combobox(preset_frame, values=list(addresses.spawn_rate_values.keys()), state="readonly")
        self.preset_combo.pack(side=LEFT, padx=5, fill=X, expand=True)
        self.preset_combo.bind("<<ComboboxSelected>>", self.on_preset_changed)

        self.apply_preset_button = Button(preset_frame, text="Apply Preset", command=self.apply_preset)
        self.apply_preset_button.pack(side=LEFT, padx=5)

        # Frame для чекбоксов multi-byte replacements
        self.checkbox_frame = Frame(self.parent)
        self.checkbox_frame.pack(pady=10, padx=10, fill=X)

        # Словарь для хранения состояний чекбоксов
        self.checkbox_vars = {}
        self.checkbox_widgets = {}

        # Статус
        self.status_label = Label(self.parent, text="Готов к работе", fg="green")
        self.status_label.pack(pady=5)



        self.checkbox_frame.pack(pady=10, padx=10, fill=X)

        # Создать чекбоксы для каждого multi-byte replacement
        for address_name, address_info in addresses.multi_byte_replacements.items():
            if isinstance(address_info, dict):
                # Multi-byte replacement - словарь с информацией
                var = BooleanVar()
                self.checkbox_vars[address_name] = var

                # Создать фрейм для каждого multi-byte replacement
                replacement_frame = Frame(self.checkbox_frame)
                replacement_frame.pack(fill=X, pady=2)

                cb = Checkbutton(replacement_frame, text=address_name, variable=var)
                cb.pack(side=LEFT)
                file_path = self.main_menu.project_path + "/PlantsVsZombies.exe"
                with open(file_path, "rb") as f:
                    f.seek(address_info["addresses"])
                    value = f.read(10)
                    if value == address_info["original_bytes"]:
                        var.set(0)
                    else:
                        var.set(1)
                self.checkbox_widgets[address_name] = cb



    def on_category_changed(self, event):
        """Обработчик изменения категории"""
        category = self.category_combo.get()
        if category in self.categories:
            addresses_list = list(self.categories[category].keys())
            self.address_combo['values'] = addresses_list
            self.address_combo.set('')  # Сбросить выбор
            self.current_value_label.config(text="Не выбрано")

    def on_global_mode_changed(self):
        """Обработчик изменения глобального режима редактирования"""
        # Update status label to show current mode
        if hasattr(self, 'main_menu') and hasattr(self.main_menu, 'global_edit_mode_var'):
            mode = self.main_menu.global_edit_mode_var.get()
            if mode == "exe":
                if not self.exe_file_path:
                    self.status_label.config(text="Выберите EXE файл для редактирования", fg="orange")
                else:
                    self.status_label.config(text=f"Режим EXE: {os.path.basename(self.exe_file_path)}", fg="green")
            else:
                self.status_label.config(text="Режим процесса", fg="green")

    def on_address_changed(self, event):
        """Обработчик изменения адреса"""
        self.refresh_current_value()

    def refresh_current_value(self):
        """Обновить текущее значение из памяти или exe файла"""
        # Get global mode from parent MainMenu
        if hasattr(self, 'main_menu') and hasattr(self.main_menu, 'global_edit_mode_var'):
            global_mode = self.main_menu.global_edit_mode_var.get()
        else:
            global_mode = "process"  # Default fallback

        if global_mode == "process":
            if not self.ensure_process_connected():
                return
        elif global_mode == "exe":
            if not self.exe_file_path:
                self.status_label.config(text="Выберите EXE файл для редактирования", fg="orange")
                return

        category = self.category_combo.get()
        address_name = self.address_combo.get()

        if not category or not address_name:
            return

        # Обычные категории
        address = self.categories[category][address_name]

        if global_mode == "process":
            value = file_io_manager.read_memory_data(address, 4)
        else:
            value = file_io_manager.read_file_data(self.exe_file_path, address, 4)

        if value is not None:
            # Handle bytes objects by converting to integer
            if isinstance(value, bytes):
                int_value = int.from_bytes(value, byteorder='little')
                self.current_value_label.config(text=f"{int_value} (0x{value.hex().upper()})")
            else:
                # Handle integer values
                self.current_value_label.config(text=f"{value} (0x{value:08X})")
        else:
            self.current_value_label.config(text="Ошибка чтения")
            self.status_label.config(text="Ошибка чтения из памяти/файла", fg="red")

    def apply_value(self):
        """Применить новое значение"""
        # Get global mode from parent MainMenu
        if hasattr(self, 'main_menu') and hasattr(self.main_menu, 'global_edit_mode_var'):
            global_mode = self.main_menu.global_edit_mode_var.get()
        else:
            global_mode = "process"  # Default fallback

        if global_mode == "process":
            if not self.ensure_process_connected():
                return
        elif global_mode == "exe":
            if not self.exe_file_path:
                self.status_label.config(text="Выберите EXE файл для редактирования", fg="orange")
                return

        try:
            # Определить формат ввода (hex или decimal)
            value_text = self.value_entry.get().strip()
            if value_text.startswith('0x') or value_text.startswith('0X'):
                new_value = int(value_text, 16)
            else:
                new_value = int(value_text)

            category = self.category_combo.get()
            address_name = self.address_combo.get()

            if not category or not address_name:
                messagebox.showerror("Ошибка", "Выберите категорию и адрес")
                return


            # Обычные категории
            address = self.categories[category][address_name]

            if global_mode == "process":
                if file_io_manager.write_memory_data(address, new_value, size=4):
                    self.status_label.config(text=f"Значение {new_value} записано успешно", fg="green")
                    self.refresh_current_value()  # Обновить отображение
                else:
                    self.status_label.config(text="Ошибка записи в память", fg="red")
            else:
                if file_io_manager.write_file_data(self.exe_file_path, address, new_value, size=4):
                    self.status_label.config(text=f"Значение {new_value} записано в файл успешно", fg="green")
                    self.refresh_current_value()  # Обновить отображение
                else:
                    self.status_label.config(text="Ошибка записи в файл", fg="red")

        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат значения. Используйте число или hex (0x...)")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")

    def ensure_process_connected(self):
        """Убедиться, что подключены к процессу PVZ"""
        try:
            import ctypes
            import psutil

            # Проверить, запущен ли процесс
            process_id = file_io_manager.find_pvz_process()
            if not process_id:
                self.status_label.config(text="PlantsVsZombies.exe не запущен", fg="red")
                messagebox.showerror("Ошибка", "Запустите PlantsVsZombies.exe перед изменением значений")
                return False

            # Если процесс изменился или не подключены
            if self.current_process_id != process_id or not self.process_handle:
                # Закрыть старый handle
                if self.process_handle:
                    try:
                        ctypes.windll.kernel32.CloseHandle(self.process_handle)
                    except:
                        pass

                # Открыть новый handle
                self.process_handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, process_id)  # PROCESS_ALL_ACCESS
                self.current_process_id = process_id

                if not self.process_handle:
                    self.status_label.config(text="Не удалось подключиться к процессу", fg="red")
                    return False

            return True
        except Exception as e:
            self.status_label.config(text=f"Ошибка подключения: {e}", fg="red")
            return False

    def on_preset_changed(self, event):
        """Обработчик изменения предустановки spawn rate"""
        preset_name = self.preset_combo.get()
        if preset_name in addresses.spawn_rate_values:
            preset_values = addresses.spawn_rate_values[preset_name]
            # Показать информацию о предустановке
            info_text = f"{preset_name}\n"
            for addr, value in preset_values.items():
                info_text += f"{addr}: {value}\n"
            self.status_label.config(text=info_text, fg="blue")

    def apply_preset(self):
        """Применить выбранную предустановку spawn rate"""
        # Get global mode from parent MainMenu
        if hasattr(self, 'main_menu') and hasattr(self.main_menu, 'global_edit_mode_var'):
            global_mode = self.main_menu.global_edit_mode_var.get()
        else:
            global_mode = "process"  # Default fallback

        if global_mode == "process":
            if not self.ensure_process_connected():
                return
        elif global_mode == "exe":
            if not self.exe_file_path:
                self.status_label.config(text="Выберите EXE файл для редактирования", fg="orange")
                return

        preset_name = self.preset_combo.get()
        if not preset_name or preset_name not in addresses.spawn_rate_values:
            messagebox.showerror("Ошибка", "Выберите предустановку")
            return

        preset_values = addresses.spawn_rate_values[preset_name]
        success_count = 0
        total_count = len(preset_values)

        # Применить все значения из предустановки
        for address_str, value in preset_values.items():
            # Преобразовать строковый адрес в числовой
            address = int(address_str, 16)

            try:
                if global_mode == "process":
                    if file_io_manager.write_memory_data(self.process_handle, address, value, size=1):  # Spawn rate использует байты
                        success_count += 1
                    else:
                        self.status_label.config(text=f"Ошибка записи в память для {address_str}", fg="red")
                        return
                else:
                    if file_io_manager.write_file_data(self.exe_file_path, address, value, size=1):  # Spawn rate использует байты
                        success_count += 1
                    else:
                        self.status_label.config(text=f"Ошибка записи в файл для {address_str}", fg="red")
                        return
            except Exception as e:
                self.status_label.config(text=f"Ошибка применения предустановки: {e}", fg="red")
                return

        if success_count == total_count:
            self.status_label.config(text=f"Предустановка '{preset_name}' применена успешно!", fg="green")
            self.refresh_current_value()  # Обновить отображение текущих значений
        else:
            self.status_label.config(text="Ошибка применения предустановки", fg="red")

project_mn = ProjectManager()
start_menu = StartMenu(project_mn)
start_menu.root.mainloop()
