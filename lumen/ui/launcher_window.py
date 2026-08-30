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

from lumen.core.config import LumenConfig
from lumen.core.fuzzy import score_item
from lumen.core.logging import debug, info
from lumen.core.models import ItemCategory, SearchResult
from lumen.providers.applications import ApplicationProvider
from lumen.providers.base import BaseProvider
from lumen.providers.calculator import CalculatorProvider
from lumen.providers.clipboard import ClipboardProvider
from lumen.providers.commands import CommandProvider
from lumen.providers.krunner import KRunnerProvider
from lumen.providers.locations import LocationsProvider
from lumen.providers.recent_files import RecentFilesProvider
from lumen.providers.system_actions import SystemActionsProvider
from lumen.providers.web_search import WebSearchProvider
from lumen.ui.animations import WindowAnimationManager
from lumen.ui.result_list import ResultItemDelegate, ResultListWidget
from lumen.ui.search_bar import SearchBar
from lumen.ui.theme import generate_stylesheet, get_theme


class LauncherWindow(QWidget):
    """Modern, centered floating command palette overlay window."""

    def __init__(self, config: Optional[LumenConfig] = None):
        super().__init__()
        self.config = config or LumenConfig().load()
        self.theme = get_theme(self.config.theme)
        self.anim_manager = WindowAnimationManager(
            self,
            duration_ms=self.config.animation_duration_ms if self.config.enable_animations else 0,
        )

        # Provider list
        self.providers: List[BaseProvider] = []
        self._init_providers()

        # Navigation stack for submenus
        # Each entry is a tuple: (title: str, items: List[SearchResult])
        self.nav_stack: List[tuple[str, List[SearchResult]]] = []

        # Setup UI
        self._init_window_flags()
        self._init_ui()
        self._apply_theme()

        # Connect signals
        self._connect_signals()

        # Initial index / scan
        self.refresh_all_providers()

    def _init_window_flags(self) -> None:
        """Configures frameless floating window properties."""
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
        self.cmd_provider = CommandProvider(
            commands=self.config.commands,
            enabled=p_cfg.get("commands", True),
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
            self.cmd_provider,
            self.app_provider,
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
        # Outer container layout for drop shadow margins
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
            "↑↓ Navigate   •   ↵ Launch   •   Tab Submenu   •   Esc Dismiss",
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
        self.search_bar.activate_signal.connect(self._on_activate_item)
        self.search_bar.dismiss_signal.connect(self.dismiss)
        self.search_bar.drill_down_signal.connect(self._on_drill_down)
        self.search_bar.pop_level_signal.connect(self._on_pop_level)

        self.result_list.itemActivated.connect(lambda _: self._on_activate_item())
        self.result_list.itemClicked.connect(lambda _: self._on_activate_item())

    def _on_search_query_changed(self, query: str) -> None:
        """Called whenever search bar text changes."""
        self.update_results(query)

    def _on_navigate_list(self, key: int) -> None:
        if key in (Qt.Key.Key_Down, Qt.Key.Key_PageDown):
            self.result_list.select_next()
        elif key in (Qt.Key.Key_Up, Qt.Key.Key_PageUp):
            self.result_list.select_previous()

    def _on_activate_item(self) -> None:
        """Executes currently selected item or enters submenu."""
        selected = self.result_list.get_selected_result()
        if not selected:
            return

        # If item has subcommands and query is not an exact match on action, enter submenu
        if selected.has_subcommands():
            self.push_submenu(selected.title, selected.subcommands)
            return

        # Execute action and dismiss launcher
        self.dismiss()
        QTimer.singleShot(50, lambda: selected.execute())

    def _on_drill_down(self) -> None:
        """Enters submenu if current item has subcommands."""
        selected = self.result_list.get_selected_result()
        if selected and selected.has_subcommands():
            self.push_submenu(selected.title, selected.subcommands)

    def _on_pop_level(self) -> None:
        """Pops one level up the navigation stack."""
        if self.nav_stack:
            self.pop_submenu()

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
        if not self.nav_stack:
            self.breadcrumb_label.setVisible(False)
        else:
            path_str = " > ".join([title for title, _ in self.nav_stack])
            self.breadcrumb_label.setText(f"Lumen  ›  {path_str}")
            self.breadcrumb_label.setVisible(True)

    def update_results(self, query: str) -> None:
        """Computes and populates search results with safe provider execution."""
        self.result_list.clear()
        q = query.strip()

        # If inside a submenu, search only within current submenu items
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
                        scored = SearchResult(
                            id=item.id,
                            title=item.title,
                            subtitle=item.subtitle,
                            category=item.category,
                            icon_name=item.icon_name,
                            score=score,
                            action=item.action,
                            subcommands=item.subcommands,
                            badge=item.badge,
                            keywords=item.keywords,
                            shortcut_hint=item.shortcut_hint,
                            context=item.context,
                            origin_provider=item.origin_provider,
                        )
                        results.append(scored)
                results.sort(key=lambda x: x.score, reverse=True)
        else:
            # Search across all enabled providers using error-safe boundaries
            all_results: List[SearchResult] = []
            for provider in self.providers:
                if provider.enabled:
                    res = provider.safe_search(q)
                    all_results.extend(res)

            # Sort descending by match score
            all_results.sort(key=lambda x: x.score, reverse=True)
            results = all_results[: self.config.max_results]

        # If user typed a query and no results were found, display clean empty state
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

        # Dynamically adjust window height based on result count
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
        self._update_breadcrumb()
        self.search_bar.clear()
        self.update_results("")

        self.center_on_active_screen()
        self.anim_manager.animate_show(on_finished=lambda: self.search_bar.setFocus())
        self.raise_()
        self.activateWindow()
        self.search_bar.setFocus()

    def dismiss(self) -> None:
        """Hides the launcher overlay with subtle transition."""
        self.anim_manager.animate_hide()
        self.search_bar.clear()
        self.nav_stack.clear()

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
                # Allow a tiny grace period to avoid instant dismiss during launch
                QTimer.singleShot(120, self._check_focus_and_hide)
        super().changeEvent(event)

    def _check_focus_and_hide(self) -> None:
        if not self.isActiveWindow() and self.isVisible():
            self.dismiss()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            if self.nav_stack:
                self.pop_submenu()
            else:
                self.dismiss()
            event.accept()
            return
        super().keyPressEvent(event)
