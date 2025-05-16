import streamlit as st
import pandas as pd
from matplotlib import pyplot as plt
from plotly import graph_objs as go
from sklearn.linear_model import LinearRegression
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
from streamlit_star_rating import st_star_rating
import os

st.title("Food Recommendation System")
st.text("Let us help you with ordering")
st.image("foood.jpg")

## nav = st.sidebar.radio("Navigation",["Home","IF Necessary 1","If Necessary 2"])

st.subheader("Whats your preference?")
vegn = st.radio("Vegetables or none!", ["veg", "non-veg"], index=1)

st.subheader("What Cuisine do you prefer?")
cuisine = st.selectbox(
    "Choose your favourite!",
    [
        "Healthy Food",
        "Snack",
        "Dessert",
        "Japanese",
        "Indian",
        "French",
        "Mexican",
        "Italian",
        "Chinese",
        "Beverage",
        "Thai",
    ],
)


st.subheader("How well do you want the dish to be?")  # RATING
val = st.slider("from poor to the best!", 0, 10)

food = pd.read_csv("../input/food.csv")
ratings = pd.read_csv("../input/ratings.csv")
combined = pd.merge(ratings, food, on="Food_ID")
# ans = food.loc[(food.C_Type == cuisine) & (food.Veg_Non == vegn),['Name','C_Type','Veg_Non']]

ans = combined.loc[
    (combined.C_Type == cuisine)
    & (combined.Veg_Non == vegn)
    & (combined.Rating >= val),
    ["Name", "C_Type", "Veg_Non"],
]
names = ans["Name"].tolist()
x = np.array(names)
ans1 = np.unique(x)

finallist = ""
bruh = st.checkbox("Choose your Dish")
if bruh == True:
    finallist = st.selectbox("Our Choices", ans1)


##### IMPLEMENTING RECOMMENDER ######
dataset = ratings.pivot_table(index="Food_ID", columns="User_ID", values="Rating")
dataset.fillna(0, inplace=True)
csr_dataset = csr_matrix(dataset.values)
dataset.reset_index(inplace=True)

model = NearestNeighbors(metric="cosine", algorithm="brute", n_neighbors=20, n_jobs=-1)
model.fit(csr_dataset)


# Fungsi rekomendasi makanan
def food_recommendation(Food_Name):
    n = 9
    FoodList = food[food["Name"].str.contains(Food_Name)]
    if len(FoodList):
        Foodi = FoodList.iloc[0]["Food_ID"]
        Foodi = dataset[dataset["Food_ID"] == Foodi].index[0]
        distances, indices = model.kneighbors(csr_dataset[Foodi], n_neighbors=n + 1)
        Food_indices = sorted(
            list(zip(indices.squeeze().tolist(), distances.squeeze().tolist())),
            key=lambda x: x[1],
        )[:0:-1]
        Recommendations = []
        for val in Food_indices:
            Foodi = dataset.iloc[val[0]]["Food_ID"]
            i = food[food["Food_ID"] == Foodi].index
            Recommendations.append(
                {
                    "Name": food.iloc[i]["Name"].values[0],
                    "Distance": val[1],
                    "id": food.iloc[i]["Food_ID"].values[0],
                    "Describe": food.iloc[i]["Describe"].values[0],  # Deskripsi makanan
                    "Image_URL": food.iloc[i]["Image_URL"].values[0],  # URL gambar
                }
            )
        df = pd.DataFrame(Recommendations, index=range(1, n + 1))
        return df
    else:
        return "No Similar Foods."


# Menampilkan rekomendasi makanan

display = food_recommendation(finallist)


# # Function to handle dialog interaction when food name is clicked
# @st.dialog("Food Details")
# def show_details(food_name, image_url, description):
#     st.write(f"**Description of {food_name}:**")
#     st.write(description)
#     st.image(image_url, use_container_width=True)


# if bruh == True:
#     bruh1 = st.checkbox("We also Recommend : ")
#     if bruh1 == True:
#         if "vote" not in st.session_state:
#             st.write("Click on the food name to see details:")
#             # Create columns to display images and names side by side
#             cols = st.columns(3)  # Adjust the number of columns for your layout
#             for i in range(len(display)):
#                 food_name = display["Name"].iloc[i]
#                 food_id = display["id"].iloc[i]
#                 image_url = display["Image_URL"].iloc[i]
#                 description = display["Describe"].iloc[i]

