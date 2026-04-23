'''아이폰 17 Pro 스타일 계산기 (PyQt5 단독)

역할별로 네 클래스로 분리되어 있다.
  CalculatorDesign  : 아이폰 외형 그리기 (프레임·노치·상태바 등)
  CalculatorLogic   : 계산기 상태와 산술 연산 (UI와 무관)
  CalculatorScreen  : 버튼과 디스플레이 같은 UI 위젯
  IPhoneFrame       : 바깥 창 + 이벤트(드래그·키보드·닫기)
'''

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
        'font_size': '32px', 'pressed': '#737373',
    },
    'op': {
        'bg': '#FF9F0A', 'fg': 'white',
        'font_size': '34px', 'pressed': '#FFC966',
    },
    'func': {
        'bg': '#A5A5A5', 'fg': 'black',
        'font_size': '26px', 'pressed': '#D4D4D2',
    },
}
BUTTON_RADIUS = '32px'
BUTTON_MIN_WIDTH = 74
BUTTON_MIN_HEIGHT = 60
OP_ACTIVE_BG = 'white'
OP_ACTIVE_FG = '#FF9F0A'
OP_ACTIVE_PRESSED = '#FFE5B4'

# ── 계산기 버튼 배치 ──
# 각 항목: (버튼 글자, 행, 열, 행 병합 수, 열 병합 수, 버튼 종류, 추가 CSS)
# 백스페이스(⌫)는 맨 위 오른쪽에 독립된 버튼으로 배치한다.
BUTTON_LAYOUT = [
    ('⌫',   0, 3, 1, 1, 'func', ''),
    ('AC',  1, 0, 1, 1, 'func', ''),
    ('+/-', 1, 1, 1, 1, 'func', ''),
    ('%',   1, 2, 1, 1, 'func', ''),
    ('÷',   1, 3, 1, 1, 'op',   ''),
    ('7',   2, 0, 1, 1, 'num',  ''),
    ('8',   2, 1, 1, 1, 'num',  ''),
    ('9',   2, 2, 1, 1, 'num',  ''),
    ('×',   2, 3, 1, 1, 'op',   ''),
    ('4',   3, 0, 1, 1, 'num',  ''),
    ('5',   3, 1, 1, 1, 'num',  ''),
    ('6',   3, 2, 1, 1, 'num',  ''),
    ('-',   3, 3, 1, 1, 'op',   ''),
    ('1',   4, 0, 1, 1, 'num',  ''),
    ('2',   4, 1, 1, 1, 'num',  ''),
    ('3',   4, 2, 1, 1, 'num',  ''),
    ('+',   4, 3, 1, 1, 'op',   ''),
    ('0',   5, 0, 1, 2, 'num',  'text-align: left; padding-left: 30px;'),
    ('.',   5, 2, 1, 1, 'num',  ''),
    ('=',   5, 3, 1, 1, 'op',   ''),
]
OPERATORS = ('+', '-', '×', '÷')

# ── 키보드 입력 매핑 (누른 키 → 계산기 버튼) ──
KEY_TEXT_MAP = {
    '+': '+', '-': '-', '*': '×', '/': '÷',
    '.': '.', '%': '%', '=': '=',
}


