from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from datetime import datetime

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        )

    def generate_report(self, transactions, initial_balance, current_balance):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        # Title
        title = Paragraph(
            f"Informe Financiero AMPA Sagrada Familia - {datetime.now().strftime('%d/%m/%Y')}",
            self.title_style
        )
        elements.append(title)
        elements.append(Spacer(1, 20))

        # Balance Summary
        balance_data = [
            ['Saldo Inicial', f"€{initial_balance:.2f}"],
            ['Saldo Actual', f"€{current_balance:.2f}"]
        ]
        balance_table = Table(balance_data)
        balance_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(balance_table)
        elements.append(Spacer(1, 20))

        # Transactions
        if not transactions.empty:
            trans_data = [['Fecha', 'Tipo', 'Categoría', 'Cantidad', 'Descripción']]
            for _, row in transactions.iterrows():
                trans_data.append([
                    row['date'],
                    'Ingreso' if row['type'] == 'income' else 'Gasto',
                    row['category'],
                    f"€{row['amount']:.2f}",
                    row['description']
                ])
            
            trans_table = Table(trans_data)
            trans_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(trans_table)

        doc.build(elements)
        return buffer

