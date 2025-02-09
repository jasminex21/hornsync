import json
import requests
import bcrypt
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, storage
from PIL import Image
import io

cred = credentials.Certificate('/home/jasmine/PROJECTS/hornsync/hornsync-8c2e1-412321627efe.json')
firebase_admin.initialize_app(cred)
                             # {"storageBucket": "hornsync-8c2e1.firebasestorage.app"})
DB = firestore.client()

## -------------------------------------------------------------------------------------------------
## Firebase Auth API -------------------------------------------------------------------------------
## -------------------------------------------------------------------------------------------------
def create_user(name, email, password, role):
    # email as unique identifier
    doc_ref = DB.collection('users').document(email) 

    doc_ref.set({
        'email': email,
        'name': name,
        'passwordHash': password,
        'role': role,  # student or org
        'preferences': {} # preferences to be updated later
    })

def get_organizations():

    users_ref = DB.collection('users')

    query = users_ref.where('role', '==', 'Organization')
    docs = query.stream()

    organizations = []
    for doc in docs:
        user_data = doc.to_dict() 
        organizations.append(user_data)
    
    return organizations

def update_user_preferences(email, preferences):

    try:
        doc_ref = DB.collection('users').document(email)

        doc_ref.update({"preferences": preferences})

        print("User preferences updated successfully.")

    except Exception as e:
        print(f"Error updating user preferences: {str(e)}")

def get_user_info(email): 
    try:
        doc_ref = DB.collection('users').document(email)
        doc = doc_ref.get()

        if doc.exists:
            user_data = doc.to_dict()  
            return user_data
        else:
            print(f"No user data found for user with email {email}")
            return None

    except Exception as e:
        print(f"Error getting user preferences: {str(e)}")
        return None
    
# def store_image(logo):
#     image = Image.open(logo)
#     img_bytes = io.BytesIO()
#     image.save(img_bytes, format=image.format)
#     img_bytes = img_bytes.getvalue()

#     blob = BUCKET.blob(f"org_logos/{logo.name}")
#     blob.upload_from_string(img_bytes, 
#                             content_type=f"image/{logo.type.split('/')[-1]}")

#     blob.make_public()
#     image_url = blob.public_url

#     return image_url

def sign_in_with_email_and_password(email, password):
    request_ref = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={0}".format(st.secrets['FIREBASE_WEB_API_KEY'])
    headers = {"content-type": "application/json; charset=UTF-8"}
    data = json.dumps({"email": email, "password": password, "returnSecureToken": True})
    request_object = requests.post(request_ref, headers=headers, data=data)
    raise_detailed_error(request_object)
    return request_object.json()

def get_account_info(id_token):
    request_ref = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/getAccountInfo?key={0}".format(st.secrets['FIREBASE_WEB_API_KEY'])
    headers = {"content-type": "application/json; charset=UTF-8"}
    data = json.dumps({"idToken": id_token})
    request_object = requests.post(request_ref, headers=headers, data=data)
    raise_detailed_error(request_object)
    return request_object.json()

def send_email_verification(id_token):
    request_ref = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/getOobConfirmationCode?key={0}".format(st.secrets['FIREBASE_WEB_API_KEY'])
    headers = {"content-type": "application/json; charset=UTF-8"}
    data = json.dumps({"requestType": "VERIFY_EMAIL", "idToken": id_token})
    request_object = requests.post(request_ref, headers=headers, data=data)
    raise_detailed_error(request_object)
    return request_object.json()

def send_password_reset_email(email):
    request_ref = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/getOobConfirmationCode?key={0}".format(st.secrets['FIREBASE_WEB_API_KEY'])
    headers = {"content-type": "application/json; charset=UTF-8"}
    data = json.dumps({"requestType": "PASSWORD_RESET", "email": email})
    request_object = requests.post(request_ref, headers=headers, data=data)
    raise_detailed_error(request_object)
    return request_object.json()

def create_user_with_email_and_password(email, password):
    request_ref = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/signupNewUser?key={0}".format(st.secrets['FIREBASE_WEB_API_KEY'])
    headers = {"content-type": "application/json; charset=UTF-8" }
    data = json.dumps({"email": email, "password": password, "returnSecureToken": True})
    request_object = requests.post(request_ref, headers=headers, data=data)
    raise_detailed_error(request_object)
    return request_object.json()

