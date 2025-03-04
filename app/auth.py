import streamlit as st
import hashlib
import os

def init_auth():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

def get_password_hash(password):
    """Generate a secure hash of the password."""
    if not password:
        return None
    return hashlib.sha256(str(password).encode()).hexdigest()

def login():
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: auto;
        padding: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.image("attached_assets/LogoAMPA.png", width=200)
        st.title("AMPA Sagrada Familia Badajoz")

        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")

        if st.button("Iniciar Sesión"):
            stored_user = os.getenv("ADMIN_USER")
            stored_pass = os.getenv("ADMIN_PASS")

            if not stored_user or not stored_pass:
                st.error("Error: Credenciales no configuradas correctamente")
                return

            input_pass_hash = get_password_hash(password)

            # Compare the password directly without hashing the stored password
            if username == stored_user and password == stored_pass:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")

def logout():
    st.session_state.authenticated = False
    st.rerun()