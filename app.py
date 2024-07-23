import streamlit as st
import pandas as pd
from datetime import datetime
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.foundation_models.extensions.langchain import WatsonxLLM
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
import sqlite3

# Watsonx API 설정
my_credentials = {
    "url": "https://us-south.ml.cloud.ibm.com",
    "apikey": "hkEEsPjALuKUCakgA4IuR0SfTyVC9uT0qlQpA15Rcy8U"  # 실제 API 키로 교체
}

params = {
    GenParams.MAX_NEW_TOKENS: 1000,
    GenParams.TEMPERATURE: 0.1,
}

LLAMA2_model = Model(
    model_id='meta-llama/llama-2-70b-chat',
    credentials=my_credentials,
    params=params,
    project_id="16acfdcc-378f-4268-a2f4-ba04ca7eca08"  # 실제 프로젝트 ID로 교체
)

llm = WatsonxLLM(LLAMA2_model)

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

def create_sqlite_table_from_df(df, table_name='transactions'):
    conn = sqlite3.connect(':memory:')
    df.to_sql(table_name, conn, index=False, if_exists='replace')
    return conn

def call_watsonx_api(query, table_name, columns):
    # QUERY 생성
    QUERY = f"""
    <</SYS>>

    [INST]
    To ensure the generated SQL queries follow best practices for SQLite, please adhere to the following guidelines:
    1. **Identify the Table and Columns**:
       - Ensure the table being queried is `{table_name}`.
       - Use the provided columns `{columns}` for querying.

    2. **Filter by Specific Conditions**:
       - Apply the `WHERE` clause for filtering based on specific conditions such as Collector or category.
       - Example: To filter transactions for 'John' in the 'Green' category, use:
         ```sql
         SELECT * FROM {table_name} WHERE Collector = 'John' AND category = 'Green';
         ```

    3. **Date Filtering and Grouping**:
       - Use `>=` and `<=` operators for date filtering.
         ```sql
         SELECT * FROM {table_name} WHERE date >= '2023-01-01' AND date <= '2023-12-31';
         ```
       - To group by month, use `GROUP BY strftime('%m', date)`:
         ```sql
         SELECT strftime('%m', date) AS month, COUNT(*) FROM {table_name} GROUP BY month;
         ```

    4. **Query Execution**:
       - Ensure the query does not include non-SQLite syntax such as `DATE_TRUNC` or backticks.
       - Execute the query to retrieve results.

    5. **Check and Validate Results**:
       - If the query result is `[(None,)]`, re-run the query to verify.

    Please generate an SQL query based on the following input query:
    {query}
    [/INST]
    """

    # LLM 응답 받기
    response = llm(QUERY)

    # 응답을 텍스트 형식으로 파싱하여 필요한 정보를 추출
    try:
        response_text = response.split("Response:")[1].split("---------------------- line break")[0].strip()
    except IndexError:
        st.error("Unexpected response format from the LLM.")
        return ""

    # 가이드라인을 적용하여 SQL 쿼리 검토 및 조정
    def apply_guidelines(sql_query):
        # 비-SQLite 문법 제거
        sql_query = sql_query.replace('DATE_TRUNC', '')  # DATE_TRUNC 제거
        sql_query = sql_query.replace('`', '')           # 백틱 제거

        # 특정 조건에 따라 필터 추가
        if 'Collector' in sql_query and 'category' in sql_query:
            if 'date' in sql_query:
                # 날짜 필터링이 >= 및 <= 연산자를 사용하는지 확인
                sql_query = sql_query.replace('BETWEEN', '>=').replace('AND', 'AND').replace('TO', '<=')

        # 월별 그룹화 확인 및 수정
        if 'GROUP BY' in sql_query:
            if 'strftime' not in sql_query:
                sql_query = sql_query.replace('GROUP BY', 'GROUP BY strftime(\'%m\', date)')

        return sql_query

    # 가이드라인을 적용하여 SQL 쿼리 수정
    sql_query = apply_guidelines(response_text)
    return sql_query

def execute_sql_query(conn, query):
    try:
        # SQL 쿼리를 실행하고 결과를 DataFrame으로 반환
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        # 오류가 발생한 경우 메시지 출력 및 빈 DataFrame 반환
        st.error(f"SQL query failed: {e}")
        return pd.DataFrame()

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
        conn = create_sqlite_table_from_df(df)
        columns = ', '.join(df.columns)
        response = call_watsonx_api(query, 'transactions', columns)
        
        if response:
            # SQL 질의 실행 및 결과 표시
            filtered_df = execute_sql_query(conn, response)
            
            if filtered_df.empty:
                st.warning("조건에 맞는 데이터가 없습니다.")
            
            st.write("필터링된 결과:")
            st.dataframe(filtered_df)
        else:
            st.warning("유효한 SQL 쿼리를 생성할 수 없습니다.")
        
    else:
        st.write("질문을 입력하세요.")

    # 원본 CSV 테이블 표시
    st.write("원본 CSV 테이블:")
    st.dataframe(df)
else:
    st.warning("CSV 파일을 업로드하세요.")
