import os

os.environ['DISPLAY'] = ':0'

import psycopg2
import uuid
import pandas as pd
from logzero import logger
from datetime import datetime
import webbrowser
import time
import pyautogui
import logzero
import streamlit as st



#call_button_image = "call_button.png"

logzero.logfile("log.log")


def connect_questdb():
    # Connection parameters
    connection_params = {
        "user": "admin",
        "password": "quest",
        "host": "43.204.237.29",
        "port": "8812",
        "database": "qdb"
    }

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(**connection_params)
    
    cursor = conn.cursor()
    
    return conn, cursor

#@st.cache_data(max_entries=50, show_spinner='Loading ...')
def sql_read_query_df( query ):
    conn, cursor = connect_questdb()
    
    df = pd.read_sql_query(query,conn)
    
    conn.close()
    
    return df


#@st.cache_data(max_entries=50, show_spinner='Loading ...')
def execute_sql_query( query ):
    conn, cursor = connect_questdb()
    
    cursor.execute(query,conn)
    
    conn.close()

#@st.cache_data(max_entries=50, show_spinner='Loading ...')
def fetchone_sql_query( fetch_one_query ):
    conn, cursor = connect_questdb()
        
    cursor.execute( fetch_one_query )

    # Fetch the result
    fetch_result = cursor.fetchone()
    
    conn.close()
    
    return fetch_result
    
@st.cache_data( ttl='2hr', show_spinner='Loading ...')
def valid_user( combination ):
    
    value_0 = fetchone_sql_query( f""" SELECT 1 FROM credentials_smartcall WHERE combination = '{combination}' """ )
    
    value = True if value_0 else False
    
    return value
    
@st.cache_data( ttl='2hr', show_spinner='Loading ...')
def login(username, password, org_id):
   
    combined_credentials = f"{username}__{password}__{org_id}"
        
    login_status = valid_user( combined_credentials )
    
    role_result = fetchone_sql_query(f""" SELECT role FROM credentials_smartcall WHERE combination = '{combined_credentials}' """)
    
    role = role_result[0] if role_result else None
        
    return login_status, role

def generate_unique_id( length ):
    
    unique_id = str(uuid.uuid4())
    
    short_id = unique_id[:length]
    
    return short_id

def get_number_to_call( org_id ):
        
    #num_to_call_results = fetchone_sql_query(f"""SELECT id, contact, customer_name, customer_email, customer_address, customer_domain FROM contacts_smartcall WHERE org_id = '{org_id}' AND call_status='pending' AND agent_username IS NULL""")
    
    
    num_to_call_results = sql_read_query_df(f"""SELECT id, contact, customer_name, customer_email, customer_address, customer_domain FROM contacts_smartcall WHERE org_id = '{org_id}' AND call_status='pending' AND agent_username IS NULL LIMIT 1""")
               
    if num_to_call_results is not None:
        
        #cust_info_df_fetched = pd.DataFrame( [num_to_call_results], columns=['contact_id', 'customer_domain', 'customer_name', 'customer_email', 'num_to_call', 'customer_address'] )
        
        cust_info_df_fetched = num_to_call_results
                
    else:
        cust_info_df_fetched = pd.DataFrame( columns=['contact', 'customer_name', 'customer_email', 'customer_address', 'customer_domain'])
                
    return cust_info_df_fetched


def next_iteration( org_id, agent_username ):
    
    cust_info_df_fetched = get_number_to_call(org_id)
    
    if len( cust_info_df_fetched ) == 0:
        
        logger.info('No number to call')
        
        skype_uri = 'No number to call'
        
    else:
        current_datetime = datetime.now()
        
        called_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S.%f")
        
        call_date = datetime.strptime(called_datetime, "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%d")
        
        # Update agent information to avoid multiple agents calling the same number
        
        agent_update_query = f"UPDATE contacts_smartcall SET agent_username = '{agent_username}', called_datetime = '{called_datetime}', call_date = '{call_date}' WHERE id = '{cust_info_df_fetched.id[0]}' AND org_id = '{org_id}'"
            
        execute_sql_query(agent_update_query)
        
        logger.info(f"contact: {cust_info_df_fetched.contact[0]}, Agent: {agent_username}, org_id: {org_id}, id : {cust_info_df_fetched.id[0]}")
        
        skype_uri = f"skype:{str( cust_info_df_fetched.contact[0] )}?call"
        
    return cust_info_df_fetched, skype_uri

def call_number(number):
    try:
        logger.info(f"Calling number: {number}")

        # Generate Skype URI for the number
        skype_uri = f"skype:{number}?call"
        
        logger.info(skype_uri)

        # Open the Skype URI in a new tab of the default web browser
        webbrowser.open_new_tab(skype_uri)
        
        # Wait for a moment for the Skype app to open
        time.sleep(5)
                
        if (number[1:].isdigit() if number.startswith('+') else number.isdigit()) if number else False:
            # Use pyautogui to simulate a mouse click on the call button
            #pyautogui.click(x=977, y=852)  # Replace with the actual coordinates
            
            logger.info('Number is detected')
            
            button_position = pyautogui.locateOnScreen(call_button_image, confidence=0.6)
            
            logger.info(f"button_position: {button_position}")
            
            if button_position:
                
                 logger.info('Before Click')
                
                 pyautogui.click(button_position)
                
                 logger.info('After Click')

        # Wait for the Enter key to be pressed before continuing to the next call
        #print("Press the Enter key to continue to the next call...")
        #keyboard.wait("enter")
        
        return skype_uri

    except Exception as e:
        logger.error(f"Exception occurred : {e}")
        logger.warning(f"Error calling number: {number}")