class CalculatorDesign:
    '''아이폰 17 Pro 외형을 QPainter로 그리는 렌더러.

    상태는 없고, draw(painter) 진입점에서 레이어를 순서대로 그린다.
      1) 외부 그림자
      2) 알루미늄 프레임 / 유리 / OLED 영역
      3) Dynamic Island (Face ID, 전면 카메라)
      4) 상태바 (시계 · 신호 · 와이파이 · 배터리)
      5) 홈 인디케이터
      6) 측면 물리 버튼 (액션·볼륨·전원·카메라 컨트롤)
    '''

    def draw(self, painter):
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

    # ── 외부 그림자 (부드러운 다층) ──
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

    # ── 알루미늄 프레임 + 유리 + OLED ──
    def _draw_body_and_screen(self, painter, phone_x, phone_y):
        body_rect = QRectF(phone_x, phone_y, PHONE_WIDTH, PHONE_HEIGHT)
        body_path = QPainterPath()
        body_path.addRoundedRect(body_rect, PHONE_RADIUS, PHONE_RADIUS)

        frame_grad = QLinearGradient(
            body_rect.topLeft(), body_rect.bottomRight()
        )
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
        inset_path.addRoundedRect(
            inset_rect, PHONE_RADIUS - 2, PHONE_RADIUS - 2
        )
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

    # ── Dynamic Island (Face ID + 전면 카메라) ──
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

        # 전면 카메라 (렌즈 반사광 포함)
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

    # ── 상태바 (시계 · 신호 · 와이파이 · 배터리) ──
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
        painter.drawRoundedRect(
            QRectF(batt_x, batt_y, batt_w, batt_h), 3, 3
        )
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

    # ── 홈 인디케이터 ──
    def _draw_home_indicator(self, painter, phone_x, screen_rect):
        hi_w, hi_h = 140, 5
        hi_x = phone_x + (PHONE_WIDTH - hi_w) / 2
        hi_y = screen_rect.bottom() - 10
        painter.setBrush(QBrush(QColor('white')))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(hi_x, hi_y, hi_w, hi_h), 3, 3)

    # ── 측면 물리 버튼 ──
    def _draw_side_buttons(self, painter, phone_x, phone_y):
        painter.setPen(Qt.NoPen)

        # 왼쪽: 액션 버튼 / 볼륨 업·다운
        self._draw_side_key(
            painter, phone_x - 2, phone_y + 130, 4, 28, reverse=False
        )
        vol_up_y = phone_y + 130 + 28 + 22
        self._draw_side_key(
            painter, phone_x - 2, vol_up_y, 4, 55, reverse=False
        )
        vol_dn_y = vol_up_y + 55 + 14
        self._draw_side_key(
            painter, phone_x - 2, vol_dn_y, 4, 55, reverse=False
        )

        # 오른쪽: 전원 버튼 / 카메라 컨트롤 (아이폰 17 Pro 신기능)
        pw_x = phone_x + PHONE_WIDTH - 2
        pw_y = phone_y + 160
        self._draw_side_key(painter, pw_x, pw_y, 4, 85, reverse=True)

        cc_y = pw_y + 85 + 50
        cc_x, cc_w, cc_h = pw_x, 4, 36
        self._draw_side_key(
            painter, cc_x, cc_y, cc_w, cc_h, reverse=True, radius=2
        )
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


