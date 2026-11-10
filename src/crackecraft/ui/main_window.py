from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QStackedWidget, QTextEdit, QVBoxLayout, QWidget, QComboBox,
)

from crackecraft.config import Settings
from crackecraft.services.apk import APKService
from crackecraft.workers import Worker


NAV = [("⌂", "Inicio"), ("▣", "Dispositivo Android"), ("⚙", "Ajustes"), ("≡", "Consola")]


def make_card(name: str = "Card") -> QFrame:
    frame = QFrame()
    frame.setObjectName(name)
    return frame


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = Settings()
        self.apk_service = APKService()
        self.pool = QThreadPool.globalInstance()
        self.workers: set[Worker] = set()
        self.apk_path: Path | None = None
        self.devices: list[tuple[str, str]] = []
        self.setWindowTitle("CrackeCraft · Android APK")
        self.setMinimumSize(900, 640)
        self.resize(1120, 760)
        self._build_ui()
        self._load_settings()
        self.refresh_devices()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        main = QHBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(225)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 24, 18, 20)
        side.setSpacing(8)
        brand_row = QHBoxLayout()
        mark = QLabel("C")
        mark.setObjectName("BrandMark")
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setFixedSize(38, 38)
        brand = QLabel("CRACKECRAFT")
        brand.setObjectName("BrandTitle")
        brand_row.addWidget(mark)
        brand_row.addWidget(brand)
        brand_row.addStretch(1)
        side.addLayout(brand_row)
        side.addSpacing(30)
        self.nav_buttons: list[QPushButton] = []
        for index, (icon, label) in enumerate(NAV):
            button = QPushButton(f"{icon}   {label}")
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, i=index: self.show_page(i))
            side.addWidget(button)
            self.nav_buttons.append(button)
        side.addStretch(1)
        self.sidebar_target = QLabel("Sin dispositivo conectado")
        self.sidebar_target.setObjectName("Muted")
        self.sidebar_target.setWordWrap(True)
        side.addWidget(self.sidebar_target)
        main.addWidget(sidebar)

        content = QWidget()
        column = QVBoxLayout(content)
        column.setContentsMargins(30, 22, 30, 20)
        column.setSpacing(16)
        header = QHBoxLayout()
        self.page_title = QLabel("Inicio")
        self.page_title.setObjectName("PageTitle")
        header.addWidget(self.page_title)
        header.addStretch(1)
        target_button = QPushButton("Android: buscando…")
        target_button.setObjectName("QuietButton")
        target_button.clicked.connect(lambda: self.show_page(1))
        self.target_header = target_button
        header.addWidget(target_button)
        column.addLayout(header)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._home_page())
        self.pages.addWidget(self._device_page())
        self.pages.addWidget(self._settings_page())
        self.pages.addWidget(self._console_page())
        column.addWidget(self.pages, 1)
        footer = QHBoxLayout()
        self.status = QLabel("Listo")
        self.status.setObjectName("Muted")
        footer.addWidget(self.status)
        footer.addStretch(1)
        self.console_button = QPushButton("Abrir consola")
        self.console_button.setObjectName("QuietButton")
        self.console_button.clicked.connect(lambda: self.show_page(3))
        footer.addWidget(self.console_button)
        column.addLayout(footer)
        main.addWidget(content, 1)
        self.nav_buttons[0].setChecked(True)
        self.setStyleSheet(self._style())

    def _home_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        hero = make_card("Hero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(28, 24, 24, 24)
        copy = QVBoxLayout()
        eyebrow = QLabel("ANDROID EDITION")
        eyebrow.setObjectName("Eyebrow")
        title = QLabel("Tu mundo.\nTu dispositivo.")
        title.setObjectName("HeroTitle")
        subtitle = QLabel("Instala y abre tu APK de Minecraft en Android.")
        subtitle.setObjectName("Muted")
        copy.addWidget(eyebrow)
        copy.addSpacing(10)
        copy.addWidget(title)
        copy.addWidget(subtitle)
        copy.addStretch(1)
        self.play_button = QPushButton("▶   INSTALAR Y JUGAR")
        self.play_button.setObjectName("PlayButton")
        self.play_button.setMinimumHeight(50)
        self.play_button.clicked.connect(self.install_and_play)
        copy.addWidget(self.play_button, 0, Qt.AlignmentFlag.AlignLeft)
        artwork = QLabel()
        artwork.setObjectName("HeroArt")
        artwork.setMinimumWidth(300)
        artwork.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_image = Path(__file__).parents[1] / "assets" / "hero.svg"
        artwork.setPixmap(QPixmap(str(hero_image)).scaled(440, 240, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
        hero_layout.addLayout(copy, 1)
        hero_layout.addWidget(artwork, 1)
        layout.addWidget(hero)

        apk_card = make_card()
        apk_layout = QVBoxLayout(apk_card)
        apk_layout.setContentsMargins(22, 18, 22, 18)
        top = QHBoxLayout()
        apk_label = QLabel("ARCHIVO APK")
        apk_label.setObjectName("Eyebrow")
        top.addWidget(apk_label)
        top.addStretch(1)
        self.apk_state = QLabel("No hay APK seleccionada")
        self.apk_state.setObjectName("Tag")
        top.addWidget(self.apk_state)
        apk_layout.addLayout(top)
        path_row = QHBoxLayout()
        self.apk_path_field = QLineEdit()
        self.apk_path_field.setReadOnly(True)
        self.apk_path_field.setPlaceholderText("Selecciona una APK local de Minecraft")
        choose = QPushButton("Seleccionar APK…")
        choose.setObjectName("AccentButton")
        choose.clicked.connect(self.choose_apk)
        path_row.addWidget(self.apk_path_field, 1)
        path_row.addWidget(choose)
        apk_layout.addLayout(path_row)
        layout.addWidget(apk_card)

        target_card = make_card()
        target_layout = QHBoxLayout(target_card)
        target_layout.setContentsMargins(22, 16, 22, 16)
        target_copy = QVBoxLayout()
        target_title = QLabel("DISPOSITIVO DE DESTINO")
        target_title.setObjectName("Eyebrow")
        target_copy.addWidget(target_title)
        target_copy.addWidget(QLabel("Emulador Android o contenedor Waydroid"))
        target_layout.addLayout(target_copy, 1)
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(300)
        self.device_combo.currentIndexChanged.connect(self._device_changed)
        target_layout.addWidget(self.device_combo)
        refresh = QPushButton("↻")
        refresh.setToolTip("Buscar dispositivos Android conectados")
        refresh.clicked.connect(self.refresh_devices)
        target_layout.addWidget(refresh)
        layout.addWidget(target_card)

        package_card = make_card()
        package_layout = QFormLayout(package_card)
        package_layout.setContentsMargins(22, 14, 22, 14)
        package_layout.setHorizontalSpacing(18)
        self.package_field = QLineEdit()
        self.package_field.setText(self.settings.package_id)
        package_layout.addRow("Identificador Android", self.package_field)
        hint = QLabel("Minecraft Bedrock suele usar com.mojang.minecraftpe. Puedes editarlo si tu APK usa otro identificador.")
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        package_layout.addRow("", hint)
        layout.addWidget(package_card)

        activity = make_card()
        activity_layout = QVBoxLayout(activity)
        activity_layout.setContentsMargins(22, 12, 22, 12)
        activity_head = QHBoxLayout()
        activity_head.addWidget(QLabel("ACTIVIDAD"))
        activity_head.addStretch(1)
        self.progress_label = QLabel("Sin instalaciones activas")
        self.progress_label.setObjectName("Muted")
        activity_head.addWidget(self.progress_label)
        activity_layout.addLayout(activity_head)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(7)
        activity_layout.addWidget(self.progress_bar)
        layout.addWidget(activity)
        layout.addStretch(1)
        return page

    def _device_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        panel = make_card()
        inner = QVBoxLayout(panel)
        inner.setContentsMargins(22, 20, 22, 20)
        heading = QLabel("Dispositivos Android detectados")
        heading.setObjectName("SectionTitle")
        explanation = QLabel("Abre el emulador antes de buscar. Con ADB, debe aparecer en estado «device»; autoriza la depuración USB si Android lo solicita.")
        explanation.setObjectName("Muted")
        explanation.setWordWrap(True)
        inner.addWidget(heading)
        inner.addWidget(explanation)
        self.device_list = QListWidget()
        inner.addWidget(self.device_list, 1)
        controls = QHBoxLayout()
        self.refresh_button = QPushButton("Buscar de nuevo")
        self.refresh_button.setObjectName("AccentButton")
        self.refresh_button.clicked.connect(self.refresh_devices)
        controls.addWidget(self.refresh_button)
        controls.addStretch(1)
        inner.addLayout(controls)
        layout.addWidget(panel, 1)
        return page

    def _settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        panel = make_card()
        form = QFormLayout(panel)
        form.setContentsMargins(24, 22, 24, 22)
        form.setVerticalSpacing(18)
        self.backend_combo = QComboBox()
        self.backend_combo.addItem("Automático", "auto")
        self.backend_combo.addItem("ADB · emulador Android", "adb")
        self.backend_combo.addItem("Waydroid · Linux", "waydroid")
        self.adb_path_field = QLineEdit()
        self.adb_path_field.setPlaceholderText("Detección automática o selecciona adb.exe")
        adb_row = QHBoxLayout()
        adb_row.addWidget(self.adb_path_field, 1)
        browse = QPushButton("Buscar…")
        browse.clicked.connect(self.choose_adb)
        adb_row.addWidget(browse)
        form.addRow("Entorno Android", self.backend_combo)
        form.addRow("Ruta de ADB", adb_row)
        layout.addWidget(panel)
        note = QLabel("En Windows, inicia primero un emulador compatible y habilita ADB. En Linux puedes usar Waydroid iniciado, o ADB con otro emulador. CrackeCraft no incorpora un emulador Android.")
        note.setObjectName("Muted")
        note.setWordWrap(True)
        layout.addWidget(note)
        save = QPushButton("Guardar ajustes")
        save.setObjectName("AccentButton")
        save.clicked.connect(self.save_settings)
        layout.addWidget(save, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addStretch(1)
        return page

    def _console_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        self.console = QTextEdit()
        self.console.setObjectName("Console")
        self.console.setReadOnly(True)
        layout.addWidget(self.console)
        clear = QPushButton("Limpiar consola")
        clear.clicked.connect(self.console.clear)
        layout.addWidget(clear, 0, Qt.AlignmentFlag.AlignRight)
        return page

    @staticmethod
    def _style() -> str:
        return """
        QWidget { background: #0e1015; color: #e9eaf2; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 13px; }
        #Sidebar { background: #11131a; border-right: 1px solid #20232e; }
        #BrandMark { background: #7c5cff; color: white; border-radius: 11px; font-size: 23px; font-weight: 800; }
        #BrandTitle { color: #f4f2ff; font-size: 14px; font-weight: 800; letter-spacing: 1px; }
        #PageTitle { font-size: 24px; font-weight: 700; }
        #NavButton { text-align: left; color: #9298a9; border: 0; border-radius: 9px; padding: 12px 13px; font-size: 14px; }
        #NavButton:hover { color: #f2f3fa; background: #1a1d27; }
        #NavButton:checked { color: #fff; background: #242034; border: 1px solid #4d3d91; }
        #Card { background: #161922; border: 1px solid #272b37; border-radius: 16px; }
        #Hero { background: #171a25; border: 1px solid #2a2c3b; border-radius: 18px; }
        #Eyebrow { color: #959bae; font-size: 10px; font-weight: 700; letter-spacing: 1.3px; }
        #HeroTitle { color: white; font-size: 32px; font-weight: 750; }
        #SectionTitle { color: #f5f5fb; font-size: 19px; font-weight: 700; }
        #Muted { color: #9298a9; font-size: 12px; }
        #Tag { color: #b6a8ff; background: #29233f; border: 1px solid #46387a; border-radius: 9px; padding: 5px 9px; font-size: 11px; }
        QPushButton { background: #20232d; color: #e7e8ef; border: 1px solid #303442; border-radius: 9px; padding: 9px 14px; }
        QPushButton:hover { background: #2a2e3a; border-color: #51576b; }
        QPushButton:pressed { background: #171a22; }
        #AccentButton { background: #684ee2; color: white; border: 1px solid #816bfa; font-weight: 650; }
        #AccentButton:hover { background: #7a63f2; }
        #PlayButton { background: #7659f4; color: white; border: 1px solid #9987ff; border-radius: 11px; padding: 12px 22px; font-size: 14px; font-weight: 800; letter-spacing: .6px; }
        #PlayButton:hover { background: #8a73ff; }
        #QuietButton { background: transparent; color: #a9adba; border: 1px solid #303442; }
        QLineEdit, QComboBox, QListWidget, QTextEdit { background: #11141b; border: 1px solid #303442; border-radius: 8px; padding: 8px; selection-background-color: #684ee2; }
        QProgressBar { border: 0; border-radius: 3px; background: #252936; }
        QProgressBar::chunk { background: #7b61ff; border-radius: 3px; }
        #Console { background: #090b0f; color: #b7c0d3; font-family: Consolas, 'DejaVu Sans Mono', monospace; font-size: 11px; }
        """

    def _load_settings(self) -> None:
        for index in range(self.backend_combo.count()):
            if self.backend_combo.itemData(index) == self.settings.backend:
                self.backend_combo.setCurrentIndex(index)
                break
        self.adb_path_field.setText(self.settings.adb_path)

    def show_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        self.page_title.setText(NAV[index][1])
        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)
        if index == 1:
            self._populate_device_list()

    def choose_apk(self) -> None:
        chosen, _ = QFileDialog.getOpenFileName(self, "Seleccionar APK de Minecraft", "", "Android APK (*.apk)")
        if not chosen:
            return
        path = Path(chosen)
        try:
            self.apk_service.validate_apk(path)
        except ValueError as exc:
            QMessageBox.warning(self, "APK no válida", str(exc))
            return
        self.apk_path = path
        self.apk_path_field.setText(str(path))
        self.apk_state.setText(f"Lista · {path.stat().st_size / (1024 * 1024):.1f} MB")
        self.status.setText("APK lista para instalar")
        self._log(f"APK seleccionada: {path.name}")

    def choose_adb(self) -> None:
        chosen, _ = QFileDialog.getOpenFileName(self, "Seleccionar ADB", self.adb_path_field.text(), "ADB (adb.exe);;Todos los archivos (*)")
        if chosen:
            self.adb_path_field.setText(chosen)

    def save_settings(self) -> None:
        self.settings.backend = str(self.backend_combo.currentData())
        self.settings.adb_path = self.adb_path_field.text()
        self.settings.package_id = self.package_field.text()
        self.status.setText("Ajustes guardados")
        self._log("Ajustes actualizados")
        self.refresh_devices()

    def refresh_devices(self) -> None:
        mode = str(self.backend_combo.currentData())
        adb_path = self.adb_path_field.text().strip()
        self.status.setText("Buscando Waydroid / emuladores ADB…")
        self._run_worker(self._refresh_worker, mode, adb_path, finished=self._devices_loaded)

    def _refresh_worker(self, mode: str, adb_path: str):
        try:
            return self.apk_service.list_devices(mode, adb_path), ""
        except Exception as exc:
            return [], str(exc)

    def _devices_loaded(self, result) -> None:
        devices, error = result
        self.devices = devices
        self.device_combo.clear()
        for serial, label in devices:
            self.device_combo.addItem(label, serial)
        if not devices:
            self.device_combo.addItem("No se detectaron dispositivos", "")
        self._populate_device_list()
        if devices:
            self.status.setText(f"{len(devices)} dispositivo(s) Android listo(s)")
            self._log(f"Dispositivos detectados: {len(devices)}")
        else:
            self.status.setText(error or "No se detectaron dispositivos Android")
        self._update_target_labels()

    def _populate_device_list(self) -> None:
        if not hasattr(self, "device_list"):
            return
        self.device_list.clear()
        for _serial, label in self.devices:
            self.device_list.addItem(label)
        if not self.devices:
            self.device_list.addItem("Sin dispositivos detectados. Inicia el emulador y pulsa Buscar de nuevo.")

    def _device_changed(self, _index: int) -> None:
        self._update_target_labels()

    def _update_target_labels(self) -> None:
        label = self.device_combo.currentText() if self.device_combo.count() else "Sin dispositivo conectado"
        self.target_header.setText(label)
        self.sidebar_target.setText(label)

    def install_and_play(self) -> None:
        if not self.apk_path:
            QMessageBox.information(self, "Selecciona una APK", "Elige primero el archivo APK de Minecraft.")
            return
        try:
            self.apk_service.validate_apk(self.apk_path)
            package_id = self.apk_service.validate_package_id(self.package_field.text())
        except ValueError as exc:
            QMessageBox.warning(self, "Revisa la APK", str(exc))
            return
        mode = str(self.backend_combo.currentData())
        serial = str(self.device_combo.currentData() or "")
        adb_path = self.adb_path_field.text().strip()
        self.settings.package_id = package_id
        self.play_button.setEnabled(False)
        self.progress_bar.setRange(0, 0)
        self.status.setText("Preparando instalación…")
        self._log(f"Instalación iniciada en {serial or mode}")
        self._run_worker(
            self._install_worker, self.apk_path, package_id, mode, adb_path, serial,
            finished=self._install_finished, progress=True,
        )

    def _install_worker(self, apk: Path, package_id: str, mode: str, adb_path: str, serial: str, progress) -> str:
        return self.apk_service.install_and_launch(apk, package_id, mode, adb_path, serial, progress)

    def _install_finished(self, message: str) -> None:
        self.play_button.setEnabled(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_label.setText(message)
        self.status.setText(message)
        self._log(message)

    def _run_worker(self, function, *args, finished=None, progress=False) -> Worker:
        if progress:
            worker = Worker(lambda: function(*args, lambda label, value, maximum: worker.signals.progress.emit(label, value, maximum)))
        else:
            worker = Worker(function, *args)
        self.workers.add(worker)
        worker.signals.failed.connect(lambda details, w=worker: self._worker_failed(w, details))
        worker.signals.finished.connect(lambda result, w=worker: self._worker_finished(w, result, finished))
        if progress:
            worker.signals.progress.connect(self._progress_changed)
        self.pool.start(worker)
        return worker

    def _worker_finished(self, worker: Worker, result, callback) -> None:
        self.workers.discard(worker)
        if callback:
            try:
                callback(result)
            except Exception as exc:
                self._show_error(str(exc))

    def _worker_failed(self, worker: Worker, details: str) -> None:
        self.workers.discard(worker)
        self._show_error(details.split("\n\n", 1)[0])

    def _show_error(self, message: str) -> None:
        self.play_button.setEnabled(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_label.setText("La instalación no se completó")
        self.status.setText("Error en la operación Android")
        self._log(f"ERROR: {message}")
        QMessageBox.critical(self, "CrackeCraft", message)

    def _progress_changed(self, label: str, value: int, maximum: int) -> None:
        self.progress_label.setText(label)
        if maximum > 0:
            self.progress_bar.setRange(0, maximum)
            self.progress_bar.setValue(min(value, maximum))
        else:
            self.progress_bar.setRange(0, 0)
        self.status.setText(label)

    def _log(self, message: str) -> None:
        line = f"[{datetime.now():%H:%M:%S}] {message}"
        self.console.append(line)
        try:
            with (self.settings.app_data_dir() / "crackecraft.log").open("a", encoding="utf-8") as stream:
                stream.write(line + "\n")
        except OSError:
            pass

