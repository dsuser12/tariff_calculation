import pyodbc 

def server_access():
    database = 'CARGO'
    server = '10.10.10.80,9003'  
    username = 'dataservice' 
    password = 'dsDnata123$' 
    server_cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    return server_cnxn
