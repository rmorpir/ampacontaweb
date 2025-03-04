import streamlit as st
import hashlib
import os

def init_auth():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

def get_password_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

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
        st.image("assets/ampa_logo.svg", width=200)
        st.title("AMPA Sagrada Familia Badajoz")
        
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        
        # In production, use environment variables or secure storage
        ADMIN_USER = os.getenv("ADMIN_USER", "admin")
        ADMIN_PASS = os.getenv("ADMIN_PASS", get_password_hash("admin123"))
        
        if st.button("Iniciar Sesión"):
            if username == ADMIN_USER and get_password_hash(password) == ADMIN_PASS:
                st.session_state.authenticated = True
                st.experimental_rerun()
            else:
                st.error("Usuario o contraseña incorrectos")

def logout():
    st.session_state.authenticated = False
    st.experimental_rerun()
