from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

import psutil
from PySide6.QtCore import Qt, QProcess, QThreadPool, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QDialogButtonBox,
    QFileDialog, QFormLayout, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QProgressBar,
    QPushButton, QSpinBox, QStackedWidget, QTableWidget, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QWidget,
)

from crackecraft.config import Settings
from crackecraft.services.auth import MicrosoftAuth
from crackecraft.services.credential_store import CredentialStore
from crackecraft.services.minecraft import MinecraftService
from crackecraft.workers import Worker


NAV_ITEMS = [("⌂", "Inicio"), ("◫", "Versiones"), ("▤", "Instalaciones"), ("◇", "Mods"), ("⚙", "Ajustes"), ("◉", "Cuenta")]


def card(parent: QWidget | None = None, name: str = "Card") -> QFrame:
    frame = QFrame(parent)
    frame.setObjectName(name)
    frame.setFrameShape(QFrame.Shape.NoFrame)
    return frame


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = Settings()
        self.minecraft = MinecraftService()
        self.credentials = CredentialStore()
        self.auth = MicrosoftAuth(self.credentials)
        self.active_account_id = self.settings.active_account
        self.current_account: dict[str, str] | None = None
        self.pool = QThreadPool.globalInstance()
        self._workers: set[Worker] = set()
        self.versions: list[dict] = []
        self._loading_versions = False
        self.process: QProcess | None = None
        self.setWindowTitle("CrackeCraft")
        self.setMinimumSize(980, 680)
        self.resize(1240, 820)
        self._build()
        self._load_settings_into_form()
        self._update_account_labels()
        self.refresh_versions()
        self.refresh_installed()

    def _build(self) -> None:
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 24, 18, 18)
        side.setSpacing(8)
        brand = QHBoxLayout()
        mark = QLabel("C")
        mark.setObjectName("BrandMark")
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setFixedSize(38, 38)
        brand_title = QLabel("CRACKECRAFT")
        brand_title.setObjectName("BrandTitle")
        brand.addWidget(mark)
        brand.addWidget(brand_title)
        brand.addStretch(1)
        side.addLayout(brand)
        side.addSpacing(30)
        self.nav_buttons: list[QPushButton] = []
        for index, (icon, label) in enumerate(NAV_ITEMS):
            button = QPushButton(f"{icon}   {label}")
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, i=index: self.show_page(i))
            side.addWidget(button)
            self.nav_buttons.append(button)
        side.addStretch(1)
        self.sidebar_account = QLabel("Sin sesión")
        self.sidebar_account.setObjectName("SmallMuted")
        side.addWidget(self.sidebar_account)
        layout.addWidget(sidebar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(32, 24, 32, 22)
        content_layout.setSpacing(18)
        header = QHBoxLayout()
        self.page_title = QLabel("Inicio")
        self.page_title.setObjectName("PageTitle")
        header.addWidget(self.page_title)
        header.addStretch(1)
        self.header_account = QPushButton("Iniciar sesión")
        self.header_account.setObjectName("QuietButton")
        self.header_account.clicked.connect(lambda: self.show_page(5))
        header.addWidget(self.header_account)
        content_layout.addLayout(header)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._home_page())
        self.stack.addWidget(self._versions_page())
        self.stack.addWidget(self._installations_page())
        self.stack.addWidget(self._mods_page())
        self.stack.addWidget(self._settings_page())
        self.stack.addWidget(self._account_page())
        content_layout.addWidget(self.stack, 1)

        footer = QHBoxLayout()
        self.status_label = QLabel("Listo")
        self.status_label.setObjectName("SmallMuted")
        self.console_toggle = QPushButton("Consola⌄")
        self.console_toggle.setObjectName("QuietButton")
        self.console_toggle.clicked.connect(self.toggle_console)
        footer.addWidget(self.status_label)
        footer.addStretch(1)
        footer.addWidget(self.console_toggle)
        content_layout.addLayout(footer)
        self.console = QTextEdit()
        self.console.setObjectName("Console")
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(150)
        self.console.hide()
        content_layout.addWidget(self.console)
        layout.addWidget(content, 1)
        self.nav_buttons[0].setChecked(True)
        self.setStyleSheet(self._stylesheet())

    def _home_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        hero = card(name="Hero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(28, 24, 20, 24)
        copy = QVBoxLayout()
        eyebrow = QLabel("TU AVENTURA EMPIEZA AQUÍ")
        eyebrow.setObjectName("Eyebrow")
        headline = QLabel("Un mundo\npor descubrir.")
        headline.setObjectName("HeroTitle")
        tagline = QLabel("Minecraft Java Edition, preparado a tu manera.")
        tagline.setObjectName("SmallMuted")
        copy.addWidget(eyebrow)
        copy.addSpacing(8)
        copy.addWidget(headline)
        copy.addWidget(tagline)
        copy.addStretch(1)
        self.play_button = QPushButton("▶   JUGAR")
        self.play_button.setObjectName("PlayButton")
        self.play_button.setMinimumHeight(50)
        self.play_button.clicked.connect(self.play_selected)
        copy.addWidget(self.play_button, 0, Qt.AlignmentFlag.AlignLeft)
        art = QLabel()
        art.setMinimumWidth(320)
        art.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_path = Path(__file__).parents[1] / "assets" / "hero.svg"
        art.setPixmap(QPixmap(str(image_path)).scaled(490, 250, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
        art.setObjectName("HeroArt")
        hero_layout.addLayout(copy, 1)
        hero_layout.addWidget(art, 1)
        layout.addWidget(hero)

        row = QHBoxLayout()
        version_card = card(name="Card")
        vlayout = QVBoxLayout(version_card)
        vlayout.setContentsMargins(22, 18, 22, 18)
        title_row = QHBoxLayout()
        vtitle = QLabel("VERSIÓN DE JUEGO")
        vtitle.setObjectName("Eyebrow")
        title_row.addWidget(vtitle)
        title_row.addStretch(1)
        self.install_state = QLabel("Sin instalar")
        self.install_state.setObjectName("Tag")
        title_row.addWidget(self.install_state)
        vlayout.addLayout(title_row)
        self.home_version = QComboBox()
        self.home_version.setMinimumHeight(42)
        self.home_version.currentTextChanged.connect(self._home_version_changed)
        vlayout.addWidget(self.home_version)
        self.home_profile = QLabel("Perfil: Principal")
        self.home_profile.setObjectName("SmallMuted")
        vlayout.addWidget(self.home_profile)
        row.addWidget(version_card, 3)

        account_card = card(name="Card")
        alayout = QVBoxLayout(account_card)
        alayout.setContentsMargins(22, 18, 22, 18)
        alabel = QLabel("CUENTA MICROSOFT")
        alabel.setObjectName("Eyebrow")
        self.home_account = QLabel("Inicia sesión para jugar")
        self.home_account.setObjectName("SectionTitle")
        account_hint = QLabel("Se requiere Minecraft: Java Edition en la cuenta.")
        account_hint.setObjectName("SmallMuted")
        account_button = QPushButton("Gestionar cuenta  →")
        account_button.setObjectName("QuietButton")
        account_button.clicked.connect(lambda: self.show_page(5))
        alayout.addWidget(alabel)
        alayout.addWidget(self.home_account)
        alayout.addWidget(account_hint)
        alayout.addStretch(1)
        alayout.addWidget(account_button, 0, Qt.AlignmentFlag.AlignLeft)
        row.addWidget(account_card, 2)
        layout.addLayout(row)

        progress_card = card(name="Card")
        playout = QVBoxLayout(progress_card)
        playout.setContentsMargins(22, 14, 22, 14)
        ptop = QHBoxLayout()
        ptop.addWidget(QLabel("ACTIVIDAD"))
        ptop.addStretch(1)
        self.progress_text = QLabel("Sin descargas activas")
        self.progress_text.setObjectName("SmallMuted")
        ptop.addWidget(self.progress_text)
        playout.addLayout(ptop)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(7)
        playout.addWidget(self.progress_bar)
        layout.addWidget(progress_card)
        layout.addStretch(1)
        return page

    def _versions_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        toolbar = QHBoxLayout()
        self.version_filter = QComboBox()
        self.version_filter.addItems(["Lanzamientos", "Snapshots", "Todas"])
        self.version_filter.currentIndexChanged.connect(self._populate_versions)
        toolbar.addWidget(self.version_filter)
        toolbar.addStretch(1)
        refresh = QPushButton("Actualizar lista")
        refresh.clicked.connect(self.refresh_versions)
        self.install_version_button = QPushButton("Instalar versión")
        self.install_version_button.setObjectName("AccentButton")
        self.install_version_button.clicked.connect(self.install_selected_version)
        toolbar.addWidget(refresh)
        remove = QPushButton("Eliminar versión instalada")
        remove.clicked.connect(self.remove_selected_version)
        toolbar.addWidget(remove)
        toolbar.addWidget(self.install_version_button)
        layout.addLayout(toolbar)
        self.version_table = QTableWidget(0, 3)
        self.version_table.setHorizontalHeaderLabels(["Versión", "Canal", "Fecha de publicación"])
        self.version_table.horizontalHeader().setStretchLastSection(True)
        self.version_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.version_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.version_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.version_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.version_table.doubleClicked.connect(self.install_selected_version)
        layout.addWidget(self.version_table, 1)
        return page

    def _installations_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        intro = QLabel("Cada perfil tiene su propio directorio de mundos, ajustes y mods.")
        intro.setObjectName("SmallMuted")
        layout.addWidget(intro)
        self.profile_list = QListWidget()
        layout.addWidget(self.profile_list, 1)
        controls = QHBoxLayout()
        create = QPushButton("＋ Nuevo perfil")
        create.setObjectName("AccentButton")
        create.clicked.connect(self.create_profile)
        select = QPushButton("Usar perfil")
        select.clicked.connect(self.use_selected_profile)
        remove = QPushButton("Eliminar perfil")
        remove.clicked.connect(self.delete_profile)
        controls.addWidget(create)
        controls.addStretch(1)
        controls.addWidget(select)
        controls.addWidget(remove)
        layout.addLayout(controls)
        return page

    def _mods_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        panel = card(name="Card")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(26, 24, 26, 24)
        heading = QLabel("Mods por instalación")
        heading.setObjectName("SectionTitle")
        self.mods_path_label = QLabel("")
        self.mods_path_label.setObjectName("SmallMuted")
        explanation = QLabel("Esta versión inicial gestiona la carpeta de mods de cada perfil. Fabric y Forge no están habilitados hasta integrar sus instaladores oficiales; no se copiarán mods a otras instalaciones.")
        explanation.setObjectName("SmallMuted")
        explanation.setWordWrap(True)
        open_mods = QPushButton("Abrir carpeta de mods")
        open_mods.setObjectName("AccentButton")
        open_mods.clicked.connect(self.open_mods_folder)
        panel_layout.addWidget(heading)
        panel_layout.addSpacing(8)
        panel_layout.addWidget(self.mods_path_label)
        panel_layout.addWidget(explanation)
        panel_layout.addSpacing(8)
        panel_layout.addWidget(open_mods, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(panel)
        layout.addStretch(1)
        return page

    def _settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        panel = card(name="Card")
        form = QFormLayout(panel)
        form.setContentsMargins(24, 22, 24, 22)
        form.setHorizontalSpacing(24)
        form.setVerticalSpacing(18)
        self.client_id_field = QLineEdit()
        self.client_id_field.setPlaceholderText("UUID del registro de aplicación Microsoft")
        self.directory_field = QLineEdit()
        browse = QPushButton("Elegir…")
        browse.clicked.connect(self._browse_directory)
        dir_row = QHBoxLayout()
        dir_row.addWidget(self.directory_field, 1)
        dir_row.addWidget(browse)
        self.ram_spin = QSpinBox()
        self.ram_spin.setRange(1024, max(2048, int(psutil.virtual_memory().total / (1024 * 1024) * 0.8)))
        self.ram_spin.setSingleStep(512)
        self.java_field = QLineEdit()
        self.java_field.setPlaceholderText("Automático: runtime de Minecraft o Java del sistema")
        java_browse = QPushButton("Elegir…")
        java_browse.clicked.connect(self._browse_java)
        java_row = QHBoxLayout()
        java_row.addWidget(self.java_field, 1)
        java_row.addWidget(java_browse)
        self.jvm_args_field = QLineEdit()
        self.jvm_args_field.setPlaceholderText("Argumentos JVM opcionales; separados por espacios")
        self.java_detected = QLabel("")
        self.java_detected.setObjectName("SmallMuted")
        form.addRow("Microsoft App Client ID", self.client_id_field)
        form.addRow("Directorio del juego", dir_row)
        form.addRow("Memoria máxima", self.ram_spin)
        form.addRow("Ejecutable Java", java_row)
        form.addRow("Java detectado", self.java_detected)
        form.addRow("Argumentos JVM", self.jvm_args_field)
        layout.addWidget(panel)
        privacy = QLabel("El launcher usa el inicio de sesión oficial Microsoft con PKCE. Las claves de sesión se guardan en el almacén seguro del sistema operativo; no guardamos contraseñas.")
        privacy.setObjectName("SmallMuted")
        privacy.setWordWrap(True)
        layout.addWidget(privacy)
        save = QPushButton("Guardar ajustes")
        save.setObjectName("AccentButton")
        save.clicked.connect(self.save_settings)
        layout.addWidget(save, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addStretch(1)
        return page

    def _account_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        panel = card(name="Card")
        inner = QVBoxLayout(panel)
        inner.setContentsMargins(24, 22, 24, 22)
        title = QLabel("Cuentas")
        title.setObjectName("SectionTitle")
        hint = QLabel("Inicia sesión con Microsoft. CrackeCraft verifica el acceso a Minecraft antes de lanzar el juego.")
        hint.setWordWrap(True)
        hint.setObjectName("SmallMuted")
        self.account_list = QListWidget()
        self.account_list.currentItemChanged.connect(self._account_selected)
        inner.addWidget(title)
        inner.addWidget(hint)
        inner.addWidget(self.account_list, 1)
        controls = QHBoxLayout()
        login = QPushButton("＋ Añadir cuenta Microsoft")
        login.setObjectName("AccentButton")
        login.clicked.connect(self.sign_in)
        use = QPushButton("Usar cuenta")
        use.clicked.connect(self.use_selected_account)
        remove = QPushButton("Quitar cuenta")
        remove.clicked.connect(self.remove_selected_account)
        controls.addWidget(login)
        controls.addStretch(1)
        controls.addWidget(use)
        controls.addWidget(remove)
        inner.addLayout(controls)
        layout.addWidget(panel, 1)
        return page

    @staticmethod
    def _stylesheet() -> str:
        return """
        QWidget { background: #0e1015; color: #e9eaf2; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 13px; }
        #Sidebar { background: #11131a; border-right: 1px solid #20232e; }
        #BrandMark { background: #7c5cff; color: white; border-radius: 11px; font-size: 23px; font-weight: 800; }
        #BrandTitle { color: #f4f2ff; font-size: 14px; font-weight: 800; letter-spacing: 1.1px; }
        #PageTitle { font-size: 24px; font-weight: 700; }
        #NavButton { text-align: left; color: #9298a9; border: 0; border-radius: 9px; padding: 12px 13px; font-size: 14px; }
        #NavButton:hover { color: #f2f3fa; background: #1a1d27; }
        #NavButton:checked { color: #fff; background: #242034; border: 1px solid #4d3d91; }
        #Card { background: #161922; border: 1px solid #272b37; border-radius: 16px; }
        #Hero { background: #171a25; border: 1px solid #2a2c3b; border-radius: 18px; }
        #HeroArt { border-radius: 12px; }
        #Eyebrow { color: #959bae; font-size: 10px; font-weight: 700; letter-spacing: 1.3px; }
        #HeroTitle { color: white; font-size: 32px; font-weight: 750; }
        #SectionTitle { color: #f5f5fb; font-size: 19px; font-weight: 700; }
        #SmallMuted { color: #9298a9; font-size: 12px; }
        #Tag { color: #b6a8ff; background: #29233f; border: 1px solid #46387a; border-radius: 9px; padding: 5px 9px; font-size: 11px; }
        QPushButton { background: #20232d; color: #e7e8ef; border: 1px solid #303442; border-radius: 9px; padding: 9px 14px; }
        QPushButton:hover { background: #2a2e3a; border-color: #51576b; }
        QPushButton:pressed { background: #171a22; }
        #AccentButton { background: #684ee2; color: white; border: 1px solid #816bfa; font-weight: 650; }
        #AccentButton:hover { background: #7a63f2; }
        #PlayButton { background: #7659f4; color: white; border: 1px solid #9987ff; border-radius: 11px; padding: 12px 22px; font-size: 14px; font-weight: 800; letter-spacing: .6px; }
        #PlayButton:hover { background: #8a73ff; }
        #QuietButton { background: transparent; color: #a9adba; border: 1px solid #303442; }
        QLineEdit, QComboBox, QSpinBox, QListWidget, QTableWidget, QTextEdit { background: #11141b; border: 1px solid #303442; border-radius: 8px; padding: 8px; selection-background-color: #684ee2; }
        QComboBox::drop-down { border: 0; width: 24px; }
        QHeaderView::section { background: #191c25; color: #9ca2b3; border: 0; padding: 9px; }
        QTableWidget { gridline-color: #252935; }
        QProgressBar { border: 0; border-radius: 3px; background: #252936; }
        QProgressBar::chunk { background: #7b61ff; border-radius: 3px; }
        #Console { background: #090b0f; color: #b7c0d3; font-family: Consolas, 'DejaVu Sans Mono', monospace; font-size: 11px; }
        """

    def show_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self.page_title.setText(NAV_ITEMS[index][1])
        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)
        if index == 2:
            self._populate_profiles()
        elif index == 3:
            self._update_mods_path()
        elif index == 5:
            self._populate_accounts()

    def _run_worker(self, function, *args, finished=None, progress=False) -> Worker:
        if progress:
            worker = Worker(lambda: function(*args, lambda status, value, maximum: worker.signals.progress.emit(status, value, maximum)))
        else:
            worker = Worker(function, *args)
        self._workers.add(worker)
        worker.signals.failed.connect(lambda details, w=worker: self._worker_failed_for(w, details))
        worker.signals.finished.connect(lambda result, w=worker: self._worker_finished(w, result, finished))
        if progress:
            worker.signals.progress.connect(self._download_progress)
        self.pool.start(worker)
        return worker

    def _worker_failed_for(self, worker: Worker, details: str) -> None:
        self._workers.discard(worker)
        self._worker_failed(details)

    def _worker_finished(self, worker: Worker, result, callback) -> None:
        self._workers.discard(worker)
        if callback:
            try:
                callback(result)
            except Exception as exc:
                self._worker_failed(str(exc))

    def _worker_failed(self, details: str) -> None:
        self.status_label.setText("Se produjo un error")
        message = details.split("\n\n", 1)[0]
        self._log(f"ERROR: {message}")
        QMessageBox.critical(self, "CrackeCraft", message)
        self.play_button.setEnabled(True)
        self.install_version_button.setEnabled(True)

    def _log(self, message: str) -> None:
        line = f"[{datetime.now():%H:%M:%S}] {message}"
        self.console.append(line)
        try:
            log_path = self.settings.app_data_dir() / "crackecraft.log"
            with log_path.open("a", encoding="utf-8") as stream:
                stream.write(line + "\n")
        except OSError:
            pass

    def toggle_console(self) -> None:
        self.console.setVisible(not self.console.isVisible())
        self.console_toggle.setText("Consola⌃" if self.console.isVisible() else "Consola⌄")

    def refresh_versions(self) -> None:
        self.status_label.setText("Consultando el catálogo oficial de versiones…")
        self._run_worker(self.minecraft.versions, finished=self._versions_loaded)

    def _versions_loaded(self, versions: list[dict]) -> None:
        self.versions = versions
        self._populate_versions()
        ids = [str(v.get("id", "")) for v in versions]
        self._loading_versions = True
        self.home_version.clear()
        self.home_version.addItems(ids)
        profiles = self.settings.profiles()
        if not profiles and ids:
            release = next((v["id"] for v in versions if v.get("type") == "release"), ids[0])
            profiles["default"] = {"name": "Principal", "version": release}
            self.settings.save_profiles(profiles)
            self.settings.selected_profile = "default"
        selected = profiles.get(self.settings.selected_profile, {})
        if selected.get("version") in ids:
            self.home_version.setCurrentText(selected["version"])
        self._loading_versions = False
        self._populate_profiles()
        self._update_home_status()
        self.status_label.setText(f"{len(versions)} versiones disponibles")

    def _populate_versions(self, *_args) -> None:
        if not hasattr(self, "version_table"):
            return
        selected_filter = self.version_filter.currentIndex()
        visible = [v for v in self.versions if selected_filter == 2 or (selected_filter == 0 and v.get("type") == "release") or (selected_filter == 1 and v.get("type") == "snapshot")]
        self.version_table.setRowCount(len(visible))
        for row, version in enumerate(visible):
            self.version_table.setItem(row, 0, QTableWidgetItem(str(version.get("id", ""))))
            kind = str(version.get("type", "custom"))
            self.version_table.setItem(row, 1, QTableWidgetItem({"release": "Estable", "snapshot": "Snapshot", "old_beta": "Beta", "old_alpha": "Alpha"}.get(kind, kind)))
            released = version.get("releaseTime", "")
            if hasattr(released, "strftime"):
                released = released.strftime("%Y-%m-%d")
            elif isinstance(released, str):
                released = released[:10]
            self.version_table.setItem(row, 2, QTableWidgetItem(str(released or "—")))

    def _selected_version(self) -> str:
        row = self.version_table.currentRow()
        item = self.version_table.item(row, 0) if row >= 0 else None
        if item:
            return item.text()
        return self.home_version.currentText()

    def install_selected_version(self, *_args) -> None:
        version = self._selected_version()
        if not version:
            return
        self.install_version_button.setEnabled(False)
        self.status_label.setText(f"Instalando Minecraft {version}…")
        self.progress_text.setText(f"Preparando Minecraft {version}")
        self._log(f"Instalación iniciada: {version}")
        self._run_worker(self._install_job, version, self.settings.game_dir, finished=lambda _result: self._install_finished(version), progress=True)

    def _install_job(self, version: str, game_root: Path, progress) -> None:
        self.minecraft.install(version, game_root, progress)

    def remove_selected_version(self) -> None:
        version = self._selected_version()
        if not version:
            return
        if version not in getattr(self, "installed_ids", set()):
            QMessageBox.information(self, "Versión", f"Minecraft {version} no está instalado.")
            return
        answer = QMessageBox.question(self, "Eliminar versión", f"Eliminar los archivos de Minecraft {version}? Los perfiles y sus mundos se conservarán; tendrás que instalar de nuevo esta versión para jugar.")
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.minecraft.remove_version(version, self.settings.game_dir)
        except Exception as exc:
            QMessageBox.critical(self, "No se pudo eliminar", str(exc))
            return
        self._log(f"Versión eliminada: {version}")
        self.refresh_installed()
        self.status_label.setText(f"Versión {version} eliminada")

    def _install_finished(self, version: str) -> None:
        self.install_version_button.setEnabled(True)
        self.progress_text.setText(f"Minecraft {version} está listo")
        self.progress_bar.setValue(100)
        self.status_label.setText(f"Versión {version} instalada y verificada")
        self._log(f"Versión instalada/verificada: {version}")
        self.refresh_installed()

    def _download_progress(self, status: str, value: int, maximum: int) -> None:
        self.progress_text.setText(status)
        if maximum > 0:
            self.progress_bar.setMaximum(maximum)
            self.progress_bar.setValue(min(value, maximum))
        else:
            self.progress_bar.setRange(0, 0)
        self.status_label.setText(status)

    def refresh_installed(self) -> None:
        self._run_worker(self.minecraft.installed_versions, self.settings.game_dir, finished=self._installed_loaded)

    def _installed_loaded(self, versions: list[dict]) -> None:
        self.installed_ids = {str(v.get("id", "")) for v in versions}
        self._update_home_status()
        self._populate_profiles()

    def _home_version_changed(self, version: str) -> None:
        if self._loading_versions:
            return
        profiles = self.settings.profiles()
        current = profiles.get(self.settings.selected_profile)
        if current and version:
            current["version"] = version
            self.settings.save_profiles(profiles)
        self._update_home_status()

    def _update_home_status(self) -> None:
        version = self.home_version.currentText() if hasattr(self, "home_version") else ""
        installed = getattr(self, "installed_ids", set())
        self.install_state.setText("Instalada" if version in installed else "Pendiente")
        selected = self.settings.profiles().get(self.settings.selected_profile, {"name": "Principal"})
        self.home_profile.setText(f"Perfil: {selected.get('name', 'Principal')}")

    def _populate_profiles(self) -> None:
        if not hasattr(self, "profile_list"):
            return
        profiles = self.settings.profiles()
        self.profile_list.clear()
        for profile_id, data in profiles.items():
            installed = "  •  instalado" if data.get("version") in getattr(self, "installed_ids", set()) else "  •  pendiente"
            item = QListWidgetItem(f"{data.get('name', 'Perfil')}   |   {data.get('version', 'Sin versión')}{installed}")
            item.setData(Qt.ItemDataRole.UserRole, profile_id)
            self.profile_list.addItem(item)
            if profile_id == self.settings.selected_profile:
                self.profile_list.setCurrentItem(item)
        self._update_home_status()

    def create_profile(self) -> None:
        if not self.versions:
            QMessageBox.information(self, "Versiones", "Actualiza el catálogo de versiones antes de crear un perfil.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Nuevo perfil")
        form = QFormLayout(dialog)
        name = QLineEdit()
        name.setPlaceholderText("Por ejemplo: Supervivencia")
        version = QComboBox()
        version.addItems([str(v["id"]) for v in self.versions if v.get("type") == "release"])
        form.addRow("Nombre", name)
        form.addRow("Versión", version)
        buttons = QDialogButtonBox()
        buttons.addButton(QDialogButtonBox.StandardButton.Ok)
        buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted or not name.text().strip():
            return
        profile_id = uuid.uuid4().hex
        profiles = self.settings.profiles()
        profiles[profile_id] = {"name": name.text().strip(), "version": version.currentText()}
        self.settings.save_profiles(profiles)
        self.settings.selected_profile = profile_id
        self._populate_profiles()
        self._update_mods_path()

    def use_selected_profile(self) -> None:
        item = self.profile_list.currentItem()
        if not item:
            return
        self.settings.selected_profile = item.data(Qt.ItemDataRole.UserRole)
        data = self.settings.profiles()[self.settings.selected_profile]
        self.home_version.setCurrentText(data.get("version", ""))
        self._update_home_status()
        self._update_mods_path()

    def delete_profile(self) -> None:
        item = self.profile_list.currentItem()
        if not item:
            return
        profile_id = item.data(Qt.ItemDataRole.UserRole)
        if len(self.settings.profiles()) <= 1:
            QMessageBox.information(self, "Perfil", "Debe quedar al menos un perfil.")
            return
        choice = QMessageBox.question(self, "Eliminar perfil", "Se eliminará el perfil del launcher. Sus partidas y archivos se conservarán en disco.")
        if choice != QMessageBox.StandardButton.Yes:
            return
        profiles = self.settings.profiles()
        profiles.pop(profile_id, None)
        self.settings.save_profiles(profiles)
        if self.settings.selected_profile == profile_id:
            self.settings.selected_profile = next(iter(profiles))
        self._populate_profiles()

    def _profile_game_dir(self) -> Path:
        profile_id = self.settings.selected_profile
        return self.settings.game_dir / "crackecraft_profiles" / profile_id

    def _update_mods_path(self) -> None:
        path = self._profile_game_dir() / "mods"
        self.mods_path_label.setText(str(path))

    def open_mods_folder(self) -> None:
        path = self._profile_game_dir() / "mods"
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _browse_directory(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Directorio de Minecraft", self.directory_field.text())
        if chosen:
            self.directory_field.setText(chosen)

    def _browse_java(self) -> None:
        chosen, _ = QFileDialog.getOpenFileName(self, "Seleccionar Java", self.java_field.text())
        if chosen:
            self.java_field.setText(chosen)

    def _load_settings_into_form(self) -> None:
        self.client_id_field.setText(self.settings.client_id)
        self.directory_field.setText(str(self.settings.game_dir))
        self.ram_spin.setValue(self.settings.memory_mb)
        self.java_field.setText(self.settings.java_path)
        self.jvm_args_field.setText(self.settings.jvm_args)
        self.java_detected.setText(self.minecraft.java_executable())

    def save_settings(self) -> None:
        directory = Path(self.directory_field.text()).expanduser()
        if not directory.is_absolute():
            QMessageBox.warning(self, "Directorio", "El directorio del juego debe ser una ruta absoluta.")
            return
        self.settings.client_id = self.client_id_field.text()
        self.settings.game_dir = directory
        self.settings.memory_mb = self.ram_spin.value()
        self.settings.java_path = self.java_field.text()
        self.settings.jvm_args = self.jvm_args_field.text()
        self.status_label.setText("Ajustes guardados")
        self._log("Ajustes actualizados")
        self.refresh_installed()

    def _populate_accounts(self) -> None:
        self.account_list.clear()
        accounts = self.settings.accounts()
        for account_id, data in accounts.items():
            item = QListWidgetItem(f"{data.get('name', 'Microsoft account')}   ·   {account_id[:8]}")
            item.setData(Qt.ItemDataRole.UserRole, account_id)
            self.account_list.addItem(item)
            if account_id == getattr(self, "active_account_id", ""):
                self.account_list.setCurrentItem(item)

    def _account_selected(self, item: QListWidgetItem | None, _previous=None) -> None:
        if item:
            self.selected_account_id = item.data(Qt.ItemDataRole.UserRole)

    def sign_in(self) -> None:
        client_id = self.settings.client_id
        if not client_id:
            self.show_page(4)
            QMessageBox.information(self, "Configuración necesaria", "Añade el Client ID de una aplicación Microsoft en Ajustes. Usa una aplicación de escritorio pública, sin secreto de cliente.")
            return
        self.status_label.setText("Abriendo inicio de sesión Microsoft en el navegador…")
        self._log("Inicio de sesión Microsoft iniciado")
        self._run_worker(self.auth.login, client_id, finished=self._signed_in)

    def _signed_in(self, account: dict[str, str]) -> None:
        account_id = account.get("id", "")
        if not account_id or not account.get("refresh_token"):
            raise RuntimeError("Microsoft no devolvió una sesión completa de Minecraft.")
        self.credentials.save(account_id, account)
        accounts = self.settings.accounts()
        accounts[account_id] = {"name": account.get("name", "Minecraft player")}
        self.settings.save_accounts(accounts)
        self.active_account_id = account_id
        self.settings.active_account = account_id
        self.current_account = account
        self._update_account_labels()
        self._populate_accounts()
        self.status_label.setText(f"Sesión iniciada como {account.get('name')}")
        self._log(f"Sesión iniciada: {account.get('name')}")

    def use_selected_account(self) -> None:
        account_id = getattr(self, "selected_account_id", "")
        if not account_id:
            return
        self.active_account_id = account_id
        self.settings.active_account = account_id
        self.current_account = None
        self._update_account_labels()
        self.status_label.setText("Cuenta seleccionada; se renovará la sesión al jugar.")

    def remove_selected_account(self) -> None:
        account_id = getattr(self, "selected_account_id", "")
        if not account_id:
            return
        if QMessageBox.question(self, "Quitar cuenta", "Se eliminarán las credenciales guardadas de CrackeCraft.") != QMessageBox.StandardButton.Yes:
            return
        try:
            self.credentials.delete(account_id)
        except Exception as exc:
            QMessageBox.warning(self, "Almacén de credenciales", str(exc))
            return
        accounts = self.settings.accounts()
        accounts.pop(account_id, None)
        self.settings.save_accounts(accounts)
        if getattr(self, "active_account_id", "") == account_id:
            self.active_account_id = ""
            self.settings.active_account = ""
            self.current_account = None
        self._populate_accounts()
        self._update_account_labels()

    def _update_account_labels(self) -> None:
        accounts = self.settings.accounts()
        account_id = getattr(self, "active_account_id", "")
        name = accounts.get(account_id, {}).get("name", "")
        if name:
            self.sidebar_account.setText(name)
            self.header_account.setText(name)
            self.home_account.setText(name)
        else:
            self.sidebar_account.setText("Sin sesión")
            self.header_account.setText("Iniciar sesión")
            self.home_account.setText("Inicia sesión para jugar")

    def play_selected(self) -> None:
        profile = self.settings.profiles().get(self.settings.selected_profile)
        account_id = getattr(self, "active_account_id", "")
        if not profile:
            QMessageBox.information(self, "Perfil", "Crea o selecciona un perfil en Instalaciones.")
            return
        if not account_id:
            self.show_page(5)
            QMessageBox.information(self, "Cuenta Microsoft", "Inicia sesión con una cuenta que tenga Minecraft: Java Edition.")
            return
        self.play_button.setEnabled(False)
        version = profile.get("version") or self.home_version.currentText()
        if not version:
            self.play_button.setEnabled(True)
            QMessageBox.warning(self, "Versión", "Selecciona una versión antes de jugar.")
            return
        self.status_label.setText("Renovando la sesión y preparando Minecraft…")
        self.progress_text.setText("Comprobando la sesión de Microsoft")
        profile_path = self._profile_game_dir()
        profile_path.mkdir(parents=True, exist_ok=True)
        self._run_worker(self._prepare_launch, account_id, version, profile_path, self.settings.game_dir, self.settings.memory_mb, self.settings.java_path, self.settings.jvm_args, self.settings.client_id, finished=self._launch_ready, progress=True)

    def _prepare_launch(self, account_id: str, version: str, profile_path: Path, game_root: Path, memory_mb: int, java_path: str, jvm_args: str, client_id: str, progress) -> tuple[dict[str, str], list[str], str]:
        refreshed = self.auth.refresh(client_id, account_id)
        self.minecraft.install(version, game_root, progress)
        command = self.minecraft.launch_command(version, game_root, profile_path, refreshed, memory_mb, java_path, jvm_args)
        return refreshed, command, str(profile_path)

    def _launch_ready(self, result: tuple[dict[str, str], list[str], str]) -> None:
        account, command, profile_dir = result
        self.current_account = account
        self.progress_bar.setValue(100)
        self.progress_text.setText("Minecraft está iniciándose")
        process = QProcess(self)
        process.setProgram(command[0])
        process.setArguments(command[1:])
        process.setWorkingDirectory(profile_dir)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        process.readyReadStandardOutput.connect(lambda: self._consume_process_output(process))
        process.errorOccurred.connect(lambda error: self._process_error(process, error))
        process.finished.connect(lambda code, status: self._process_finished(process, code, status))
        self.process = process
        self._log("Minecraft iniciado; el comando con credenciales no se registra.")
        process.start()

    def _consume_process_output(self, process: QProcess) -> None:
        # noinspection PyTypeChecker
        raw = bytes(process.readAllStandardOutput()).decode("utf-8", errors="replace")
        secrets = []
        if self.current_account:
            secrets = [self.current_account.get("access_token", ""), self.current_account.get("refresh_token", "")]
        for secret in filter(None, secrets):
            raw = raw.replace(secret, "[token redacted]")
        for line in raw.splitlines():
            if line.strip():
                self.console.append(line)

    def _process_error(self, _process: QProcess, error) -> None:
        self._log(f"Error de proceso Minecraft: {error}")
        self.play_button.setEnabled(True)
        self.status_label.setText("No se pudo iniciar Minecraft")

    def _process_finished(self, _process: QProcess, code: int, _status) -> None:
        self.play_button.setEnabled(True)
        self.status_label.setText("Minecraft se cerró" if code == 0 else f"Minecraft terminó con código {code}")
        self._log(f"Proceso Minecraft finalizado: código {code}")
        self.process = None


