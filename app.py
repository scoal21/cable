import streamlit as st
import pandas as pd
import gspread
import json

# 페이지 기본 설정
st.set_page_config(layout="wide", page_title="(의장1부 송운) 케이블 재고 관리")

# --- 1. 구글 시트 연결 (최신 방식) ---
@st.cache_resource
def init_connection():
    # 금고(Secrets)에서 열쇠 꺼내기
    creds_dict = json.loads(st.secrets["gcp_json"])
    
    # ⭐️ 핵심 해결책: 꼬여버린 줄바꿈(\n) 기호를 정상적인 엔터로 강제 변환!
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
    # gspread 최신 방식으로 즉시 연결
    client = gspread.service_account_from_dict(creds_dict)
    return client

client = init_connection()

# ⚠️ 여기에 본인의 구글 스프레드시트 주소를 홑따옴표/쌍따옴표 안에 꼭 넣어주세요!
SHEET_URL = "https://docs.google.com/spreadsheets/d/1EU2_T8CFF8XK5b4jsynv2KuiMcsMViRtWM9BPyZy5e0/edit?gid=0#gid=0"
sheet = client.open_by_url(SHEET_URL).sheet1

# --- 2. 데이터 불러오기 / 저장하기 함수 ---
def load_data():
    try:
        return sheet.get_all_records()
    except:
        return []

def save_data(data):
    sheet.clear()
    header = ["name", "spec", "qty"]
    if not data:
        sheet.update(range_name="A1", values=[header])
        return
        
    rows = [header]
    for item in data:
        rows.append([item.get("name", ""), item.get("spec", ""), int(item.get("qty", 0))])
    
    sheet.update(range_name="A1", values=rows)

# 앱 실행 시 구글 시트에서 최신 데이터 가져오기
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# --- 메인 화면 ---
st.title("⚓ (의장1부 송운) 케이블 재고 관리 시스템")

# 다중 접속을 위한 동기화 버튼
if st.button("🔄 최신 데이터 구글시트에서 불러오기"):
    st.session_state.data = load_data()
    st.success("최신 데이터로 업데이트 되었습니다!")

st.markdown("### 🔍 검색")
search_term = st.text_input("케이블 명 또는 특이사항 검색", placeholder="검색어를 입력하세요...")

# 신규 등록 (사이드바)
with st.sidebar:
    st.header("📝 신규 자재 등록")
    with st.form("add_form", clear_on_submit=True):
        new_name = st.text_input("케이블 명")
        new_spec = st.text_input("특이사항")
        new_qty = st.number_input("초기 수량", min_value=0, value=0)
        submitted = st.form_submit_button("등록")
        
        if submitted:
            if new_name:
                new_item = {"name": new_name, "spec": new_spec, "qty": int(new_qty)}
                st.session_state.data.append(new_item)
                save_data(st.session_state.data) # 구글 시트에 즉시 저장
                st.success(f"'{new_name}' 등록 완료!")
                st.rerun()
            else:
                st.error("케이블 명을 입력해주세요.")

# 재고 리스트 표시 (헤더)
st.divider()
col1, col2, col3, col4, col5 = st.columns([2, 3, 1, 2, 1])
with col1: st.markdown("**케이블 명**")
with col2: st.markdown("**특이사항**")
with col3: st.markdown("**현재 재고**")
with col4: st.markdown("**입/출고**")
with col5: st.markdown("**관리**")
st.divider()

filtered_indices = []
for i, item in enumerate(st.session_state.data):
    if search_term:
        if (search_term.lower() in str(item.get('name', '')).lower()) or (search_term.lower() in str(item.get('spec', '')).lower()):
            filtered_indices.append(i)
    else:
        filtered_indices.append(i)

if not filtered_indices and search_term:
    st.warning("해당하는 사양이 없습니다.")

for i in filtered_indices:
    item = st.session_state.data[i]
    c1, c2, c3, c4, c5 = st.columns([2, 3, 1, 2, 1])
    
    with c1: st.write(f"**{item.get('name', '')}**")
    with c2: st.write(item.get('spec', ''))
    with c3: st.markdown(f"<h4 style='color: blue; margin:0;'>{item.get('qty', 0)}</h4>", unsafe_allow_html=True)
        
    with c4:
        change_val = st.number_input("수량", min_value=0, key=f"num_{i}", label_visibility="collapsed")
        btn_col1, btn_col2 = st.columns(2)
        if btn_col1.button("➕", key=f"add_{i}", use_container_width=True):
            if change_val > 0:
                st.session_state.data[i]['qty'] += int(change_val)
                save_data(st.session_state.data) # 구글 시트에 즉시 반영
                st.rerun()
                
        if btn_col2.button("➖", key=f"sub_{i}", use_container_width=True):
            if change_val > 0:
                st.session_state.data[i]['qty'] -= int(change_val)
                save_data(st.session_state.data) # 구글 시트에 즉시 반영
                st.rerun()

    with c5:
        if st.button("🗑️", key=f"del_{i}"):
            del st.session_state.data[i]
            save_data(st.session_state.data) # 구글 시트에서도 즉시 삭제
            st.rerun()
            
    st.divider()
