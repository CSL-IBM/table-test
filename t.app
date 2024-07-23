import streamlit as st
import pandas as pd

# CSV 파일 로드
csv_file_path = '/mnt/data/transactions.csv'  # 업로드된 CSV 파일 경로
df = pd.read_csv(csv_file_path)

# 페이지 제목
st.title("CSV 파일 기반 질문 응답 시스템")

# 질문 입력
query = st.text_input("질문을 입력하세요:")

# 질문에 따른 필터링 함수
def filter_dataframe(query, df):
    if "Collector가" in query and "인 인보이스를 알려줘" in query:
        collector_name = query.split("Collector가")[1].split("인 인보이스를 알려줘")[0].strip()
        filtered_df = df[df['Collector'] == collector_name]
        return filtered_df
    else:
        st.warning("지원하지 않는 질문 형식입니다.")
        return df

# 필터링된 데이터프레임
filtered_df = filter_dataframe(query, df)

# 필터링된 테이블 표시
st.write("필터링된 결과:")
st.dataframe(filtered_df)

# 원본 CSV 테이블 표시
st.write("원본 CSV 테이블:")
st.dataframe(df)
