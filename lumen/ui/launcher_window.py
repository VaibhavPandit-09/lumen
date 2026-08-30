"""
Main floating command palette overlay window for Lumen.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

from PyQt6.QtCore import QEvent, QPoint, QRect, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QFont, QGuiApplication, QIcon, QKeyEvent, QScreen
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from lumen.core.actions.dispatcher import ActionDispatcher, DispatchResult, DispatchStatus
from lumen.core.config import LumenConfig
from lumen.core.fuzzy import score_item
from lumen.core.logging import debug, info
from lumen.core.models import ItemCategory, SearchResult
from lumen.providers.actions import CustomActionsProvider
from lumen.providers.applications import ApplicationProvider
from lumen.providers.base import BaseProvider
from lumen.providers.calculator import CalculatorProvider
from lumen.providers.clipboard import ClipboardProvider
from lumen.providers.commands import CommandProvider
from lumen.providers.conversions import ConversionsProvider
from lumen.providers.currency import CurrencyProvider
from lumen.providers.krunner import KRunnerProvider
from lumen.providers.locations import LocationsProvider
from lumen.providers.packages import PackagesProvider
from lumen.providers.recent_files import RecentFilesProvider
from lumen.providers.system_actions import SystemActionsProvider
from lumen.providers.updates import UpdatesProvider
from lumen.providers.web_search import WebSearchProvider
from lumen.ui.animations import WindowAnimationManager
from lumen.ui.navigation import NavigationLevel, NavigationManager
from lumen.ui.result_list import ResultItemDelegate, ResultListWidget
from lumen.ui.search_bar import SearchBar
from lumen.ui.theme import generate_stylesheet, get_theme
from lumen.ui.tray import LumenTrayCompanion


class LauncherWindow(QWidget):
    """Modern, centered floating command palette overlay window."""

    # Cross-thread safety signals for async action dispatch
    _progress_signal = pyqtSignal(str)
    _complete_signal = pyqtSignal(object)

    def __init__(self, config: Optional[LumenConfig] = None):
        super().__init__()
        self.config = config or LumenConfig().load()
        self.theme = get_theme(self.config.theme)
        self.anim_manager = WindowAnimationManager(
            self,
            duration_ms=self.config.animation_duration_ms if self.config.enable_animations else 0,
        )

        # Optional tray companion
        self.tray_companion: Optional[LumenTrayCompanion] = None
        if self.config.enable_tray:
            self.tray_companion = LumenTrayCompanion(self)

        # Provider list
        self.providers: List[BaseProvider] = []
        self._init_providers()

        # Confirmation state tracking
        self._pending_confirmation: Optional[SearchResult] = None

        # Navigation stack for submenus and hierarchical navigation
        self.nav_stack: List[tuple[str, List[SearchResult]]] = []
        self.nav_manager = NavigationManager()

        # Setup UI
        self._init_window_flags()
        self._init_ui()
        self._apply_theme()

        # Connect signals
        self._connect_signals()

        # Initial index / scan
        self.refresh_all_providers()

    def _init_window_flags(self) -> None:
        """Configures frameless floating overlay window properties."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        self.setWindowTitle("Lumen")
        self.setMinimumWidth(self.config.window_width)
        self.resize(self.config.window_width, 420)

    def _init_providers(self) -> None:
        """Initializes all search providers according to config."""
        p_cfg = self.config.providers

        self.app_provider = ApplicationProvider(
            hidden_applications=self.config.hidden_applications,
            enabled=p_cfg.get("applications", True),
        )
        self.pkg_provider = PackagesProvider(
            enabled=p_cfg.get("packages", True),
        )
        self.updates_provider = UpdatesProvider(
            enabled=p_cfg.get("updates", True),
        )
        self.cmd_provider = CommandProvider(
            commands=self.config.commands,
            enabled=p_cfg.get("commands", True),
        )
        self.act_provider = CustomActionsProvider(
            actions_dir=self.config.actions_dir,
            enabled=p_cfg.get("actions", True),
        )
        self.sys_provider = SystemActionsProvider(
            enabled=p_cfg.get("system_actions", True),
        )
        self.loc_provider = LocationsProvider(
            enabled=p_cfg.get("locations", True),
        )
        self.calc_provider = CalculatorProvider(
            enabled=p_cfg.get("calculator", True) and self.config.calculator_auto_evaluate,
        )
        self.conv_provider = ConversionsProvider(
            enabled=p_cfg.get("conversions", True),
        )
        self.cur_provider = CurrencyProvider(
            enabled=p_cfg.get("currency", True),
        )
        self.recent_provider = RecentFilesProvider(
            enabled=p_cfg.get("recent_files", True),
        )
        self.clip_provider = ClipboardProvider(
            enabled=p_cfg.get("clipboard", True),
        )
        self.krunner_provider = KRunnerProvider(
            enabled=p_cfg.get("krunner", True),
        )
        self.web_provider = WebSearchProvider(
            engine_template=self.config.web_search_engine,
            enabled=p_cfg.get("web_search", True),
        )

        self.providers = [
            self.calc_provider,
            self.conv_provider,
            self.cur_provider,
            self.act_provider,
            self.cmd_provider,
            self.app_provider,
            self.pkg_provider,
            self.updates_provider,
            self.sys_provider,
            self.loc_provider,
            self.krunner_provider,
            self.recent_provider,
            self.clip_provider,
            self.web_provider,
        ]

    def refresh_all_providers(self) -> None:
        """Initializes and refreshes all active providers."""
        for p in self.providers:
            try:
                p.initialize()
            except Exception as e:
                print(f"[Lumen] Error initializing provider {p.name}: {e}")

    def _init_ui(self) -> None:
        """Builds UI layout and subwidgets."""
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(12, 12, 12, 12)
        outer_layout.setSpacing(0)

        # Main styled card container
        self.container = QWidget(self)
        self.container.setObjectName("LumenContainer")

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(12, 12, 12, 8)
        container_layout.setSpacing(6)

        # Breadcrumb label
        self.breadcrumb_label = QLabel(self.container)
        self.breadcrumb_label.setObjectName("LumenBreadcrumb")
        self.breadcrumb_label.setVisible(False)
        container_layout.addWidget(self.breadcrumb_label)

        # Search Bar
        self.search_bar = SearchBar(self.container)
        container_layout.addWidget(self.search_bar)

        # Result List
        self.result_list = ResultListWidget(self.container)
        self.delegate = ResultItemDelegate(
            theme=self.theme, show_badges=self.config.show_badges, parent=self.result_list
        )
        self.result_list.setItemDelegate(self.delegate)
        container_layout.addWidget(self.result_list)

        # Footer helper info
        self.footer_label = QLabel(
            "↑↓ Navigate   •   ↵ Execute   •   Click Launch   •   Esc Dismiss",
            self.container,
        )
        self.footer_label.setObjectName("LumenFooter")
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        container_layout.addWidget(self.footer_label)

        outer_layout.addWidget(self.container)

        # Subtle shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)

    def _apply_theme(self) -> None:
        """Applies stylesheet and active theme."""
        self.setStyleSheet(generate_stylesheet(self.theme, opacity=self.config.opacity))
        self.delegate.theme = self.theme

    def _connect_signals(self) -> None:
        """Connects search and navigation events."""
        self.search_bar.textChanged.connect(self._on_search_query_changed)
        self.search_bar.navigate_signal.connect(self._on_navigate_list)
        self.search_bar.activate_signal.connect(lambda: self._on_item_activated())
        self.search_bar.dismiss_signal.connect(self._on_escape_pressed)
        self.search_bar.drill_down_signal.connect(self._on_drill_down)
        self.search_bar.pop_level_signal.connect(self._on_pop_level)

        self.result_list.itemActivated.connect(lambda item: self._on_item_activated(item.data(Qt.ItemDataRole.UserRole)))
        self.result_list.itemClicked.connect(lambda item: self._on_item_activated(item.data(Qt.ItemDataRole.UserRole)))

        # Cross-thread safety: async dispatch callbacks emit signals
        # which are delivered on the Qt main thread
        self._progress_signal.connect(self._on_action_progress)
        self._complete_signal.connect(self._on_action_complete)

    def _on_search_query_changed(self, query: str) -> None:
        """Called whenever search bar text changes."""
        self._pending_confirmation = None
        self._update_breadcrumb()
        self.update_results(query)

    def _on_navigate_list(self, key: int) -> None:
        if key in (Qt.Key.Key_Down, Qt.Key.Key_PageDown):
            self.result_list.select_next()
        elif key in (Qt.Key.Key_Up, Qt.Key.Key_PageUp):
            self.result_list.select_previous()

    def _on_item_activated(self, item: Optional[SearchResult] = None) -> None:
        """Executes the currently selected item or drills into submenu, handling confirmation."""
        if not item:
            item = self.result_list.get_selected_result()
        if not item:
            return

        # If item is a navigation root category (e.g. Apps, Packages, Updates, Commands, Files, System)
        if item.id.startswith("nav:"):
            self._navigate_to_category(item)
            return

        # If item requires subcommands / drill down
        if item.has_subcommands():
            self.push_submenu(item.title, item.subcommands)
            return

        confirmed = (self._pending_confirmation == item)

        # Dispatch action through canonical ActionDispatcher
        # Use signal .emit methods for thread-safe cross-thread callbacks
        res = ActionDispatcher.dispatch(
            item=item,
            on_progress=self._progress_signal.emit,
            on_complete=self._complete_signal.emit,
            confirmed=confirmed,
        )

        if res.status == DispatchStatus.CONFIRMATION_REQUIRED:
            self._pending_confirmation = item
            prompt = res.message or f"Confirm: {item.title}?"
            self.breadcrumb_label.setText(f"⚠️ {prompt} — Press Enter again or click to execute (Esc to cancel)")
            self.breadcrumb_label.setStyleSheet("color: #F59E0B; font-size: 11px; font-weight: bold;")
            self.breadcrumb_label.setVisible(True)
            return

        self._pending_confirmation = None

        if res.dismiss_window:
            self.dismiss()

    def _navigate_to_category(self, item: SearchResult) -> None:
        """Navigates to a specific category surface with filtered provider context."""
        cat_map = {
            "nav:apps": ("Apps", "applications", "Search applications..."),
            "nav:packages": ("Packages", "packages", "Search, install, or remove software..."),
            "nav:updates": ("Updates", "updates", "Search or run updates..."),
            "nav:commands": ("Commands", "commands", "Search custom commands..."),
            "nav:files": ("Files", "files", "Search files and locations..."),
            "nav:system": ("System", "system_actions", "System actions..."),
        }

        title, p_filter, placeholder = cat_map.get(
            item.id, (item.title, None, f"Search {item.title.lower()}...")
        )

        level = NavigationLevel(
            title=title,
            provider_filter=p_filter,
            placeholder_text=placeholder,
            icon_name=item.icon_name,
        )
        self.nav_manager.push(level)
        self.search_bar.clear()
        self.search_bar.setPlaceholderText(placeholder)
        self._update_breadcrumb()
        self.update_results("")

    def _pop_navigation_level(self) -> None:
        """Pops one level up the hierarchical navigation stack."""
        self.nav_manager.pop()
        curr = self.nav_manager.current_level()
        if curr:
            self.search_bar.setPlaceholderText(curr.placeholder_text)
        else:
            self.search_bar.setPlaceholderText("Type to search, calculate, or execute commands...")
        self.search_bar.clear()
        self._update_breadcrumb()
        self.update_results("")

    def _on_action_progress(self, progress_text: str) -> None:
        """Shows non-blocking progress in the breadcrumb bar."""
        self.breadcrumb_label.setText(f"⚙️ {progress_text}")
        self.breadcrumb_label.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: bold;")
        self.breadcrumb_label.setVisible(True)

    def _on_action_complete(self, result: DispatchResult) -> None:
        """Called when an async action completes."""
        if result.status == DispatchStatus.SUCCESS:
            self.breadcrumb_label.setText(f"✓ {result.message}")
            self.breadcrumb_label.setStyleSheet("color: #10B981; font-size: 11px; font-weight: bold;")
            # Immediately re-index desktop applications
            try:
                self.app_provider.scanner.scan()
            except Exception:
                pass
        else:
            self.breadcrumb_label.setText(f"❌ {result.message}")
            self.breadcrumb_label.setStyleSheet("color: #EF4444; font-size: 11px; font-weight: bold;")

    def _on_drill_down(self) -> None:
        """Enters submenu if current item has subcommands."""
        selected = self.result_list.get_selected_result()
        if selected and selected.id.startswith("nav:"):
            self._navigate_to_category(selected)
        elif selected and selected.has_subcommands():
            self.push_submenu(selected.title, selected.subcommands)

    def _on_pop_level(self) -> None:
        """Pops one level up the navigation or submenu stack."""
        if self.nav_stack:
            self.pop_submenu()
        elif not self.nav_manager.is_at_root():
            self._pop_navigation_level()

    def push_submenu(self, title: str, items: List[SearchResult]) -> None:
        """Pushes a new submenu level onto navigation stack."""
        self.nav_stack.append((title, items))
        self.search_bar.clear()
        self._update_breadcrumb()
        self.update_results("")

    def pop_submenu(self) -> None:
        """Pops previous submenu level."""
        if self.nav_stack:
            self.nav_stack.pop()
            self.search_bar.clear()
            self._update_breadcrumb()
            self.update_results("")

    def _update_breadcrumb(self) -> None:
        """Updates top breadcrumb header label."""
        if self._pending_confirmation:
            return

        if self.nav_stack:
            path_str = " > ".join([title for title, _ in self.nav_stack])
            self.breadcrumb_label.setText(f"Lumen  ›  {path_str}")
            self.breadcrumb_label.setStyleSheet(f"color: {self.theme.accent_color}; font-size: 11px; font-weight: bold;")
            self.breadcrumb_label.setVisible(True)
        elif not self.nav_manager.is_at_root():
            path_str = self.nav_manager.breadcrumb_path()
            self.breadcrumb_label.setText(path_str)
            self.breadcrumb_label.setStyleSheet(f"color: {self.theme.accent_color}; font-size: 11px; font-weight: bold;")
            self.breadcrumb_label.setVisible(True)
        else:
            self.breadcrumb_label.setVisible(False)

    def update_results(self, query: str) -> None:
        """Computes and populates search results with safe provider execution."""
        self.result_list.clear()
        q = query.strip()

        # 1. If inside a submenu, search only within current submenu items
        if self.nav_stack:
            current_items = self.nav_stack[-1][1]
            if not q:
                results = current_items
            else:
                results = []
                for item in current_items:
                    matched, score = score_item(
                        query=q,
                        title=item.title,
                        subtitle=item.subtitle,
                        keywords=item.keywords,
                        category=item.category,
                    )
                    if matched:
                        results.append(item)
                results.sort(key=lambda x: x.score, reverse=True)

        # 2. If inside a category surface (NavigationLevel), query filtered providers
        elif not self.nav_manager.is_at_root():
            curr_level = self.nav_manager.current_level()
            p_filter = curr_level.provider_filter if curr_level else None
            results = []

            if p_filter == "applications":
                results = self.app_provider.safe_search(q)
            elif p_filter == "packages":
                results = self.pkg_provider.safe_search(q)
            elif p_filter == "updates":
                results = self.updates_provider.safe_search(q)
            elif p_filter == "commands":
                results = self.cmd_provider.safe_search(q)
            elif p_filter == "files":
                results = self.loc_provider.safe_search(q) + self.recent_provider.safe_search(q)
            elif p_filter == "system_actions":
                results = self.sys_provider.safe_search(q)

            results.sort(key=lambda x: x.score, reverse=True)

        # 3. If at Root level
        else:
            if not q:
                # Show root navigation categories
                results = self.nav_manager.get_root_categories()
            else:
                # Unified multi-provider search
                all_results: List[SearchResult] = []
                for provider in self.providers:
                    if provider.enabled:
                        res = provider.safe_search(q)
                        all_results.extend(res)

                all_results.sort(key=lambda x: x.score, reverse=True)
                results = all_results[: self.config.max_results]

        # Empty state fallback (when user typed a query and nothing matched)
        if q and not results:
            from lumen.core.runner import open_path_or_url
            import urllib.parse
            encoded = urllib.parse.quote_plus(q)
            web_url = self.config.web_search_engine.replace("%s", encoded)

            empty_item = SearchResult(
                id="empty:search",
                title=f"No matching local results for '{q}'",
                subtitle="Press Enter to search the web in default browser",
                category=ItemCategory.WEB.value,
                icon_name="system-search",
                action=lambda url=web_url: open_path_or_url(url),
                badge="Web Search",
                is_empty_state=True,
            )
            results = [empty_item]

        # Populate ListWidget
        for item in results:
            list_item = QListWidgetItem(self.result_list)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.result_list.addItem(list_item)

        # Select first result by default
        if self.result_list.count() > 0:
            self.result_list.setCurrentRow(0)

        # Dynamically adjust window height
        item_count = self.result_list.count()
        desired_height = 110 + (max(1, item_count) * 52)
        if self.breadcrumb_label.isVisible():
            desired_height += 24
        self.resize(self.config.window_width, max(140, min(desired_height, 650)))

    def center_on_active_screen(self) -> None:
        """Centers launcher horizontally and places in top 20% of active screen with cursor."""
        cursor_pos = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor_pos) or QGuiApplication.primaryScreen()
        if not screen:
            return

        geo = screen.geometry()
        win_w = self.width()
        x = geo.x() + (geo.width() - win_w) // 2
        y = geo.y() + int(geo.height() * 0.18)
        self.move(x, y)

    def show_launcher(self) -> None:
        """Presents the launcher window, focuses search input, and resets state."""
        self.nav_stack.clear()
        self.nav_manager.reset()
        self._pending_confirmation = None
        self._update_breadcrumb()
        self.search_bar.clear()
        self.search_bar.setPlaceholderText("Type to search, calculate, or execute commands...")
        self.update_results("")

        self.result_list.activate_hover_guard()
        self.center_on_active_screen()
        self.anim_manager.animate_show(on_finished=lambda: self.search_bar.setFocus())
        self.raise_()
        self.activateWindow()
        self.search_bar.setFocus()

    def dismiss(self) -> None:
        """Hides the launcher overlay with subtle transition and full state reset."""
        self.anim_manager.animate_hide()
        self._pending_confirmation = None
        self.search_bar.clear()
        self.search_bar.setPlaceholderText("Type to search, calculate, or execute commands...")
        self.nav_stack.clear()
        self.nav_manager.reset()
        self._update_breadcrumb()

    def toggle(self) -> None:
        """Toggles visibility of launcher."""
        if self.isVisible() and self.isActiveWindow():
            self.dismiss()
        else:
            self.show_launcher()

    def changeEvent(self, event: QEvent) -> None:
        """Auto-hide launcher when user clicks outside or window loses focus."""
        if event.type() == QEvent.Type.ActivationChange:
            if not self.isActiveWindow():
                QTimer.singleShot(120, self._check_focus_and_hide)
        super().changeEvent(event)

    def _check_focus_and_hide(self) -> None:
        if not self.isActiveWindow() and self.isVisible():
            self.dismiss()

    def closeEvent(self, event) -> None:
        """Prevent WM from destroying the launcher window; hide instead."""
        event.ignore()
        self.dismiss()

    def _on_escape_pressed(self) -> None:
        """
        Implements the proper escape key hierarchy:
        1. Cancel pending confirmation prompt
        2. Pop submenu navigation level
        3. Pop hierarchical category navigation level
        4. Clear search text (if non-empty)
        5. Dismiss the launcher
        """
        if self._pending_confirmation:
            self._pending_confirmation = None
            self._update_breadcrumb()
            self.update_results(self.search_bar.text())
        elif self.nav_stack:
            self.pop_submenu()
        elif not self.nav_manager.is_at_root():
            self._pop_navigation_level()
        elif self.search_bar.text():
            self.search_bar.clear()
        else:
            self.dismiss()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self._on_escape_pressed()
            event.accept()
            return
        super().keyPressEvent(event)
