import pandas as pd
import streamlit as st
from io import StringIO
from datetime import datetime
import seaborn as sns
import matplotlib.pyplot as plt

# Title of the app
st.title("2G Traffic (Erlang)")

# Cache the data loading function
@st.cache_data
def load_data(uploaded_file):
    file_content = uploaded_file.read().decode('utf-8')
    lines = file_content.splitlines()
    start_index = 0
    for i, line in enumerate(lines):
        if "Start Time" in line:
            start_index = i
            break
    structured_data = lines[start_index:]
    structured_data_str = "\n".join(structured_data)
    df = pd.read_csv(StringIO(structured_data_str))
    return df

# Step 1: Upload the CSV file
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    # Load the data with caching
    with st.spinner("Loading data..."):
        df = load_data(uploaded_file)
    st.success("Data loaded successfully!")

    # Convert "Start Time" to datetime
    df["Start Time"] = pd.to_datetime(df["Start Time"])

    # Extract "Cell_Sector" from "GCELL" column
    df["Cell_Sector"] = df["GCELL"].str.extract(r'(?i)LABEL\s*[:=]\s*([\w\s()-]+)')

    # Extract "Site" from "GCELL" column (assuming site name is part of the label)
    df["Site"] = df["GCELL"].str.extract(r'(?i)LABEL\s*[:=]\s*([\w\s()-]+)')

    # Rename the column with a colon to remove the colon
    df = df.rename(columns={"K3014:Traffic Volume on TCH (Erl)": "K3014_Traffic_Volume_on_TCH_Erl"})

    # Add filters in the main area
    st.write("### Filters")

    # Site filter (text input for typing the site name)
    site_search = st.text_input(
        "Search Site",
        placeholder="Type the site name..."
    )

    # Initialize selected_sectors as an empty list
    selected_sectors = []

    # Show sector filter only if a site is selected
    if site_search:
        # Filter sectors based on the searched site
        sectors_for_selected_site = df[df["Site"].str.contains(site_search, case=False, na=False)]["Cell_Sector"].unique()

        # Sector filter (multi-select)
        selected_sectors = st.multiselect(
            "Select Sectors",
            options=sectors_for_selected_site,
            default=None  # No default selection
        )

        # Show date range filter only if sectors are selected
        if selected_sectors:
            # Display the available date range
            min_date = df["Start Time"].min().date()
            max_date = df["Start Time"].max().date()
            st.write(f"Available Date Range: **{min_date}** to **{max_date}**")

            st.write("Select Date Range:")
            date_range = st.date_input(
                "",
                value=[],  # Initialize with no default selection
                min_value=min_date,
                max_value=max_date
            )

            # Filter data based on user input
            if len(date_range) == 2:  # Only filter if a valid date range is selected
                with st.spinner("Filtering data..."):
                    filtered_df = df[
                        (df["Start Time"].dt.date >= date_range[0]) & 
                        (df["Start Time"].dt.date <= date_range[1]) & 
                        (df["Site"].str.contains(site_search, case=False, na=False)) &  # Filter by site name
                        (df["Cell_Sector"].isin(selected_sectors))
                    ]
                st.success("Data filtered successfully!")

                # Display the first 5 rows of the filtered DataFrame
                st.write("First 5 rows of the filtered DataFrame:")
                st.write(filtered_df.head())

                # Show the graph only if filters are applied and data is available
                if not filtered_df.empty:
                    st.write("### Traffic Volume Over Time by Sector")

                    # Create a Seaborn line plot
                    plt.figure(figsize=(12, 6))
                    sns.lineplot(
                        data=filtered_df,
                        x="Start Time",
                        y="K3014_Traffic_Volume_on_TCH_Erl",
                        hue="Cell_Sector",
                        style="Cell_Sector",
                        markers=True,
                        dashes=False
                    )
                    plt.title("Traffic Volume Over Time by Sector")
                    plt.xlabel("Start Time")
                    plt.ylabel("Traffic Volume")
                    plt.xticks(rotation=45)
                    plt.legend(title="Sector", bbox_to_anchor=(1.05, 1), loc='upper left')
                    plt.tight_layout()

                    # Display the plot in Streamlit
                    st.pyplot(plt)
                else:
                    st.warning("No data found for the selected filters.")
            else:
                st.warning("Please select a valid date range.")
        else:
            st.warning("Please select sectors.")
    else:
        st.warning("Please select a site.")