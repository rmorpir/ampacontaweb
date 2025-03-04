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
    
    # Show storage status
    if drive_manager.service:
        st.sidebar.success("✅ Conectado a Google Drive")
    else:
        st.sidebar.warning("⚠️ Usando almacenamiento local (sin conexión a Google Drive)")

    # Sidebar
    st.sidebar.image("attached_assets/LogoAMPA.png", width=200)
    selected_option = st.sidebar.selectbox(
        "Menú",
        ["Inicio", "Registrar Movimiento", "Buscar Movimientos", "Generar Informe", "Configuración"]
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
        
        # Añadir selector de fecha
        transaction_date = st.date_input(
            "Fecha", 
            value=datetime.now(),
            format="DD/MM/YYYY"
        )

        if st.button("Registrar"):
            financial_manager.add_transaction(
                'income' if transaction_type == "Ingreso" else 'expense',
                category,
                amount,
                description,
                transaction_date.strftime('%Y-%m-%d')
            )
            st.success("Movimiento registrado correctamente")

    elif selected_option == "Buscar Movimientos":
        st.title("Buscar Movimientos")

        col1, col2 = st.columns(2)
        
        with col1:
            search_term = st.text_input("Buscar por descripción")
        
        with col2:
            # Opciones de filtrado por fecha
            use_date_filter = st.checkbox("Filtrar por fecha")
            
        if use_date_filter:
            date_col1, date_col2 = st.columns(2)
            with date_col1:
                start_date = st.date_input("Fecha inicial", datetime.now() - datetime.timedelta(days=30))
            with date_col2:
                end_date = st.date_input("Fecha final", datetime.now())
                
        # Aplicar filtros
        filtered_data = financial_manager.transactions
        
        if search_term:
            filtered_data = filtered_data[
                filtered_data['description'].str.contains(search_term, case=False)
            ]
            
        if use_date_filter:
            filtered_data = filtered_data[
                (filtered_data['date'] >= start_date.strftime('%Y-%m-%d')) & 
                (filtered_data['date'] <= end_date.strftime('%Y-%m-%d'))
            ]
            
        # Mostrar datos con formato
        if not filtered_data.empty:
            # Agregar una columna de índices para seleccionar transacciones
            filtered_data_with_index = filtered_data.reset_index().rename(columns={'index': 'original_index'})
            selected_row = st.dataframe(filtered_data_with_index.sort_values(by='date', ascending=False))
            
            # Opciones para editar o eliminar
            st.subheader("Editar o Eliminar Movimiento")
            
            col1, col2 = st.columns(2)
            with col1:
                selected_index = st.number_input("ID del movimiento a modificar", 
                                               min_value=-1, 
                                               max_value=len(financial_manager.transactions)-1, 
                                               value=-1,
                                               step=1)
            
            if selected_index >= 0:
                # Mostrar formulario de edición
                trans = financial_manager.transactions.iloc[selected_index]
                
                transaction_type = st.radio("Tipo de Movimiento", 
                                          ["Ingreso", "Gasto"], 
                                          index=0 if trans['type'] == 'income' else 1)
                
                categories = (financial_manager.INCOME_CATEGORIES 
                             if transaction_type == "Ingreso" 
                             else financial_manager.EXPENSE_CATEGORIES)
                
                cat_index = 0
                try:
                    if transaction_type == "Ingreso" and trans['category'] in financial_manager.INCOME_CATEGORIES:
                        cat_index = financial_manager.INCOME_CATEGORIES.index(trans['category'])
                    elif transaction_type == "Gasto" and trans['category'] in financial_manager.EXPENSE_CATEGORIES:
                        cat_index = financial_manager.EXPENSE_CATEGORIES.index(trans['category'])
                except ValueError:
                    cat_index = 0
                
                category = st.selectbox("Categoría", categories, index=cat_index)
                
                amount = st.number_input("Cantidad (€)", 
                                        min_value=0.0, 
                                        value=float(trans['amount']), 
                                        step=0.01)
                
                description = st.text_area("Descripción", value=trans['description'])
                
                try:
                    date_obj = datetime.strptime(trans['date'], '%Y-%m-%d')
                except:
                    date_obj = datetime.now()
                
                transaction_date = st.date_input(
                    "Fecha", 
                    value=date_obj,
                    format="DD/MM/YYYY"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Actualizar Movimiento"):
                        success = financial_manager.update_transaction(
                            selected_index,
                            'income' if transaction_type == "Ingreso" else 'expense',
                            category,
                            amount,
                            description,
                            transaction_date.strftime('%Y-%m-%d')
                        )
                        if success:
                            st.success("Movimiento actualizado correctamente")
                            st.rerun()
                        else:
                            st.error("Error al actualizar el movimiento")
                
                with col2:
                    if st.button("Eliminar Movimiento", type="primary", help="Esta acción no se puede deshacer"):
                        if st.confirm("¿Estás seguro de que deseas eliminar este movimiento? Esta acción no se puede deshacer."):
                            success = financial_manager.delete_transaction(selected_index)
                            if success:
                                st.success("Movimiento eliminado correctamente")
                                st.rerun()
                            else:
                                st.error("Error al eliminar el movimiento")
            else:
                st.info("Selecciona un ID de movimiento para editar o eliminar")
        else:
            st.info("No se encontraron movimientos con los filtros aplicados")

    elif selected_option == "Generar Informe":
        st.title("Generar Informe")
        
        # Date range selection
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Fecha inicial", 
                value=datetime.now().replace(day=1),  # First day of current month
                format="DD/MM/YYYY"
            )
        with col2:
            end_date = st.date_input(
                "Fecha final", 
                value=datetime.now(),
                format="DD/MM/YYYY"
            )
            
        # Format dates for filtering
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # Option to include all transactions
        include_all = st.checkbox("Incluir todas las transacciones (ignorar rango de fechas)")
        
        if st.button("Generar PDF"):
            if include_all:
                start_date_str = None
                end_date_str = None
                
            pdf_buffer = pdf_generator.generate_report(
                financial_manager.transactions,
                financial_manager.initial_balance,
                financial_manager.get_balance(),
                start_date_str,
                end_date_str
            )

            report_filename = f"informe_ampa_{datetime.now().strftime('%Y%m%d')}"
            if not include_all:
                report_filename += f"_{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}"
                
            st.download_button(
                label="Descargar Informe",
                data=pdf_buffer.getvalue(),
                file_name=f"{report_filename}.pdf",
                mime="application/pdf"
            )
    
    elif selected_option == "Configuración":
        st.title("Configuración")

        # Sección de Google Drive
        st.subheader("Conexión a Google Drive")

        # Mostrar estado de la conexión
        if drive_manager.service:
            st.success("✅ Conectado a Google Drive")

            # Mostrar ID de la carpeta actual
            st.info(f"ID de carpeta utilizado actualmente: {drive_manager.shared_folder_id}")

            # Botón para mostrar carpetas disponibles
            if st.button("Explorar carpetas disponibles"):
                folders = drive_manager.list_available_folders()
                if folders:
                    st.write("Carpetas disponibles:")
                    for folder in folders:
                        st.write(f"- **{folder['name']}**: `{folder['id']}`")
                else:
                    st.warning("No se encontraron carpetas o no hay permiso para listarlas")

            # Campo para actualizar ID de carpeta
            new_folder_id = st.text_input("Actualizar ID de carpeta", value=drive_manager.shared_folder_id)
            if st.button("Guardar nuevo ID de carpeta"):
                if new_folder_id and new_folder_id != drive_manager.shared_folder_id:
                    drive_manager.shared_folder_id = new_folder_id
                    st.success(f"ID de carpeta actualizado a: {new_folder_id}")
                    st.info("Recuerde reiniciar la aplicación para que los cambios surtan efecto")
        else:
            st.error("❌ No hay conexión a Google Drive")
            st.info("Para conectar con Google Drive, necesita configurar las credenciales adecuadas en las variables de entorno")

        st.divider()

        # Saldo inicial
        st.subheader("Saldo Inicial")
        current_initial_balance = financial_manager.initial_balance
        new_initial_balance = st.number_input("Saldo Inicial (€)", 
                                            value=float(current_initial_balance), 
                                            step=0.01)

        if st.button("Actualizar Saldo Inicial"):
            financial_manager.set_initial_balance(new_initial_balance)
            st.success("Saldo inicial actualizado correctamente")