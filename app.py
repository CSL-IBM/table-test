import streamlit as st
import pandas as pd
from datetime import datetime
import re  # 정규 표현식 모듈 추가

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

    # 날짜 조건 처리 함수
    def parse_date_conditions(query):
        date_conditions = {}
        # 날짜 이후, 이전, 특정 날짜에 대한 패턴 정의
        date_patterns = [
            (r'(\w+)가 (\d{4}-\d{2}-\d{2}) 이후', 'after'),
            (r'(\w+)가 (\d{4}-\d{2}-\d{2}) 이전', 'before'),
            (r'(\w+)가 (\d{4}-\d{2}-\d{2})', 'on')
        ]
        
        for pattern, condition_type in date_patterns:
            match = re.search(pattern, query)
            if match:
                column = match.group(1)
                date_value = match.group(2)
                if column in [DUE_DATE, INVOICE_DATE, FORECAST_DATE]:  # 날짜 열만 필터링
                    date_conditions[column] = (condition_type, date_value)
        
        return date_conditions

    # 조건 추출 함수
    def extract_conditions(query):
        # 필터링할 열과 값을 추출하는 정규 표현식 패턴 정의
        patterns = {
            CATEGORY: f"{CATEGORY}는",
            CUSTOMER_NAME: f"{CUSTOMER_NAME}는",
            CUSTOMER_NUMBER: f"{CUSTOMER_NUMBER}는",
            INVOICE_NUMBER: f"{INVOICE_NUMBER}는",
            INVOICE_AMOUNT: f"{INVOICE_AMOUNT}는",
            INVOICE_DATE: f"{INVOICE_DATE}는",
            DUE_DATE: f"{DUE_DATE}는",
            FORECAST_CODE: f"{FORECAST_CODE}는",
            FORECAST_DATE: f"{FORECAST_DATE}는",
            COLLECTOR: f"{COLLECTOR}는"
        }
        
        conditions = {}
        date_conditions = parse_date_conditions(query)
        
        # 조건 추출
        for column, pattern in patterns.items():
            if pattern in query:
                try:
                    value = re.split(r'이야|이고', query.split(pattern)[1].strip())[0].strip()
                    if column in df.columns and column not in date_conditions:
                        conditions[column] = value
                except IndexError:
                    st.warning(f"질문에서 '{column}'의 값을 추출할 수 없습니다.")
        
        return conditions, date_conditions

    # 질문에 따른 필터링 함수
    def filter_dataframe(query, df):
        conditions, date_conditions = extract_conditions(query)
        
        # 필터링
        filtered_df = df.copy()
        for column, value in conditions.items():
            filtered_df = filtered_df[filtered_df[column].astype(str).str.strip() == value]
        
        # 날짜 필터링
        for column, (condition_type, date_value) in date_conditions.items():
            date_value = datetime.strptime(date_value, '%Y-%m-%d')
            if condition_type == 'after':
                filtered_df = filtered_df[filtered_df[column].apply(pd.to_datetime, errors='coerce') > date_value]
            elif condition_type == 'before':
                filtered_df = filtered_df[filtered_df[column].apply(pd.to_datetime, errors='coerce') < date_value]
            elif condition_type == 'on':
                filtered_df = filtered_df[filtered_df[column].apply(pd.to_datetime, errors='coerce') == date_value]
        
        if filtered_df.empty:
            st.warning("조건에 맞는 데이터가 없습니다.")
        
        return filtered_df

    if query:
        # 필터링된 데이터프레임
        filtered_df = filter_dataframe(query, df)

        # 필터링된 테이블 표시
        st.write("필터링된 결과:")
        st.dataframe(filtered_df)
    else:
        st.write("질문을 입력하세요.")

    # 원본 CSV 테이블 표시
    st.write("원본 CSV 테이블:")
    st.dataframe(df)
else:
    st.warning("CSV 파일을 업로드하세요.")
