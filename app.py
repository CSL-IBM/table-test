import streamlit as st
import pandas as pd
from datetime import datetime
import requests  # HTTP 요청을 보내기 위한 모듈 추가

# Watsonx API 설정
WATSONX_API_URL = 'https://api.watsonx.ibm.com/v1/your-endpoint'  # 실제 엔드포인트로 교체
WATSONX_API_KEY = 'your-api-key'  # 실제 API 키로 교체

# 페이지 제목
st.title("CSV 파일 기반 질문 응답 시스템")

# 열 이름 변수 정의
CATEGORY = "Category"
CUSTOMER_NAME = "CustomerName"
CUSTOMER_NUMBER = "CustomerNumber"
INVOICE_NUMBER = "InvoiceNumber"
INVOICE_AMOUNT = "InvoiceAmount"
INVOICE_DATE = "InvoiceDate"
DUE_DATE = "DueDate"
FORECAST_CODE = "ForecastCode"
FORECAST_DATE = "ForecastDate"
COLLECTOR = "Collector"

# 파일 업로드
uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type=["csv"])

def call_watsonx_api(query):
    headers = {
        'Authorization': f'Bearer {WATSONX_API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        'query': query,
        'context': {
            'data': 'contextual information if needed'
        }
    }
    response = requests.post(WATSONX_API_URL, headers=headers, json=payload)
    response.raise_for_status()  # API 요청 실패 시 예외 발생
    return response.json()

if uploaded_file is not None:
    # CSV 파일 로드
    df = pd.read_csv(uploaded_file)
    
    # 예시 질문
    st.write("예시 질문:")
    st.write(f"'{CATEGORY}는 Red 이고, {COLLECTOR}는 John이야'")
    st.write(f"'{CUSTOMER_NAME}는 Alice 이고, {INVOICE_AMOUNT}는 5000이야'")
    st.write(f"'{INVOICE_DATE}는 2024-07-01 이고, {FORECAST_CODE}는 FC2024야'")
    st.write(f"'{DUE_DATE}가 2024-07-01 이후'")  # 날짜 조건 예시
    st.write(f"'{INVOICE_DATE}는 2024-07-01 이고, {FORECAST_CODE}는 FCST야'")  # 복합 조건 예시

    query = st.text_input("질문을 입력하세요:")

    if query:
        # Watsonx API를 호출하여 질문 분석
        response = call_watsonx_api(query)
        extracted_conditions = response.get('conditions', {})
        date_conditions = response.get('date_conditions', {})
        
        # 필터링
        filtered_df = df.copy()
        for column, value in extracted_conditions.items():
            if column in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[column].astype(str).str.strip() == value]
        
        # 날짜 필터링
        for column, (condition_type, date_value) in date_conditions.items():
            date_value = datetime.strptime(date_value, '%Y-%m-%d')
            if column in filtered_df.columns:
                if condition_type == 'after':
                    filtered_df = filtered_df[filtered_df[column].apply(pd.to_datetime, errors='coerce') > date_value]
                elif condition_type == 'before':
                    filtered_df = filtered_df[filtered_df[column].apply(pd.to_datetime, errors='coerce') < date_value]
                elif condition_type == 'on':
                    filtered_df = filtered_df[filtered_df[column].apply(pd.to_datetime, errors='coerce') == date_value]
        
        if filtered_df.empty:
            st.warning("조건에 맞는 데이터가 없습니다.")
        
        st.write("필터링된 결과:")
        st.dataframe(filtered_df)
    else:
        st.write("질문을 입력하세요.")

    # 원본 CSV 테이블 표시
    st.write("원본 CSV 테이블:")
    st.dataframe(df)
else:
    st.warning("CSV 파일을 업로드하세요.")
