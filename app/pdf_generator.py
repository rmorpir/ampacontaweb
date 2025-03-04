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

    def generate_report(self, transactions, initial_balance, current_balance, start_date=None, end_date=None):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # Filter transactions by date if date range is provided
        if start_date and end_date:
            filtered_transactions = transactions[
                (transactions['date'] >= start_date) & 
                (transactions['date'] <= end_date)
            ]
        else:
            filtered_transactions = transactions
            
        # Calculate period balance
        if not filtered_transactions.empty:
            period_income = filtered_transactions[filtered_transactions['type'] == 'income']['amount'].sum()
            period_expenses = filtered_transactions[filtered_transactions['type'] == 'expense']['amount'].sum()
            period_balance = period_income - period_expenses
        else:
            period_balance = 0

        # Title with date range if provided
        title_text = f"Informe Financiero AMPA Sagrada Familia - {datetime.now().strftime('%d/%m/%Y')}"
        if start_date and end_date:
            title_text += f"\nPeríodo: {start_date} a {end_date}"
            
        title = Paragraph(title_text, self.title_style)
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

        # Add period summary if date range is provided
        if start_date and end_date:
            period_data = [
                ['Balance del Período', f"€{period_balance:.2f}"]
            ]
            period_table = Table(period_data)
            period_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (0, -1), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(period_table)
            elements.append(Spacer(1, 20))
        
        # Transactions
        if not filtered_transactions.empty:
            trans_data = [['Fecha', 'Tipo', 'Categoría', 'Cantidad', 'Descripción']]
            for _, row in filtered_transactions.iterrows():
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

