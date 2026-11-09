from io import BytesIO
from xml.sax.saxutils import escape

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, TableStyle


def _pdf_text(value):
    if value is None:
        return ''
    return str(value).encode('latin-1', 'replace').decode('latin-1')


def build_trade_recap_pdf(username, trades):
    trades = list(trades)
    closed_trades = [trade for trade in trades if trade.exit_price is not None]
    wins = sum(1 for trade in closed_trades if trade.pnl is not None and trade.pnl > 0)
    net_pnl = sum((trade.pnl or 0) for trade in trades)
    buy_count = sum(1 for trade in trades if trade.order_type == 'BUY')
    sell_count = sum(1 for trade in trades if trade.order_type == 'SELL')
    win_rate = wins / len(closed_trades) * 100 if closed_trades else 0

    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title='Trade Journal Recap',
        author=_pdf_text(username),
        pageCompression=0,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='RecapTitle',
        parent=styles['Title'],
        alignment=TA_LEFT,
        textColor=colors.HexColor('#172033'),
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        spaceAfter=3 * mm,
    ))
    styles.add(ParagraphStyle(
        name='RecapMeta',
        parent=styles['Normal'],
        textColor=colors.HexColor('#596579'),
        fontSize=9,
        leading=13,
    ))
    styles.add(ParagraphStyle(
        name='MetricLabel',
        parent=styles['Normal'],
        textColor=colors.HexColor('#596579'),
        fontSize=8,
        leading=10,
    ))
    styles.add(ParagraphStyle(
        name='Cell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=9,
        wordWrap='CJK',
    ))
    styles.add(ParagraphStyle(
        name='CellHeader',
        parent=styles['Cell'],
        textColor=colors.white,
        fontName='Helvetica-Bold',
    ))
    styles.add(ParagraphStyle(
        name='CellRight',
        parent=styles['Cell'],
        alignment=TA_RIGHT,
    ))
    styles.add(ParagraphStyle(
        name='CellCenter',
        parent=styles['Cell'],
        alignment=TA_CENTER,
    ))

    def cell(value, style='Cell'):
        return Paragraph(escape(_pdf_text(value)), styles[style])

    story = [
        Paragraph('Trade Journal Recap', styles['RecapTitle']),
        Paragraph(
            'Akun: {} &nbsp;&nbsp;|&nbsp;&nbsp; Dibuat: {} &nbsp;&nbsp;|&nbsp;&nbsp; '
            'Periode: seluruh riwayat'.format(
                escape(_pdf_text(username)),
                timezone.localtime().strftime('%d %b %Y, %H:%M'),
            ),
            styles['RecapMeta'],
        ),
        Spacer(1, 5 * mm),
    ]

    metrics = [
        ('TOTAL TRADE', str(len(trades))),
        ('TRADE SELESAI', str(len(closed_trades))),
        ('WIN RATE', '{:.1f}%'.format(win_rate)),
        ('NET PNL', '${:,.2f}'.format(net_pnl)),
        ('BUY / SELL', '{} / {}'.format(buy_count, sell_count)),
    ]
    metric_cells = []
    for label, value in metrics:
        metric_cells.append(Paragraph(
            '{}<br/><font size="12"><b>{}</b></font>'.format(
                escape(label), escape(_pdf_text(value))
            ),
            styles['MetricLabel'],
        ))
    metric_table = LongTable(
        [metric_cells],
        colWidths=[(landscape(A4)[0] - 24 * mm) / len(metrics)] * len(metrics),
    )
    metric_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f3f5f8')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#dce2ea')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dce2ea')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    story.extend([metric_table, Spacer(1, 7 * mm)])

    headers = [
        'Tanggal',
        'Pair',
        'Arah',
        'Lot',
        'Entry',
        'Exit',
        'PnL',
        'Strategi',
        'Emosi',
        'Catatan',
    ]
    rows = [[cell(header, 'CellHeader') for header in headers]]
    for trade in trades:
        rows.append([
            cell(timezone.localtime(trade.date_time).strftime('%Y-%m-%d %H:%M')),
            cell(trade.pair),
            cell(trade.get_order_type_display(), 'CellCenter'),
            cell(trade.lot_size, 'CellRight'),
            cell(trade.entry_price, 'CellRight'),
            cell(trade.exit_price if trade.exit_price is not None else 'Berjalan', 'CellRight'),
            cell('${:,.2f}'.format(trade.pnl) if trade.pnl is not None else '-', 'CellRight'),
            cell(trade.strategy),
            cell(trade.emotion),
            cell(trade.notes),
        ])

    available_width = landscape(A4)[0] - 24 * mm
    column_widths = [58, 48, 34, 36, 48, 48, 54, 75, 58]
    column_widths.append(available_width - sum(column_widths))
    trade_table = LongTable(
        rows,
        colWidths=column_widths,
        repeatRows=1,
        hAlign='LEFT',
    )
    trade_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#172033')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [
            colors.white,
            colors.HexColor('#f7f8fa'),
        ]),
        ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#dce2ea')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ALIGN', (3, 1), (6, -1), 'RIGHT'),
    ]))
    story.append(Paragraph('Rincian trade', styles['Heading2']))
    story.append(Spacer(1, 2 * mm))
    if trades:
        story.append(trade_table)
    else:
        story.append(Paragraph('Belum ada trade yang tercatat.', styles['RecapMeta']))

    def draw_page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#798397'))
        canvas.drawRightString(
            landscape(A4)[0] - 12 * mm,
            7 * mm,
            'Trade Journal  |  Halaman {}'.format(doc.page),
        )
        canvas.restoreState()

    document.build(story, onFirstPage=draw_page_number, onLaterPages=draw_page_number)
    return output.getvalue()
