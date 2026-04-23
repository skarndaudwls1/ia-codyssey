from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout,
    QPushButton, QLabel, QVBoxLayout,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QRectF, QTime, QTimer, QPointF
from PyQt5.QtGui import (
    QPainter, QPainterPath, QColor, QPen, QBrush, QFont, QFontMetrics,
    QLinearGradient, QRadialGradient
)


# ── 아이폰 17 Pro 외형 크기 ──
PHONE_WIDTH = 400
PHONE_HEIGHT = 840

SHADOW_MARGIN = 32
WIN_WIDTH = PHONE_WIDTH + SHADOW_MARGIN * 2
WIN_HEIGHT = PHONE_HEIGHT + SHADOW_MARGIN * 2

PHONE_RADIUS = 62
FRAME_THICKNESS = 4
INNER_BEZEL = 3
SCREEN_RADIUS = 54

ISLAND_WIDTH = 118
ISLAND_HEIGHT = 34
ISLAND_TOP_OFFSET = 14

STATUS_BAR_HEIGHT = 58
HOME_INDICATOR_HEIGHT = 34

# ── 계산기 로직 상수 ──
MAX_INPUT_DIGITS = 15
TOAST_DURATION_MS = 1500
TOAST_Y_RATIO = 0.38
DISPLAY_AVAIL_WIDTH_FALLBACK = 320
DISPLAY_H_MARGINS = 40 + 24  # 레이아웃 좌우 여백 + 디스플레이 안쪽 여백

# ── 글꼴 목록 (한글 대체 글꼴 포함) ──
FONT_FAMILY = (
    '"Helvetica Neue", "Helvetica", "Arial", '
    '"Malgun Gothic", "Apple SD Gothic Neo", '
    '"Noto Sans CJK KR", "Noto Sans KR", sans-serif'
)

# ── 버튼 타입별 스타일 ──
BUTTON_STYLES = {
    'num': {
        'bg': '#333333', 'fg': 'white',
        'font_size': '34px', 'pressed': '#737373',
    },
    'op': {
        'bg': '#FF9F0A', 'fg': 'white',
        'font_size': '36px', 'pressed': '#FFC966',
    },
    'func': {
        'bg': '#A5A5A5', 'fg': 'black',
        'font_size': '28px', 'pressed': '#D4D4D2',
    },
}
BUTTON_RADIUS = '37px'
OP_ACTIVE_BG = 'white'
OP_ACTIVE_FG = '#FF9F0A'
OP_ACTIVE_PRESSED = '#FFE5B4'

# ── 계산기 버튼 배치 ──
# 각 항목: (버튼 글자, 행, 열, 행 병합 수, 열 병합 수, 버튼 종류, 추가 CSS)
BUTTON_LAYOUT = [
    ('AC',  0, 0, 1, 1, 'func', ''),
    ('+/-', 0, 1, 1, 1, 'func', ''),
    ('%',   0, 2, 1, 1, 'func', ''),
    ('÷',   0, 3, 1, 1, 'op',   ''),
    ('7',   1, 0, 1, 1, 'num',  ''),
    ('8',   1, 1, 1, 1, 'num',  ''),
    ('9',   1, 2, 1, 1, 'num',  ''),
    ('×',   1, 3, 1, 1, 'op',   ''),
    ('4',   2, 0, 1, 1, 'num',  ''),
    ('5',   2, 1, 1, 1, 'num',  ''),
    ('6',   2, 2, 1, 1, 'num',  ''),
    ('-',   2, 3, 1, 1, 'op',   ''),
    ('1',   3, 0, 1, 1, 'num',  ''),
    ('2',   3, 1, 1, 1, 'num',  ''),
    ('3',   3, 2, 1, 1, 'num',  ''),
    ('+',   3, 3, 1, 1, 'op',   ''),
    ('0',   4, 0, 1, 2, 'num',  'text-align: left; padding-left: 30px;'),
    ('.',   4, 2, 1, 1, 'num',  ''),
    ('=',   4, 3, 1, 1, 'op',   ''),
]
OPERATORS = ('+', '-', '×', '÷')

