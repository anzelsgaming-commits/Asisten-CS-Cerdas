import streamlit as st
from PyPDF2 import PdfReader
import os 
import google.generativeai as genai
# Note: Karena kita tidak pakai Langchain lagi, import di sini sederhana.


# --- KONFIGURASI API KEY ---
try:
    # Mengambil API key dari file .streamlit/secrets.toml
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
except KeyError:
    st.error("❌ ERROR: Kunci API Google tidak ditemukan.")
    st.info("Mohon cek file .streamlit/secrets.toml Anda.")
    st.stop()
except Exception as e:
    st.error(f"❌ ERROR saat konfigurasi API Key: {e}")
    st.stop()


# --- FUNGSI-FUNGSI LOGIKA (MESINNYA) ---

@st.cache_resource
def get_pdf_text(pdf_docs_list):
    """Membaca teks dari daftar file PDF yang diunggah."""
    text = ""
    for pdf_doc in pdf_docs_list:
        try:
            pdf_reader = PdfReader(pdf_doc)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        except Exception as e:
            st.warning(f"⚠️ Gagal membaca file {pdf_doc.name}: {e}")
    return text

def get_answer_with_context(raw_text, question):
    """
    Meminta jawaban dari Gemini dengan SELURUH konteks dokumen.
    Logic Fallback (Ramah) ada di dalam prompt.
    """
    
    # Model AI (Gemini Flash terbaru)
    model_instance = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Anda adalah asisten yang ramah dan cerdas dari PT [NAMA PERUSAHAAN KLIEN]. 
    
    Instruksi Jawaban:
    1. Jawab pertanyaan hanya berdasarkan dokumen di bawah.
    2. Jika pertanyaan tidak relevan dengan dokumen (misal: 'Makan apa hari ini?'), JAWAB DENGAN RAMAH dan katakan bahwa Anda adalah AI khusus yang hanya bisa membahas topik terkait perusahaan atau dokumen yang diberikan. **Contoh jawaban Fallback:** 'Wah, saya tidak tahu. Saya adalah asisten AI yang fokus membantu dengan informasi dari dokumen perusahaan.'
    3. Selalu pertahankan nada yang profesional, sopan, dan bersahabat.
    
    --- DOKUMEN KONTEKS ---
    {raw_text[:20000]} 
    
    --- PERTANYAAN ---
    {question}
    
    Jawaban:
    """
    
    # Panggil metode generate_content yang benar
    response = model_instance.generate_content(prompt)
    return response.text

# --- TAMPILAN APLIKASI WEB (UI) ---

def main():
    # Konfigurasi halaman web
    st.set_page_config(page_title="Asisten CS Cerdas", layout="wide")
    st.title("🤖 Asisten CS Cerdas: Chat dengan PDF Anda")
    st.write("🔥 **Versi Sederhana, Dijamin Jalan!** Upload dokumen (PDF) Anda dan tanyakan isinya.")

    # Sidebar (menu samping)
    with st.sidebar:
        st.header("Upload Dokumen")
        pdf_docs = st.file_uploader(
            "Upload file PDF Anda", 
            type="pdf",
            accept_multiple_files=True
        )
        
        # Tombol untuk memproses PDF
        if st.button("Proses Dokumen"):
            if pdf_docs:
                with st.spinner("⏳ Sedang memproses PDF..."):
                    raw_text = get_pdf_text(pdf_docs)
                    
                    if not raw_text:
                        st.error("❌ Gagal mengekstrak teks. Coba PDF lain.")
                    else:
                        # Simpan seluruh raw_text di session state
                        st.session_state.raw_text = raw_text
                        st.session_state.processing_done = True
                        st.success("✅ Dokumen berhasil diproses dan siap ditanya!")

            else:
                st.error("Mohon upload file PDF terlebih dahulu.")

    # Area chat utama
    st.header("Tanyakan Sesuatu")
    
    # Cek apakah dokumen sudah diproses
    if "processing_done" in st.session_state and st.session_state.processing_done:
        user_question = st.text_input("Ketik pertanyaan Anda di sini:")

        if user_question: # Jika pengguna mengetik pertanyaan
            try:
                raw_text = st.session_state.raw_text # Ambil raw_text dari session state
                
                with st.spinner("⏳ AI sedang berpikir..."):
                    # Mendapatkan jawaban langsung dari Gemini
                    response_text = get_answer_with_context(raw_text, user_question)
                
                # Tampilkan jawaban
                st.subheader("🤖 Jawaban dari AI:")
                st.write(response_text)

            except Exception as e:
                st.error(f"❌ Terjadi error saat bertanya ke AI: {e}")
                st.info("Tips: Pastikan koneksi internet Anda stabil.")
    else:
        st.info("Silakan upload PDF dan klik 'Proses Dokumen' di sidebar.")

# Menjalankan aplikasi
if __name__ == "__main__":
    main()