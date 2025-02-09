import streamlit as st
from firebase_admin import firestore, storage
from gcsa.google_calendar import GoogleCalendar
from gcsa.calendar import Calendar
import time
import io
import pandas as pd
from PIL import Image
from datetime import datetime, timedelta
from st_aggrid import AgGrid, JsCode, ColumnsAutoSizeMode, AgGridTheme
from st_aggrid.grid_options_builder import GridOptionsBuilder
import plotly.graph_objects as go
from plotly.graph_objects import Layout
from collections import Counter

import auth_functions
import gcal_functions
import rec_functions
import img

st.set_page_config(layout='wide',
                   page_title="Hornsync",
                   initial_sidebar_state='collapsed',
                   page_icon="./hornsync_logo.png")

### GLOBAL VARS ###
THEME = {
        "background_color": "#CE9363",
        "button_color": "#BF5700", 
        "inputs": "#B1784A", 
        "text_color": "white"}


ACCOUNT_TYPES = ["Student", "Organization"]
ROLE_MAP = {
    0: "Student",
    1: "Organization"
}
INTERESTS = ["Computer Science", 
             "Data Science",
             "Biological Sciences",
             "Technology",
             "Fitness", 
             "Sports",
             "Social", 
             "Cultural", 
             "Business",
             "Entrepreneurship",
             "Humanities",
             "Writing", 
             "Arts"]

INTERESTS_CAPTION = {
    "Student": "Select your interests",
    "Organization": "Select categories relevant to your organization"
}

ORGANIZATIONS = auth_functions.get_organizations()

ORG_INFO = []
for org in ORGANIZATIONS: 
    keep_info = {
        "Logo": org["preferences"]["image_url"],
        "Name": org["name"],
        "Categories": org["preferences"]["interests"],
        "Description": org["preferences"]["description"]
    }
    ORG_INFO.append(keep_info)

ORGS_DF = pd.DataFrame(ORG_INFO)
print(f"ORGS: ", ORG_INFO)
ORG_NAMES = [org["name"] for org in ORGANIZATIONS]
ORG_EMAILS = [org["email"] for org in ORGANIZATIONS]
ORG_MAP = dict(zip(ORG_NAMES, ORG_EMAILS))

if "USER_DATA" not in st.session_state: 
    st.session_state.USER_DATA = {}
if "first_sign_in" not in st.session_state: 
    st.session_state.first_sign_in = False

### FUNCTIONS ###

