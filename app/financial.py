import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime

class FinancialManager:
    EXPENSE_CATEGORIES = [
        "Donaciones", "Verbena", "Charlas y talleres",
        "Cesiones al Colegio", "Otros"
    ]
    INCOME_CATEGORIES = [
        "Cuota de socios", "Subvención", "Donación",
        "Venta de Lotería", "Otros"
    ]

    def __init__(self, drive_manager):
        self.drive_manager = drive_manager
        self.load_data()

    def load_data(self):
        self.transactions = self.drive_manager.load_data('transactions.csv')
        if self.transactions.empty:
            self.transactions = pd.DataFrame({
                'date': [], 'type': [], 'category': [],
                'amount': [], 'description': []
            })
        self.initial_balance = float(self.drive_manager.load_data('balance.csv').get('balance', 0))

    def save_data(self):
        self.drive_manager.save_data(self.transactions, 'transactions.csv')
        self.drive_manager.save_data({'balance': [self.initial_balance]}, 'balance.csv')

    def add_transaction(self, transaction_type, category, amount, description):
        new_transaction = pd.DataFrame({
            'date': [datetime.now().strftime('%Y-%m-%d')],
            'type': [transaction_type],
            'category': [category],
            'amount': [amount],
            'description': [description]
        })
        self.transactions = pd.concat([self.transactions, new_transaction], ignore_index=True)
        self.save_data()a()

    def get_balance(self):
        total_income = self.transactions[self.transactions['type'] == 'income']['amount'].sum()
        total_expenses = self.transactions[self.transactions['type'] == 'expense']['amount'].sum()
        return self.initial_balance + total_income - total_expenses

    def create_summary_chart(self):
        fig = go.Figure()
        
        # Income by category
        income_by_category = self.transactions[
            self.transactions['type'] == 'income'
        ].groupby('category')['amount'].sum()
        
        # Expenses by category
        expenses_by_category = self.transactions[
            self.transactions['type'] == 'expense'
        ].groupby('category')['amount'].sum()

        fig.add_trace(go.Bar(
            x=income_by_category.index,
            y=income_by_category.values,
            name='Ingresos',
            marker_color='green'
        ))

        fig.add_trace(go.Bar(
            x=expenses_by_category.index,
            y=expenses_by_category.values,
            name='Gastos',
            marker_color='red'
        ))

        fig.update_layout(
            title='Resumen de Ingresos y Gastos por Categoría',
            xaxis_title='Categoría',
            yaxis_title='Cantidad (€)',
            barmode='group'
        )

        return fig
