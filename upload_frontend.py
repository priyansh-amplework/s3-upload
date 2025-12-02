import streamlit as st
import requests
import os


BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8004")
st.title("📄 Document Upload to S3")

doc_type = st.selectbox(
    "Select document type",
    ["personality", "instructions", "Tier1", "Tier2"]
)

uploaded_file = st.file_uploader(
    "Upload PDF, DOCX, or PPTX",
    type=["pdf", "docx", "pptx", "ppt"]
)

if uploaded_file and doc_type:
    if st.button("Upload to S3"):
        with st.spinner("Processing..."):
            files = {"file": uploaded_file}
            data = {"type": doc_type}

            backend_url = f"{BACKEND_URL}/api/get-upload-url"

            response = requests.post(backend_url, files=files, data=data)

            if response.status_code != 200:
                st.error("Backend error: " + response.text)
            else:
                res = response.json()
                upload_url = res["uploadUrl"]
                key = res["key"]

                put_response = requests.put(upload_url, data=uploaded_file.getvalue())

                if put_response.status_code == 200:
                    st.success(f"Uploaded to S3 ✔️\n\nKey: `{key}`")
                else:
                    st.error("Upload failed: " + str(put_response.text))
