import pandas as pd
import pyodbc
import json
import tkinter as tk
from tkinter import simpledialog
from tkcalendar import Calendar
from tqdm import tqdm

# Load all necessary data from the excel an json file
config = json.load(open(r'', 'r'))
excel_file = r''

# What's the best way to add date, do we hard code it?
# Have a pop-up for a date based on the file name and would need to re-adjusted if needed

def Add_Student_To_Program():
    connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={config['server_name']};DATABASE={config['database_name']};UID={config['username']};PWD={config['password']}'
    connection = pyodbc.connect(connection_string)
    cursor = connection.cursor()

    df = pd.read_excel(excel_file)
    pbar = tqdm(total=len(df), desc='Progress')

    selected_date = excel_file.split("/")[1][0:10].split('-')

    def on_close():
        root.quit()
        root.destroy()

    root = tk.Tk()
    root.withdraw()
    root.title('Check Date')

    top = tk.Toplevel(root)
    top.protocol("WM_DELETE_WINDOW", on_close)
    top.title('Check Date')

    cal = Calendar(top, selectmode='day', month=int(selected_date[0]), day=int(selected_date[1]), year=int(selected_date[2]))
    cal.pack()

    date_var = tk.StringVar(value=f"Selected Date: {cal.get_date()}")

    def update_label(event=None):
        date_var.set(f"Selected Date: {cal.get_date()}")

    cal.bind("<<CalendarSelected>>", update_label)

    def onSubmit():
        program_id = grab_program_event_id(cursor)
        for row in df.to_dict('records'):
            student_key = check_student_exists(cursor, list(row.values()))
            if student_key:
                upload_record(cursor, [student_key[0], program_id, cal.get_date(), ''])
        connection.commit()
        connection.close()
        top.destroy()
        root.quit()

    tk.Label(top, textvariable=date_var).pack()
    tk.Button(top, text='Ok', command=onSubmit).pack()

    root.mainloop()
    root.destroy()

    
def check_student_exists(cursor, row):
    cursor.execute("""
        SELECT Student_TAF_Key
        FROM Student
        WHERE Student_School_Name = 'Technology Access Foundation Academy at Saghalie'
        AND Student_ID = ?
        AND Student_Name_First = ?
        AND Student_Name_Last = ?
    """, (row))
    return cursor.fetchone()

def grab_program_event_id(cursor):
    cursor.execute("""
    SELECT ProgramID
    FROM ProgramsEvents
    WHERE ProgramAcronym = 'PSRTRIP' 
    """)
    return cursor.fetchone()[0]

def upload_record(cursor, data):
    cursor.execute(
        '''
        SELECT *
        FROM StudentPrograms
        WHERE SP_Student_TAF_Key = ?
        AND ProgramID = ?
        AND ProgramDateTime = ?
        AND SP_ProgramData = ?
        '''
    , data)
    fetch = cursor.fetchall()
    if not (fetch):
        cursor.execute(
            '''
            INSERT INTO StudentPrograms(SP_Student_TAF_Key, ProgramID, ProgramDateTime, SP_ProgramData)
            VALUES(?, ?, ?, ?)
            '''
        , data)
    
Add_Student_To_Program()