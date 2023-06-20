import os
import tempfile
import streamlit as st
from streamlit_chat import message
from pdfquery import PDFQuery
from webquery import WebQuery

st.set_page_config(page_title="Chatbot")


def display_messages():
    st.subheader("Chat")
    for i, (msg, is_user) in enumerate(st.session_state["messages"]):
        message(msg, is_user=is_user, key=str(i))
    st.session_state["thinking_spinner"] = st.empty()


def process_input():
    if st.session_state["user_input"] and len(st.session_state["user_input"].strip()) > 0:
        user_text = st.session_state["user_input"].strip()
        if st.session_state["input_type"] == "PDF":
            with st.session_state["thinking_spinner"], st.spinner(f"Thinking"):
                query_text = st.session_state["pdfquery"].ask(user_text)
        elif st.session_state["input_type"] == "URL":
            with st.session_state["thinking_spinner"], st.spinner(f"Thinking"):
                query_text = st.session_state["webquery"].ask(user_text)

        st.session_state["messages"].append((user_text, True))
        st.session_state["messages"].append((query_text, False))


def ingest_input():
    if st.session_state["input_url"] and len(st.session_state["input_url"].strip()) > 0:
        url = st.session_state["input_url"].strip()
        with st.session_state["thinking_spinner"], st.spinner(f"Thinking"):
            ingest_text = st.session_state["webquery"].ingest(url)


def read_and_save_file():
    st.session_state["pdfquery"].forget()  # to reset the knowledge base
    st.session_state["messages"] = []
    st.session_state["user_input"] = ""

    file_paths = []
    for file in st.session_state["file_uploader"]:
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(file.getbuffer())
            file_path = tf.name
            file_paths.append(file_path)

        with st.session_state["ingestion_spinner"], st.spinner(f"Ingesting files"):
            st.session_state["pdfquery"].ingest(file_paths)

    for file_path in file_paths:
        os.remove(file_path)


def is_openai_api_key_set() -> bool:
    return len(st.session_state["OPENAI_API_KEY"]) > 0


def main():
    if len(st.session_state) == 0:
        st.session_state["messages"] = []
        st.session_state["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "")
        st.session_state["url"] = ""
        if is_openai_api_key_set():
            st.session_state["pdfquery"] = PDFQuery(st.session_state["OPENAI_API_KEY"])
            st.session_state["webquery"] = WebQuery(st.session_state["OPENAI_API_KEY"])
        else:
            st.session_state["pdfquery"] = None
            st.session_state["webquery"] = None

    st.header("Chatbot")

    if st.text_input("OpenAI API Key", value=st.session_state["OPENAI_API_KEY"], key="input_OPENAI_API_KEY", type="password"):
        if (
            len(st.session_state["input_OPENAI_API_KEY"]) > 0
            and st.session_state["input_OPENAI_API_KEY"] != st.session_state["OPENAI_API_KEY"]
        ):
            st.session_state["OPENAI_API_KEY"] = st.session_state["input_OPENAI_API_KEY"]
            if st.session_state["pdfquery"] is not None:
                st.warning("Please upload the files again.")
            st.session_state["messages"] = []
            st.session_state["user_input"] = ""
            st.session_state["input_url"] = ""
            st.session_state["pdfquery"] = PDFQuery(st.session_state["OPENAI_API_KEY"])
            st.session_state["webquery"] = WebQuery(st.session_state["OPENAI_API_KEY"])

    st.subheader("Select input type")
    input_type = st.selectbox("Input type", ["PDF", "URL"])
    st.session_state["input_type"] = input_type

    if input_type == "PDF":
        st.subheader("Upload PDF document")
        st.file_uploader(
            "Upload document",
            type=["pdf"],
            key="file_uploader",
            on_change=read_and_save_file,
            label_visibility="collapsed",
            accept_multiple_files=True,
            disabled=not is_openai_api_key_set(),
        )
    elif input_type == "URL":
        st.subheader("Add a URL")
        st.text_input("Input url", value=st.session_state["url"], key="input_url", disabled=not is_openai_api_key_set(), on_change=ingest_input)

    st.session_state["ingestion_spinner"] = st.empty()

    display_messages()
    st.text_input("Message", key="user_input", disabled=not is_openai_api_key_set(), on_change=process_input)

if __name__ == "__main__":
    main()
