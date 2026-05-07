import streamlit as st
import re
import pandas as pd
from collections import Counter

TOKEN_RULES = [
    ('KEYWORD', r'\b(int|float|string|if|else|while|for|return|void|bool|true|false|print|def|class|import|from|True|False|None|and|or|not|in|is|elif|pass|break|continue|lambda|with|as|try|except|finally|raise|input|len|range|type|str|list|dict|tuple|set)\b'),
    ('NUMBER', r'\b\d+(\.\d+)?\b'),
    ('STRING', r'"[^"]*"|\'[^\']*\''),
    ('IDENTIFIER', r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
    ('OPERATOR', r'==|!=|<=|>=|\+=|-=|\*\*|[+\-\*/=<>!&|%^~]'),
    ('DELIMITER', r'[;,(){}[\]:]'),
    ('COMMENT', r'#[^\n]*|//[^\n]*'),
    ('WHITESPACE', r'\s+'),
]

COLORS = {
    'KEYWORD': '#FF6B6B',
    'IDENTIFIER': '#4ECDC4',
    'NUMBER': '#FFE66D',
    'STRING': '#A8E6CF',
    'OPERATOR': '#FF8B94',
    'DELIMITER': '#B4B4FF',
    'COMMENT': '#AAAAAA',
    'UNKNOWN': '#FF0000',
}

TYPE_DESCRIPTIONS = {
    'KEYWORD': 'Kata kunci bawaan bahasa pemrograman',
    'IDENTIFIER': 'Nama yang dibuat oleh programmer',
    'NUMBER': 'Nilai angka dalam kode',
    'STRING': 'Data teks yang diapit tanda kutip',
    'OPERATOR': 'Simbol untuk operasi atau perbandingan',
    'DELIMITER': 'Tanda baca pemisah bagian kode',
    'COMMENT': 'Teks penjelasan yang diabaikan kompiler',
    'UNKNOWN': '⚠️ Karakter tidak dikenal',
}

OPERATOR_MAP = {
    '+': 'Operator penjumlahan',
    '-': 'Operator pengurangan',
    '*': 'Operator perkalian',
    '/': 'Operator pembagian',
    '=': 'Operator penugasan (assignment)',
    '==': 'Operator perbandingan sama dengan',
    '!=': 'Operator perbandingan tidak sama dengan',
    '<': 'Operator lebih kecil dari',
    '>': 'Operator lebih besar dari',
    '<=': 'Operator lebih kecil atau sama dengan',
    '>=': 'Operator lebih besar atau sama dengan',
    '%': 'Operator sisa bagi (modulo)',
    '**': 'Operator perpangkatan',
    '+=': 'Operator tambah sekaligus assign',
    '-=': 'Operator kurang sekaligus assign',
}

KEYWORD_MAP = {
    'int': 'Tipe data bilangan bulat',
    'float': 'Tipe data bilangan desimal',
    'string': 'Tipe data teks',
    'str': 'Tipe data teks (Python)',
    'bool': 'Tipe data boolean (benar/salah)',
    'void': 'Fungsi tanpa nilai kembalian',
    'if': 'Percabangan — jika kondisi benar',
    'else': 'Percabangan — jika kondisi salah',
    'elif': 'Percabangan — kondisi alternatif',
    'while': 'Perulangan selama kondisi benar',
    'for': 'Perulangan dengan iterasi',
    'return': 'Mengembalikan nilai dari fungsi',
    'def': 'Mendefinisikan fungsi baru',
    'class': 'Mendefinisikan kelas baru',
    'import': 'Mengimpor modul atau library',
    'from': 'Mengimpor dari modul tertentu',
    'print': 'Menampilkan output ke layar',
    'input': 'Menerima input dari pengguna',
    'True': 'Nilai boolean benar',
    'False': 'Nilai boolean salah',
    'None': 'Nilai kosong / tidak ada nilai',
    'and': 'Operator logika DAN',
    'or': 'Operator logika ATAU',
    'not': 'Operator logika BUKAN',
    'in': 'Mengecek keanggotaan dalam koleksi',
    'is': 'Mengecek identitas objek',
    'pass': 'Pernyataan kosong, tidak melakukan apa-apa',
    'break': 'Menghentikan perulangan',
    'continue': 'Melanjutkan ke iterasi berikutnya',
    'lambda': 'Fungsi anonim satu baris',
    'with': 'Mengelola konteks (context manager)',
    'as': 'Memberi alias pada import atau context',
    'try': 'Mencoba menjalankan kode berisiko error',
    'except': 'Menangani error yang terjadi',
    'finally': 'Selalu dijalankan setelah try/except',
    'raise': 'Memunculkan error secara manual',
    'len': 'Fungsi untuk menghitung panjang data',
    'range': 'Fungsi untuk membuat urutan angka',
    'type': 'Fungsi untuk mengecek tipe data',
    'list': 'Tipe data list (daftar)',
    'dict': 'Tipe data dictionary (kamus)',
    'tuple': 'Tipe data tuple (daftar tetap)',
    'set': 'Tipe data set (himpunan unik)',
    'true': 'Nilai boolean benar (C/C++)',
    'false': 'Nilai boolean salah (C/C++)',
}

DELIMITER_MAP = {
    ';': 'Tanda akhir pernyataan',
    ',': 'Tanda pemisah elemen',
    ':': 'Tanda pembuka blok kode',
    '(': 'Tanda buka kurung',
    ')': 'Tanda tutup kurung',
    '{': 'Tanda buka kurung kurawal',
    '}': 'Tanda tutup kurung kurawal',
    '[': 'Tanda buka kurung siku',
    ']': 'Tanda tutup kurung siku',
}

def get_token_meaning(ttype, value):
    if ttype == 'NUMBER':
        if '.' in value:
            return f'Bilangan desimal (float): {value}'
        else:
            return f'Bilangan bulat (integer): {value}'
    if ttype == 'STRING':
        return f'Teks/string: {value}'
    if ttype == 'IDENTIFIER':
        return f'Nama variabel/fungsi: {value}'
    if ttype == 'COMMENT':
        return f'Komentar programmer: {value}'
    if ttype == 'UNKNOWN':
        return f'Karakter tidak dikenal: {value}'
    if ttype == 'OPERATOR':
        return OPERATOR_MAP.get(value, f'Operator: {value}')
    if ttype == 'KEYWORD':
        return KEYWORD_MAP.get(value, f'Kata kunci: {value}')
    if ttype == 'DELIMITER':
        return DELIMITER_MAP.get(value, f'Delimiter: {value}')
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
st.markdown("Masukkan source code Python atau C di bawah ini, lalu klik **Tokenize** untuk melihat hasil analisis token.")

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
    for i, (t, v) in enumerate(tokens):
        table_data.append({
            "No": i + 1,
            "Token": v,
            "Tipe": t,
            "Arti Token": get_token_meaning(t, v),
            "Penjelasan Tipe": TYPE_DESCRIPTIONS.get(t, '-')
        })
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