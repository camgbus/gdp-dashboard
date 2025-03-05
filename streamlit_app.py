import os
import sqlite3
import streamlit as st
import pandas as pd
import math
from pathlib import Path
from local.paths import db_path

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Head CT Report Findings',
    page_icon=':brain:', # This is an emoji shortcode. Could be a URL too.
)

# Set the title that appears at the top of the page.
'''
# :brain: Head CT Report Findings

Common findings identified in head CT radiology reports.
'''

# Add some spacing
''
''

@st.cache_data
def get_data():
    
    # Collect all reports_ into one data frame
    report_dbs = [f for f in os.listdir(db_path) if f.startswith('reports_') and f.endswith('.db')]
    dfs = []
    for db in report_dbs:
        db_path_full = os.path.join(db_path, db)
        conn = sqlite3.connect(db_path_full)
        df = pd.read_sql_query("SELECT * FROM reports", conn)
        conn.close()
        dfs.append(df)
    reports_df = pd.concat(dfs, ignore_index=True)

    # Collect all annotations
    annotations = {"artifacts": "artifacts.db", "findings": "findings.db", "devices": "medical_devices.db"}
    annotations_dfs = {}

    for annotation, db_name in annotations.items():
        db_file_path = os.path.join(db_path, db_name)
        conn = sqlite3.connect(db_file_path)
        table_query = "SELECT name FROM sqlite_master WHERE type='table';"
        table_name = pd.read_sql_query(table_query, conn)["name"].iloc[0]
        df = pd.read_sql_query(f"SELECT * FROM {table_name};", conn)
        conn.close()
        annotations_dfs[annotation] = df

    return reports_df, annotations_dfs["findings"], annotations_dfs["artifacts"], annotations_dfs["devices"]

reports_df, findings_df, artifacts_df, devices_df = get_data()

annotated_reports = reports_df[reports_df["is_reviewed"] == 1]
nr_annotated_reports = len(annotated_reports) + 1
st.header(f'Annotated reports', divider='gray')
progress_bar = st.progress(0)
progress_bar.progress(nr_annotated_reports / 150)
status_text = st.empty()
status_text.text(f"Progress: {nr_annotated_reports}/{150}")

st.header(f'Present findings', divider='gray')


findings_df['finding'] = findings_df['finding'].str.lower()
words_to_remove = ['tiny', 'left', 'right', 'posterior', 'thin', 'mild']
findings_df['finding'] = findings_df['finding'].apply(lambda x: ' '.join([word for word in x.split() if word.lower() not in words_to_remove]))


findings = findings_df[findings_df["is_present"] == 1]["finding"].value_counts()
present_findings = pd.DataFrame(findings).rename(columns={"finding": "count"})
st.bar_chart(present_findings)

st.header(f'Explicitly missing findings', divider='gray')
missing_findings = findings_df[findings_df["is_present"] == 0]["finding"].value_counts()
st.bar_chart(missing_findings)

st.header(f'Commonly used medical devices', divider='gray')
devices_df = devices_df.rename(columns={"catheter": "device"})
# Split rows containing 'and' in device column into separate rows
split_rows = []
for idx, row in devices_df.iterrows():
    if ' and ' in str(row['device']):
        devices = row['device'].split(' and ')
        for device in devices:
            new_row = row.copy()
            new_row['device'] = device.strip()
            split_rows.append(new_row)
    else:
        split_rows.append(row)
devices_df = pd.DataFrame(split_rows)
# Replace 'tube' with 'line' in device column
devices_df['device'] = devices_df['device'].str.replace('enteric', 'enteric tube')
devices_df['device'] = devices_df['device'].str.replace('endotracheal tubes', 'endotracheal tube')



devices_df['device'] = devices_df['device'].str.lower()
words_to_remove = ['left', 'right', 'frontal', 'posterior', 'multiple']
devices_df['device'] = devices_df['device'].apply(lambda x: ' '.join([word for word in x.split() if word.lower() not in words_to_remove]))
devices = devices_df["device"].value_counts()
st.bar_chart(devices)

st.header(f'Ocurring artifacts', divider='gray')
artifacts_df['artifact'] = artifacts_df['artifact'].str.lower()
words_to_remove = ['mild', 'artifact']
artifacts_df['artifact'] = artifacts_df['artifact'].apply(lambda x: ' '.join([word for word in x.split() if word.lower() not in words_to_remove]))

artifacts = artifacts_df["artifact"].value_counts()
st.bar_chart(artifacts)
