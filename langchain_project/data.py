from gemini_key import GEMINI_API_KEY
from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import time
import json
import mysql.connector
import os
import re

os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.6)

def ask_query(data, query):
    if query:
        if isinstance(data, pd.DataFrame):
            if re.search(r"(visualize|bar|line|pie)", query, re.IGNORECASE):
                columns = data.columns
                match = re.search(r"(\w+)\s+(bar|line|pie)", query, re.IGNORECASE)
                if match:
                    column = match.group(1).strip() # added strip to remove extra spaces
                    chart_type = match.group(2).lower()
                    if column in columns:
                        if chart_type == "bar":
                            try:
                                st.bar_chart(data[column].value_counts())
                            except Exception as e:
                                st.write(f"Error creating bar chart: {e}")
                        elif chart_type == "pie":
                            try:
                                fig1, ax1 = plt.subplots()
                                ax1.pie(data[column].value_counts(), labels=data[column].value_counts().index, autopct='%1.1f%%')
                                st.pyplot(fig1)
                            except Exception as e:
                                st.write(f"Error creating pie chart: {e}")
                        elif chart_type == "line":
                            if pd.api.types.is_numeric_dtype(data[column]):
                                try:
                                    st.line_chart(data[column])
                                except Exception as e:
                                    st.write(f"Error creating line chart: {e}")
                            else:
                                st.write("Line charts only work with numbers.")
                    else:
                        st.write(f"Column '{column}' not found. Available columns: {', '.join(columns)}")
                else:
                    st.write("Please specify column and chart type.")
            elif re.search(r"(view|show|display)", query, re.IGNORECASE):
                st.dataframe(data)
            elif re.search(r"(remove nan|dropna)", query, re.IGNORECASE):
                cleaned_df = data.dropna()
                st.dataframe(cleaned_df)
            elif re.search(r"(describe|analysis|analyze)", query, re.IGNORECASE):
                st.dataframe(data.describe())
            elif re.search(r"(save to sql|save)", query, re.IGNORECASE):
                table_name = st.text_input("Enter table name:")
                if st.button("Save to SQL") and table_name:
                    try:
                        conn = mysql.connector.connect(host="localhost", user="root", password="", database="langchain_data")
                        cursor = conn.cursor()
                        for index, row in data.iterrows():
                            placeholders = ", ".join(["%s"] * len(row))
                            columns = ", ".join(data.columns)
                            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                            cursor.execute(sql, tuple(row))
                        conn.commit()
                        st.write("Data saved to SQL!")
                    except Exception as e:
                        st.write(f"Error saving to SQL: {e}")
                    finally:
                        if 'conn' in locals() and conn.is_connected():
                            cursor.close()
                            conn.close()
            else:
                data_string = data.to_csv(index=False)
                prompt = f"Given data:\n{data_string}\n\nAnswer: {query} "
                response = llm.invoke(prompt).content
                st.write("Answer:", response)
                time.sleep(1)
        else:
            prompt = f"Given data:\n{data}\n\nAnswer: {query}"
            response = llm.invoke(prompt).content
            st.write("Answer:", response)
            time.sleep(1)

st.title("Data analysis")
uploaded_file = st.file_uploader("Upload a file", type=["csv", "xlsx", "txt", "json"])

if uploaded_file is not None:
    try:
        if uploaded_file.type == "text/csv" or uploaded_file.type == "application/vnd.ms-excel" or uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            try:
                data = pd.read_csv(uploaded_file)
            except:
                data = pd.read_excel(uploaded_file)
        elif uploaded_file.type == "text/plain":
            data = uploaded_file.getvalue().decode("utf-8")
        elif uploaded_file.type == "application/json":
            data = pd.DataFrame(json.load(uploaded_file))
        else:
            st.write("Unsupported file type.")
            data = None
    except Exception as e:
        st.write(f"Error loading file: {e}")
        data = None

    if data is not None:
        query = st.text_input("Enter your query:")
        if st.button("Execute Query"):
            ask_query(data, query)