def apply_theme(selected_theme):
    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap');

    .stApp > header {{
        background-color: transparent;
    }}
    .stApp {{
        background: {selected_theme['background_color']};
        color: {selected_theme["text_color"]};
        font-family: 'Outfit', sans-serif;
    }}
    button[data-baseweb="tab"] {{
        background-color: transparent !important;
    }}
    [data-baseweb="popover"], div[data-baseweb="popover"] > div {{
        background-color: {"grey" if selected_theme["text_color"] == "black" else "#262730"};
    }}
    [data-testid="stSidebar"] {{
        background: {selected_theme['background_color']};
    }}
    button {{
        background-color: {selected_theme['button_color']} !important;
    }}
    button:disabled {{
        background-color: transparent !important;
    }}
    div[data-baseweb="select"] > div, div[data-baseweb="base-input"] > input, div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="popover"] {{
        background-color: {selected_theme["inputs"]};
        color: {selected_theme["text_color"]};
        -webkit-text-fill-color: {selected_theme["text_color"]} !important;
        font-weight: 600 !important;
        font-family: 'Outfit', sans-serif;
    }}
    p, ul, li {{
        color: {selected_theme["text_color"]};
        font-weight: 600 !important;
        font-size: large !important;
        font-family: 'Outfit', sans-serif !important;
    }}
    h3, h2, h1, strong, h4 {{
        color: {selected_theme["text_color"]};
        font-weight: 900 !important;
        font-family: 'Outfit', sans-serif !important;
    }}

    h1 {{
        font-size: 48px !important;
    }}

    [data-baseweb="tag"] {{
        background: {selected_theme['button_color']} !important;
        color: {selected_theme["text_color"]};
        font-family: 'Outfit', sans-serif;
    }}
    th {{
        color: {selected_theme["text_color"]} !important;
        font-weight: 900 !important;
        text-align: left !important;
        font-family: 'Outfit', sans-serif;
    }}
    td {{
        color: {selected_theme["text_color"]} !important;
        font-weight: 600 !important;
        font-family: 'Outfit', sans-serif;
    }}
    .ag-header-row, .ag-header-row-column, .ag-header-container {{
        background-color: #C77532 !important; 
        color: white !important;
        font-family: 'Poppins', sans-serif !important;
        font-size: 18px !important;
        font-weight: bold !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def student_form(email):

    with st.form("student_form"):
        
        followed = st.multiselect("Select organizations to follow", 
                                  options=ORG_NAMES, 
                                  default=st.session_state.USER_DATA["preferences"].get("orgs_followed", None)) 

        interests = st.multiselect(INTERESTS_CAPTION["Student"], 
                                   options=INTERESTS, 
                                   default=st.session_state.USER_DATA["preferences"].get("interests", None)) 
        
        submit_btn = st.form_submit_button(label='Submit')

        if submit_btn:

            preferences = {
                "orgs_followed": followed,
                "interests": interests
            }

            auth_functions.update_user_preferences(email, preferences)
            st.session_state.USER_DATA = auth_functions.get_user_info(email)
            st.success("Preferences saved!")
            return preferences
        
        return None

def organizations_form(email): 

    with st.form("organizations_form"): 

        acronym = st.text_input("Club acronym")
        interests = st.multiselect(INTERESTS_CAPTION["Organization"], 
                                   options=INTERESTS, 
                                   default=st.session_state.USER_DATA["preferences"].get("interests", None))  
        description = st.text_area(label="Organization description")
        gcal_id = st.text_input("Google Calendar ID")
        # club_logo = st.file_uploader("Upload logo", type=["png", "jpg", "jpeg"])
        submit_btn = st.form_submit_button(label="Submit")    

        if submit_btn:

            # if club_logo:
            #     image_url = auth_functions.store_image(club_logo)

            preferences = {
                "club_acronym": acronym,
                "description": description,
                "gcal_id": gcal_id,
                "interests": interests
            }
            auth_functions.update_user_preferences(email, preferences)
            st.session_state.USER_DATA = auth_functions.get_user_info(email)
            st.success("Preferences saved!")
            return preferences
        
        return None

### UI ###
apply_theme(THEME)

with st.columns(5)[2]: 
    st.markdown("<h1 style='text-align: center;'>Hornsync</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center;'>{img.img_to_html('hornsync_logo.png')}</p>", unsafe_allow_html=True)

    # st.image("./hornsync_logo.png")

# USER NOT LOGGED IN
if 'user_info' not in st.session_state:
    col1,col2,col3 = st.columns([1,2,1])

    # authentication form
    do_you_have_an_account = col2.selectbox(label='Do you have an account?',
                                            options=('Yes', 'No', 'I forgot my password'))
    
    auth_form = col2.form(key='Authentication form',
                          clear_on_submit=False)

    name = auth_form.text_input(label="Name") if do_you_have_an_account == "No" else auth_form.empty()
    email = auth_form.text_input(label='Email')
    password = auth_form.text_input(label='Password',
                                    type='password') if do_you_have_an_account in {'Yes','No'} else auth_form.empty()
    role = auth_form.segmented_control("Role", 
                                       options=ACCOUNT_TYPES,
                                       selection_mode="single") if do_you_have_an_account == "No" else auth_form.empty()
    auth_notification = col2.empty()

    # sign in
    if do_you_have_an_account == 'Yes' and auth_form.form_submit_button(label='Sign In',use_container_width=True,type='primary'):
        with auth_notification, st.spinner('Signing in...'):
            auth_functions.sign_in(email, password)

    # create account
    elif do_you_have_an_account == 'No' and auth_form.form_submit_button(label='Create Account',
                                                                         use_container_width=True,
                                                                         type='primary'):
        with auth_notification, st.spinner('Creating account'):
            auth_functions.create_account(name, email, password, role)
            
        with auth_notification, st.spinner("Signing in..."):
            auth_functions.sign_in(email, password)
            # st.session_state.USER_DATA = auth_functions.get_user_info(email)

    # password reset
    elif do_you_have_an_account == 'I forgot my password' and auth_form.form_submit_button(label='Send Password Reset Email',use_container_width=True,type='primary'):
        with auth_notification, st.spinner('Sending password reset link'):
            auth_functions.reset_password(email)

    # authentication success and warning messages
    if 'auth_success' in st.session_state:
        auth_notification.success(st.session_state.auth_success)
        del st.session_state.auth_success
    elif 'auth_warning' in st.session_state:
        auth_notification.warning(st.session_state.auth_warning)
        del st.session_state.auth_warning

# USER HAS LOGGED IN 
else:
    email = st.session_state.user_info['email']
    # print(f"email {email}")
    st.session_state.USER_DATA = auth_functions.get_user_info(email)
    print(st.session_state.USER_DATA)

    home_tab, info_tab, recs_tab = st.tabs(["Home", "Info", "Recommendations"])
    with home_tab: 
        expand = True if ((len(st.session_state.USER_DATA["preferences"]) == 0)) else False
        text = f"### Welcome to Hornsync, {st.session_state.USER_DATA['name']}!" if expand else f"### Welcome back, {st.session_state.USER_DATA['name']}!"
        caption = f"Please fill out your preferences - you can modify them later!" if expand else f"Update your preferences"

        st.markdown(text)

        with st.expander("Update preferences", expanded=expand):

            if st.session_state.USER_DATA["role"] == "Student": 
                user_form = student_form(email)

            else: 
                user_form = organizations_form(email)
        
        if st.session_state.USER_DATA["role"] == "Student": 

            user_clubs = st.session_state.USER_DATA["preferences"]["orgs_followed"]
            user_club_emails = [ORG_MAP[club] for club in user_clubs]
            user_interests = st.session_state.USER_DATA["preferences"]["interests"]
            user_club_info = [auth_functions.get_user_info(m) for m in user_club_emails]
            user_club_acronyms = [info["preferences"]["club_acronym"] for info in user_club_info]

            user_clubs = st.session_state.USER_DATA["preferences"]["orgs_followed"]
            user_club_emails = [ORG_MAP[club] for club in user_clubs]
            user_interests = st.session_state.USER_DATA["preferences"]["interests"]
            user_club_info = [auth_functions.get_user_info(m) for m in user_club_emails]
            user_club_acronyms = [info["preferences"]["club_acronym"] for info in user_club_info]
            print(f"CLUB INFO {user_club_info}")

            user_cats = []
            for info in user_club_info: 
                user_cats += info["preferences"]["interests"]

            c1, c2, c3 = st.columns(3)
            generate_gcal = c2.button("Generate consolidated calendar", type="primary")

            if generate_gcal: 

                EVENTS = gcal_functions.combine_events(user_club_acronyms, 
                                                        [info["preferences"]["gcal_id"] for info in user_club_info])
                consolidated_calendar = gcal_functions.consolidate_calendar(EVENTS=EVENTS, 
                                                                            org_names=user_clubs)
                iframe = gcal_functions.get_gcal_embed(consolidated_calendar.id)
                print(iframe)
                st.markdown(iframe, unsafe_allow_html=True)

            with info_tab: 

                st.markdown("### Available Clubs")
                table_col, stats_col = st.columns([3, 2])
                # with table_col: 
                builder = GridOptionsBuilder.from_dataframe(ORGS_DF)

                builder.configure_column("Logo",
                                        headerName="Logo", 
                                        width=300,
                                        cellRenderer=JsCode("""
                                            class UrlCellRenderer {
                                            init(params) {
                                                this.eGui = document.createElement('img');
                                                this.eGui.setAttribute('src', params.value);
                                                this.eGui.setAttribute('style', "width:80px;height:80px");
                                            }
                                            getGui() {
                                                return this.eGui;
                                            }
                                            }"""
                                        )
                                    )   
                
                header_style = {
                    "backgroundColor": "#C77532",  
                    "color": "white",  
                    "fontWeight": "bold",  
                    "fontFamily": "Avantgarde, TeX Gyre Adventor, URW Gothic L, sans-serif",
                    "fontSize": "18px"}

                builder.configure_column("Description", wrapText=True, autoHeight=True)
                builder.configure_column("Categories", wrapText=True, autoHeight=True)

                builder.configure_column("Logo", width=100)
                builder.configure_column("Name", width=250)
                builder.configure_column("Categories", width=250)
                builder.configure_column("Description", flex=3)


                builder.configure_grid_options(rowHeight=150, suppressColumnVirtualisation=True)
                options = builder.build()

                # options["domLayout"] = "autoHeight"
                options["defaultColDef"] = {"cellStyle": {"backgroundColor": "#B1784A",
                                                        "fontFamily": "Avantgarde, TeX Gyre Adventor, URW Gothic L, sans-serif",
                                                        "fontSize": "15px"},
                                            "headerStyle": header_style}

                grid = AgGrid(ORGS_DF, 
                            gridOptions=options,
                            columns_auto_size_mode=ColumnsAutoSizeMode.NO_AUTOSIZE,
                            allow_unsafe_jscode=True, 
                            theme=AgGridTheme.ALPINE,
                            fit_columns_on_grid_load=True,
                            height=700)
                # with stats_col: 
                    
                    # st.markdown("#### Your Top Categories")
                    # # only for student
                    
                    # category_counts = Counter(user_cats)

                    # labels = list(category_counts.keys())
                    # values = list(category_counts.values())

                    # colors = ["bf5700","c36619","c77532","cb844b","ce9363","d29d71"]

                    # # layout = Layout(paper_bgcolor='rgba(0,0,0,0)',
                    # #                 plot_bgcolor='rgba(0,0,0,0)')

                    # fig = go.Figure(data=[go.Pie(labels=labels, 
                    #                             values=values, 
                    #                             hole=.3,
                    #                             marker=dict(colors=colors, 
                    #                                         line=dict(color="black", width=1)),
                    #                             hovertemplate=('<b>%{label}</b><br>' 
                    #                                             '# of clubs: %{value}<br>' 
                    #                                             'Pct.: %{percent:.2%}<br>' 
                    #                                             '<extra></extra>'))])
                    # fig.update_layout({"paper_bgcolor": "rgba(0, 0, 0, 0)",
                    #                 "plot_bgcolor": "rgba(0, 0, 0, 0)"})
                    
                    # st.plotly_chart(fig, use_container_width=True)

                    # st.markdown("#### Recommended Organizations")
                    # # orgs user is not already in
                    # other_orgs = [info for info in ORG_INFO if info["Name"] not in user_clubs]
                    # print(f"OTHERS: {other_orgs}")
                    # ranks = rec_functions.return_ranks(user_interests, other_orgs)
                    # st.write(ranks)
                    # st.markdown(f"Recommended clubs based on your interests: {[ranks[i][0] for i in range(2)]}")
    
            with recs_tab: 
                cats, recs = st.columns(2)
                with cats:
                    st.markdown("### Your Top Categories")
                    # only for student
                    category_counts = Counter(user_cats)

                    labels = list(category_counts.keys())
                    values = list(category_counts.values())

                    colors = ["bf5700","c36619","c77532","cb844b","ce9363","d29d71"]

                    # layout = Layout(paper_bgcolor='rgba(0,0,0,0)',
                    #                 plot_bgcolor='rgba(0,0,0,0)')

                    fig = go.Figure(data=[go.Pie(labels=labels, 
                                                values=values, 
                                                hole=.3,
                                                marker=dict(colors=colors, 
                                                            line=dict(color="black", width=1)),
                                                hovertemplate=('<b>%{label}</b><br>' 
                                                                '# of clubs: %{value}<br>' 
                                                                'Pct.: %{percent:.2%}<br>' 
                                                                '<extra></extra>'))])
                    fig.update_layout({"paper_bgcolor": "rgba(0, 0, 0, 0)",
                                    "plot_bgcolor": "rgba(0, 0, 0, 0)"})
                    
                    st.plotly_chart(fig, use_container_width=True)

                with recs: 
                    st.markdown("### Recommended Organizations")
                    st.markdown(f"Hornsync recommends organizations for you based on the overlap between your interests and each organization's categories, as well as by analyzing each organization's description.")

                    st.divider()
                    st.markdown(f"<u>Your interests<u>: {', '.join(user_interests)}", unsafe_allow_html=True)
                    # orgs user is not already in
                    other_orgs = [info for info in ORG_INFO if info["Name"] not in user_clubs]
                    ranks = rec_functions.return_ranks(user_interests, other_orgs)
                    print(f"RANKS: {ranks}")
                    # st.write(ranks)
                    st.markdown(f"Recommended clubs for you: ") #{', '.join([ranks[i][0] for i in range(2)])}
                    ranks_str = ""
                    for i in range(3): 
                        ranks_str += f"* {ranks[i][0]} ({round(ranks[i][1], 2)})\n"
                    st.markdown(ranks_str)
                    



    with st.sidebar:

        st.markdown("## Settings")
        st.header('Sign out:')
        st.button(label='Sign Out',on_click=auth_functions.sign_out,type='primary')

        st.header('Delete account:')
        password = st.text_input(label='Confirm your password',type='password')
        st.button(label='Delete Account',on_click=auth_functions.delete_account,args=[password],type='primary')