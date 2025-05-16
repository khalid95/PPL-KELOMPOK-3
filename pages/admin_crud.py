import streamlit as st
import pandas as pd
import os

# ===============================
# PATH & SETUP
# ===============================
FOOD_PATH = "input/food.csv"
RATINGS_PATH = "input/ratings.csv"

st.set_page_config(page_title="🔒 Admin CRUD", layout="wide")

# Sembunyikan sidebar navigation multipage
st.markdown("""
   <style>
   [data-testid="stSidebarNav"] { display: none; }
   </style>
""", unsafe_allow_html=True)

st.title("🔐 Admin Panel – Manage Food Items")

# ===============================
# LOGIN ADMIN SEDERHANA
# ===============================
if "admin_logged_in" not in st.session_state:
   st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
   with st.form("login_form"):
      username = st.text_input("Username")
      password = st.text_input("Password", type="password")
      submit = st.form_submit_button("Login")
      if submit:
         if username == "admin" and password == "admin123":
               st.session_state.admin_logged_in = True
               st.success("Login successful ✅")
               st.rerun()
         else:
               st.error("Invalid credentials")
   st.stop()

# ===============================
# HELPER FUNCTIONS
# ===============================
def load_food():
   if os.path.exists(FOOD_PATH):
      return pd.read_csv(FOOD_PATH)
   return pd.DataFrame(columns=["Food_ID", "Name", "C_Type", "Veg_Non", "Describe", "Image_URL"])

def save_food(df):
   df.to_csv(FOOD_PATH, index=False)

def load_ratings():
   if os.path.exists(RATINGS_PATH):
      return pd.read_csv(RATINGS_PATH)
   return pd.DataFrame(columns=["User_ID", "Food_ID", "Rating"])

def save_ratings(df):
   df.to_csv(RATINGS_PATH, index=False)

def get_average_rating(food_id):
   ratings = load_ratings()
   if food_id in ratings["Food_ID"].values:
      return round(ratings[ratings["Food_ID"] == food_id]["Rating"].mean(), 2)
   return 0.0

# ===============================
# MAIN UI
# ===============================
tab1, tab2, tab3, tab4 = st.tabs(["📋 View All", "➕ Add", "📝 Edit/Delete", "⭐ Add Rating"])

# ========== VIEW ALL ==========
with tab1:
   st.subheader("📋 All Food Items with Average Rating")
   df = load_food()

   if df.empty:
      st.info("No food data found.")
   else:
      df["Avg_Rating"] = df["Food_ID"].apply(get_average_rating)
      st.dataframe(df, use_container_width=True)

# ========== ADD FOOD ==========
with tab2:
   st.subheader("➕ Add New Food")
   with st.form("add_food"):
      name = st.text_input("Name")
      ctype = st.text_input("Cuisine Type")
      veg = st.radio("Veg or Non-Veg", ["veg", "non-veg"])
      desc = st.text_area("Description")
      image = st.text_input("Image URL")
      submit = st.form_submit_button("Add Food")

      if submit:
         df = load_food()
         new_id = int(df["Food_ID"].max()) + 1 if not df.empty else 1
         new_row = {
               "Food_ID": new_id,
               "Name": name,
               "C_Type": ctype,
               "Veg_Non": veg,
               "Describe": desc,
               "Image_URL": image,
         }
         df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
         save_food(df)
         st.success(f"✅ Food '{name}' added with ID {new_id}")

# ========== EDIT / DELETE ==========
with tab3:
   st.subheader("📝 Edit or ❌ Delete Food")
   df = load_food()

   if df.empty:
      st.warning("No data to edit.")
   else:
      selected_id = st.selectbox("Select Food ID to Edit/Delete", df["Food_ID"])
      row = df[df["Food_ID"] == selected_id].iloc[0]

      with st.form("edit_form"):
         name = st.text_input("Name", row["Name"])
         ctype = st.text_input("Cuisine Type", row["C_Type"])
         veg = st.radio("Veg or Non-Veg", ["veg", "non-veg"], index=0 if row["Veg_Non"] == "veg" else 1)
         desc = st.text_area("Description", row["Describe"])
         image = st.text_input("Image URL", row["Image_URL"])
         rating = get_average_rating(selected_id)
         st.markdown(f"**⭐ Average Rating:** `{rating}`")

         update = st.form_submit_button("Update Food")
         if update:
               df.loc[df["Food_ID"] == selected_id, ["Name", "C_Type", "Veg_Non", "Describe", "Image_URL"]] = [
                  name, ctype, veg, desc, image
               ]
               save_food(df)
               st.success(f"✅ Food ID {selected_id} updated.")

      if st.button("❌ Delete This Food"):
         df = df[df["Food_ID"] != selected_id]
         save_food(df)
         st.warning(f"🗑️ Food ID {selected_id} deleted.")

# ========== ADD RATING ==========
with tab4:
   st.subheader("⭐ Simulate Adding a Rating")
   df = load_food()

   if df.empty:
      st.warning("No food to rate.")
   else:
      food_id = st.selectbox("Food ID", df["Food_ID"])
      user_id = st.number_input("User ID", min_value=1, step=1)
      rating = st.slider("Rating", 0.0, 10.0, 5.0, 0.1)

      if st.button("Submit Rating"):
         ratings_df = load_ratings()
         new_row = {
               "User_ID": user_id,
               "Food_ID": food_id,
               "Rating": rating
         }
         ratings_df = pd.concat([ratings_df, pd.DataFrame([new_row])], ignore_index=True)
         save_ratings(ratings_df)
         st.success("✅ Rating saved to ratings.csv")
