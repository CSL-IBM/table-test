import streamlit as st
import pandas as pd

# 페이지 제목
st.title("CSV 파일 기반 질문 응답 시스템")

# 파일 업로드
uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type=["csv"])

if uploaded_file is not None:
    # CSV 파일 로드
    df = pd.read_csv(uploaded_file)
    
    # 질문 입력
    st.write("예시 질문:")
    st.write("'Collector가 John으로 filter 걸어'")
    st.write("'Collector가 Alice로 filter 걸어'")
    st.write("'Collector가 Bob으로 filter 걸어'")
    
    query = st.text_input("질문을 입력하세요:")

    # 질문에 따른 필터링 함수
    def filter_dataframe(query, df):
        # "Collector가" 이후의 값을 추출
        if "Collector가" in query and "으로 filter 걸어" in query:
            collector_name = query.split("Collector가")[1].split("으로 filter 걸어")[0].strip()
            filtered_df = df[df['Collector'] == collector_name]
            return filtered_df
        else:
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