class CalculatorLogic:
    '''계산기의 "머리" — 상태와 산술 연산만 담당하고 UI는 모른다.

    UI(CalculatorScreen)는 아래 메서드를 호출해 상태를 바꾸고,
    display / history_text / can_backspace / is_error 네 가지 조회로
    화면을 새로 그린다. Qt에 의존하지 않으므로 단위 테스트도 쉽다.
    '''

    def __init__(self):
        # 화면에 표시 중인 문자열 (예: '123', '0.5', '-1,000', '오류')
        self._display = '0'
        # 첫 번째 피연산자 (float). 아직 연산자를 안 눌렀으면 None
        self._first = None
        # 현재 연산자 ('+', '-', '×', '÷'). 없으면 None
        self._op = None
        # 연산자 방금 눌러서 두 번째 피연산자 입력을 기다리는 중?
        self._waiting = False
        # 방금 '=' 을 눌러 결과가 표시된 직후인가?
        self._done = False
        # 연산자 체인이 일어났을 때 누적한 원본 수식 (예: "9 + 5 + 3")
        self._prefix = ''

    # ── 외부에서 조회하는 값들 ──

    @property
    def display(self):
        '''메인 디스플레이에 보일 문자열.'''
        return self._display

    @property
    def is_error(self):
        return self._display == '오류'

    def can_backspace(self):
        '''마지막 자리 삭제가 의미 있는 상태인지.'''
        return (
            not self.is_error
            and not self._done
            and not self._waiting
            and self._strip(self._display) != '0'
        )

    def history_text(self):
        '''수식 표시줄 텍스트. = 누르기 전까지 실시간 미리보기 포함.'''
        if self._first is None or self._op is None:
            return ''
        op = self._op
        # prefix가 있으면 첫 피연산자는 이미 그 안에 포함됨
        base = self._prefix if self._prefix else self._fmt(self._first)

        if self._waiting:
            return f'{base} {op}'

        # 두 번째 피연산자 입력 중 — 결과를 미리 계산해 붙여 보여준다
        try:
            second = float(self._strip(self._display))
        except ValueError:
            return f'{base} {op} {self._display}'

        preview = self._apply(self._first, op, second)
        if preview is None:
            return f'{base} {op} {self._display}'
        return f'{base} {op} {self._display} = {self._fmt(preview)}'

    # ── 사용자 입력 처리 ──

    def input_digit(self, digit):
        '''숫자 한 자리 입력. 자릿수 초과로 무시되면 False.'''
        if self.is_error:
            return True
        if self._waiting or self._done:
            # 연산자 직후나 결과 직후에 숫자를 누르면 새 피연산자 시작
            self._display = digit
            self._waiting = False
            self._done = False
            return True
        raw = self._strip(self._display)
        if sum(1 for c in raw if c.isdigit()) >= MAX_INPUT_DIGITS:
            return False
        raw = digit if raw == '0' else raw + digit
        self._display = self._format_number(raw)
        return True

    def input_dot(self):
        if self.is_error:
            return
        if self._waiting or self._done:
            self._display = '0.'
            self._waiting = False
            self._done = False
            return
        raw = self._strip(self._display)
        if '.' not in raw:
            self._display = self._format_number(raw + '.')

    def input_operator(self, op):
        if self.is_error:
            return
        current = float(self._strip(self._display))

        # 연산자를 이어서 누르는 경우 (예: 9 + 5 ×)
        # → 이전 식을 먼저 계산하고, 원본 수식은 prefix에 누적해 둔다
        if (self._first is not None
                and not self._waiting
                and self._op is not None):
            first_str = self._fmt(self._first)
            if self._prefix == '':
                self._prefix = f'{first_str} {self._op} {self._display}'
            else:
                self._prefix += f' {self._op} {self._display}'
            self._resolve(final=False)
            current = float(self._strip(self._display))

        self._first = current
        self._op = op
        self._waiting = True
        self._done = False

    def equal(self):
        '''= 버튼 동작. 체인 누적 기록도 함께 비운다.'''
        self._resolve(final=True)

    def clear(self):
        '''AC — 모든 상태 초기화.'''
        self._display = '0'
        self._first = None
        self._op = None
        self._waiting = False
        self._done = False
        self._prefix = ''

    def toggle_sign(self):
        if self._display in ('0', '오류'):
            return
        raw = self._strip(self._display)
        raw = raw[1:] if raw.startswith('-') else '-' + raw
        self._display = self._format_number(raw)

    def percent(self):
        if self.is_error:
            return
        self._display = self._fmt(float(self._strip(self._display)) / 100)

    def backspace(self):
        '''마지막 한 자리 삭제 (= 누른 직후나 연산자 대기 중엔 무시).'''
        if not self.can_backspace():
            return
        raw = self._strip(self._display)
        if raw.startswith('-') and len(raw) <= 2:
            new_raw = '0'
        elif len(raw) <= 1:
            new_raw = '0'
        else:
            new_raw = raw[:-1]
            if new_raw == '-':
                new_raw = '0'
        self._display = self._format_number(new_raw)

    # ── 내부 계산 엔진 ──

    def _resolve(self, final):
        '''현재 대기 중인 연산을 실제로 수행.
        final=True면 = 버튼이 눌린 경우이므로 prefix까지 초기화.'''
        if self._op is None or self._first is None:
            return
        second = float(self._strip(self._display))
        result = self._apply(self._first, self._op, second)
        if result is None:
            self._display = '오류'
        else:
            self._display = self._fmt(result)
        self._first = None
        self._op = None
        self._waiting = False
        self._done = True
        if final:
            self._prefix = ''

    @staticmethod
    def _apply(a, op, b):
        '''두 숫자와 연산자로 결과를 얻는다. 오류 시 None.'''
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

    # ── 숫자 문자열 변환 ──

    @staticmethod
    def _strip(text):
        '''표시 문자열에서 콤마를 제거하고 '오류'는 '0'으로 돌려준다.'''
        if text == '오류':
            return '0'
        return text.replace(',', '')

    def _format_number(self, raw):
        '''원시 숫자 문자열에 천 단위 콤마를 넣어 표시 문자열을 만든다.'''
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
    def _comma_int(digits):
        '''정수 문자열에 3자리마다 콤마를 삽입.'''
        if digits == '':
            return '0'
        rev = digits[::-1]
        chunks = [rev[i:i + 3] for i in range(0, len(rev), 3)]
        return ','.join(chunks)[::-1]

    def _fmt(self, value):
        '''float 계산 결과를 표시 문자열로 변환한다.
        너무 크거나 너무 작으면 과학적 표기법(예: 9.0000E+15)으로 바꾼다.'''
        if value != 0 and (abs(value) >= 1e16 or abs(value) < 1e-6):
            return f'{value:.4E}'
        if value == int(value):
            return self._format_number(str(int(value)))
        # 소수부 10자리까지만 남기고 뒤의 0은 제거
        raw = f'{value:.10f}'.rstrip('0').rstrip('.')
        if raw in ('', '-'):
            raw = '0'
        return self._format_number(raw)


