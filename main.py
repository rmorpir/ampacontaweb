import streamlit as st
from app.auth import init_auth, login, logout
from app.drive_manager import DriveManager
from app.financial import FinancialManager
from app.pdf_generator import PDFGenerator
from datetime import datetime
import io

# Initialize session state
init_auth()

# Main application
if not st.session_state.authenticated:
    login()
else:
    st.set_page_config(page_title="AMPA Sagrada Familia - Contabilidad", layout="wide")

    # Initialize managers
    drive_manager = DriveManager()
    financial_manager = FinancialManager(drive_manager)
    pdf_generator = PDFGenerator()

    # Sidebar
    st.sidebar.image("attached_assets/LogoAMPA.png", width=200)
    selected_option = st.sidebar.selectbox(
        "Menú",
        ["Inicio", "Registrar Movimiento", "Buscar Movimientos", "Generar Informe"]
    )

    if st.sidebar.button("Cerrar Sesión"):
        logout()

    # Main content
    if selected_option == "Inicio":
        st.title("Dashboard")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Saldo Actual", f"€{financial_manager.get_balance():.2f}")

        with col2:
            st.metric("Número de Transacciones", len(financial_manager.transactions))

        st.plotly_chart(financial_manager.create_summary_chart(), use_container_width=True)

    elif selected_option == "Registrar Movimiento":
        st.title("Registrar Movimiento")

        transaction_type = st.radio("Tipo de Movimiento", ["Ingreso", "Gasto"])

        categories = (financial_manager.INCOME_CATEGORIES 
                     if transaction_type == "Ingreso" 
                     else financial_manager.EXPENSE_CATEGORIES)

        category = st.selectbox("Categoría", categories)
        amount = st.number_input("Cantidad (€)", min_value=0.0, step=0.01)
        description = st.text_area("Descripción")

        if st.button("Registrar"):
            financial_manager.add_transaction(
                'income' if transaction_type == "Ingreso" else 'expense',
                category,
                amount,
                description
            )
            st.success("Movimiento registrado correctamente")

    elif selected_option == "Buscar Movimientos":
        st.title("Buscar Movimientos")

        search_term = st.text_input("Buscar por descripción")

        if search_term:
            filtered_data = financial_manager.transactions[
                financial_manager.transactions['description'].str.contains(search_term, case=False)
            ]
            st.dataframe(filtered_data)
        else:
            st.dataframe(financial_manager.transactions)

    elif selected_option == "Generar Informe":
        st.title("Generar Informe")

        if st.button("Generar PDF"):
            pdf_buffer = pdf_generator.generate_report(
                financial_manager.transactions,
                financial_manager.initial_balance,
                financial_manager.get_balance()
            )

            st.download_button(
                label="Descargar Informe",
                data=pdf_buffer.getvalue(),
                file_name=f"informe_ampa_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )