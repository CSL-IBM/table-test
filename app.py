import streamlit as st
import pandas as pd

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

    query = st.text_input("질문을 입력하세요:")

    # 질문에 따른 필터링 함수
    def filter_dataframe(query, df):
        # 필터링할 열과 값을 추출하는 정규 표현식 패턴 정의
        import re
        
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
        
        # 조건을 저장할 딕셔너리
        conditions = {}
        
        for column, pattern in patterns.items():
            if pattern in query:
                try:
                    value = query.split(pattern)[1].split("이야")[0].strip()
                    if column in df.columns:
                        conditions[column] = value
                except IndexError:
                    st.warning(f"질문에서 '{column}'의 값을 추출할 수 없습니다.")
        
        if conditions:
            filtered_df = df.copy()
            for column, value in conditions.items():
                filtered_df = filtered_df[filtered_df[column] == value]
            return filtered_df
        
        st.warning("지원하지 않는 질문 형식입니다.")
        return pd.DataFrame()  # 빈 데이터프레임 반환

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
