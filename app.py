import streamlit as st
import google.generativeai as genai
import os

# ==============================================================================
# 🛠️ PENGATURAN KONSTANTA (PENTING! UBAH SESUAI KEBUTUHAN ANDA)
# ==============================================================================

# GANTI INI DENGAN API KEY GEMINI ANDA!
# Catatan: Di aplikasi Streamlit, lebih baik gunakan st.secrets atau variabel lingkungan
# daripada menyimpan API Key langsung di kode.
# Namun, untuk demonstrasi, kita akan menyimpan di sini.
API_KEY = "AIzaSyARI77nf1RNJjR7CLq8nLyAuSCRixUgrjI" # <--- GANTI BAGIAN INI!

# Nama model Gemini yang akan digunakan.
MODEL_NAME = 'gemini-1.5-flash'
TEMPERATURE = 0.4
MAX_OUTPUT_TOKENS = 500

# ==============================================================================
# 🧑‍🔬 KONTEKS AWAL CHATBOT (INI BAGIAN YANG BISA SISWA MODIFIKASI!)
# ==============================================================================

# Definisikan peran chatbot Anda di sini.
INITIAL_CHATBOT_CONTEXT = [
    {
        "role": "user",
        "parts": ["Kamu adalah ahli kimia. Berikan reaksi kimia yang bermanfaat. Jawaban singkat dan faktual. Tolak pertanyaan non-kimia."]
    },
    {
        "role": "model",
        "parts": ["Baik! Saya akan menyampaikan reaksi kimia. Silakan ajukan pertanyaan Anda."]
    }
]

# ==============================================================================
# ⚙️ FUNGSI UNTUK INISIALISASI
# ==============================================================================

def initialize_gemini():
    """Menginisialisasi konfigurasi Gemini API dan model."""
    if API_KEY == "AIzaSyARI77nf1RNJjR7CLq8nLyAuSCRixUgrjI" or not API_KEY:
        st.error("⚠️ **Peringatan:** API Key belum diatur. Harap ganti 'AIzaSyARI77nf1RNJjR7CLq8nLyAuSCRixUgrjI' dengan API Key Anda.")
        st.stop()

    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel(
            MODEL_NAME,
            generation_config=genai.types.GenerationConfig(
                temperature=TEMPERATURE,
                max_output_tokens=MAX_OUTPUT_TOKENS
            )
        )
        return model
    except Exception as e:
        st.error(f"❌ **Kesalahan Inisialisasi Gemini:** {e}")
        st.stop()

# ==============================================================================
# 🚀 APLIKASI UTAMA STREAMLIT
# ==============================================================================

st.set_page_config(page_title=f"Chatbot Kimia {MODEL_NAME}", layout="centered")
st.title("🧑‍🔬 Gemini Chatbot Kimia")
st.caption(f"Didukung oleh Google Gemini API ({MODEL_NAME})")

# Inisialisasi Model di Session State
if 'model' not in st.session_state:
    st.session_state.model = initialize_gemini()
    st.success(f"Model '{MODEL_NAME}' berhasil diinisialisasi.")

# Inisialisasi Riwayat Chat di Session State
# Riwayat akan disimpan dalam format yang digunakan oleh Gemini Chat
if "messages" not in st.session_state:
    # Masukkan konteks awal ke riwayat chat
    st.session_state.messages = INITIAL_CHATBOT_CONTEXT

# Tombol untuk mereset chat
if st.button("🔄 Mulai Chat Baru"):
    st.session_state.messages = INITIAL_CHATBOT_CONTEXT
    st.rerun()

# --- Tampilkan Riwayat Chat ---
# Loop untuk menampilkan setiap pesan, kecuali konteks awal (pesan ke-0)
for message in st.session_state.messages[1:]:
    with st.chat_message(message["role"]):
        st.markdown(message["parts"][0])

# --- Proses Input Pengguna ---
if user_input := st.chat_input(INITIAL_CHATBOT_CONTEXT[1]["parts"][0]):
    # 1. Tambahkan pesan pengguna ke riwayat chat
    st.session_state.messages.append({"role": "user", "parts": [user_input]})

    # 2. Tampilkan pesan pengguna
    with st.chat_message("user"):
        st.markdown(user_input)

    # 3. Dapatkan respons dari Gemini
    with st.spinner("Chatbot: Sedang membalas..."):
        try:
            # Menggunakan riwayat chat dari st.session_state
            chat_session = st.session_state.model.start_chat(history=st.session_state.messages)
            
            # Karena riwayat sudah ada di chat_session, kita hanya perlu mengirim pesan terakhir.
            # Namun, API Gemini SDK Python tidak memiliki metode "continue_chat" sederhana
            # seperti ini, jadi kita akan membuat sesi baru setiap kali dan mengirim pesan.
            # Alternatif yang lebih efisien adalah menyimpan objek `chat` itu sendiri di session_state.

            # Hapus pesan terakhir (input user) dari riwayat sesi baru untuk mencegah duplikasi
            # Ini adalah workaround karena start_chat membutuhkan *semua* riwayat.
            # Kita akan mengembalikan pesan terakhir (input user) setelah mendapatkan respons.

            # Lebih baik: Kirim pesan terakhir dan biarkan model menambahkan respons
            response = st.session_state.model.generate_content(
                user_input, 
                config=genai.types.GenerateContentConfig(
                    system_instruction=INITIAL_CHATBOT_CONTEXT[0]["parts"][0]
                )
            )

            # Untuk memastikan riwayat chat multi-turn berfungsi, kita gunakan model.start_chat:
            # *TIPS:* Gunakan objek chat di session_state untuk menghindari pengiriman riwayat berulang
            # *CATATAN:* Untuk kesederhanaan, kita akan tetap menggunakan format generate_content
            # *PERBAIKAN:* Mari kita gunakan *session_state* untuk objek *chat* agar lebih efisien.
            
            # Inisialisasi objek chat di state jika belum ada
            if 'chat_session' not in st.session_state:
                 # Gunakan riwayat penuh
                st.session_state.chat_session = st.session_state.model.start_chat(history=st.session_state.messages)
            
            # Kirim pesan pengguna (tanpa riwayat karena sudah ada di objek chat)
            response = st.session_state.chat_session.send_message(user_input, request_options={"timeout": 60})

            # Tambahkan respons model ke riwayat chat di Streamlit
            st.session_state.messages.append({"role": "model", "parts": [response.text]})

            # 4. Tampilkan respons model
            with st.chat_message("model"):
                st.markdown(response.text)

        except Exception as e:
            error_message = f"❌ **Kesalahan Komunikasi Gemini:** {e}"
            st.error(error_message)
            # Opsional: Hapus input pengguna terakhir jika terjadi error
            # st.session_state.messages.pop()
