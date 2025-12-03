import streamlit as st
import requests
from pathlib import Path
import os
BACKEND_BASE = "https://s3-upload-i2ix.onrender.com"


# ═══════════════════════════════════════════════════════════
# 📝 CHANGE YOUR LOGO PATH HERE
# ═══════════════════════════════════════════════════════════
LOGO_PATH = "ona.png"  # ⬅️ CHANGE THIS TO YOUR IMAGE PATH
# ═══════════════════════════════════════════════════════════

# Page config
st.set_page_config(
    page_title="Knowledge Base Upload - Ona Wealth Mentor",
    page_icon="📚",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #E8D5E8 0%, #F0E5F0 50%, #E8D5E8 100%);
    }
    
    .main-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 1rem 2rem;
    }
    
    .header-section {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 4rem;
    }
    
    .logo-container {
        flex: 0 0 auto;
    }
    
    .content-wrapper {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 4rem;
        align-items: start;
    }
    
    .left-section {
        padding-right: 2rem;
    }
    
    .main-heading {
        font-size: 3.5rem;
        font-weight: 700;
        color: #1a1a1a;
        line-height: 1.2;
        margin-bottom: 2rem;
    }
    
    .subheading {
        font-size: 2rem;
        font-weight: 600;
        color: #2d2d2d;
        margin-bottom: 1.5rem;
        line-height: 1.3;
    }
    
    .description {
        font-size: 1.2rem;
        color: #4a4a4a;
        line-height: 1.6;
        margin-bottom: 2rem;
    }
    
    .upload-card {
        background: transparent;
        padding: 0;
    }
    
    .card-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2d2d2d;
        margin-bottom: 1.5rem;
    }
    
    .stRadio > label {
        font-size: 1rem;
        font-weight: 600;
        color: #2d2d2d;
        margin-bottom: 1rem;
    }
    
    .stRadio > div {
        gap: 0.5rem;
    }
    
    .stRadio > div > label {
        background: #f8f9fa;
        padding: 0.75rem 1.25rem;
        border-radius: 12px;
        border: 2px solid transparent;
        transition: all 0.3s ease;
    }
    
    .stRadio > div > label:hover {
        border-color: #8B6FA8;
        background: #f0e5f0;
    }
    
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #8B6FA8 0%, #6B4F88 100%);
        color: white;
        font-size: 1.1rem;
        font-weight: 600;
        padding: 1rem 2rem;
        border-radius: 16px;
        border: none;
        box-shadow: 0 4px 12px rgba(139, 111, 168, 0.4);
        transition: all 0.3s ease;
        margin-top: 1.5rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(139, 111, 168, 0.5);
    }
    
    .file-item {
        background: #f8f9fa;
        padding: 0.75rem 1.25rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        border-left: 4px solid #8B6FA8;
    }
    
    .security-badge {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-top: 2rem;
        padding: 1rem;
        background: rgba(139, 111, 168, 0.1);
        border-radius: 12px;
    }
    
    .security-text {
        font-size: 0.95rem;
        color: #4a4a4a;
    }
    
    div[data-testid="stFileUploader"] {
        background: #f8f9fa;
        border: 2px dashed #8B6FA8;
        border-radius: 16px;
        padding: 2rem;
    }
    
    div[data-testid="stFileUploader"]:hover {
        border-color: #6B4F88;
        background: #f0e5f0;
    }
</style>
""", unsafe_allow_html=True)

# Main container
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Header with logo
col_logo, col_spacer = st.columns([1, 3])
with col_logo:
    logo_path = Path(LOGO_PATH)
    if logo_path.exists():
        st.image(LOGO_PATH, width=180)
    else:
        st.markdown("### Ona Wealth Mentor")

# Content wrapper
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("""
    <div class="left-section">
        <h1 class="main-heading">Knowledge Base Upload for Ona</h1>
        <h2 class="subheading">Empower AI with Expert Knowledge.</h2>
        <p class="description">
            Upload your documents to enhance Ona's knowledge base.
        </p>
      
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown('<h2 style="font-size: 1.8rem; font-weight: 600; color: #2d2d2d; margin-bottom: 1.5rem;">Select Document Category</h2>', unsafe_allow_html=True)
    
    doc_type = st.radio(
        "category",
        ["Personality Assessment", "Instructions & Guidelines", "Tier 1 Documents", "Tier 2 Documents"],
        label_visibility="collapsed"
    )
    
    # Map display names to backend values
    doc_type_map = {
        "Personality Assessment": "personality",
        "Instructions & Guidelines": "instructions",
        "Tier 1 Documents": "Tier1",
        "Tier 2 Documents": "Tier2"
    }
    
    st.markdown('<br>', unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Upload your documents",
        type=["pdf", "docx", "pptx", "ppt"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        st.markdown(f'<p style="font-weight: 600; color: #2d2d2d;">{len(uploaded_files)} file(s) selected:</p>', unsafe_allow_html=True)
        for file in uploaded_files:
            st.markdown(f'<div class="file-item">📄 {file.name}</div>', unsafe_allow_html=True)
    
    if uploaded_files and doc_type:
        if st.button("Upload to Knowledge Base", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            success_count = 0
            fail_count = 0
            results = []
            
            for idx, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Uploading {idx + 1}/{len(uploaded_files)}: {uploaded_file.name}")
                
                try:
                    uploaded_file.seek(0)
                    
                    files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                    data = {"type": doc_type_map[doc_type]}
                    
                    backend_url = f"{BACKEND_BASE}/api/get-upload-url"
                    
                    response = requests.post(backend_url, files=files, data=data)
                    
                    if response.status_code != 200:
                        results.append(("❌", uploaded_file.name, f"Failed: {response.text}"))
                        fail_count += 1
                    else:
                        res = response.json()
                        upload_url = res["uploadUrl"]
                        key = res["key"]
                        
                        uploaded_file.seek(0)
                        put_response = requests.put(upload_url, data=uploaded_file.getvalue())
                        
                        if put_response.status_code == 200:
                            results.append(("✅", uploaded_file.name, f"Key: `{key}`"))
                            success_count += 1
                        else:
                            results.append(("❌", uploaded_file.name, f"Storage failed: {put_response.text}"))
                            fail_count += 1
                            
                except Exception as e:
                    results.append(("❌", uploaded_file.name, f"Error: {str(e)}"))
                    fail_count += 1
                
                progress_bar.progress((idx + 1) / len(uploaded_files))
            
            status_text.empty()
            progress_bar.empty()
            
            # Show summary
            if success_count > 0:
                st.success(f"✅ {success_count} file(s) uploaded successfully!")
            if fail_count > 0:
                st.error(f"❌ {fail_count} file(s) failed to upload")
            
            # Show detailed results
            with st.expander("View detailed results"):
                for icon, filename, message in results:
                    st.write(f"{icon} **{filename}**: {message}")
            
            if success_count == len(uploaded_files):
                st.balloons()

st.markdown('</div>', unsafe_allow_html=True)

