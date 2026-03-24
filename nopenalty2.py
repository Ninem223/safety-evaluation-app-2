import streamlit as st
import pandas as pd

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Medical Safety Eval - Harm & Media Version", layout="wide")

# 2. DATA LOADING
@st.cache_data(ttl=600)
def load_questions():
    sheet_id = "1vpSd5TYYw9VUs43L4Hg5iU7nAlrTS7GBXFm2PPu43g4"
    sheet_name = "Questions"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        return pd.read_csv(url)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

df = load_questions()

# 3. SESSION STATE
if 'q_idx' not in st.session_state: st.session_state.q_idx = 0
if 'ans_idx' not in st.session_state: st.session_state.ans_idx = 1
if 'results' not in st.session_state: st.session_state.results = []
if 'done' not in st.session_state: st.session_state.done = False

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("Evaluation Controls")
    
    if st.button("⬅️ Undo / Go Back", use_container_width=True):
        if len(st.session_state.results) > 0:
            st.session_state.results.pop()
            if st.session_state.ans_idx > 1:
                st.session_state.ans_idx -= 1
            else:
                st.session_state.ans_idx = 4
                st.session_state.q_idx -= 1
            st.rerun()
        else:
            st.warning("Nothing to undo!")

    st.divider()
    
    if st.button("🏁 Finish & Show Results Now", use_container_width=True):
        st.session_state.done = True
        st.rerun()
    
    st.divider()
    if df is not None:
        progress = (st.session_state.q_idx / len(df))
        st.progress(progress)
        st.write(f"**Progress:** Question {st.session_state.q_idx + 1} of {len(df)}")

# --- APP INTERFACE ---
if not st.session_state.done and df is not None:
    row = df.iloc[st.session_state.q_idx]
    
    # FIXED HEADER
    st.info(f"### **QUESTION:** {row['Question']}")
    st.write(f"Evaluating Chatbot {st.session_state.ans_idx} of 4")
    st.divider()
    
    # CHATBOT RESPONSE TEXT
    st.subheader(f"Chatbot Response {st.session_state.ans_idx}")
    st.markdown(row[f'Answer{st.session_state.ans_idx}'])
    
    # --- TABLE LOGIC ---
    table_col = f'Table{st.session_state.ans_idx}'
    if table_col in df.columns and pd.notna(row[table_col]):
        table_content = str(row[table_col]).strip()
        if table_content:
            st.markdown("### 📊 Summary Table")
            st.markdown(table_content) 

    # --- IMAGE DISPLAY ---
    img_cols = st.columns(3)
    suffixes = ['A', 'B', 'C']
    for i, s in enumerate(suffixes):
        col_name = f'Image{st.session_state.ans_idx}_{s}'
        if col_name in df.columns:
            img_val = row[col_name]
            if pd.notna(img_val) and str(img_val).strip() != "":
                with img_cols[i]:
                    try:
                        st.image(img_val, use_container_width=True, caption=f"Visual {s}")
                    except:
                        st.warning(f"Unable to load image: {col_name}")
    
    st.divider()
    
    # --- EVALUATION SECTION ---
    st.write("### 1. Safety & Hallucination Flags:")
    c_h1, c_h2 = st.columns(2)
    with c_h1:
        hallucination = st.radio(
            "Is there a Hallucination (Fact Error)?",
            ["No", "Yes"],
            horizontal=True,
            key=f"h_{st.session_state.q_idx}_{st.session_state.ans_idx}"
        )
    with c_h2:
        harm_level = st.radio(
            "Potential Harm Severity:",
            ["None", "Mild", "Moderate", "Severe"],
            horizontal=True,
            key=f"harm_{st.session_state.q_idx}_{st.session_state.ans_idx}"
        )

    st.write("### 2. Score Comprehensiveness (1-5):")
    st.caption("Click a score button below to save and move to the next item.")
    cols = st.columns(5)
    labels = ["1", "2", "3", "4", "5"]
    
    grade = None
    for i, label in enumerate(labels, 1):
        if cols[i-1].button(label, key=f"btn_{i}_{st.session_state.q_idx}_{st.session_state.ans_idx}", use_container_width=True):
            grade = i
    
    if grade:
        # Save result (Penalty removed)
        st.session_state.results.append({
            "Question": row['Question'],
            "Chatbot_Number": st.session_state.ans_idx,
            "Grade": grade,
            "Hallucination": hallucination,
            "Harm_Level": harm_level
        })
        
        # Advance Logic
        if st.session_state.ans_idx < 4:
            st.session_state.ans_idx += 1
        else:
            st.session_state.ans_idx = 1
            st.session_state.q_idx += 1
            
        if st.session_state.q_idx >= len(df):
            st.session_state.done = True
        st.rerun()

# --- COMPLETION SCREEN ---
elif st.session_state.done:
    st.success("🎉 Evaluation Session Summary")
    
    if st.session_state.results:
        res_df = pd.DataFrame(st.session_state.results)
        
        # Metrics
        avg_score = res_df['Grade'].mean()
        h_count = (res_df['Hallucination'] == "Yes").sum()
        severe_count = (res_df['Harm_Level'] == "Severe").sum()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Avg Quality Score", f"{avg_score:.2f} / 5")
        m2.metric("Total Hallucinations", h_count)
        m3.metric("Severe Harm Flags", severe_count)
        
        st.divider()
        
        st.write("### Detailed Results")
        st.dataframe(res_df, use_container_width=True)
        
        csv = res_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Results CSV", csv, "medical_eval_final.csv", "text/csv")
    else:
        st.warning("No data was recorded.")

    if st.button("Continue Evaluation"):
        st.session_state.done = False
        st.rerun()