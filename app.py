import streamlit as st
import pandas as pd
from datetime import datetime
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.foundation_models.extensions.langchain import WatsonxLLM
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
import sqlite3
import json  # JSON 응답 파싱을 위해 추가

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
    QUERY = f"""
    <<SYS>> 
    You are a powerful text-to-SQLite model, and your role is to answer questions about a database. You are given questions and context regarding the Invoice details table, which represents the detailed records of currently open invoices.
    The table name is {table_name} and corresponding columns are {columns}.
    You must run SQLite queries to the table to find an answer. Ensure your query does not include any non-SQLite syntax such as DATE_TRUNC or any use of backticks (`) or "```sql". Then, execute this query against the 'transactions' table and provide the answer.

    Guidelines:
    - Filter results using the current time zone: only when query specifies a specific date/time period. You should use ">=" or "<=" operators to filter the date or use "GROUP BY strftime('%m', date)" for grouping into month. Assume the date format in the database is 'YYYY-MM-DD'.
    - If the query result is [(None,)], run the SQLite query again to double check the answer. 
    - If a specific category is mentioned in the inquiry, such as 'Yellow', 'Red', or 'Green', use the "WHERE" condition in your SQL query to filter transactions by that category. For example, when asked for the complete invoice details for 'Green', use "FROM transactions WHERE category = 'Green'".
    - If not asked for a specific category, you shouldn't filter any category out. On the other hand, you should use "where" condition to do the filtering. When asked for the average amount in a category, use the SQLite query (AVG(amount) WHERE category = 'category_name').
    - When asked for 'highest' or 'lowest', use SQL function MAX() or MIN() respectively.
    - If a specific condition is provided in the inquiry, such as mentioning a specific Collector like 'John', 'David', 'Lisa', 'Mary', or 'Michael', and specifying a category such as 'Yellow', 'Red', or 'Green', use the "WHERE" clause in your SQL query to filter transactions accordingly. For example, if you need to fetch invoice details for 'John' and 'Green', you would use "FROM transactions WHERE Collector = 'John' AND category = 'Green'".

    Use the following format to answer the inquiry:

    Response: Result of the SQLite-compatible SQL query. If you know the transaction details such as the Category, Customer Name, Customer #, Inv. #, Inv. Amt, Inv. Date, Due Date, Forecast Code, Forecast Date, and Collector, mention it in your answer to be more clear.
    ---------------------- line break
    <br>
    ---------------------- line break
    <br>
    Explanation: Concise and succinct explanation on your thought process on how to get the final answer including the relevant transaction details such as the Category, Customer Name, Customer #, Inv. #, Inv. Amt, Inv. Date, Due Date, Forecast Code, Forecast Date, and Collector.
    ---------------------- line break
    <br>
    ---------------------- line break
    <br>
    Advice: Provide tips here, such as reminding users of progress for invoices with a due date within 10 days by comparing the due date with today.
    <</SYS>>

    [INST] 
    {query}
    [/INST]
    """
    response = llm(QUERY)
    # JSON 응답을 파싱하여 필요한 정보를 추출
    response_json = json.loads(response)
    sql_query = response_json["choices"][0]["text"].split("Response:")[1].split("---------------------- line break")[0].strip()
    return sql_query

def execute_sql_query(conn, query):
    try:
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
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
        
        # SQL 질의 실행 및 결과 표시
        filtered_df = execute_sql_query(conn, response)
        
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
