import streamlit as st
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
from streamlit_star_rating import st_star_rating
import os

# ==============================
# Konfigurasi Halaman
# ==============================
st.set_page_config(page_title="🍽️ Food Recommender", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebarNavItems"] {
        display: none;
    }
    [data-testid="stSidebarNav"] > div:first-child {
        display: none;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================
# Sidebar: Preferensi Pengguna
# ==============================
st.sidebar.image("foood.jpg", caption="Find Your Favorite Food!", use_container_width=True)
st.sidebar.title("🍴 Food Preferences")

vegn = st.sidebar.radio("Vegetables or not?", ["veg", "non-veg"], index=1)
cuisine = st.sidebar.selectbox("Choose Cuisine", [
    "Healthy Food", "Snack", "Dessert", "Japanese", "Indian", "French",
    "Mexican", "Italian", "Chinese", "Beverage", "Thai",
])
val = st.sidebar.slider("Rating", 0, 10, 5)

# Tombol untuk melakukan pencarian
if st.sidebar.button("🔎 Search"):
    food = pd.read_csv("input/food.csv")
    ratings = pd.read_csv("input/ratings.csv")
    combined = pd.merge(ratings, food, on="Food_ID")

    filtered = combined.loc[
        (combined.C_Type == cuisine) &
        (combined.Veg_Non == vegn) &
        (combined.Rating >= val),
        ["Name", "C_Type", "Veg_Non"]
    ]
    dish_list = np.unique(filtered["Name"].tolist())

    st.session_state.combined = combined
    st.session_state.dish_list = dish_list
    st.session_state.selected_dish = None

# ==============================
# Header Aplikasi
# ==============================
st.title("🍽️ AI-Powered Food Recommendation System")
st.markdown("#### _Let us recommend the best dishes based on your preferences!_")

# ==============================
# Tombol Dish
# ==============================
if "dish_list" in st.session_state:
    st.markdown("### 🍛 Select a Dish You Know or Like as a Starting Point : ")
    st.caption("We'll use it to recommend similar dishes others also enjoyed.")
    dish_list = st.session_state.dish_list
    cols = st.columns(min(5, len(dish_list)))
    for i, dish in enumerate(dish_list):
        with cols[i % len(cols)]:
            if st.button(dish, key=f"btn_{dish}"):
                st.session_state.selected_dish = dish

# ==============================
# Fungsi Rekomendasi
# ==============================
def food_recommendation(Food_Name):
    # Membaca file food.csv dan ratings.csv
    food = pd.read_csv("input/food.csv")
    ratings = pd.read_csv("input/ratings.csv")

    # Membuat pivot table dari data ratings
    dataset = ratings.pivot_table(index="Food_ID", columns="User_ID", values="Rating")
    dataset.fillna(0, inplace=True)  # Mengisi nilai NaN dengan 0
    print(dataset)
    csr_dataset = csr_matrix(dataset.values)  # Mengubah data menjadi matriks sparse (CSR format)
    print(csr_dataset)
    dataset.reset_index(inplace=True)

    # Melatih model Nearest Neighbors dengan metrik cosine similarity
    model = NearestNeighbors(metric="cosine", algorithm="brute", n_neighbors=20, n_jobs=-1)
    model.fit(csr_dataset)

    # Jumlah rekomendasi yang akan ditampilkan
    n = 9

    # Mencari makanan berdasarkan nama yang cocok
    FoodList = food[food["Name"].str.contains(Food_Name, case=False, na=False)]
    if len(FoodList):
        # Ambil Food_ID dari makanan yang ditemukan
        Foodi = FoodList.iloc[0]["Food_ID"]
        Foodi_index = dataset[dataset["Food_ID"] == Foodi].index[0]

        # Menentukan nilai `cuisine` dan `veg_non` berdasarkan data makanan yang dipilih
        
        veg_non = FoodList.iloc[0]["Veg_Non"]

        # Mencari tetangga terdekat (rekomendasi makanan)
        distances, indices = model.kneighbors(csr_dataset[Foodi_index], n_neighbors=n + 1)
        Food_indices = sorted(
            list(zip(indices.squeeze().tolist(), distances.squeeze().tolist())),
            key=lambda x: x[1]
        )[:0:-1]  # Mengambil rekomendasi selain makanan yang dipilih

        # Menyaring hasil berdasarkan `C_Type` dan `Veg_Non`
        Recommendations = []
        for val in Food_indices:
            Foodi = dataset.iloc[val[0]]["Food_ID"]
            i = food[food["Food_ID"] == Foodi].index

            # Filter berdasarkan `C_Type` dan `Veg_Non`
            if food.iloc[i]["Veg_Non"].values[0] == veg_non:
                Recommendations.append({
                    "Name": food.iloc[i]["Name"].values[0],
                    "Distance": val[1],
                    "id": food.iloc[i]["Food_ID"].values[0],
                    "Describe": food.iloc[i]["Describe"].values[0],
                    "Image_URL": food.iloc[i]["Image_URL"].values[0],
                })

        # Mengembalikan hasil rekomendasi dalam bentuk DataFrame
        return pd.DataFrame(Recommendations, index=range(1, len(Recommendations) + 1))

    return pd.DataFrame()

# ==============================
# Fungsi Simpan Rating
# ==============================
def save_rating(food_id, rating_value):
    csv_path = "input/ratings.csv"
    if os.path.exists(csv_path):
        ratings_df = pd.read_csv(csv_path)
        last_user_id = ratings_df["User_ID"].max() if not ratings_df.empty else 0
        new_user_id = last_user_id + 1
    else:
        ratings_df = pd.DataFrame(columns=["User_ID", "Food_ID", "Rating", "Timestamp"])
        new_user_id = 1
    new_rating = pd.DataFrame({
        "User_ID": [new_user_id],
        "Food_ID": [food_id],
        "Rating": [rating_value],
    })
    ratings_df = pd.concat([ratings_df, new_rating], ignore_index=True)
    ratings_df.to_csv(csv_path, index=False)

# ==============================
# Dialog Detail
# ==============================
@st.dialog("🍴 Food Details")
def show_details(food_name, food_id, image_url, description):
    st.image(image_url, use_container_width=True)
    st.markdown(f"### {food_name}")
    st.write(description)
    st.subheader("⭐ Rate this food")
    rating = st_star_rating("", maxValue=10, defaultValue=5, key=f"star_{food_id}", size=30)
    if st.button("Submit Rating", key=f"submit_{food_id}"):
        save_rating(food_id, rating)
        st.success(f"✅ Thank you for rating **{food_name}** with ⭐ {rating} stars!")

# ==============================
# Tampilkan Rekomendasi
# ==============================
if "selected_dish" in st.session_state and st.session_state.selected_dish:
    selected = st.session_state.selected_dish
    # st.markdown(f"### 🔎 Recommendations for: **{selected}**")
    st.markdown(f"### 🤖 You Might Also Like These, Based on: **{selected}**")

    with st.spinner("⏳ Generating recommendations..."):
        results = food_recommendation(selected)

    if not results.empty:
        cols = st.columns(3)
        for i, item in results.iterrows():
            with cols[i % 3]:
                st.image(item["Image_URL"], use_container_width=True)
                st.markdown(f"**{item['Name']}**")
                st.caption(item["Describe"][:80] + "...")
                if st.button("🔍 View", key=f"view_{item['id']}"):
                    show_details(item["Name"], item["id"], item["Image_URL"], item["Describe"])
    else:
        st.warning("❌ No similar foods found.")
