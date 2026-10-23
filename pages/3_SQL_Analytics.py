"""SQL Analytics page: run the 25 questions or a custom read-only query."""
import streamlit as st

from sql.queries import QUERIES
from utils.db_connection import run_readonly_query

st.set_page_config(page_title="SQL Analytics", page_icon="🧮", layout="wide")
st.title("🧮 SQL Analytics")
st.caption("Sample data in the database is synthetic, generated for SQL practice.")

tab_questions, tab_custom = st.tabs(["25 Questions", "Custom SQL"])


def show_result(df, key: str) -> None:
    """Display a result table, a CSV download and an optional bar chart."""
    st.write(f"**{len(df)} rows**")
    st.dataframe(df, hide_index=True)
    if df.empty:
        return
    st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8"),
                       file_name=f"{key}.csv", mime="text/csv", key=f"dl_{key}")
    numeric_cols = df.select_dtypes("number").columns.tolist()
    if numeric_cols and st.checkbox("Show bar chart", key=f"chart_{key}"):
        x_col = st.selectbox("X axis (labels)", df.columns.tolist(), key=f"x_{key}")
        y_col = st.selectbox("Y axis (numbers)", numeric_cols, key=f"y_{key}")
        chart_df = df.head(30).set_index(x_col)[[y_col]]
        st.bar_chart(chart_df)


with tab_questions:
    levels = ["All"] + sorted({q["level"] for q in QUERIES},
                              key=["Beginner", "Intermediate", "Advanced"].index)
    level = st.radio("Difficulty", levels, horizontal=True)
    shown = [q for q in QUERIES if level == "All" or q["level"] == level]
    labels = {f"Q{q['id']}. {q['title']}": q for q in shown}
    choice = st.selectbox("Choose a question", list(labels))
    query = labels[choice]

    st.markdown(f"**Question:** {query['question']}")
    with st.expander("Show SQL"):
        st.code(query["sql"].strip(), language="sql")

    if st.button("Run query", type="primary", key="run_q"):
        try:
            with st.spinner("Running..."):
                result = run_readonly_query(query["sql"])
            show_result(result, f"q{query['id']}")
        except Exception as exc:
            st.error(f"The query failed: {exc}")

with tab_custom:
    st.write("Type your own **SELECT** query. Only reading is allowed (the database is opened read-only).")
    st.caption("Tables: teams, players, venues, series, matches, innings, batting_performances, "
               "bowling_performances, partnerships, player_career_stats. "
               "Views: v_match_results, v_batting_detail.")
    sql_text = st.text_area("SQL", value="SELECT * FROM players LIMIT 10;", height=160)
    if st.button("Run custom query", key="run_custom"):
        try:
            show_result(run_readonly_query(sql_text), "custom")
        except ValueError as exc:
            st.warning(str(exc))
        except Exception as exc:
            st.error(f"SQL error: {exc}")
