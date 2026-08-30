"""
Custom item delegate and result list view for Lumen search results.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QPoint, QRect, QSize, Qt
from PyQt6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QStyle, QStyledItemDelegate

from lumen.core.models import SearchResult
from lumen.ui.theme import ThemeColors


class ResultItemDelegate(QStyledItemDelegate):
    """Paints search results with icons, title, subtitle, badge, and navigation hints."""

    def __init__(self, theme: ThemeColors, show_badges: bool = True, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.show_badges = show_badges

    def sizeHint(self, option, index) -> QSize:
        return QSize(option.rect.width(), 52)

    def paint(self, painter: QPainter, option, index) -> None:
        item: Optional[SearchResult] = index.data(Qt.ItemDataRole.UserRole)
        if not item:
            super().paint(painter, option, index)
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        rect = option.rect.adjusted(4, 2, -4, -2)

        # 1. Background selection pill
        if is_selected:
            path = QPainterPath()
            path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), 8, 8)
            painter.fillPath(path, QColor(self.theme.selected_bg))
        elif option.state & QStyle.StateFlag.State_MouseOver:
            path = QPainterPath()
            path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), 8, 8)
            painter.fillPath(path, QColor(self.theme.badge_bg))

        # 2. Draw Icon (28x28)
        icon_size = 28
        icon_rect = QRect(rect.x() + 10, rect.y() + (rect.height() - icon_size) // 2, icon_size, icon_size)
        
        if item.is_empty_state:
            icon = QIcon.fromTheme("system-search")
        else:
            icon = QIcon.fromTheme(item.icon_name)
            if icon.isNull():
                icon = QIcon(item.icon_name)
                if icon.isNull():
                    icon = QIcon.fromTheme("application-x-executable")

        icon.paint(painter, icon_rect, Qt.AlignmentFlag.AlignCenter)

        # Calculate right-side badges width
        right_margin = 12
        if item.has_subcommands():
            # Draw chevron arrow
            chevron_font = QFont()
            chevron_font.setPointSize(14)
            chevron_font.setBold(True)
            painter.setFont(chevron_font)
            painter.setPen(QColor("#FFFFFF" if is_selected else self.theme.accent_color))
            chevron_rect = QRect(rect.right() - right_margin - 12, rect.y(), 16, rect.height())
            painter.drawText(chevron_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, "›")
            right_margin += 22

        if self.show_badges and item.badge:
            badge_text = item.badge
            badge_font = QFont()
            badge_font.setPointSize(9)
            badge_font.setBold(True)
            painter.setFont(badge_font)
            fm = QFontMetrics(badge_font)
            badge_w = fm.horizontalAdvance(badge_text) + 14
            badge_h = 20
            badge_x = rect.right() - right_margin - badge_w
            badge_y = rect.y() + (rect.height() - badge_h) // 2
            badge_rect = QRect(badge_x, badge_y, badge_w, badge_h)

            badge_path = QPainterPath()
            badge_path.addRoundedRect(badge_rect.x(), badge_rect.y(), badge_rect.width(), badge_rect.height(), 5, 5)

            if is_selected:
                painter.fillPath(badge_path, QColor(255, 255, 255, 45))
                painter.setPen(QColor("#FFFFFF"))
            else:
                painter.fillPath(badge_path, QColor(self.theme.badge_bg))
                painter.setPen(QColor(self.theme.badge_text))

            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, badge_text)
            right_margin += badge_w + 10

        # 3. Draw Title and Subtitle
        text_left = icon_rect.right() + 14
        text_width = rect.width() - (text_left - rect.x()) - right_margin

        # Title
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QColor("#FFFFFF" if is_selected else self.theme.text_primary))

        if item.subtitle:
            title_rect = QRect(text_left, rect.y() + 7, text_width, 20)
            painter.drawText(
                title_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                painter.fontMetrics().elidedText(item.title, Qt.TextElideMode.ElideRight, text_width),
            )

            # Subtitle
            sub_font = QFont()
            sub_font.setPointSize(9)
            painter.setFont(sub_font)
            painter.setPen(QColor("rgba(255, 255, 255, 0.75)" if is_selected else self.theme.text_secondary))
            sub_rect = QRect(text_left, rect.y() + 27, text_width, 18)
            painter.drawText(
                sub_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                painter.fontMetrics().elidedText(item.subtitle, Qt.TextElideMode.ElideRight, text_width),
            )
        else:
            title_rect = QRect(text_left, rect.y(), text_width, rect.height())
            painter.drawText(
                title_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                painter.fontMetrics().elidedText(item.title, Qt.TextElideMode.ElideRight, text_width),
            )

        painter.restore()


class ResultListWidget(QListWidget):
    """Custom ListWidget displaying search results with smooth scrolling and keyboard selection."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LumenResultList")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setMouseTracking(True)

    def select_next(self) -> None:
        count = self.count()
        if count == 0:
            return
        curr = self.currentRow()
        next_row = (curr + 1) % count
        self.setCurrentRow(next_row)

    def select_previous(self) -> None:
        count = self.count()
        if count == 0:
            return
        curr = self.currentRow()
        prev_row = (curr - 1 + count) % count
        self.setCurrentRow(prev_row)

    def get_selected_result(self) -> Optional[SearchResult]:
        item = self.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None

    def mouseMoveEvent(self, event):
        item = self.itemAt(event.pos())
        if item:
            self.setCurrentItem(item)
        super().mouseMoveEvent(event)