def delete_user_account(id_token):
    request_ref = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/deleteAccount?key={0}".format(st.secrets['FIREBASE_WEB_API_KEY'])
    headers = {"content-type": "application/json; charset=UTF-8"}
    data = json.dumps({"idToken": id_token})
    request_object = requests.post(request_ref, headers=headers, data=data)
    raise_detailed_error(request_object)
    return request_object.json()

def raise_detailed_error(request_object):
    try:
        request_object.raise_for_status()
    except requests.exceptions.HTTPError as error:
        raise requests.exceptions.HTTPError(error, request_object.text)

## -------------------------------------------------------------------------------------------------
## Authentication functions ------------------------------------------------------------------------
## -------------------------------------------------------------------------------------------------

def sign_in(email:str, password:str) -> None:
    try:
        # Attempt to sign in with email and password
        id_token = sign_in_with_email_and_password(email,password)['idToken']

        # Get account information
        user_info = get_account_info(id_token)["users"][0]

        # Save user info to session state and rerun (no email verification check)
        st.session_state.user_info = user_info
        st.rerun()

    except requests.exceptions.HTTPError as error:
        error_message = json.loads(error.args[1])['error']['message']
        if error_message in {"INVALID_EMAIL","EMAIL_NOT_FOUND","INVALID_PASSWORD","MISSING_PASSWORD"}:
            st.session_state.auth_warning = 'Error: Use a valid email and password'
        else:
            st.session_state.auth_warning = 'Error: Please try again later'

    except Exception as error:
        print(error)
        st.session_state.auth_warning = 'Error: Please try again later'


def create_account(name:str, email:str, password:str, role:str) -> None:
    try:
        # Create account (and save id_token)
        id_token = create_user_with_email_and_password(email, password)['idToken']
        create_user(name, email, password, role)

        # Create account and send email verification
        # send_email_verification(id_token)
        st.session_state.auth_success = "Account successfully created! You may now log in"
        # st.session_state.auth_success = 'Check your inbox to verify your email'
    
    except requests.exceptions.HTTPError as error:
        error_message = json.loads(error.args[1])['error']['message']
        if error_message == "EMAIL_EXISTS":
            st.session_state.auth_warning = 'Error: Email belongs to existing account'
        elif error_message in {"INVALID_EMAIL","INVALID_PASSWORD","MISSING_PASSWORD","MISSING_EMAIL","WEAK_PASSWORD"}:
            st.session_state.auth_warning = 'Error: Use a valid email and password'
        else:
            st.session_state.auth_warning = 'Error: Please try again later'
    
    except Exception as error:
        print(error)
        st.session_state.auth_warning = 'Error: Please try again later'


def reset_password(email:str) -> None:
    try:
        send_password_reset_email(email)
        st.session_state.auth_success = 'Password reset link sent to your email'
    
    except requests.exceptions.HTTPError as error:
        error_message = json.loads(error.args[1])['error']['message']
        if error_message in {"MISSING_EMAIL","INVALID_EMAIL","EMAIL_NOT_FOUND"}:
            st.session_state.auth_warning = 'Error: Use a valid email'
        else:
            st.session_state.auth_warning = 'Error: Please try again later'    
    
    except Exception:
        st.session_state.auth_warning = 'Error: Please try again later'


def sign_out() -> None:
    st.session_state.clear()
    st.session_state.auth_success = 'You have successfully signed out'


def delete_account(password:str) -> None:
    try:
        # Confirm email and password by signing in (and save id_token)
        id_token = sign_in_with_email_and_password(st.session_state.user_info['email'],password)['idToken']
        
        # Attempt to delete account
        delete_user_account(id_token)
        st.session_state.clear()
        st.session_state.auth_success = 'You have successfully deleted your account'

    except requests.exceptions.HTTPError as error:
        error_message = json.loads(error.args[1])['error']['message']
        print(error_message)

    except Exception as error:
        print(error)
