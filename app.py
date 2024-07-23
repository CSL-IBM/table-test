import streamlit as st
import sqlite3
import requests
import pandas as pd
from io import StringIO
from datetime import datetime
import pytz
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.foundation_models.extensions.langchain import WatsonxLLM
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
from langchain_experimental.sql import SQLDatabaseChain
from sqlalchemy import create_engine, inspect

# Watsonx 모델 설정
my_credentials = {
    "url": "https://us-south.ml.cloud.ibm.com",
    "apikey": "hkEEsPjALuKUCakgA4IuR0SfTyVC9uT0qlQpA15Rcy8U"
}

params = {
    GenParams.MAX_NEW_TOKENS: 1000,
    GenParams.TEMPERATURE: 0.1,
}

LLAMA2_model = Model(
    model_id='meta-llama/llama-2-70b-chat',
    credentials=my_credentials,
    params=params,
    project_id="16acfdcc-378f-4268-a2f4-ba04ca7eca08",
)

llm = WatsonxLLM(LLAMA2_model)

# Streamlit 애플리케이션
def init_db():
    # Create SQLite engine
    engine = create_engine('sqlite:///history.db')
    conn = sqlite3.connect('history.db', check_same_thread=False)

    # Drop table if exists and create it
    conn.execute("DROP TABLE IF EXISTS transactions")
    conn.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Category TEXT,
            CustomerName TEXT,
            CustomerNumber TEXT,
            InvoiceNumber TEXT,
            InvoiceAmount INTEGER,
            InvoiceDate DATE,
            DueDate DATE,
            ForecastCode TEXT,
            ForecastDate DATE,
            Collector TEXT
        );
    """)

    # Load CSV data from GitHub
    github_csv_url = "https://raw.githubusercontent.com/CSL-IBM/table-test/main/transactions.csv"
    response = requests.get(github_csv_url)
    response.raise_for_status()
    csv_data = response.content.decode('utf-8')
    data = pd.read_csv(StringIO(csv_data))

    # Rename columns if necessary to match the SQL table schema
    column_mapping = {
        'No': 'id',  # Example mapping, adjust as necessary
        'Category': 'Category',
        'CustomerName': 'CustomerName',
        'CustomerNumber': 'CustomerNumber',
        'InvoiceNumber': 'InvoiceNumber',
        'InvoiceAmount': 'InvoiceAmount',
        'InvoiceDate': 'InvoiceDate',
        'DueDate': 'DueDate',
        'ForecastCode': 'ForecastCode',
        'ForecastDate': 'ForecastDate',
        'Collector': 'Collector'
    }
    data.rename(columns=column_mapping, inplace=True)

    # Convert date columns to string format
    date_columns = ['InvoiceDate', 'DueDate', 'ForecastDate']
    for col in date_columns:
        if col in data.columns:
            data[col] = pd.to_datetime(data[col], errors='coerce').dt.strftime('%Y-%m-%d')

    # Write data to SQL
    try:
        data.to_sql('transactions', engine, if_exists='append', index=False)
    except Exception as e:
        st.error(f"Error occurred while writing data to SQL: {e}")

    conn.commit()
    conn.close()

def get_table_columns(table_name):
    engine = create_engine('sqlite:///history.db')
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return columns

table_name = 'transactions'
columns = get_table_columns(table_name)

QUERY = """
<<SYS>> 
You are a powerful text-to-SQLite model, and your role is to answer questions about a database. You are given questions and context regarding the Invoice details table, which represents the detailed records of currently open invoices.
The table name is {table_name} and corresponding columns are {columns}.
You must run SQLite queries to the table to find an answer. Ensure your query does not include any non-SQLite syntax such as DATE_TRUNC or any use of backticks (`) or "```sql". Then, execute this query against the 'transactions' table and provide the answer.

Guidelines:
- Filter results using the current time zone: {time} only when query specifies a specific date/time period. You should use ">=" or "<=" operators to filter the date or use "GROUP BY strftime('%m', date)" for grouping into month.  Assume the date format in the database is 'YYYY-MM-DD'.
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
{inquiry}
[/INST]
"""

# Initialize database
init_db()

# Create the database chain
db_chain = SQLDatabaseChain.from_llm(llm, SQLDatabase.from_uri("sqlite:///history.db"), verbose=True)

st.title('Invoice Query System')

# Input form for user inquiry
with st.form(key='inquiry_form'):
    inquiry = st.text_area('Enter your inquiry:')
    submit_button = st.form_submit_button(label='Submit')

    if submit_button:
        # Handle transaction queries
        prompt = QUERY.format(
            table_name=table_name,
            columns=', '.join(columns),
            time=datetime.now(pytz.timezone('America/New_York')).strftime('%Y-%m-%d %H:%M:%S'),
            inquiry=inquiry
        )
        response = db_chain.run(prompt)

        # Display response
        st.write("Response:", response)

        # Fetch transactions data to display
        conn = sqlite3.connect('history.db', check_same_thread=False)
        cursor = conn.execute('SELECT * FROM transactions')
        data = cursor.fetchall()
        conn.close()

        # Display the transactions table
        st.write("Transactions Table:")
        st.dataframe(pd.DataFrame(data, columns=columns))
