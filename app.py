import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import io

# 페이지 제목
st.title("Box 링크에서 CSV 데이터 추출")

# 고정된 Box 다운로드 링크
box_download_link = "https://ibm.box.com/s/3smxr9uzi7gxaz66x7jzlvve42b76qmf"

try:
    # 파일 다운로드
    response = requests.get(box_download_link)
    response.raise_for_status()  # HTTP 오류 발생 시 예외를 발생시킴

    # HTML 파일 파싱
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # HTML에서 데이터를 포함한 태그 찾기 (예: <pre>, <code>, <table> 등)
    # 이 예제에서는 <pre> 태그에 데이터가 있다고 가정합니다.
    data = soup.find('pre')  # 데이터가 포함된 태그 찾기
    
    if data:
        # 데이터가 문자열로 포함되어 있는 경우
        data_text = data.get_text()
        
        # 문자열을 CSV 형식으로 변환하기 위해 StringIO 사용
        file_content = io.StringIO(data_text)
        
        # CSV 데이터를 DataFrame으로 읽기
        df = pd.read_csv(
            file_content,
            delimiter=',',  # 데이터가 쉼표로 구분되어 있다고 가정
            encoding='utf-8'
        )
        
        # 열 이름을 딕셔너리의 키로 사용
        column_dict = {col: col for col in df.columns}

        # 예시 질문
        st.write("예시 질문:")
        st.write(f"'{column_dict.get('Category')}는 Red 이고, {column_dict.get('Collector')}는 John이야'")
        st.write(f"'{column_dict.get('CustomerName')}는 Alice 이고, {column_dict.get('InvoiceAmount')}는 5000이야'")
        st.write(f"'{column_dict.get('InvoiceDate')}는 2024-07-01 이고, {column_dict.get('ForecastCode')}는 FC2024야'")
        st.write(f"'{column_dict.get('DueDate')}가 2024-07-01 이후'")  # 날짜 조건 예시
        st.write(f"'{column_dict.get('InvoiceDate')}는 2024-07-01 이고, {column_dict.get('ForecastCode')}는 FCST야'")  # 복합 조건 예시

        query = st.text_input("질문을 입력하세요:")

        # 날짜 조건 처리 함수
        def parse_date_conditions(query):
            date_conditions = {}
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
                    if column in column_dict.values():  # 열 이름이 DataFrame에 존재하는지 확인
                        date_conditions[column] = (condition_type, date_value)
            
            return date_conditions

        # 조건 추출 함수
        def extract_conditions(query):
            conditions = {}
            date_conditions = parse_date_conditions(query)
            
            # 문자열 조건 추출
            patterns = {col: f"{col}는" for col in column_dict.values()}
            for pattern in patterns.values():
                if pattern in query:
                    column = next(col for col, pat in patterns.items() if pat == pattern)
                    try:
                        value = re.split(r'이야|이고', query.split(pattern)[1].strip())[0].strip()
                        if column in df.columns and column not in date_conditions:
                            conditions[column] = value
                    except IndexError:
                        st.warning(f"질문에서 '{column}'의 값을 추출할 수 없습니다.")
            
            return conditions, date_conditions

        # 질문에 따른 필터링 함수
        def filter_dataframe(query, df):
            patterns = {col: f"{col}는" for col in column_dict.values()}
            
            conditions, date_conditions = extract_conditions(query)
            
            filtered_df = df.copy()
            for column, value in conditions.items():
                if column in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df[column].astype(str).str.strip() == value]
            
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
        st.error("데이터를 찾을 수 없습니다.")

except requests.exceptions.RequestException as e:
    st.error(f"파일 다운로드 중 오류가 발생했습니다: {e}")
except pd.errors.ParserError as e:
    st.error(f"CSV 파일을 읽는 중 오류가 발생했습니다: {e}")
