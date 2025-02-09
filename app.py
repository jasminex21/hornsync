import streamlit as st
import auth_functions
from firebase_admin import firestore

st.set_page_config(layout='wide',
                   page_title="Hornsync",
                   initial_sidebar_state='collapsed')

### GLOBAL VARS ###
THEME = {"background_color": "#212145",
         "button_color": "#1D1D34",
         "inputs": "#4e4466",
         "text_color": "white"}
ACCOUNT_TYPES = ["Student", "Organization"]
ROLE_MAP = {
    0: "Student",
    1: "Organization"
}
INTERESTS = ["Computer Science", 
             "Biological Sciences",
             "Fitness", 
             "Sports",
             "Social", 
             "Cultural", 
             "Philanthropy",
             "Greek Life", 
             "Technology", 
             "Religion",
             "Pharmacy",
             "Humanities",
             "Art"]

INTERESTS_CAPTION = {
    "Student": "Select your interests",
    "Organization": "Select categories relevant to your organization"
}

ORGANIZATIONS = auth_functions.get_organizations()
ORG_NAMES = [org["name"] for org in ORGANIZATIONS]


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
        color: {selected_theme["text_color"]};
        font-family: 'Outfit', sans-serif;
    }}
    button[data-baseweb="tab"] {{
        background-color: transparent !important;
    }}
    div[data-baseweb="select"] > div, div[data-baseweb="base-input"] > input, div[data-baseweb="base-input"] > textarea {{
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
    [data-baseweb="tag"] {{
        color: {selected_theme["text_color"]};
        font-family: 'Outfit', sans-serif !important;
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
        gcal_id = st.text_input("Google Calendar ID")
        submit_btn = st.form_submit_button(label="Submit")    

        if submit_btn:
            preferences = {
                "club_acronym": acronym,
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

st.title("Hornsync")

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

    home_tab, info_tab = st.tabs(["Home", "Info"])
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

    with st.sidebar:

        st.markdown("### Settings")
        st.header('Sign out:')
        st.button(label='Sign Out',on_click=auth_functions.sign_out,type='primary')

        st.header('Delete account:')
        password = st.text_input(label='Confirm your password',type='password')
        st.button(label='Delete Account',on_click=auth_functions.delete_account,args=[password],type='primary')