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
        balance_df = self.drive_manager.load_data('balance.csv')
        if balance_df.empty:
            self.initial_balance = 0.0
        else:
            self.initial_balance = float(balance_df['balance'].iloc[0])

    def save_data(self):
        self.drive_manager.save_data(self.transactions, 'transactions.csv')
        self.drive_manager.save_data({'balance': [self.initial_balance]}, 'balance.csv')

    def add_transaction(self, transaction_type, category, amount, description, date=None):
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
            
        new_transaction = pd.DataFrame({
            'date': [date],
            'type': [transaction_type],
            'category': [category],
            'amount': [amount],
            'description': [description]
        })
        self.transactions = pd.concat([self.transactions, new_transaction], ignore_index=True)
        self.save_data()
        
    def update_transaction(self, index, transaction_type, category, amount, description, date):
        if index >= 0 and index < len(self.transactions):
            self.transactions.at[index, 'date'] = date
            self.transactions.at[index, 'type'] = transaction_type
            self.transactions.at[index, 'category'] = category
            self.transactions.at[index, 'amount'] = amount
            self.transactions.at[index, 'description'] = description
            self.save_data()
            return True
        return False
        
    def delete_transaction(self, index):
        if index >= 0 and index < len(self.transactions):
            self.transactions = self.transactions.drop(index).reset_index(drop=True)
            self.save_data()
            return True
        return False

    def get_balance(self):
        total_income = self.transactions[self.transactions['type'] == 'income']['amount'].sum()
        total_expenses = self.transactions[self.transactions['type'] == 'expense']['amount'].sum()
        return self.initial_balance + total_income - total_expenses
        
    def set_initial_balance(self, new_balance):
        self.initial_balance = float(new_balance)
        self.save_data()

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