class CalculatorScreen(QWidget):
    '''아이폰 화면 안쪽의 "얼굴" — 위젯 배치와 이벤트 처리.

    계산 자체는 self._logic(CalculatorLogic)에 위임한다.
    모든 사용자 입력은 _on_button(text) 하나로 모이고,
    상태 변경 후에는 _sync_ui() 하나로 화면을 다시 맞춘다.
    '''

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._logic = CalculatorLogic()
        self._buttons = {}  # 버튼 텍스트 → QPushButton

        self._init_ui()
        self._sync_ui()

    # ── 화면 구성 ──

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
        grid.setSpacing(9)
        grid.setContentsMargins(0, 0, 0, 0)

        for entry in BUTTON_LAYOUT:
            text, row, col, row_span, col_span, btn_type, extra = entry
            button = self._make_button(text, btn_type, extra)
            self._buttons[text] = button
            grid.addWidget(button, row, col, row_span, col_span)

        return grid

    def _make_button(self, text, btn_type, extra):
        button = QPushButton(text)
        button.setCursor(Qt.PointingHandCursor)
        button.setFocusPolicy(Qt.NoFocus)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        button.setMinimumSize(BUTTON_MIN_WIDTH, BUTTON_MIN_HEIGHT)
        button.setStyleSheet(self._button_style(btn_type, extra=extra))
        button.clicked.connect(lambda _, t=text: self._on_button(t))
        return button

    def _init_toast(self):
        self.toast_label = QLabel('', self)
        self.toast_label.setAlignment(Qt.AlignCenter)
        self.toast_label.setAttribute(
            Qt.WA_TransparentForMouseEvents, True
        )
        self.toast_label.setStyleSheet(
            'background-color: rgba(60, 60, 60, 230);'
            'color: white;'
            'font-size: 14px;'
            f'font-family: {FONT_FAMILY};'
            'padding: 12px 22px;'
            'border-radius: 14px;'
        )
        self.toast_label.hide()

    # ── 스타일 ──

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

    # ── 사용자 입력 → Logic 호출 ──

    def _on_button(self, text):
        # '오류' 상태에서는 AC만 받아 상태를 초기화한다
        if self._logic.is_error and text != 'AC':
            return

        if text.isdigit():
            ok = self._logic.input_digit(text)
            if not ok:
                self._show_max_digit_notice()
            self._highlight_operator(None)
        elif text == '.':
            self._logic.input_dot()
            self._highlight_operator(None)
        elif text in OPERATORS:
            self._logic.input_operator(text)
            self._highlight_operator(text)
        elif text == '=':
            self._logic.equal()
            self._highlight_operator(None)
        elif text == 'AC':
            self._logic.clear()
            self._highlight_operator(None)
        elif text == '⌫':
            self._logic.backspace()
        elif text == '+/-':
            self._logic.toggle_sign()
        elif text == '%':
            self._logic.percent()

        self._sync_ui()

    # ── Logic 상태 → UI 반영 ──

    def _sync_ui(self):
        # 디스플레이 — 텍스트 길이에 맞춰 글자 크기 자동 조정
        text = self._logic.display
        size = self._fit_font_size(text, self._available_width(), 80, 24)
        self._apply_display_style(size)
        self.display.setText(text)

        # 수식 표시줄
        self._set_history_text(self._logic.history_text())

        # 백스페이스 버튼은 의미 있는 상태에서만 활성화
        backspace_btn = self._buttons.get('⌫')
        if backspace_btn is not None:
            backspace_btn.setEnabled(self._logic.can_backspace())

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

    def _highlight_operator(self, op):
        '''활성 연산자 버튼만 흰 배경 + 주황 글자로 강조.'''
        for key in OPERATORS:
            button = self._buttons[key]
            button.setStyleSheet(
                self._button_style('op', active=(key == op))
            )

    # ── 보조 UI ──

    @staticmethod
    def _fit_font_size(text, avail, start, minimum, step=2):
        '''QFontMetrics로 실제 폭을 재서 맞는 최대 폰트 크기 반환.'''
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

    def _show_max_digit_notice(self):
        '''15자리 초과 입력 시 안내 팝업을 1.5초간 띄운다.'''
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


