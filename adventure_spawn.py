from tkinter import *
from tkinter import filedialog, simpledialog, messagebox, ttk
import os,shutil,struct
from file_io_utils import file_io_manager
    
class AdventureSpawnEditor:
    def __init__(self, parent_frame, project_path, main_menu):
        self.parent = parent_frame
        self.project_path = project_path
        self.main_menu = main_menu
        self.grid_width = 50  # Ширина игрового поля (50 клеток)
        self.grid_height = 32  # Высота игрового поля (32 клетки)
        self.cell_size = 24    # Размер клетки в пикселях (увеличен для лучшей видимости)
        self.grid_data = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]  # 0 - красный, 1 - зеленый

        # Загрузить текущие значения спавна в зависимости от глобального режима
        self.load_spawn_values_from_current_mode()

        # Инициализировать переменные для UI
        self.spawn_checkbox_var = BooleanVar()
        current_value = self.read_address_value(0x00D6A3, size=1)
        if current_value is not None:
            self.spawn_checkbox_var.set(current_value == 0xEB)
        else:
            self.spawn_checkbox_var.set(False)

        # Названия рядов (зомби)
        self.row_names = [
            "Zombie", "Flag", "Conehead", "Pole Vaulter", "Buckethead", "Newspaper",
            "Screen Door", "Football", "Dancing", "Backup Dancer", "Ducky Tube", "Snorkel",
            "Zomboni", "Bobsled Team", "Dolphin Rider", "Jack-In-The-Box", "Balloon",
            "Digger", "Pogo", "Yeti", "Bungee", "Ladder", "Catapult", "Gargantuar",
            "Imp", "Zomboss", "Peashooter", "Wall-nut", "Jalapeno", "Gatling Pea",
            "Squash", "Tall-Nut", "Giga-Garg"
        ]

        # Названия столбцов (уровни)
        self.col_names = []
        for world in range(1, 6):  # Миры 1-5
            for level in range(1, 11):  # Уровни 1-10
                self.col_names.append(f"{world}-{level}")

        # Создать основную рамку для всего интерфейса
        self.main_frame = Frame(self.parent)
        self.main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Создать кнопки управления
        self.create_control_buttons()

        # Создать область с подписями и сеткой
        self.create_grid_area()

        # Нарисовать сетку
        self.draw_grid()
        # Переменные для креста курсора
        self.crosshair_lines = []
        # Привязать обработчики событий
        self.canvas.bind("<Button-1>", self.on_cell_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Leave>", self.hide_crosshair)

    def load_spawn_values_from_current_mode(self):
        """Загрузить текущие значения спавна в зависимости от глобального режима"""
        # Get global mode from main menu
        if hasattr(self, 'main_menu') and hasattr(self.main_menu, 'global_edit_mode_var'):
            global_mode = self.main_menu.global_edit_mode_var.get()
        else:
            global_mode = "process"  # Default fallback

        if global_mode == "process":
            self.load_spawn_values_from_process()
        else:
            self.load_spawn_values_from_exe()

    def load_spawn_values_from_exe(self):
        """Загрузить текущие значения спавна из exe файла"""
        try:
            exe_path = self.project_path + "/PlantsVsZombies.exe"

            if not os.path.exists(exe_path):
                return

            # Чтение значений спавна для каждой клетки
            base_address = 0x2A35B4
            cells_read = 0
            for row in range(self.grid_height):
                for col in range(self.grid_width):
                    # Рассчитать адрес спавна: 0x2A35B4 + x * 0x04 + y * 0xCC
                    spawn_address = base_address + col * 0x04 + row * 0xCC

                    # Чтение байта из exe файла
                    value_bytes = file_io_manager.read_file_data(exe_path, spawn_address, size=1)

                    if value_bytes is not None:
                        # Convert bytes to integer
                        import struct
                        value = struct.unpack('<B', value_bytes)[0]
                        # Установить значение в grid_data (1 если значение != 0, иначе 0)
                        self.grid_data[row][col] = 1 if value != 0 else 0
                        cells_read += 1
                    else:
                        print(f"Не удалось прочитать адрес {hex(spawn_address)}")
                        self.grid_data[row][col] = 0

            print(f"DEBUG: Successfully read {cells_read} cells from EXE file")
            print("Значения спавна загружены из EXE файла")

        except Exception as e:
            print(f"Ошибка загрузки значений спавна: {e}")
            # В случае ошибки заполнить сетку нулями
            self.grid_data = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]

    def load_spawn_values_from_process(self):
        """Загрузить текущие значения спавна из процесса"""
        try:
            import ctypes
            import psutil
            process_id = None
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] == 'PlantsVsZombies.exe':
                    process_id = proc.info['pid']
                    break

            if not process_id:
                if hasattr(self, 'coord_label'):
                    self.coord_label.config(text="PlantsVsZombies.exe не запущен")
                return

            process_handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, process_id)
            if not process_handle:
                if hasattr(self, 'coord_label'):
                    self.coord_label.config(text="Не удалось подключиться к процессу")
                return

            # Чтение значений спавна для каждой клетки
            base_address = 0x2A35B4
            for row in range(self.grid_height):
                for col in range(self.grid_width):
                    # Рассчитать адрес спавна: 0x2A35B4 + x * 0x04 + y * 0xCC
                    spawn_address = base_address + col * 0x04 + row * 0xCC
                    process_address = spawn_address + 0x400000

                    buffer = ctypes.create_string_buffer(1)
                    bytes_read = ctypes.c_size_t()

                    if ctypes.windll.kernel32.ReadProcessMemory(process_handle, ctypes.c_void_p(process_address), buffer, 1, ctypes.byref(bytes_read)):
                        value = struct.unpack('<B', buffer.raw)[0]
                        # Установить значение в grid_data (1 если значение != 0, иначе 0)
                        self.grid_data[row][col] = 1 if value != 0 else 0
                    else:
                        print(f"Не удалось прочитать адрес {hex(spawn_address)} из процесса")
                        self.grid_data[row][col] = 0

            ctypes.windll.kernel32.CloseHandle(process_handle)
            print("Значения спавна загружены из процесса")

        except Exception as e:
            print(f"Ошибка загрузки значений спавна из процесса: {e}")
            # В случае ошибки заполнить сетку нулями
            self.grid_data = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]

    def refresh_grid(self):
        """Обновить сетку в зависимости от текущего режима"""
        # Get global mode from main menu
        if hasattr(self, 'main_menu') and hasattr(self.main_menu, 'global_edit_mode_var'):
            global_mode = self.main_menu.global_edit_mode_var.get()
 

        if global_mode == "process":
            self.load_spawn_values_from_process()
        else:
            self.load_spawn_values_from_exe()

        # Перерисовать сетку
        self.draw_grid()
        if hasattr(self, 'coord_label'):
            self.coord_label.config(text=f"Сетка обновлена ({global_mode})")

    def read_address_value(self, address, size=1):
        """Прочитать значение из адреса в процессе или exe файле"""
        # Get global mode from main menu
        global_mode = "process"  # Default fallback
        if hasattr(self, 'main_menu') and hasattr(self.main_menu, 'global_edit_mode_var'):
            global_mode = self.main_menu.global_edit_mode_var.get()

        if global_mode == "process":
            return self.read_process_value(address, size)
        else:
            return file_io_manager.read_file_data(self.project_path + "/PlantsVsZombies.exe", address, size)

    def read_process_value(self, address, size=1):
        """Прочитать значение из процесса"""
        try:
            import ctypes
            import psutil
            process_id = None
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] == 'PlantsVsZombies.exe':
                    process_id = proc.info['pid']
                    break

            if process_id:
                process_handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, process_id)
                if process_handle:
                    buffer = ctypes.create_string_buffer(size)
                    bytes_read = ctypes.c_size_t()

                    process_address = address + 0x400000
                    if ctypes.windll.kernel32.ReadProcessMemory(process_handle, ctypes.c_void_p(process_address), buffer, size, ctypes.byref(bytes_read)):
                        if size == 1:
                            return struct.unpack('<B', buffer.raw)[0]
                        elif size == 2:
                            return struct.unpack('<H', buffer.raw)[0]
                        elif size == 4:
                            return struct.unpack('<I', buffer.raw)[0]
                    ctypes.windll.kernel32.CloseHandle(process_handle)
            return None
        except Exception as e:
            print(f"Error reading process value: {e}")
            return None

    def create_control_buttons(self):
        """Создать кнопки управления"""
        button_frame = Frame(self.parent)
        button_frame.pack(pady=10, padx=10, fill=X)  # Увеличен отступ сверху

        # Создать внутренний frame для кнопок с отступом от верха
        inner_button_frame = Frame(button_frame)
        inner_button_frame.pack(pady=(20, 5))  # Отступ сверху 20px

        # Кнопка выбора exe файла (теперь используется только когда выбран глобальный режим EXE)
        self.select_exe_button = Button(inner_button_frame, text="Выбрать EXE", command=self.select_exe_file)
        self.select_exe_button.pack(side=LEFT, padx=5)

        # Чекбокс для переключения спавна
        self.spawn_checkbox = Checkbutton(inner_button_frame, text="Включить спавн приключений",
                                          variable=self.spawn_checkbox_var, command=self.on_spawn_checkbox_changed)
        self.spawn_checkbox.pack(side=LEFT, padx=5)

        # Кнопка обновления сетки
        self.refresh_button = Button(inner_button_frame, text="Обновить сетку", command=self.refresh_grid)
        self.refresh_button.pack(side=LEFT, padx=5)

        # Метка для отображения статуса
        self.coord_label = Label(inner_button_frame, text="Режим: Процесс", fg="blue")
        self.coord_label.pack(side=LEFT, padx=5)

    def get_column_x_position(self, col):
        """Получить x-позицию столбца без отступов между мирами"""
        label_width = 120
        return col * self.cell_size + label_width

    def create_grid_area(self):
        """Создать область с подписями рядов, столбцов и сеткой на одном Canvas"""
        # Основная рамка уже создана и упакована в __init__

        # Рассчитать размеры Canvas с учетом места для подписей
        label_width = 120  # Ширина области подписей рядов
        label_height = 30  # Высота области подписей столбцов

        # Рассчитать ширину canvas с учетом отступов между мирами
        # get_column_x_position возвращает левую позицию столбца, поэтому для ширины
        # нужно взять правую позицию последнего столбца
        last_col_left_x = self.get_column_x_position(self.grid_width - 1)
        self.canvas_width = last_col_left_x + self.cell_size
        self.canvas_height = self.grid_height * self.cell_size + label_height

        # Создать Canvas для всего интерфейса
        self.canvas = Canvas(self.main_frame, width=self.canvas_width, height=self.canvas_height, bg='white')
        self.canvas.pack()

        # Нарисовать подписи рядов (слева)
        self.row_label_widgets = []
        for i, row_name in enumerate(self.row_names):
            # Фон для подписей рядов
            self.canvas.create_rectangle(0, i * self.cell_size + label_height,
                                       label_width, (i + 1) * self.cell_size + label_height,
                                       fill='black', outline='gray')

            # Текст подписей рядов
            self.canvas.create_text(10, i * self.cell_size + label_height + self.cell_size//2,
                                  text=row_name, anchor=W, font=("Arial", 8), fill="white")

        # Нарисовать подписи столбцов (сверху)
        self.col_label_widgets = []
        for i, col_name in enumerate(self.col_names):
            # Фон для подписей столбцов с учетом отступов
            x1 = self.get_column_x_position(i)
            x2 = x1 + self.cell_size

            self.canvas.create_rectangle(x1, 0, x2, label_height,
                                       fill='black', outline='gray')

            # Текст подписей столбцов
            x_pos = x1 + self.cell_size//2
            self.canvas.create_text(x_pos, label_height//2,
                                  text=col_name, anchor=CENTER, font=("Arial", 9), fill="white")
    def draw_grid(self):
        """Нарисовать сетку клеток"""
        self.canvas.delete("all")  # Очистить canvas

        # Нарисовать подписи рядов (слева)
        self.row_label_widgets = []
        for i, row_name in enumerate(self.row_names):
            # Фон для подписей рядов
            self.canvas.create_rectangle(0, i * self.cell_size + 30,
                                       120, (i + 1) * self.cell_size + 30,
                                       fill='black', outline='gray')

            # Текст подписей рядов
            self.canvas.create_text(10, i * self.cell_size + 30 + self.cell_size//2,
                                  text=row_name, anchor=W, font=("Arial", 8), fill="white")

        # Нарисовать подписи столбцов (сверху) с учетом отступов между мирами
        self.col_label_widgets = []
        for i, col_name in enumerate(self.col_names):
            # Фон для подписей столбцов с учетом отступов
            x1 = self.get_column_x_position(i)
            x2 = x1 + self.cell_size

            self.canvas.create_rectangle(x1, 0, x2, 30,
                                       fill='black', outline='gray')

            # Текст подписей столбцов
            x_pos = x1 + self.cell_size//2
            self.canvas.create_text(x_pos, 15,
                                  text=col_name, anchor=CENTER, font=("Arial", 9), fill="white")

        # Нарисовать сетку клеток с учетом отступов между мирами
        for row in range(self.grid_height):
            for col in range(self.grid_width):
                # Использовать get_column_x_position для правильного позиционирования
                x1 = self.get_column_x_position(col)
                y1 = row * self.cell_size + 30   # Отступ сверху для подписей столбцов
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                # Определить цвет клетки
                if self.grid_data[row][col] == 0:
                    color = "red"
                else:
                    color = "green"

                # Нарисовать клетку
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="gray", width=1)

    def get_column_from_x(self, x):
        """Получить номер столбца по x-координате без отступов между мирами"""
        label_width = 120
        if x < label_width:
            return -1

        # Найти столбец простым расчетом
        col = (x - label_width) // self.cell_size
        if 0 <= col < self.grid_width:
            return col
        return -1

    def on_cell_click(self, event):
        col = self.get_column_from_x(event.x)
        row = (event.y - 30) // self.cell_size   # Отступ сверху 30px

        # Проверить границы
        if 0 <= row < self.grid_height and 0 <= col < self.grid_width:
            new_value = 1 - self.grid_data[row][col]  # 0 -> 1, 1 -> 0

            base_address = 0x2A35B4
            spawn_address = base_address + col * 0x04 + row * 0xCC

            # Сохранить изменения в зависимости от выбранного режима
            write_success = False
            # Get global mode from main menu
            if hasattr(self, 'main_menu') and hasattr(self.main_menu, 'global_edit_mode_var'):
                global_mode = self.main_menu.global_edit_mode_var.get()
            else:
                global_mode = "process"  # Default fallback

            if global_mode == "process":
                write_success = self.write_spawn_value_to_process(spawn_address, new_value)
            else:
                write_success = self.write_spawn_value_to_exe(spawn_address, new_value)

            # Обновить клетку только если запись прошла успешно
            if write_success:
                self.grid_data[row][col] = new_value
                self.update_cell(row, col)
                self.on_mouse_move(event)  # Pass the event to show crosshair at clicked position

    def update_cell(self, row, col):
        """Обновить цвет одной клетки"""
        # Добавить отступы для позиционирования клетки
        x1 = col * self.cell_size + 120  # Отступ слева для подписей рядов
        y1 = row * self.cell_size + 30   # Отступ сверху для подписей столбцов
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size

        # Определить цвет клетки
        if self.grid_data[row][col] == 0:
            color = "red"
        else:
            color = "green"

        # Обновить клетку
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="gray", width=1)

    def on_mouse_move(self, event=None):
        """Обработчик движения мыши - отображение креста курсора"""
        # Удалить старый крест
        self.hide_crosshair()

        # Определить координаты клетки
        col = self.get_column_from_x(event.x)
        row = (event.y - 30) // self.cell_size

        if 0 <= row < self.grid_height and 0 <= col < self.grid_width:
            x1 = col * self.cell_size + 120
            y1 = row * self.cell_size + 30
            x2 = x1 + self.cell_size
            y2 = y1 + self.cell_size

            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            self.crosshair_lines.append(self.canvas.create_line(0, center_y, self.canvas_width, center_y, fill="yellow", width=2))
            self.crosshair_lines.append(self.canvas.create_line(center_x, 0, center_x, self.canvas_height, fill="yellow", width=2))

    def hide_crosshair(self,event=None):
        for line in self.crosshair_lines:
            self.canvas.delete(line)
        self.crosshair_lines.clear()

    def write_spawn_value_to_process(self, address, value):
        """Записать значение в адрес спавна в процессе"""
        try:
            import ctypes
            import psutil
            process_id = None
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] == 'PlantsVsZombies.exe':
                    process_id = proc.info['pid']
                    break

            if process_id:
                process_handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, process_id)

                if process_handle:
                    buffer = struct.pack('<B', value)
                    bytes_written = ctypes.c_size_t()

                    process_address = address + 0x400000

                    if ctypes.windll.kernel32.WriteProcessMemory(process_handle,ctypes.c_void_p(process_address),buffer,1,ctypes.byref(bytes_written)):
                        return True
                    else:
                        return False
                else:
                    if hasattr(self, 'coord_label'):
                        self.coord_label.config(text="Не удалось подключиться к процессу")
                    return False
            else:
                if hasattr(self, 'coord_label'):
                    self.coord_label.config(text="PlantsVsZombies.exe не запущен")
                return False

        except Exception as e:
            if hasattr(self, 'coord_label'):
                self.coord_label.config(text=f"Ошибка записи спавна: {e}")
            print(f"Error writing spawn value: {e}")
            return False

    def write_spawn_value_to_exe(self, address, value):
        """Записать значение в адрес спавна в exe файл"""
        try:
            exe_path = self.project_path + "/PlantsVsZombies.exe"
            if not os.path.exists(exe_path):
                return False

            # Создать бэкап перед изменением
            backup_path = exe_path + '.backup'
            shutil.copy2(exe_path, backup_path)

            with open(exe_path, 'r+b') as f:
                file_address = address
                f.seek(file_address)

                data = struct.pack('<B', value)
                f.write(data)
                return True

        except Exception as e:
            if hasattr(self, 'coord_label'):
                self.coord_label.config(text=f"Ошибка записи в exe файл: {e}")
            print(f"Error writing to exe file: {e}")
            return False

    def on_global_mode_changed(self):
        """Обработчик изменения глобального режима редактирования"""
        # Update status label to show current mode
        if hasattr(self, 'main_menu') and hasattr(self.main_menu, 'global_edit_mode_var'):
            mode = self.main_menu.global_edit_mode_var.get()
            if mode == "exe":
                if not hasattr(self, 'exe_file_path') or not self.exe_file_path:
                    if hasattr(self, 'coord_label'):
                        self.coord_label.config(text="Выберите EXE файл для редактирования", fg="orange")
                else:
                    if hasattr(self, 'coord_label'):
                        self.coord_label.config(text=f"Режим EXE: {os.path.basename(self.exe_file_path)}", fg="green")
            else:
                if hasattr(self, 'coord_label'):
                    self.coord_label.config(text="Режим процесса", fg="green")
        else:
            # Fallback to process mode if global variable not accessible
            if hasattr(self, 'coord_label'):
                self.coord_label.config(text="Режим процесса", fg="green")

    def on_edit_mode_changed(self):
        """Обработчик изменения режима редактирования"""
        # Get global mode from main menu
        if hasattr(self, 'main_menu') and hasattr(self.main_menu, 'global_edit_mode_var'):
            global_mode = self.main_menu.global_edit_mode_var.get()
            print(global_mode)
        else:
            global_mode = "process"  # Default fallback

        if global_mode == "process":
            if hasattr(self, 'coord_label'):
                self.coord_label.config(text="Режим: Процесс")
        else:
            if not hasattr(self, 'exe_file_path') or not self.exe_file_path:
                self.select_exe_file()
            else:
                if hasattr(self, 'coord_label'):
                    self.coord_label.config(text="Режим: EXE файл")

        # Обновить сетку при смене режима
        self.refresh_grid()

    def select_exe_file(self):
        """Выбрать exe файл для редактирования"""
        file_path = filedialog.askopenfilename(title="Выберите PlantsVsZombies.exe",filetypes=[("Executable files", "*.exe"), ("All files", "*.*")])
        if file_path:
            self.exe_file_path = file_path
            if hasattr(self, 'coord_label'):
                self.coord_label.config(text=f"Режим: EXE файл - {os.path.basename(file_path)}", fg="green")
            # Обновить сетку для загрузки данных из EXE файла
            self.refresh_grid()

    def on_spawn_checkbox_changed(self):
        """Обработчик изменения состояния чекбокса спавна"""
        address = 0x00D6A3
        if self.spawn_checkbox_var.get():
            new_value = 0xEB
        else:
            new_value = 0x7D

        # Записать значение в зависимости от режима редактирования
        # Get global mode from main menu
        if hasattr(self, 'main_menu') and hasattr(self.main_menu, 'global_edit_mode_var'):
            global_mode = self.main_menu.global_edit_mode_var.get()
        else:
            global_mode = "process"  # Default fallback

        if global_mode == "process":
            self.write_spawn_value_to_process(address, new_value)
        else:
            self.write_spawn_value_to_exe(address, new_value)

    def get_grid_data(self):
        """Получить данные сетки"""
        return self.grid_data.copy()

    def set_grid_data(self, data):
        """Установить данные сетки"""
        if len(data) == self.grid_height and len(data[0]) == self.grid_width:
            self.grid_data = [row[:] for row in data]
            self.draw_grid()