#                 with cols[i % 3]:  # Distribute items evenly across columns
#                     # Show food image
#                     st.image(image_url, use_container_width=True)

#                     # Create clickable food names with a click triggering dialog
#                     # if st.button(food_name, key=food_id):
#                     #     with st.dialog(f"{food_name} Details"):
#                     #         st.image(image_url, use_column_width=True)
#                     #         st.write(f"**Description:** {description}")
#                     #         st.write(f"**Food ID:** {food_id}")
#                     if st.button(food_name, key=food_id):
#                         show_details(food_name, image_url, description)
#         else:
#             st.write(
#                 f"You already viewed the details for {st.session_state.vote['item']}"
#             )


# if bruh == True:
#     bruh1 = st.checkbox("We also Recommend : ")
#     if bruh1 == True:
#         for i in range(len(display)):
#             st.write(f"Name: {display['Name'].iloc[i]}, ID: {display['id'].iloc[i]}")


# Function to handle dialog interaction when food name is clicked
@st.dialog("Food Details")
def show_details(food_name, food_id, image_url, description):
    st.write(f"**Description of {food_name}:**")
    st.write(description)
    st.image(image_url, use_column_width=True)
    
    # Add star rating component
    st.subheader("Rate this food")
    rating = st_star_rating("", maxValue=10, defaultValue=5, key=f"star_rating_{food_id}", size=30)
    
    # Add submit button for rating
    if st.button("Submit Rating", key=f"submit_rating_{food_id}"):
        save_rating(food_id, rating)
        st.success(f"Thank you for rating {food_name} with {rating} stars!")

# Function to save rating to CSV
def save_rating(food_id, rating_value):
    # Define CSV file path
    csv_path = "../input/ratings.csv"
    
    # Create or load rating dataframe
    if os.path.exists(csv_path):
        ratings_df = pd.read_csv(csv_path)
        # Get the last User_ID and increment by 1
        last_user_id = ratings_df["User_ID"].max() if not ratings_df.empty else 0
        new_user_id = last_user_id + 1
    else:
        # If file doesn't exist, create new dataframe with headers
        ratings_df = pd.DataFrame(columns=["User_ID", "Food_ID", "Rating", "Timestamp"])
        new_user_id = 1
    
    # Add new rating entry
    new_rating = pd.DataFrame({
        "User_ID": [new_user_id],
        "Food_ID": [food_id],
        "Rating": [rating_value],
        
    })
    
    # Append to the existing ratings
    ratings_df = pd.concat([ratings_df, new_rating], ignore_index=True)
    
    # Save back to CSV
    ratings_df.to_csv(csv_path, index=False)
    
    # Store in session state that user has voted
    st.session_state.vote = {"item": food_id, "rating": rating_value}

# Main app code
if bruh == True:
    bruh1 = st.checkbox("We also Recommend : ")
    if bruh1 == True:
        if "vote" not in st.session_state:
            st.write("Click on the food name to see details:")
            # Create columns to display images and names side by side
            cols = st.columns(3)  # Adjust the number of columns for your layout
            for i in range(len(display)):
                food_name = display["Name"].iloc[i]
                food_id = display["id"].iloc[i]
                image_url = display["Image_URL"].iloc[i]
                description = display["Describe"].iloc[i]
                
                with cols[i % 3]:  # Distribute items evenly across columns
                    # Show food image
                    st.image(image_url, use_column_width=True)
                    
                    # Create clickable food names with a click triggering dialog
                    if st.button(food_name, key=food_id):
                        show_details(food_name, food_id, image_url, description)
        else:
            st.write(
                f"You already rated food ID {st.session_state.vote['item']} with {st.session_state.vote['rating']} stars"
            )
            del st.session_state.vote
            st.rerun()
            
            # Option to rate another item
            if st.button("Rate another food"):
                del st.session_state.vote
                st.rerun()