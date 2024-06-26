import streamlit as st
import pandas as pd
from questdb.ingress import Sender
import uuid
from logzero import logger
import logzero
import plotly.express as px
from datetime import datetime, timedelta, date
import time
import datetime


# ef5d909f

import utilities

icon_image = 'icon.jpg'

logzero.logfile("log.log")

st.set_page_config(layout="wide")

host = "13.126.180.220"

conf = "http::addr=13.126.180.220:9000;"

# State management -----------------------------------------------------------

state = st.session_state


def init_state(key, value):
  if key not in state:
    state[key] = value

# generic callback to set state
def _set_state_cb(**kwargs):
    for state_key, widget_key in kwargs.items():
        val = state.get(widget_key, None)
        if val is not None or val == "":
            setattr(state, state_key, state[widget_key])

def _set_login_cb(username, password, org_id):
    state.login_successful, state.role = utilities.login(username, password, org_id)
    
def _reset_login_cb():
    state.login_successful = False
    state.username = ""
    state.password = ""
    state.org_id - ""

init_state('login_successful', False)
init_state('username', '')
init_state('password', '')
init_state('org_id', '')

def main():
    
    col0_0, col0_1 = st.columns([10,1])
    
    with col0_0:
        st.title(":orange[Smartcall]")
        
    with col0_1:
        st.image(icon_image, width=100)
    
    # Get session state
    if "login_successful" not in st.session_state:
        st.session_state.login_successful = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "password" not in st.session_state:
        st.session_state.password = ""
    if "org_id" not in st.session_state:
        st.session_state.org_id = ""
       
    
    # If login is successful
    if state.login_successful:
                
        logged_user_combination = f"{state.username}__{state.password}__{state.org_id}"
        
        id_status = utilities.fetchone_sql_query(f""" SELECT status FROM credentials_smartcall WHERE combination = '{logged_user_combination}' """)
        
        if id_status[0] != 'active':
            st.warning( 'Your ID is deactivated. Please contact admin.')
        else:
        
            if state.role == 'organization_admin':
                                        
                refresh_metrics_value = st.button('Display Metrics')
                            
                col01, col02, col03 = st.columns([2, 3, 2])
                
                if refresh_metrics_value:
                
                    with col01:
                        st.subheader(':green[Call status]', divider='orange')
                                            
                        call_status_grouped_df = utilities.sql_read_query_df(f"SELECT call_status, COUNT(*) AS num_calls FROM contacts_smartcall_2 WHERE org_id = '{state.org_id}' GROUP BY call_status;")
                    
                        st.table( call_status_grouped_df )
                        
                    with col02:
                        st.subheader(':green[Calls per agent]', divider='orange')
                        
                        agent_grouped_df = utilities.sql_read_query_df(f"SELECT agent_username, call_date, COUNT(*) AS num_calls FROM contacts_smartcall_2 WHERE org_id = '{state.org_id}' GROUP BY agent_username, call_date ORDER BY agent_username, call_date;")
                    
                        st.write( agent_grouped_df )
                        
                    with col03:
                        st.subheader(':green[Call action]', divider='orange')
                        
                        actions_grouped_df = utilities.sql_read_query_df(f"SELECT call_action, COUNT(*) AS num_actions FROM contacts_smartcall_2 WHERE org_id = '{state.org_id}' GROUP BY call_action;")
                    
                        st.write( actions_grouped_df )
                        
                    st.subheader(':green[Graphs]', divider='green')
                    
                    col04, col05, col06 = st.columns([2,3,3])
                    
                    with col04:
                    
                        call_status_graph = px.bar(call_status_grouped_df, x='call_status', y='num_calls', title = "Call status distribution", text = 'num_calls', width = 300, labels = { 'call_status': 'Call Status', 'num_calls': 'Number of Calls' } )
                                    
                        st.plotly_chart(call_status_graph)
                        
                    with col05:
                        
                        agents_num_call_df = utilities.sql_read_query_df(f"SELECT agent_username, COUNT(*) AS num_calls FROM contacts_smartcall_2 WHERE org_id = '{state.org_id}' GROUP BY agent_username ORDER BY agent_username;")
                    
                        agent_calls_graph = px.bar(agents_num_call_df.dropna(subset=['agent_username']), x='agent_username', y='num_calls', title = "Calls per agent", text = 'num_calls', width = 500, labels = { 'agent_username': 'Agents', 'num_calls': 'Number of Calls' } )
                                    
                        st.plotly_chart(agent_calls_graph)
                        
                                            
                    with col06:
                    
                        actions_graph = px.bar(actions_grouped_df.dropna(subset=['call_action']), x='call_action', y='num_actions', title = "Actions for various calls", text = 'num_actions', width = 500, labels = { 'call_action': 'Action Type', 'num_actions': 'Number of Actions' } )
                                    
                        st.plotly_chart(actions_graph)
                
                st.subheader(':green[Upload contacts]', divider='orange')
        
                # Input fields
                col1, col2, col3_1, col3_2, col3_3, col3_4, col3_5 = st.columns([3, 2, 2, 2, 2, 2, 1])
                
                with col1:
                    uploaded_file = st.file_uploader("Upload contacts file", type=["csv", "xlsx"])
                    
                if uploaded_file is not None:
                    st.subheader(":green[Uploaded File (first 50 rows shown):]")
                    # Check the file type and read accordingly
                    if uploaded_file.name.endswith(".csv"):
                        uploaded_df = pd.read_csv(uploaded_file, dtype=str)
                    elif uploaded_file.name.endswith((".xls", ".xlsx")):
                        uploaded_df = pd.read_excel(uploaded_file, engine='openpyxl', dtype=str)
                    else:
                        st.error("Invalid file format. Please upload a CSV or Excel file.")
                        return
                            
                    st.dataframe(uploaded_df.head(50))
                            
                
                with col2:
                    contacts_column = st.selectbox("Select contacts column", list( uploaded_df.columns ) if uploaded_file else [], index = None )
                with col3_1:
                    names_column = st.selectbox("Name (Optional)", list( uploaded_df.columns ) if uploaded_file else [], index = None )
                with col3_2:
                    email_column = st.selectbox("Email (Optional)", list( uploaded_df.columns ) if uploaded_file else [], index = None )
                with col3_3:
                    address_column = st.selectbox("Address (Optional)", list( uploaded_df.columns ) if uploaded_file else [], index = None )
                with col3_4:
                    domain_column = st.selectbox("Domain (Optional)", list( uploaded_df.columns ) if uploaded_file else [], index = None )                                    
                with col3_5:
                    st.write('')
                    st.write('')
                    
                    upload_file_button = st.button("Upload", disabled=(uploaded_file is None or not contacts_column))
                    
                    if upload_file_button:
                        
                        insert_df = pd.DataFrame(columns=['id', 'contact', 'customer_name', 'customer_email', 'customer_address', 'customer_domain', 'call_status', 'org_id'], dtype=str)
                        
                        insert_df['contact'] = uploaded_df[contacts_column].values
                        
                        
                        if names_column is not None:
                            insert_df['customer_name'] = uploaded_df[names_column].values
                        else:
                            insert_df['customer_name'] = ''
                                                
                        if email_column is not None:
                            insert_df['customer_email'] = uploaded_df[email_column].values
                        else:
                            insert_df['customer_email'] = ''
                                                
                        if address_column is not None:
                            insert_df['customer_address'] = uploaded_df[address_column].values
                        else:
                            insert_df['customer_address'] = ''
                            
                        if domain_column is not None:
                            insert_df['customer_domain'] = uploaded_df[domain_column].values
                        else:
                            insert_df['customer_domain'] = ''
                        
                        
                        insert_df['file_id'] = uploaded_file.name + '_' + state.org_id + '_' + str( datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') )
                        
                        insert_df['file_status'] = 'active'   #... By default data is active
                                                
                        insert_df['org_id'] = state.org_id
                        
                        insert_df['call_status'] = 'pending'
                                                
                        insert_df['id'] = [ str(uuid.uuid4()) for _ in range(len(uploaded_df)) ]

                        insert_df['timestamp'] = utilities.generate_timestamps(length=len(insert_df), increment=datetime.timedelta(milliseconds=100))
                                                                                            
                        #.. Insert uploaded data to database      
                        with Sender.from_conf(conf) as sender:
                            
                            sender.dataframe(insert_df, table_name='contacts_smartcall_2', at='timestamp')
                            
                        st.success('Data uploaded successfully!')
                
                #.... Data State ....
                
                st.subheader(':green[Mark file status]', divider='orange')
                
                col04_1, col04_2, col04_3 = st.columns([2, 2, 1])
                                                
                contacts_smartcall2_df = utilities.sql_read_query_df(f"select file_id from contacts_smartcall_2 where call_status = 'pending' AND org_id = '{state.org_id}'")
                                
                with col04_1:
                    selected_file_id = st.selectbox("File ID", set( contacts_smartcall2_df.file_id ), key = 'file_id', index = None )
                    
                with col04_2:
                    selected_file_status = st.selectbox("File Status", ['active', 'stale'], key = 'selected_file_status', index = None )
                    
                with col04_3:
                    st.write('')
                    st.write('')
                    
                    if st.button("Update File Status"):
                        
                        if not ( selected_file_id and selected_file_status ):
                            st.markdown("<p style='color: red;'>Please provide all inputs.</p>", unsafe_allow_html=True)
                        else:
                            utilities.execute_sql_query( f"UPDATE contacts_smartcall_2 SET file_status = '{selected_file_status}' WHERE file_id = '{selected_file_id}'" )
                           
                        st.success( 'File status updated !' )
                
                # Display Files Info
                
                st.subheader(':green[Files Info]', divider='orange')
                
                files_info_df = utilities.sql_read_query_df( f"""SELECT file_id, file_status,
                                                            
                       COUNT(*) AS total_records,
                       
                       SUM(CASE WHEN call_status = 'pending' THEN 1 ELSE 0 END) AS calls_pending,
                       
                       SUM(CASE WHEN call_status = 'ongoing' THEN 1 ELSE 0 END) AS calls_ongoing,
                       
                       SUM(CASE WHEN call_status = 'complete' THEN 1 ELSE 0 END) AS calls_complete
                       
                FROM contacts_smartcall_2 WHERE org_id = '{state.org_id}' GROUP BY file_id, file_status;""" )
                
                if st.button("Display Files Info"):
                    
                    st.write( files_info_df )
                
                #.... Create new agent logic
                
                st.subheader(':green[Create new agent]', divider='orange')
                
                # Input fields
                col4, col5, col6, col7 = st.columns([2, 2, 2, 1])
                
                with col4:
                    new_agent_name = st.text_input("Name", key = 'new_agent_name', max_chars = 100 )            
                with col5:
                    new_agent_username = st.text_input("Username", key = 'new_agent_username', max_chars = 100 )
                with col6:
                    new_agent_password = st.text_input("Password", key = 'new_agent_password', max_chars = 100 )
                    
                with col7:
                    st.write('')
                    st.write('')
                    
                    create_new_agent_button = st.button("Create New Agent")
                    
                    if create_new_agent_button:
                        if not ( new_agent_name and new_agent_username and new_agent_password ):
                            st.markdown("<p style='color: red;'>Please provide all inputs.</p>", unsafe_allow_html=True)
                        else:
                            
                            org_max_agents_df = utilities.sql_read_query_df(f"select max_active_agents from credentials_smartcall where role = 'organization_admin' AND org_id = '{state.org_id}'")
                            
                            org_max_agents = org_max_agents_df['max_active_agents'].iloc[0]
                            
                            num_agents_df = utilities.sql_read_query_df(f"select COUNT(*) from credentials_smartcall where role = 'agent' AND status = 'active' AND org_id = '{state.org_id}'")
                            
                            num_agents = num_agents_df['count'].iloc[0]
                                                        
                            if int( num_agents ) == int( org_max_agents ):
                                st.markdown("<p style='color: red;'>Maximum active agents limit is reached. Subscribe for more active agents addition.</p>", unsafe_allow_html=True)
                            else:
                            
                                data_new_agent = {
                                    'name': [new_agent_name],
                                    'username': [new_agent_username],
                                    'password': [new_agent_password],
                                    'org_id': state.org_id,
                                    'role': 'agent',
                                    'status': 'active',
                                    'timestamp': utilities.generate_timestamps(length=1, increment=datetime.timedelta(milliseconds=100))
                                }
                            
                                # Create a DataFrame
                                new_agent_df = pd.DataFrame(data_new_agent)
                                                                               
                                new_user_combination = f"{new_agent_username}__{new_agent_password}__{new_agent_df.org_id[0]}"
                                                       
                                new_agent_df['combination'] = new_user_combination
                                                                                            
                                if utilities.valid_user( new_user_combination ):
                                    st.error('This username and password combination already exists.')
                                else:
                                    with Sender.from_conf(conf) as sender:
                                        sender.dataframe(new_agent_df, table_name='credentials_smartcall', at='timestamp')
                                                                            
                                    st.success( 'New agent created successfully !' )
                
                # Logic to enable or disable agent
                
                st.subheader(':green[Configure agent]', divider='orange')
                
                col8, col9, col9_1, col10 = st.columns([2, 2, 2, 2])
                
                #if create_new_agent_button:
                
                org_agents_df = utilities.sql_read_query_df(f"select combination from credentials_smartcall where role = 'agent' AND org_id = '{state.org_id}'")
                
                
                # unique_groups_list_0 = list( org_agents_df.grouping.unique() )
                
                # unique_groups_list = list(set(i for unique_groups_list_0 in [item.split(',') for item in unique_groups_list_0] for i in unique_groups_list_0))
                                
                with col8:
                    agent_combination = st.selectbox("Agent Combination", list( org_agents_df.combination ), key = 'agent_combination', index = None )
                            
                with col9:
                    agent_new_status = st.selectbox("Status", ['active', 'inactive'], key = 'agent_new_status', index = None )
                
                with col9_1:
                    agent_reset_password = st.text_input("Reset Password (Optional)", key = 'reset_agent_password', max_chars = 100 )
                
                
                with col10:
                    st.write('')
                    st.write('')
                    
                    if st.button("Update Agent Info"):
                        if not ( agent_combination and agent_new_status ):
                            st.markdown("<p style='color: red;'>Please provide required inputs.</p>", unsafe_allow_html=True)
                        else:
                                                                                        
                            utilities.execute_sql_query( f"UPDATE credentials_smartcall SET status = '{agent_new_status}' WHERE combination = '{agent_combination}'" )
                            
                            if agent_reset_password != '':
                                
                                effective_agent_username = agent_combination.split('__')[0]
                                
                                new_user_combination = f"{effective_agent_username}__{agent_reset_password}__{state.org_id}"
                                
                                utilities.execute_sql_query( f"UPDATE credentials_smartcall SET password = '{agent_reset_password}', combination = '{new_user_combination}' WHERE combination = '{agent_combination}'" )
                                                                                          
                            st.success( 'Agent status updated !' )
                
                # Display agent table
                
                st.subheader(':green[Agents table]', divider='orange')
                
                if st.button( 'Display Agents Table' ):
    
                    org_agents_df = utilities.sql_read_query_df(f"select name, username, password, org_id, role, combination, status, grouping, timestamp from credentials_smartcall where role = 'agent' AND org_id = '{state.org_id}'")
                    
                    st.write( org_agents_df )
                
                #.... View existing contacts data ...
                
                st.subheader(':green[Existing contacts data]', divider='orange')
                
                # Input fields
                col11, col12, col13 = st.columns([2, 2, 1])
                            
                with col11:
                    from_date = st.date_input("From Date (GMT timezone)", date.today() - timedelta(days=7) )            
                with col12:
                    to_date = st.date_input("To Date (GMT timezone)")
                
                filtered_contacts_df = pd.DataFrame()    
                
                with col13:
                    st.write('')
                    st.write('')
                    
                    if st.button("View Contacts Data"):
                        if to_date < from_date :
                            st.markdown("<p style='color: red;'>To Date cannot be earlier than From Date</p>", unsafe_allow_html=True)
                        else:
                            filtered_contacts_df = utilities.sql_read_query_df( f"select * from contacts_smartcall_2 where org_id = '{state.org_id}' AND timestamp >= '{from_date} 00:00:00' AND timestamp <= '{to_date} 23:59:59' ")
                            
                st.write( filtered_contacts_df )
                                        
            elif state.role == 'admin':
                
                admin_refresh_metrics_value = st.button('Display Stats')
                            
                col120_0, col120_1 = st.columns([3, 4])
                
                if admin_refresh_metrics_value:
                    
                    #..... Drop Table Partitions ....
                    
                    data_deletion_date = ( date.today() - timedelta( days = 5 ) ).strftime( '%Y-%m-%d' )
                    
                    utilities.execute_sql_query( f"ALTER TABLE contacts_smartcall_2 DROP PARTITION WHERE timestamp < to_timestamp( '{data_deletion_date}', 'yyyy-MM-dd');" )
                    
                    org_info = utilities.sql_read_query_df("SELECT name, org_id FROM credentials_smartcall WHERE role = 'organization_admin';")
                                                                            
                    with col120_0:
                        st.subheader(':green[Agents per org]', divider='orange')
                                            
                        agents_per_org_df_0 = utilities.sql_read_query_df("SELECT org_id, status, COUNT(*) AS num_agents FROM credentials_smartcall WHERE role = 'agent' GROUP BY org_id, status ORDER BY org_id, status;")
                        
                        agents_per_org_df = pd.merge( agents_per_org_df_0, org_info, on = 'org_id', how = 'left' )
                    
                        st.write( agents_per_org_df[ [ 'name', 'org_id', 'status', 'num_agents' ] ] )
                        
                    with col120_1:
                        st.subheader(':green[Calls per agent per org]', divider='orange')
                        
                        calls_per_agent_per_org_df_0 = utilities.sql_read_query_df("SELECT org_id, agent_username, call_status, call_date, COUNT(*) AS num_calls FROM contacts_smartcall_2 GROUP BY org_id, agent_username, call_date, call_status ORDER BY org_id, agent_username, call_date, call_status;")
                        
                        calls_per_agent_per_org_df = pd.merge( calls_per_agent_per_org_df_0, org_info, on = 'org_id', how = 'left' )
                    
                        st.write( calls_per_agent_per_org_df[ [ 'name', 'org_id', 'call_date', 'agent_username', 'call_status', 'num_calls' ] ] )
                
                #.... User creation .....
                
                st.subheader(':green[User Creation]', divider='orange')
                
                col120, col121, col122, col123, col124 = st.columns([2, 2, 2, 2, 1])
                
                with col120:
                    new_name = st.text_input("Name", key = 'new_name', max_chars = 100 )            
                with col121:
                    new_username = st.text_input("Username", key = 'new_username', max_chars = 100 )
                with col122:
                    new_password = st.text_input("Password", key = 'new_password', max_chars = 100 )
                with col123:
                    new_role = st.selectbox("Role", ['organization_admin', 'referral'], key = 'new_role', index = None )
                with col124:
                    st.write('')
                    st.write('')
                    if st.button("Create New User"):
                        if not ( new_name and new_username and new_password and new_role ):
                            st.markdown("<p style='color: red;'>Please provide all inputs.</p>", unsafe_allow_html=True)
                        else:
                            data_new_user = {
                                'name': [new_name],
                                'username': [new_username],
                                'password': [new_password],
                                'role': [new_role],
                                'status': 'active',
                                'max_active_agents': '5',
                                'data_retention_days': '10',
                                'timestamp': utilities.generate_timestamps(length=1, increment=datetime.timedelta(milliseconds=100))
                            }
                        
                            # Create a DataFrame
                            new_user_df = pd.DataFrame(data_new_user)
                                                                            
                            new_user_df['org_id'] = 'nextgenai' if new_role == 'referral' else utilities.generate_unique_id(8)
                                                   
                            new_user_combination = f"{new_username}__{new_password}__{new_user_df.org_id[0]}"
                                                   
                            new_user_df['combination'] = new_user_combination
                            
                            print( new_user_df )
                            
                            new_user_df.to_csv('new_user_df.csv', index=False)
                                                                                            
                            if utilities.valid_user( new_user_combination ):
                                st.error('This username and password combination already exists.')
                            else:
                                with Sender.from_conf(conf) as sender:
                                    sender.dataframe(new_user_df, table_name='credentials_smartcall', at='timestamp')
                                                                    
                                st.success( 'New user created successfully !' )
                
                #.... Configure Organization Admin .....
                
                st.subheader(':green[Configure Organization]', divider='orange')
                            
                col125, col126, col127, col128 = st.columns([2, 2, 2, 1])
                                        
                org_admin_df = utilities.sql_read_query_df("select * from credentials_smartcall where role = 'organization_admin'")
                            
                with col125:
                    org_combination = st.selectbox("Organization Combination", list( org_admin_df.combination ), index = None )            
                with col126:
                    max_active_agents = st.number_input("Max active agents", min_value=0, max_value=10000, value=None, step = 1)
                with col127:
                    retention_days = st.number_input("Number of Days data retained", min_value=1, max_value=5*365, value=None, step = 1)
                with col128:
                    st.write('')
                    st.write('')
                    if st.button("Configure Organization"):
                        if not ( org_combination and max_active_agents and retention_days ):
                            st.markdown("<p style='color: red;'>Please provide all inputs.</p>", unsafe_allow_html=True)
                        else:
                            utilities.execute_sql_query( f"UPDATE credentials_smartcall SET max_active_agents = '{max_active_agents}', data_retention_days = '{retention_days}' WHERE combination = '{org_combination}'" )
                            st.success('Configuration updated successfully !')
                
                # Logic to enable or disable organization_admin
                
                st.subheader(':green[Enable/Disable Organization]', divider='orange')
                
                col129, col130, col131 = st.columns([2, 2, 1])
                
                org_df = utilities.sql_read_query_df(f"select * from credentials_smartcall where role = 'organization_admin'")
                
                with col129:
                    org_combination = st.selectbox("Organization Combination", list( org_df.combination ), key = 'org_combination', index = None )
                            
                with col130:
                    org_new_status = st.selectbox("Status", ['active', 'inactive'], key = 'org_new_status', index = None )
                    
                with col131:
                    st.write('')
                    st.write('')
                    
                    if st.button("Update Organization Status"):
                        if not ( org_combination and org_new_status ):
                            st.markdown("<p style='color: red;'>Please provide all inputs.</p>", unsafe_allow_html=True)
                        else:
                            utilities.execute_sql_query( f"UPDATE credentials_smartcall SET status = '{org_new_status}' WHERE combination = '{org_combination}'" )
                           
                        st.success( 'Organization status updated !' )
                        
                st.subheader(':green[Credentials Table]', divider='orange')
                                               
                if st.button( 'Display Credentials Table' ):
                    
                    credentials_df = utilities.sql_read_query_df("select * from credentials_smartcall")
                    
                    st.write( credentials_df )
                    
            elif state.role == 'agent':
                            
                # if 'call_feedback' not in st.session_state:
                #     st.session_state.call_feedback = 'None'
                    
                if 'cust_info_df' not in st.session_state:
                    st.session_state.cust_info_df = pd.DataFrame( columns=['contact', 'customer_name', 'customer_email', 'customer_address', 'customer_domain'])
                                                    
                
                st.subheader(':green[Customer Info]', divider='green')
                
                st.table( st.session_state.cust_info_df[ ['contact', 'customer_name', 'customer_email', 'customer_address', 'customer_domain'] ] )
                
                if len( st.session_state.cust_info_df ) > 0:
                               
                    url = st.session_state.cust_info_df.customer_domain[0]

                    if url is not None:
                    
                        customer_url_w_protocol = 'http://' + url if not url.startswith(('http://', 'https://')) else url
                    
                        st.markdown(f"[Visit Domain]({customer_url_w_protocol})", unsafe_allow_html=True)
                                        
                st.subheader(':green[Operations]', divider='green')
                
                col201_0, col201_1, col201_2, col201_3 = st.columns([1, 1, 2, 1])
            
                with col201_0:
                    
                    st.write('')
                    
                    st.write('')
                    
                    start_call_button = st.button("Start Call", use_container_width=True)
                                    
                    # Add callback to reset call_feedback using session state
                    if start_call_button:
                        
                        st.session_state.call_feedback = 'None'
                        
                        st.session_state.cust_info_df, skype_uri = utilities.next_iteration( st.session_state.org_id, st.session_state.username )
                                                                                
                        if len( st.session_state.cust_info_df ) == 0:
                            st.markdown( "No more numbers to call !" )
                        else:
                            st.markdown(f'<meta http-equiv="refresh" content="0;URL={skype_uri}">', unsafe_allow_html=True)
                            
                with col201_1:
                    
                    st.write('')
                    
                    st.write('')
                    
                    pause_button = st.button("Submit Feedback & Pause", use_container_width=True)
                    
                with col201_2:
                    # Display the dropdown with the updated call_feedback from session state
                    st.session_state.call_feedback = st.selectbox("Feedback", ['None', 'Not Available', 'Rejected', 'Not Interested', 'Call back', 'Answering Machine'])
                    
                with col201_3:
                    
                    st.write('')
                    
                    st.write('')
                    
                    feedback_button = st.button("Submit Feedback & Next Call", use_container_width=True)
                    
                    if feedback_button or pause_button:
                        
                        #... Submitting Feedback ...
                        
                        if len( st.session_state.cust_info_df ) > 0:
                                                        
                            call_update_status_query = f"UPDATE contacts_smartcall_2 SET call_status = 'complete', call_action = '{st.session_state.call_feedback}' WHERE id = '{st.session_state.cust_info_df.id[0]}' AND org_id = '{st.session_state.org_id}'"
                            
                            utilities.execute_sql_query(call_update_status_query)
                            
                            st.markdown( f"Status Updated: {st.session_state.call_feedback}" )
                            
                            logger.info(f"Finished Calling and status updated : {st.session_state.call_feedback}")
                            
                        #... Calling next number...
                        
                        if not pause_button:
                        
                            st.session_state.cust_info_df, skype_uri = utilities.next_iteration( st.session_state.org_id, st.session_state.username )
                                                                                    
                            if len( st.session_state.cust_info_df ) == 0:
                                st.markdown( "No more numbers to call !" )
                            else:
                                st.markdown(f'<meta http-equiv="refresh" content="0;URL={skype_uri}">', unsafe_allow_html=True)
                            
                        print( pause_button )
                                
                st.subheader(':green[Metrics]', divider='green')
                
                display_agent_metrics = st.button( "Display Metrics" )
                
                col202, col203, col204 = st.columns([10, 1, 10])
                
                if display_agent_metrics:
                    
                    current_date = date.today()
                                        
                    seven_days_ago = current_date - timedelta(days=7)
                                    
                    with col202:
                                        
                        todays_agent_stats_df = utilities.sql_read_query_df( f"SELECT call_action, COUNT(*) AS num_calls FROM contacts_smartcall_2 WHERE agent_username = '{st.session_state.username}' AND org_id = '{st.session_state.org_id}' AND call_date = '{current_date}' GROUP BY call_action;" )
                                            
                        fig = px.bar(todays_agent_stats_df, x='call_action', y='num_calls', title = "Today's Distribution of calls by Feedback" )
                                    
                        st.plotly_chart(fig)
                        
                    with col203:
                        st.write('')
                        
                    with col204:
                        
                        agent_call_freq_df = utilities.sql_read_query_df( f"SELECT call_date, COUNT(*) AS num_calls FROM contacts_smartcall_2 WHERE agent_username = '{st.session_state.username}' AND org_id = '{st.session_state.org_id}' AND timestamp >= '{seven_days_ago}' AND timestamp <= '{current_date} 23:59:59' GROUP BY call_date;" )
                        
                                        
                        fig2 = px.line(agent_call_freq_df, x="call_date", y="num_calls", title='Calls Frequency for Last 7 Days', markers = True )
                                                
                        st.plotly_chart(fig2)
                
            elif state.role == 'referral':
                pass
    else:
        st.subheader(":green[Login]")
        # Display login form
        st.text_input(
            "Organization ID:", value=state.org_id, key='org_id_input',
            on_change=_set_state_cb, kwargs={'org_id': 'org_id_input'}
        )
        st.text_input(
            "Username:", value=state.username, key='username_input',
            on_change=_set_state_cb, kwargs={'username': 'username_input'}
        )
        st.text_input(
            "Password:", type="password", value=state.password, key='password_input',
            on_change=_set_state_cb, kwargs={'password': 'password_input'}
        )
                
        login_button = st.button("Login", on_click=_set_login_cb, args=(state.username, state.password, state.org_id))
        
        # Check login credentials
        if not state.login_successful and login_button:
            st.warning("Wrong Credentials !")
                              
    

if __name__ == "__main__":
    main()

        
