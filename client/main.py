import os

import requests
import streamlit as st
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Healthcare RBAC RAG Chatbot",
    layout="centered",
    page_icon="H",
)

if "username" not in st.session_state:
    st.session_state.username = ""
    st.session_state.password = ""
    st.session_state.role = ""
    st.session_state.logged_in = False


def get_auth() -> HTTPBasicAuth:
    return HTTPBasicAuth(st.session_state.username, st.session_state.password)


def get_error_message(res: requests.Response, fallback: str) -> str:
    try:
        payload = res.json()
    except ValueError:
        text = res.text.strip()
        if text:
            return f"{fallback} (HTTP {res.status_code})"
        return fallback
    return payload.get("detail") or payload.get("message") or fallback


def auth_ui() -> None:
    st.title("Healthcare RBAC RAG")
    st.subheader("Login or Signup")

    login_tab, signup_tab = st.tabs(["Login", "Signup"])

    with login_tab:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", use_container_width=True):
            res = requests.post(
                f"{API_URL}/auth/login",
                auth=HTTPBasicAuth(username, password),
                timeout=60,
            )
            if res.status_code == 200:
                user_data = res.json()
                st.session_state.username = username
                st.session_state.password = password
                st.session_state.role = user_data["role"]
                st.session_state.logged_in = True
                st.success(f"Welcome {username}")
                st.rerun()
            else:
                st.error(get_error_message(res, "Login failed"))

    with signup_tab:
        new_user = st.text_input("New Username", key="signup_user")
        new_pass = st.text_input("New Password", type="password", key="signup_pass")
        new_role = st.selectbox("Choose Role", ["admin", "doctor", "nurse", "patient", "other"])
        if st.button("Signup", use_container_width=True):
            payload = {"username": new_user, "password": new_pass, "role": new_role}
            res = requests.post(f"{API_URL}/auth/signup", json=payload, timeout=60)
            if res.status_code == 200:
                st.success("Signup successful! You can login.")
            else:
                st.error(get_error_message(res, "Signup failed"))


def upload_docs() -> None:
    st.subheader("Upload PDF")
    st.caption("Uploaded PDFs will be available to all logged-in users.")
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if st.button("Upload Document", use_container_width=True):
        if not uploaded_file:
            st.warning("Please upload a file")
            return

        files = [("files", (uploaded_file.name, uploaded_file.getvalue(), "application/pdf"))]
        res = requests.post(
            f"{API_URL}/documents/upload-docs",
            files=files,
            auth=get_auth(),
            timeout=300,
        )
        if res.status_code == 200:
            doc_info = res.json()
            st.success(f"Uploaded: {uploaded_file.name}")
            st.info(
                f"Doc ID: {doc_info['doc_id']} | Access: {doc_info['accessible_to']} | "
                f"Chunks: {doc_info['chunk_count']}"
            )
        else:
            st.error(get_error_message(res, "Upload failed"))


def chat_interface() -> None:
    st.subheader("Ask a healthcare question")
    msg = st.text_input("Your query")

    if st.button("Send", use_container_width=True):
        if not msg.strip():
            st.warning("Please enter a query")
            return

        res = requests.post(
            f"{API_URL}/chat",
            data={"message": msg},
            auth=get_auth(),
            timeout=120,
        )
        if res.status_code == 200:
            reply = res.json()
            st.markdown("### Answer")
            st.success(reply["answer"])
            if reply.get("sources"):
                st.markdown("### Sources")
                for src in reply["sources"]:
                    st.write(f"- {src}")
        else:
            st.error(get_error_message(res, "Something went wrong."))


if not st.session_state.logged_in:
    auth_ui()
else:
    st.title(f"Welcome, {st.session_state.username}")
    st.markdown(f"**Role:** `{st.session_state.role}`")

    if st.button("Logout"):
        st.session_state.username = ""
        st.session_state.password = ""
        st.session_state.role = ""
        st.session_state.logged_in = False
        st.rerun()

    if st.session_state.role in {"admin", "doctor"}:
        upload_docs()
        st.divider()

    chat_interface()