class IPhoneFrame(QWidget):
    '''창 껍데기 — 이벤트 처리, 종료 버튼, 계산기 화면 배치.
    외형은 CalculatorDesign, 계산은 CalculatorLogic에 각각 위임한다.'''

    def __init__(self):
        super().__init__()
        self.setFixedSize(WIN_WIDTH, WIN_HEIGHT)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setFocusPolicy(Qt.StrongFocus)

        self._drag_pos = None
        self._design = CalculatorDesign()

        inset = FRAME_THICKNESS + INNER_BEZEL
        self.screen = CalculatorScreen(self)
        self.screen.setGeometry(
            SHADOW_MARGIN + inset,
            SHADOW_MARGIN + inset,
            PHONE_WIDTH - 2 * inset,
            PHONE_HEIGHT - 2 * inset,
        )

        # 상태바 시계를 30초마다 갱신
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self.update)
        self._clock_timer.start(30000)

        self._init_close_button()

    def _init_close_button(self):
        '''본체 바깥 우측 상단에 빨간 X 종료 버튼.'''
        self._close_button = QPushButton('✕', self)
        self._close_button.setFixedSize(22, 22)
        self._close_button.setFocusPolicy(Qt.NoFocus)
        self._close_button.setCursor(Qt.PointingHandCursor)
        self._close_button.setStyleSheet(
            'QPushButton {'
            '  background-color: #ff5f57;'
            '  color: white;'
            '  border: none;'
            '  border-radius: 11px;'
            '  font-size: 12px;'
            '  font-weight: bold;'
            '}'
            'QPushButton:hover {'
            '  background-color: #ff3b30;'
            '}'
        )
        self._close_button.move(WIN_WIDTH - 27, 5)
        self._close_button.clicked.connect(self.close)

    # ── 화면 그리기 (CalculatorDesign에 위임) ──
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self._design.draw(painter)

    # ── 창 드래그 이동 ──
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = (
                event.globalPos() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # ── 키보드 입력 → 계산기 버튼으로 매핑 ──
    def keyPressEvent(self, event):
        key = event.key()
        text = event.text()
        screen = self.screen

        if key == Qt.Key_Escape:
            self.close()
            return

        if text and text.isdigit() and len(text) == 1:
            screen._on_button(text)
            return

        if text in KEY_TEXT_MAP:
            screen._on_button(KEY_TEXT_MAP[text])
            return

        if key in (Qt.Key_Return, Qt.Key_Enter):
            screen._on_button('=')
        elif key == Qt.Key_Backspace:
            screen._on_button('⌫')
        elif key == Qt.Key_Delete:
            screen._on_button('AC')


if __name__ == '__main__':
    app = QApplication([])
    phone = IPhoneFrame()
    # 창 닫으면 메모리까지 완전히 해제 (재실행 시 잔여 상태 방지)
    phone.setAttribute(Qt.WA_DeleteOnClose)
    phone.show()

    # 화면 중앙 배치
    geometry = app.primaryScreen().availableGeometry()
    phone.move(
        (geometry.width() - phone.width()) // 2,
        (geometry.height() - phone.height()) // 2,
    )
    # 프레임 없는 창이 뒤로 숨는 경우 방지
    phone.raise_()
    phone.activateWindow()

    app.exec_()
