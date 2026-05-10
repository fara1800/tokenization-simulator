import streamlit as st
import re
import pandas as pd
from collections import Counter

st.set_page_config(page_title="Tokenization Simulator", page_icon="🔤")

# Identitas MBKM
st.markdown("""
<div style="text-align:center;padding:6px;background:#f0f2f6;border-radius:8px;margin-bottom:10px">
<small style="color:gray">KKN Magang Berdampak UNIPOL 2026</small>
</div>
""", unsafe_allow_html=True)

TOKEN_RULES = [
    ('COMMENT',      r'//[^\n]*|#[^\n]*'),
    ('KEYWORD',      r'\b(int|float|string|char|bool|void|if|else|elif|while|for|do|return|break|continue|true|false|True|False|None|and|or|not|in|is|pass|lambda|with|as|try|except|finally|raise|import|from|class|def|print|input|len|range|type|str|list|dict|tuple|set|pinMode|digitalWrite|digitalRead|analogWrite|analogRead|delay|delayMicroseconds|Serial|setup|loop|HIGH|LOW|INPUT|OUTPUT|INPUT_PULLUP|millis|micros|map|constrain|abs|min|max|random|randomSeed|attachInterrupt|detachInterrupt|interrupts|noInterrupts)\b'),
    ('NUMBER',       r'\b\d+\.\d+\b|\b\d+\b'),
    ('STRING',       r'"[^"]*"|\'[^\']*\''),
    ('IDENTIFIER',   r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
    ('DOT_OPERATOR', r'\.'),
    ('OPERATOR',     r'==|!=|<=|>=|\+=|-=|\*=|/=|&&|\|\||[+\-*/%=<>!&|^~]'),
    ('DELIMITER',    r'[;,(){}[\]:]'),
    ('WHITESPACE',   r'\s+'),
]

COLORS = {
    'KEYWORD':      '#FF6B6B',
    'IDENTIFIER':   '#4ECDC4',
    'NUMBER':       '#FFE66D',
    'STRING':       '#A8E6CF',
    'OPERATOR':     '#FF8B94',
    'DOT_OPERATOR': '#FFB347',
    'DELIMITER':    '#B4B4FF',
    'COMMENT':      '#AAAAAA',
    'UNKNOWN':      '#FF0000',
}

TYPE_DESCRIPTIONS = {
    'KEYWORD':      'Kata kunci bawaan bahasa pemrograman',
    'IDENTIFIER':   'Nama yang dibuat oleh programmer',
    'NUMBER':       'Nilai angka dalam kode',
    'STRING':       'Data teks yang diapit tanda kutip',
    'OPERATOR':     'Simbol untuk operasi atau perbandingan',
    'DOT_OPERATOR': 'Penghubung pemanggilan fungsi dari objek',
    'DELIMITER':    'Tanda baca pemisah bagian kode',
    'COMMENT':      'Teks penjelasan yang diabaikan kompiler',
    'UNKNOWN':      '⚠️ Karakter tidak dikenal',
}

KEYWORD_MEANINGS = {
    'int':    'Tipe data untuk menyimpan bilangan bulat. Contoh: int led = 13;',
    'float':  'Tipe data untuk menyimpan bilangan desimal. Contoh: float suhu = 36.5;',
    'char':   'Tipe data untuk menyimpan satu karakter huruf.',
    'string': 'Tipe data untuk menyimpan rangkaian teks.',
    'str':    'Tipe data teks di Python.',
    'bool':   'Tipe data yang hanya bernilai benar (true) atau salah (false).',
    'void':   'Fungsi ini tidak mengembalikan nilai — hanya menjalankan perintah saja.',
    'if':     'Cek kondisi — kalau kondisinya benar, perintah di dalamnya dijalankan.',
    'else':   'Alternatif kalau kondisi if di atasnya tidak terpenuhi.',
    'elif':   'Kondisi alternatif tambahan setelah if (khusus Python).',
    'while':  'Ulangi perintah di dalamnya selama kondisinya masih benar.',
    'for':    'Ulangi perintah sejumlah tertentu atau untuk setiap elemen.',
    'do':     'Jalankan perintah dulu, baru cek kondisinya (do-while loop).',
    'break':  'Hentikan perulangan sekarang juga, keluar dari loop.',
    'continue': 'Lewati iterasi ini dan langsung lanjut ke iterasi berikutnya.',
    'return': 'Kembalikan nilai dari fungsi ini ke tempat yang memanggilnya.',
    'def':    'Mendefinisikan fungsi baru di Python.',
    'class':  'Mendefinisikan kelas baru — cetak biru untuk membuat objek.',
    'lambda': 'Membuat fungsi kecil tanpa nama dalam satu baris.',
    'true':   'Nilai logika BENAR (digunakan di C/C++/Arduino).',
    'false':  'Nilai logika SALAH (digunakan di C/C++/Arduino).',
    'True':   'Nilai logika BENAR (digunakan di Python).',
    'False':  'Nilai logika SALAH (digunakan di Python).',
    'None':   'Nilai kosong — menandakan tidak ada nilai yang disimpan (Python).',
    'and':    'Logika DAN — kedua kondisi harus benar supaya hasilnya benar.',
    'or':     'Logika ATAU — cukup satu kondisi yang benar.',
    'not':    'Membalik nilai logika — benar jadi salah, salah jadi benar.',
    'in':     'Mengecek apakah suatu nilai ada di dalam kumpulan data.',
    'is':     'Mengecek apakah dua variabel merujuk ke objek yang sama.',
    'pass':   'Tidak melakukan apa-apa — placeholder untuk kode yang belum diisi.',
    'import': 'Mengimpor modul atau library supaya fiturnya bisa digunakan.',
    'from':   'Mengimpor bagian tertentu dari sebuah modul.',
    'as':     'Memberi nama alias pada modul yang diimpor.',
    'try':    'Coba jalankan kode ini — kalau error, tangkap di except.',
    'except': 'Tangani error yang terjadi di blok try di atasnya.',
    'finally':'Selalu dijalankan setelah try/except, baik error maupun tidak.',
    'raise':  'Memunculkan error secara sengaja.',
    'with':   'Mengelola sumber daya secara otomatis.',
    'print':  'Menampilkan teks atau nilai ke layar.',
    'input':  'Meminta pengguna memasukkan data lewat keyboard.',
    'len':    'Menghitung jumlah elemen dalam data.',
    'range':  'Membuat urutan angka untuk digunakan dalam perulangan.',
    'type':   'Mengecek tipe data dari sebuah nilai atau variabel.',
    'list':   'Tipe data list — kumpulan nilai yang bisa diubah.',
    'dict':   'Tipe data dictionary — kumpulan pasangan kunci dan nilai.',
    'tuple':  'Tipe data tuple — kumpulan nilai yang tidak bisa diubah.',
    'set':    'Tipe data set — kumpulan nilai unik tanpa duplikat.',
    'pinMode':           'Memberi tahu Arduino apakah pin ini akan jadi INPUT atau OUTPUT.',
    'digitalWrite':      'Mengirim sinyal HIGH (nyala) atau LOW (mati) ke sebuah pin.',
    'digitalRead':       'Membaca sinyal dari sebuah pin — hasilnya HIGH atau LOW.',
    'analogWrite':       'Mengirim sinyal PWM (0-255) ke pin untuk mengatur kecepatan atau kecerahan.',
    'analogRead':        'Membaca nilai analog dari pin (0-1023) — cocok untuk sensor.',
    'delay':             'Menghentikan program sementara. Satuannya milidetik (1000 = 1 detik).',
    'delayMicroseconds': 'Menghentikan program dalam satuan mikrodetik.',
    'Serial':            'Objek untuk komunikasi antara Arduino dan komputer lewat kabel USB.',
    'setup':             'Fungsi khusus Arduino yang dijalankan SEKALI saat pertama dinyalakan.',
    'loop':              'Fungsi khusus Arduino yang dijalankan BERULANG terus-menerus.',
    'HIGH':              'Nilai logika 1 — tegangan sekitar 5V pada pin Arduino.',
    'LOW':               'Nilai logika 0 — tegangan 0V (mati) pada pin Arduino.',
    'INPUT':             'Mode pin sebagai penerima sinyal dari luar (sensor, tombol).',
    'OUTPUT':            'Mode pin sebagai pengirim sinyal ke komponen (LED, motor).',
    'INPUT_PULLUP':      'Mode input dengan resistor pull-up internal — pin default HIGH.',
    'millis':            'Mengembalikan waktu (ms) sejak Arduino dinyalakan.',
    'micros':            'Mengembalikan waktu (µs) sejak Arduino dinyalakan.',
    'map':               'Mengubah rentang nilai — misalnya dari 0-1023 menjadi 0-255.',
    'constrain':         'Membatasi nilai agar tidak melebihi batas minimum dan maksimum.',
    'abs':               'Mengambil nilai mutlak (selalu positif) dari sebuah angka.',
    'min':               'Mengambil nilai terkecil dari dua angka.',
    'max':               'Mengambil nilai terbesar dari dua angka.',
    'random':            'Menghasilkan angka acak dalam rentang yang ditentukan.',
    'randomSeed':        'Menentukan titik awal untuk menghasilkan angka acak.',
    'attachInterrupt':   'Mendaftarkan fungsi yang dijalankan otomatis saat ada sinyal interrupt.',
    'detachInterrupt':   'Membatalkan interrupt yang sudah didaftarkan.',
    'interrupts':        'Mengaktifkan kembali sistem interrupt.',
    'noInterrupts':      'Mematikan sistem interrupt sementara.',
}

OPERATOR_MEANINGS = {
    '=':  'Memberikan nilai ke sebuah variabel.',
    '==': 'Mengecek apakah dua nilai sama persis.',
    '!=': 'Mengecek apakah dua nilai berbeda.',
    '+':  'Menjumlahkan dua nilai.',
    '-':  'Mengurangkan nilai kanan dari nilai kiri.',
    '*':  'Mengalikan dua nilai.',
    '/':  'Membagi nilai kiri dengan nilai kanan.',
    '%':  'Mengambil sisa hasil bagi (modulo).',
    '<':  'Mengecek apakah nilai kiri lebih kecil dari kanan.',
    '>':  'Mengecek apakah nilai kiri lebih besar dari kanan.',
    '<=': 'Mengecek apakah nilai kiri lebih kecil atau sama dengan kanan.',
    '>=': 'Mengecek apakah nilai kiri lebih besar atau sama dengan kanan.',
    '+=': 'Tambahkan nilai kanan ke variabel kiri lalu simpan.',
    '-=': 'Kurangi variabel kiri dengan nilai kanan lalu simpan.',
    '*=': 'Kalikan variabel kiri dengan nilai kanan lalu simpan.',
    '/=': 'Bagi variabel kiri dengan nilai kanan lalu simpan.',
    '&&': 'Logika DAN — kedua kondisi harus benar (C/Arduino).',
    '||': 'Logika ATAU — cukup satu kondisi benar (C/Arduino).',
    '!':  'Membalik nilai logika.',
    '&':  'Operasi bitwise AND.',
    '|':  'Operasi bitwise OR.',
    '^':  'Operasi bitwise XOR.',
    '~':  'Operasi bitwise NOT.',
}

def get_token_meaning(ttype, value, prev_ttype=None):
    if ttype == 'KEYWORD':
        return KEYWORD_MEANINGS.get(value, 'Kata kunci bawaan bahasa pemrograman.')
    if ttype == 'IDENTIFIER':
        if prev_ttype == 'DOT_OPERATOR':
            return f'Nama fungsi yang dipanggil dari objek sebelumnya: {value}()'
        return f'Nama yang dibuat programmer untuk variabel atau fungsi bernama "{value}".'
    if ttype == 'NUMBER':
        if '.' in value:
            return f'Bilangan desimal {value} — bisa untuk suhu, tegangan, atau nilai sensor.'
        return f'Bilangan bulat {value} — bisa untuk nomor pin, hitungan, atau waktu tunda.'
    if ttype == 'STRING':
        return f'Teks {value} — ditampilkan apa adanya, tidak dihitung sebagai angka.'
    if ttype == 'OPERATOR':
        return OPERATOR_MEANINGS.get(value, 'Simbol untuk operasi atau perbandingan.')
    if ttype == 'DOT_OPERATOR':
        return 'Penghubung untuk memanggil fungsi dari sebuah objek. Contoh: Serial.print()'
    if ttype == 'DELIMITER':
        delimiter_map = {
            ';': 'Tanda akhir satu baris perintah — seperti titik di akhir kalimat.',
            ',': 'Pemisah antara beberapa nilai atau parameter dalam fungsi.',
            '(': 'Pembuka — pengapit informasi atau parameter untuk sebuah perintah.',
            ')': 'Penutup — menutup pengapit informasi atau parameter.',
            '{': 'Pembuka blok kode — semua perintah di dalamnya satu kesatuan.',
            '}': 'Penutup blok kode — menandai akhir dari satu kesatuan perintah.',
            '[': 'Pembuka indeks atau elemen dalam array.',
            ']': 'Penutup indeks atau elemen dalam array.',
            ':': 'Tanda pembuka blok kode (digunakan di Python).',
        }
        return delimiter_map.get(value, 'Tanda baca untuk mengatur struktur kode.')
    if ttype == 'COMMENT':
        return 'Catatan penjelasan untuk programmer — sepenuhnya diabaikan oleh komputer.'
    if ttype == 'UNKNOWN':
        return f'⚠️ Karakter "{value}" tidak dikenal! Coba periksa apakah kamu salah ketik.'
    return f'Token: {value}'

def tokenize(code):
    tokens = []
    pos = 0
    while pos < len(code):
        match = None
        for token_type, pattern in TOKEN_RULES:
            regex = re.compile(pattern)
            match = regex.match(code, pos)
            if match:
                value = match.group(0)
                if token_type != 'WHITESPACE':
                    tokens.append((token_type, value))
                pos = match.end()
                break
        if not match:
            tokens.append(('UNKNOWN', code[pos]))
            pos += 1
    return tokens

if 'code_input' not in st.session_state:
    st.session_state.code_input = ''
if 'show_result' not in st.session_state:
    st.session_state.show_result = False

st.title("🔤 Tokenization Simulator")
st.subheader("Teknik Kompilasi — Lexical Analysis")
st.markdown("Masukkan source code Python atau C/Arduino lalu klik **Tokenize** untuk melihat hasil analisis token.")

code_input = st.text_area(
    "Masukkan Source Code:",
    height=200,
    placeholder='Contoh: int x = 5 + 3;',
    value=st.session_state.code_input,
    key=f"code_area_{st.session_state.get('_reset_key', 0)}"
)

col1, col2 = st.columns([1, 1])
with col1:
    tokenize_btn = st.button("Tokenize ▶", use_container_width=True)
with col2:
    reset_btn = st.button("🔄 Reset", use_container_width=True)

if reset_btn:
    st.session_state.code_input = ''
    st.session_state.show_result = False
    st.session_state['_reset_key'] = st.session_state.get('_reset_key', 0) + 1
    st.rerun()

if tokenize_btn:
    if code_input.strip():
        st.session_state.show_result = True
        st.session_state.code_input = code_input

if st.session_state.show_result and st.session_state.code_input.strip():
    tokens = tokenize(st.session_state.code_input)

    st.markdown("---")
    st.markdown("### 🎨 Hasil Tokenisasi")
    html = ""
    for ttype, val in tokens:
        color = COLORS.get(ttype, '#ffffff')
        html += f'<span style="background:{color};padding:3px 8px;margin:3px;border-radius:5px;font-weight:bold;display:inline-block">{val}</span>'
    st.markdown(html, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📋 Tabel Token")
    table_data = []
    prev_ttype = None
    for i, (t, v) in enumerate(tokens):
        table_data.append({
            "No": i + 1,
            "Token": v,
            "Tipe": t,
            "Arti Token": get_token_meaning(t, v, prev_ttype),
            "Penjelasan Tipe": TYPE_DESCRIPTIONS.get(t, '-')
        })
        prev_ttype = t
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 📊 Statistik Token")
    counts = Counter(t for t, v in tokens)
    stat_html = ""
    for ttype, count in counts.items():
        color = COLORS.get(ttype, '#ffffff')
        stat_html += f'<span style="background:{color};padding:3px 12px;margin:3px;border-radius:10px;display:inline-block"><b>{ttype}</b>: {count}</span>'
    st.markdown(stat_html, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📖 Legenda Tipe Token")
    for ttype, desc in TYPE_DESCRIPTIONS.items():
        color = COLORS.get(ttype, '#ffffff')
        st.markdown(f'<span style="background:{color};padding:2px 8px;border-radius:5px;font-weight:bold">{ttype}</span> — {desc}', unsafe_allow_html=True)

    unknown_tokens = [v for t, v in tokens if t == 'UNKNOWN']
    if unknown_tokens:
        st.error(f"⚠️ Ditemukan {len(unknown_tokens)} error token: {', '.join(unknown_tokens)}")
else:
    st.info("Masukkan source code terlebih dahulu!")
