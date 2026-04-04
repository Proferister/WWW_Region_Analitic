"""Генерация PDF-отчёта по теме."""
import io
import os
from fpdf import FPDF


FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")


class ReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        # Используем встроенный шрифт с поддержкой Unicode
        font_path = os.path.join(FONT_DIR, "DejaVuSans.ttf")
        bold_path = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
        if os.path.exists(font_path):
            self.add_font("DejaVu", "", font_path, uni=True)
            if os.path.exists(bold_path):
                self.add_font("DejaVu", "B", bold_path, uni=True)
            self.set_font("DejaVu", size=10)
        else:
            self.add_font("DejaVu", "", os.path.join(FONT_DIR, "DejaVuSans.ttf"), uni=True)
            self.set_font("Helvetica", size=10)

    def header(self):
        self.set_font("DejaVu", "B", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 8, "WHITEA | Аналитический отчёт", align="L", new_x="LMARGIN", new_y="NEXT")
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "", 7)
        self.set_text_color(160, 160, 160)
        self.cell(0, 10, f"Стр. {self.page_no()}/{{nb}}", align="C")


def generate_topic_pdf(data: dict) -> bytes:
    """Генерирует PDF-отчёт по одной теме. Возвращает bytes."""
    pdf = ReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # Заголовок
    pdf.set_font("DejaVu", "B", 16)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 8, data.get("title", "Без названия"))
    pdf.ln(4)

    # Мета: ранг, отрасль, локация
    pdf.set_font("DejaVu", "", 10)
    pdf.set_text_color(80, 80, 80)
    rank = data.get("rank", "")
    industry = data.get("industry", "")
    location = data.get("location", "")
    period = data.get("period", "")
    meta = f"#{rank} в топ-10  |  {industry}  |  {location}"
    if period:
        meta += f"  |  {period}"
    pdf.cell(0, 6, meta, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Сводка
    _section(pdf, "Сводка")
    pdf.set_font("DejaVu", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 6, data.get("summary", "Нет данных"))
    pdf.ln(6)

    # Статистика
    stats = data.get("stats", {})
    _section(pdf, "Почему в топе?")
    pdf.set_font("DejaVu", "", 10)
    pdf.cell(0, 6, f"Упоминания: {stats.get('mentionsGrowth', '-')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Затронуто населённых пунктов: {stats.get('locations', '-')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Негативных сообщений: {stats.get('negativePct', '-')}%", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Ключевые слова
    keywords = data.get("keywords", [])
    if keywords:
        _section(pdf, "Ключевые слова")
        pdf.set_font("DejaVu", "", 10)
        pdf.cell(0, 6, ", ".join(keywords), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)

    # Достоверность
    reliability = data.get("reliability", {})
    _section(pdf, "Проверка достоверности")
    pdf.set_font("DejaVu", "", 10)
    status_text = {
        "confirmed": "Подтверждено из независимых источников",
        "suspicious": "Обнаружены признаки накрутки",
        "unclear": "Противоречивые данные",
    }
    pdf.cell(0, 6, status_text.get(reliability.get("status", ""), "Не определено"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Подтверждённых источников: {reliability.get('confirmedSources', 0)}", new_x="LMARGIN", new_y="NEXT")
    if reliability.get("filteredBots", 0) > 0:
        pdf.cell(0, 6, f"Отфильтровано ботовых публикаций: {reliability['filteredBots']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Источники
    sources = data.get("sources", [])
    if sources:
        _section(pdf, f"Источники ({len(sources)})")
        pdf.set_font("DejaVu", "", 9)
        for i, src in enumerate(sources):
            platform = src.get("platform", "")
            channel = src.get("channel", "")
            date = src.get("date", "")
            message = src.get("message", "")[:200]

            pdf.set_font("DejaVu", "B", 9)
            pdf.cell(0, 5, f"[{platform}] {channel}  —  {date}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("DejaVu", "", 9)
            pdf.multi_cell(0, 5, message)
            pdf.ln(2)

    # Вывод
    buffer = io.BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()


def _section(pdf: ReportPDF, title: str):
    """Заголовок секции."""
    pdf.set_font("DejaVu", "B", 12)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