# ── 키보드 입력 매핑 (누른 키 → 계산기 버튼) ──
KEY_TEXT_MAP = {
    '+': '+', '-': '-', '*': '×', '/': '÷',
    '.': '.', '%': '%', '=': '=',
}


class IPhoneFrame(QWidget):
    '''아이폰 17 Pro 본체(알루미늄 프레임/노치/측면 버튼)를 그리는 바깥 위젯.'''

    def __init__(self):
        super().__init__()
        self.setFixedSize(WIN_WIDTH, WIN_HEIGHT)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setFocusPolicy(Qt.StrongFocus)

        self._drag_pos = None

        inset = FRAME_THICKNESS + INNER_BEZEL
        self.screen = CalculatorScreen(self)
        self.screen.setGeometry(
            SHADOW_MARGIN + inset,
            SHADOW_MARGIN + inset,
            PHONE_WIDTH - 2 * inset,
            PHONE_HEIGHT - 2 * inset,
        )

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self.update)
        self._clock_timer.start(30000)

    # ── 화면 그리기 (창이 다시 그려질 때마다 호출됨) ──
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        phone_x = SHADOW_MARGIN
        phone_y = SHADOW_MARGIN

        self._draw_shadow(painter, phone_x, phone_y)
        self._draw_body_and_screen(painter, phone_x, phone_y)
        screen_rect = QRectF(
            phone_x + FRAME_THICKNESS + INNER_BEZEL,
            phone_y + FRAME_THICKNESS + INNER_BEZEL,
            PHONE_WIDTH - 2 * (FRAME_THICKNESS + INNER_BEZEL),
            PHONE_HEIGHT - 2 * (FRAME_THICKNESS + INNER_BEZEL),
        )
        self._draw_dynamic_island(painter, phone_x, screen_rect)
        self._draw_status_bar(painter, screen_rect)
        self._draw_home_indicator(painter, phone_x, screen_rect)
        self._draw_side_buttons(painter, phone_x, phone_y)

    def _draw_shadow(self, painter, phone_x, phone_y):
        painter.setPen(Qt.NoPen)
        for i in range(14):
            alpha = max(0, 60 - i * 4)
            if alpha == 0:
                continue
            painter.setBrush(QColor(0, 0, 0, alpha))
            path = QPainterPath()
            path.addRoundedRect(
                QRectF(
                    phone_x - i, phone_y - i + 4,
                    PHONE_WIDTH + i * 2, PHONE_HEIGHT + i * 2,
                ),
                PHONE_RADIUS + i, PHONE_RADIUS + i,
            )
            painter.drawPath(path)

    def _draw_body_and_screen(self, painter, phone_x, phone_y):
        # 알루미늄 사이드 프레임
        body_rect = QRectF(phone_x, phone_y, PHONE_WIDTH, PHONE_HEIGHT)
        body_path = QPainterPath()
        body_path.addRoundedRect(body_rect, PHONE_RADIUS, PHONE_RADIUS)

        frame_grad = QLinearGradient(body_rect.topLeft(), body_rect.bottomRight())
        for stop, color in (
            (0.00, '#9a9c9f'), (0.20, '#c6c8cb'),
            (0.45, '#7b7d80'), (0.60, '#acaeb1'),
            (0.80, '#6a6c6f'), (1.00, '#8d8f92'),
        ):
            frame_grad.setColorAt(stop, QColor(color))
        painter.fillPath(body_path, QBrush(frame_grad))

        painter.setPen(QPen(QColor(255, 255, 255, 55), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(body_path)

        # 안쪽 어두운 테두리 (금속 단면 느낌)
        inset_rect = QRectF(
            phone_x + FRAME_THICKNESS - 1, phone_y + FRAME_THICKNESS - 1,
            PHONE_WIDTH - 2 * (FRAME_THICKNESS - 1),
            PHONE_HEIGHT - 2 * (FRAME_THICKNESS - 1),
        )
        inset_path = QPainterPath()
        inset_path.addRoundedRect(inset_rect, PHONE_RADIUS - 2, PHONE_RADIUS - 2)
        painter.setPen(QPen(QColor(0, 0, 0, 160), 1.5))
        painter.drawPath(inset_path)

        # 스크린 유리 영역
        glass_rect = QRectF(
            phone_x + FRAME_THICKNESS, phone_y + FRAME_THICKNESS,
            PHONE_WIDTH - 2 * FRAME_THICKNESS,
            PHONE_HEIGHT - 2 * FRAME_THICKNESS,
        )
        painter.setPen(Qt.NoPen)
        glass_path = QPainterPath()
        glass_path.addRoundedRect(
            glass_rect, SCREEN_RADIUS + 2, SCREEN_RADIUS + 2
        )
        painter.fillPath(glass_path, QColor('#000000'))

        # 실제 화면 영역 (검정 OLED)
        screen_rect = QRectF(
            phone_x + FRAME_THICKNESS + INNER_BEZEL,
            phone_y + FRAME_THICKNESS + INNER_BEZEL,
            PHONE_WIDTH - 2 * (FRAME_THICKNESS + INNER_BEZEL),
            PHONE_HEIGHT - 2 * (FRAME_THICKNESS + INNER_BEZEL),
        )
        screen_path = QPainterPath()
        screen_path.addRoundedRect(screen_rect, SCREEN_RADIUS, SCREEN_RADIUS)
        painter.fillPath(screen_path, QColor('#000000'))

    def _draw_dynamic_island(self, painter, phone_x, screen_rect):
        island_x = phone_x + (PHONE_WIDTH - ISLAND_WIDTH) / 2
        island_y = screen_rect.y() + ISLAND_TOP_OFFSET
        island_rect = QRectF(island_x, island_y, ISLAND_WIDTH, ISLAND_HEIGHT)
        island_path = QPainterPath()
        island_path.addRoundedRect(
            island_rect, ISLAND_HEIGHT / 2, ISLAND_HEIGHT / 2
        )
        painter.setPen(Qt.NoPen)
        painter.fillPath(island_path, QColor('#000000'))

        # Face ID 센서
        painter.setBrush(QBrush(QColor('#0d0d0d')))
        painter.drawEllipse(
            QPointF(island_x + 24, island_y + ISLAND_HEIGHT / 2), 4, 4
        )

        # 전면 카메라
        cam_r = 6
        cam_cx = island_x + ISLAND_WIDTH - 22
        cam_cy = island_y + ISLAND_HEIGHT / 2
        painter.setBrush(QBrush(QColor('#1a1a1f')))
        painter.drawEllipse(QPointF(cam_cx, cam_cy), cam_r, cam_r)

        lens_grad = QRadialGradient(QPointF(cam_cx - 1, cam_cy - 1), cam_r)
        lens_grad.setColorAt(0.0, QColor('#2a2e38'))
        lens_grad.setColorAt(0.7, QColor('#0a0c12'))
        lens_grad.setColorAt(1.0, QColor('#000000'))
        painter.setBrush(QBrush(lens_grad))
        painter.drawEllipse(QPointF(cam_cx, cam_cy), cam_r - 1, cam_r - 1)
        painter.setBrush(QBrush(QColor(255, 255, 255, 110)))
        painter.drawEllipse(QPointF(cam_cx - 2, cam_cy - 2), 1.3, 1.3)

    def _draw_status_bar(self, painter, screen_rect):
        painter.setPen(QColor('white'))
        font = QFont('Helvetica', 15)
        font.setBold(True)
        painter.setFont(font)

        time_text = QTime.currentTime().toString('h:mm')
        time_rect = QRectF(
            screen_rect.x() + 30, screen_rect.y() + 18, 90, 28
        )
        painter.drawText(time_rect, Qt.AlignLeft | Qt.AlignVCenter, time_text)

        icon_right = screen_rect.right() - 30
        icon_cy = screen_rect.y() + 32

        # 배터리
        batt_w, batt_h = 26, 12
        batt_x = icon_right - batt_w
        batt_y = icon_cy - batt_h / 2
        painter.setPen(QPen(QColor(255, 255, 255, 200), 1.2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(QRectF(batt_x, batt_y, batt_w, batt_h), 3, 3)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor('white')))
        fill_w = (batt_w - 4) * 0.92
        painter.drawRoundedRect(
            QRectF(batt_x + 2, batt_y + 2, fill_w, batt_h - 4), 1.5, 1.5
        )
        painter.drawRoundedRect(
            QRectF(batt_x + batt_w + 0.5, batt_y + 3.5, 1.8, batt_h - 7),
            0.8, 0.8,
        )

        # 와이파이 (3단 부채꼴)
        wifi_cx = batt_x - 16
        wifi_cy = icon_cy + 4
        for i, radius in enumerate((10, 7, 4)):
            path = QPainterPath()
            path.moveTo(wifi_cx, wifi_cy)
            path.arcTo(
                QRectF(
                    wifi_cx - radius, wifi_cy - radius,
                    radius * 2, radius * 2,
                ),
                45, 90,
            )
            path.closeSubpath()
            alpha = 180 if i == 0 else (220 if i == 1 else 255)
            painter.setBrush(QBrush(QColor(255, 255, 255, alpha)))
            painter.drawPath(path)
        painter.setBrush(QBrush(QColor('white')))
        painter.drawEllipse(QPointF(wifi_cx, wifi_cy), 1.5, 1.5)

        # 신호 세기
        sig_right = wifi_cx - 12
        painter.setBrush(QBrush(QColor('white')))
        for i in range(4):
            h = 3 + i * 2.5
            x = sig_right - (3 - i) * 4
            painter.drawRoundedRect(
                QRectF(x, icon_cy + 4 - h, 3, h), 0.8, 0.8
            )

    def _draw_home_indicator(self, painter, phone_x, screen_rect):
        hi_w, hi_h = 140, 5
        hi_x = phone_x + (PHONE_WIDTH - hi_w) / 2
        hi_y = screen_rect.bottom() - 10
        painter.setBrush(QBrush(QColor('white')))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(hi_x, hi_y, hi_w, hi_h), 3, 3)

    def _draw_side_buttons(self, painter, phone_x, phone_y):
        painter.setPen(Qt.NoPen)

        # 왼쪽: 액션 버튼
        self._draw_side_key(painter, phone_x - 2, phone_y + 130, 4, 28, reverse=False)
        # 왼쪽: 볼륨 업/다운
        vol_up_y = phone_y + 130 + 28 + 22
        self._draw_side_key(painter, phone_x - 2, vol_up_y, 4, 55, reverse=False)
        vol_dn_y = vol_up_y + 55 + 14
        self._draw_side_key(painter, phone_x - 2, vol_dn_y, 4, 55, reverse=False)
        # 오른쪽: 전원 버튼
        pw_x = phone_x + PHONE_WIDTH - 2
        pw_y = phone_y + 160
        self._draw_side_key(painter, pw_x, pw_y, 4, 85, reverse=True)
        # 오른쪽: 카메라 컨트롤 버튼 (아이폰 17 Pro 신기능)
        cc_y = pw_y + 85 + 50
        cc_x, cc_w, cc_h = pw_x, 4, 36
        self._draw_side_key(painter, cc_x, cc_y, cc_w, cc_h, reverse=True, radius=2)
        # 카메라 컨트롤 버튼의 센서 라인
        painter.setBrush(QBrush(QColor(0, 0, 0, 90)))
        painter.drawRect(
            QRectF(cc_x + 0.8, cc_y + cc_h / 2 - 0.5, cc_w - 1.6, 1)
        )

    @staticmethod
    def _make_side_brush(x, y, w, reverse):
        grad = QLinearGradient(x, y, x + w, y)
        if reverse:
            grad.setColorAt(0.0, QColor('#4a4c50'))
            grad.setColorAt(0.55, QColor('#8d8f92'))
            grad.setColorAt(1.0, QColor('#2f3135'))
        else:
            grad.setColorAt(0.0, QColor('#2f3135'))
            grad.setColorAt(0.45, QColor('#8d8f92'))
            grad.setColorAt(1.0, QColor('#4a4c50'))
        return QBrush(grad)

    def _draw_side_key(self, painter, x, y, w, h, reverse, radius=1.5):
        painter.setBrush(self._make_side_brush(x, y, w, reverse))
        painter.drawRoundedRect(QRectF(x, y, w, h), radius, radius)

    # ── 창 드래그 이동 ──
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # ── 키보드 입력 ──
    def keyPressEvent(self, event):
        key = event.key()
        text = event.text()
        screen = self.screen

        if key == Qt.Key_Escape:
            self.close()
            return

        if text and text.isdigit() and len(text) == 1:
            screen._button_clicked(text)
            return

        if text in KEY_TEXT_MAP:
            screen._button_clicked(KEY_TEXT_MAP[text])
            return

        if key in (Qt.Key_Return, Qt.Key_Enter):
            screen._button_clicked('=')
        elif key == Qt.Key_Backspace:
            screen._backspace()
            screen._highlight_operator(None)
        elif key == Qt.Key_Delete:
            screen._clear()
            screen._highlight_operator(None)


class CalculatorScreen(QWidget):
    '''아이폰 화면 안쪽(계산기 본체).'''

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._display_text = '0'
        self._first_operand = None
        self._operator = None
        self._waiting_for_second = False
        self._just_calculated = False
        self._ac_button = None
        self._op_buttons = {}

        self._init_ui()

    # ── 화면 구성 (위젯 배치) ──
    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(
            20, STATUS_BAR_HEIGHT, 20, HOME_INDICATOR_HEIGHT
        )
        main_layout.addStretch(1)

        # 위쪽 수식 표시줄
        self.history_label = QLabel('')
        self.history_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.history_label.setWordWrap(True)
        self.history_label.setMinimumHeight(36)
        self.history_label.setMaximumHeight(82)
        self._apply_history_style(22)
        main_layout.addWidget(self.history_label)

        # 큰 숫자 디스플레이
        self.display = QLabel('0')
        self.display.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.display.setMinimumHeight(100)
        self._apply_display_style(80)
        main_layout.addWidget(self.display)

        main_layout.addLayout(self._build_button_grid())
        self.setLayout(main_layout)

        self._init_toast()

    def _build_button_grid(self):
        grid = QGridLayout()
        grid.setSpacing(11)
        grid.setContentsMargins(0, 0, 0, 0)

        for text, row, col, row_span, col_span, btn_type, extra in BUTTON_LAYOUT:
            button = self._make_button(text, btn_type, extra)
            if text in OPERATORS:
                self._op_buttons[text] = button
            elif text == 'AC':
                self._ac_button = button
            grid.addWidget(button, row, col, row_span, col_span)

        return grid

    def _make_button(self, text, btn_type, extra):
        button = QPushButton(text)
        button.setCursor(Qt.PointingHandCursor)
        button.setFocusPolicy(Qt.NoFocus)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        button.setMinimumSize(74, 74)
        button.setStyleSheet(self._button_style(btn_type, extra=extra))
        button.clicked.connect(self._make_callback(text))
        return button

    def _init_toast(self):
        self.toast_label = QLabel('', self)
        self.toast_label.setAlignment(Qt.AlignCenter)
        self.toast_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.toast_label.setStyleSheet(
            'background-color: rgba(60, 60, 60, 230);'
            'color: white;'
            'font-size: 14px;'
            f'font-family: {FONT_FAMILY};'
            'padding: 12px 22px;'
            'border-radius: 14px;'
        )
        self.toast_label.hide()

    # ── 버튼 스타일 만들기 (CSS 문자열 반환) ──
    @staticmethod
    def _button_style(btn_type, extra='', active=False):
        style = BUTTON_STYLES[btn_type]
        if active and btn_type == 'op':
            bg, fg, pressed = OP_ACTIVE_BG, OP_ACTIVE_FG, OP_ACTIVE_PRESSED
        else:
            bg, fg, pressed = style['bg'], style['fg'], style['pressed']
        return (
            'QPushButton {'
            f'  background-color: {bg};'
            f'  color: {fg};'
            f'  font-size: {style["font_size"]};'
            f'  font-family: {FONT_FAMILY};'
            '  font-weight: 400;'
            '  border: none;'
            f'  border-radius: {BUTTON_RADIUS};'
            f'  {extra}'
            '}'
            'QPushButton:pressed {'
            f'  background-color: {pressed};'
            '}'
        )

    def _apply_display_style(self, size_px):
        self.display.setStyleSheet(
            'color: white;'
            f'font-size: {size_px}px;'
            f'font-family: {FONT_FAMILY};'
            'font-weight: 200;'
            'padding: 0 12px 6px 12px;'
            'background-color: transparent;'
        )

    def _apply_history_style(self, size_px):
        self.history_label.setStyleSheet(
            'color: #8e8e93;'
            f'font-size: {size_px}px;'
            f'font-family: {FONT_FAMILY};'
            'font-weight: 300;'
            'padding: 0 12px;'
            'background-color: transparent;'
        )

    # ── 글자 크기 자동 맞추기 (텍스트가 넘치면 줄임) ──
    @staticmethod
    def _fit_font_size(text, avail, start, minimum, step=2):
        size = start
        while size > minimum:
            font = QFont('Helvetica Neue', size)
            font.setWeight(QFont.Light)
            if QFontMetrics(font).horizontalAdvance(text) <= avail:
                break
            size -= step
        return size

    def _available_width(self):
        avail = self.width() - DISPLAY_H_MARGINS
        return avail if avail > 0 else DISPLAY_AVAIL_WIDTH_FALLBACK

    def _update_display(self):
        text = self._display_text
        size = self._fit_font_size(text, self._available_width(), 80, 24)
        self._apply_display_style(size)
        self.display.setText(text)

    def _set_history_text(self, text):
        '''수식 표시줄 — 한 줄에 안 맞으면 글자 크기를 줄이고,
        그래도 안 맞으면 두 줄로 감싼다.'''
        if not text:
            self._apply_history_style(22)
            self.history_label.setText('')
            return
        size = self._fit_font_size(text, self._available_width(), 22, 14)
        self._apply_history_style(size)
        self.history_label.setText(text)

    # ── 선택된 연산자 버튼 강조 ──
    def _highlight_operator(self, op):
        for key, btn in self._op_buttons.items():
            btn.setStyleSheet(self._button_style('op', active=(key == op)))

    def _make_callback(self, text):
        return lambda: self._button_clicked(text)

    # ── 버튼/키 입력 분기 (어떤 동작을 할지 결정) ──
    def _button_clicked(self, text):
        # '오류' 상태에서는 AC만 받는다
        if self._display_text == '오류' and text != 'AC':
            return
        if text.isdigit():
            self._input_digit(text)
            self._highlight_operator(None)
        elif text == '.':
            self._input_dot()
            self._highlight_operator(None)
        elif text in OPERATORS:
            self._input_operator(text)
            self._highlight_operator(text)
        elif text == '=':
            self._calculate()
            self._highlight_operator(None)
        elif text == 'AC':
            if self._ac_button.text() == '⌫':
                self._backspace()
            else:
                self._clear()
            self._highlight_operator(None)
        elif text == '+/-':
            self._toggle_sign()
        elif text == '%':
            self._percent()

    # ── 화면 전체 새로고침 (디스플레이·수식줄·AC 버튼을 한꺼번에) ──
    def _sync_ui(self):
        self._update_display()
        self._update_history()
        self._refresh_clear_button()

    # ── 숫자/소수점 입력 ──
    def _input_digit(self, digit):
        if self._waiting_for_second or self._just_calculated:
            self._display_text = digit
            self._waiting_for_second = False
            self._just_calculated = False
        else:
            raw = self._raw_number(self._display_text)
            if sum(1 for c in raw if c.isdigit()) >= MAX_INPUT_DIGITS:
                self._show_max_digit_notice()
                return
            raw = digit if raw == '0' else raw + digit
            self._display_text = self._format_number(raw)
        self._sync_ui()

    def _input_dot(self):
        if self._waiting_for_second or self._just_calculated:
            self._display_text = '0.'
            self._waiting_for_second = False
            self._just_calculated = False
        else:
            raw = self._raw_number(self._display_text)
            if '.' not in raw:
                self._display_text = self._format_number(raw + '.')
        self._sync_ui()

    # ── 연산자 입력 ──
    def _input_operator(self, op):
        current = self._display_as_float()

        # 이미 수식이 있고 두 번째 피연산자가 입력되었다면 먼저 계산
        if (self._first_operand is not None
                and not self._waiting_for_second
                and self._operator is not None):
            self._calculate()
            current = self._display_as_float()

        self._first_operand = current
        self._operator = op
        self._waiting_for_second = True
        self._just_calculated = False
        self._update_history()
        self._refresh_clear_button()

    # ── '=' 눌렀을 때 최종 계산 ──
    def _calculate(self):
        if self._operator is None or self._first_operand is None:
            return

        second = self._display_as_float()
        result = self._compute(self._first_operand, self._operator, second)

        if result is None:
            self._display_text = '오류'
        else:
            self._display_text = self._format_from_float(result)

        self._first_operand = None
        self._operator = None
        self._waiting_for_second = False
        self._just_calculated = True
        self._set_history_text('')  # = 누르면 수식 지우고 결과만 표시
        self._update_display()
        self._refresh_clear_button()

    # ── 기능 버튼 ──
    def _clear(self):
        self._display_text = '0'
        self._first_operand = None
        self._operator = None
        self._waiting_for_second = False
        self._just_calculated = False
        self._set_history_text('')
        self._update_display()
        self._refresh_clear_button()

    def _toggle_sign(self):
        if self._display_text in ('0', '오류'):
            return
        raw = self._raw_number(self._display_text)
        raw = raw[1:] if raw.startswith('-') else '-' + raw
        self._display_text = self._format_number(raw)
        self._sync_ui()

    def _percent(self):
        if self._display_text == '오류':
            return
        self._display_text = self._format_from_float(
            self._display_as_float() / 100
        )
        self._sync_ui()

    # ── 백스페이스(마지막 자리 삭제) ──
    def _backspace(self):
        if self._display_text == '오류':
            return
        if self._just_calculated or self._waiting_for_second:
            return
        raw = self._raw_number(self._display_text)
        if raw in ('0', ''):
            return
        if raw.startswith('-') and len(raw) <= 2:
            new_raw = '0'
        elif len(raw) <= 1:
            new_raw = '0'
        else:
            new_raw = raw[:-1]
            if new_raw == '-':
                new_raw = '0'
        self._display_text = self._format_number(new_raw)
        self._sync_ui()

    # ── AC ↔ ⌫ 전환 (입력된 숫자가 있으면 백스페이스로) ──
    def _refresh_clear_button(self):
        can_backspace = (
            self._display_text != '오류'
            and not self._just_calculated
            and not self._waiting_for_second
            and self._raw_number(self._display_text) != '0'
        )
        self._ac_button.setText('⌫' if can_backspace else 'AC')

    # ── 자릿수 초과 안내 팝업 (1.5초 후 자동 사라짐) ──
    def _show_max_digit_notice(self):
        self.toast_label.setText(
            f'최대 {MAX_INPUT_DIGITS}자리까지 입력할 수 있습니다'
        )
        self.toast_label.adjustSize()
        x = (self.width() - self.toast_label.width()) // 2
        y = int(self.height() * TOAST_Y_RATIO)
        self.toast_label.move(x, y)
        self.toast_label.show()
        self.toast_label.raise_()
        QTimer.singleShot(TOAST_DURATION_MS, self.toast_label.hide)

    # ── 실제 산술 연산 (두 숫자 + 연산자 → 결과) ──
    @staticmethod
    def _compute(a, op, b):
        try:
            if op == '+':
                r = a + b
            elif op == '-':
                r = a - b
            elif op == '×':
                r = a * b
            elif op == '÷':
                if b == 0:
                    return None
                r = a / b
            else:
                return None
        except (OverflowError, ValueError, ZeroDivisionError):
            return None
        # 무한대(inf)나 값없음(nan) 결과는 '오류'로 처리
        if r != r or abs(r) == float('inf'):
            return None
        return r

    # ── 수식 표시줄 갱신 (실시간 미리보기 포함) ──
    def _update_history(self):
        if self._first_operand is None or self._operator is None:
            self._set_history_text('')
            return

        first_str = self._format_from_float(self._first_operand)
        op = self._operator

        if self._waiting_for_second:
            self._set_history_text(f'{first_str} {op}')
            return

        # 두 번째 피연산자 입력 중 — 실시간 결과 미리보기
        try:
            second = self._display_as_float()
        except ValueError:
            self._set_history_text(f'{first_str} {op} {self._display_text}')
            return

        result = self._compute(self._first_operand, op, second)
        if result is None:
            self._set_history_text(f'{first_str} {op} {self._display_text}')
        else:
            self._set_history_text(
                f'{first_str} {op} {self._display_text} '
                f'= {self._format_from_float(result)}'
            )

    # ── 숫자 문자열 변환 (콤마 포맷 · float 변환 등) ──
    def _display_as_float(self):
        return float(self._raw_number(self._display_text))

    @staticmethod
    def _raw_number(text):
        if text == '오류':
            return '0'
        return text.replace(',', '')

    def _format_number(self, raw):
        if raw in ('', '-'):
            return '0'
        negative = raw.startswith('-')
        if negative:
            raw = raw[1:]
        if '.' in raw:
            int_part, dec_part = raw.split('.', 1)
            result = self._comma_int(int_part) + '.' + dec_part
        else:
            result = self._comma_int(raw)
        return '-' + result if negative else result

    @staticmethod
    def _comma_int(s):
        if s == '':
            return '0'
        rev = s[::-1]
        chunks = [rev[i:i + 3] for i in range(0, len(rev), 3)]
        return ','.join(chunks)[::-1]

    def _format_from_float(self, f):
        # 너무 크거나 너무 작은 값은 과학적 표기법 (예: 9.0000E+15)
        if f != 0 and (abs(f) >= 1e16 or abs(f) < 1e-6):
            return f'{f:.4E}'
        if f == int(f):
            return self._format_number(str(int(f)))
        # 소수부 10자리까지만 남기고, 뒤쪽 불필요한 0은 제거
        raw = f'{f:.10f}'.rstrip('0').rstrip('.')
        if raw in ('', '-'):
            raw = '0'
        return self._format_number(raw)


if __name__ == '__main__':
    app = QApplication([])
    phone = IPhoneFrame()
    phone.show()
    app.exec_()
