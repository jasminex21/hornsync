import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import pandas as pd

# Sample Data
data = pd.DataFrame({
    "Name": ["Alice", "Bob", "Charlie"],
    "Description": ["This is a long description that should wrap within the cell.",
                    "Short text",
                    "Another long piece of text that needs to wrap properly."]
})

# Configure AgGrid
gb = GridOptionsBuilder.from_dataframe(data)

# Apply styling to the "Description" column
gb.configure_column("Description", 
                    cellStyle={"backgroundColor": "#f4e1d2",  # Light peach background
                               "color": "#333333",           # Dark gray text
                               "fontFamily": "Arial",        # Custom font
                               "fontSize": "14px",
                               "whiteSpace": "normal",
                               "wordWrap": "break-word"}, 
                    autoHeight=True)

# Apply styling to the "Name" column
gb.configure_column("Name", 
                    cellStyle={"backgroundColor": "#d2e1f4",  # Light blue background
                               "color": "#000000",           # Black text
                               "fontWeight": "bold", 
                               "fontSize": "16px"})

grid_options = gb.build()

grid_options["domLayout"] = "autoHeight"
grid_options["defaultColDef"] = {
    "cellStyle": {
        "backgroundColor": "#f0f0f0",  # Light gray
        "fontFamily": "Verdana",
        "fontSize": "14px"
    }
}


# Display the AgGrid table
AgGrid(data, gridOptions=grid_options, height=200, fit_columns_on_grid_load=True)

