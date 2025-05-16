import streamlit as st

st.set_page_config(page_title="🍽️ Welcome", layout="centered")
hide_sidebar = """
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
"""
st.markdown(hide_sidebar, unsafe_allow_html=True)

st.title("👋 Welcome to the Food Recommendation App")
st.markdown("Start discovering your favorite dishes based on your taste!")

st.image("foood.jpg", use_container_width=True)
st.markdown("---")

if st.button("🍽️ Start Recommending Food"):
    st.switch_page("pages/new_app.py")
