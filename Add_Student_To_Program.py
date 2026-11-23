import pandas as pd
import pyodbc
import json
import tkinter as tk
from tkinter import ttk
from tkcalendar import Calendar
from tqdm import tqdm

# Load all necessary data from the excel an json file
config = json.load(open(r'', 'r'))
excel_file = r''

# Function to run the script
def Add_Student_To_Program():
    connection_string = f'DRIVER={{SQL Server}};SERVER={config['server_name']};DATABASE={config['database_name']};UID={config['username']};PWD={config['password']}'
    connection = pyodbc.connect(connection_string)
    cursor = connection.cursor()

    df = pd.read_excel(excel_file, usecols=('ID number', 'First Name', 'Last Name'))
    pbar = tqdm(total=len(df), desc='Progress')

    selected_date = excel_file.split("/")[1][0:10].split('-')

    # Function to close the script succesfully upon exit
    def on_close():
        connection.close()
        root.quit()
        root.destroy()

    root = tk.Tk()
    root.withdraw()
    root.title('Add Student to PSR Program')

    top = tk.Toplevel(root)
    top.protocol("WM_DELETE_WINDOW", on_close)

    left_frame = tk.Frame(top)
    left_frame.pack(side='left')

    right_frame = tk.Frame(top)
    right_frame.pack(side='right')

    # Creating ComboBox
    options = ['PSRTRIP', 'PSREVENT', 'PSRCLASS']
    combo_var = tk.StringVar()
    combo = ttk.Combobox(right_frame, values=options, textvariable=combo_var, state='readonly')
    if "field-trip" in excel_file:
        combo.current(0)
    elif "trades-lesson" in excel_file:
        combo.current(2)
    else:
        combo.current(1)
    combo.bind("<<ComboboxSelected>>")

    # Creating Calendar
    cal = Calendar(left_frame, selectmode='day', month=int(selected_date[0]), day=int(selected_date[1]), year=int(selected_date[2]))
    date_var = tk.StringVar(value=f"Selected Date: {cal.get_date()}")
    def update_label(event=None):
        date_var.set(f"Selected Date: {cal.get_date()}")
    cal.bind("<<CalendarSelected>>", update_label)

    # Creating Entry for Program Data
    entry = tk.Entry(right_frame)

    def onSubmit():
        program_id = grab_program_event_id(cursor, combo.get())
        for row in df.to_dict('records'):
            student_key = check_student_exists(cursor, list(row.values()))
            if student_key:
                upload_record(cursor, [student_key[0], program_id, cal.get_date(), entry.get()])
        connection.commit()
        connection.close()
        top.destroy()
        root.quit()

    def onCheck():
        program_id = grab_program_event_id(cursor, combo.get())
        count = 0
        for row in df.to_dict('records'):
            student_key = check_student_exists(cursor, list(row.values()))
            try:
                data = check_record_exists(cursor, student_key[0], program_id, cal.get_date())
                if data:
                    print(data)
                    count+=1    
            except:
                continue
        print(f"Total of Students Records Found, {count} out of {len(df)}")

    def onLook():
        count = 0
        missing_list = pd.DataFrame()
        for row in df.to_dict('records'):
            student_key = check_student_exists(cursor, list(row.values()))
            if not (student_key):
                count+=1
                missing_list = pd.concat([missing_list, pd.DataFrame([row])], ignore_index=True)
                print(row)
        print(f"Total of Students not found: {count}")
        if input("Create missing report? (y/n)")[0].lower() == 'y':
            print('Creating Missing Report File')
            missing_list.to_excel(f'files/{excel_file[6:-5]}_missing_list.xlsx', index=False)

    cal.grid(row=0, column=0)
    tk.Label(left_frame, textvariable=date_var).grid(row=1, column=0)    
    combo.grid(row=0, column=0)
    entry.grid(row=1, column=0)
    tk.Button(right_frame, text='Check for Missing', command=onLook).grid(row=2, column=0)
    tk.Button(right_frame, text='Check if Data Exists', command=onCheck).grid(row=3, column=0)
    tk.Button(right_frame, text='Push Data', command=onSubmit).grid(row=4, column=0)

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

def check_record_exists(cursor, data, program_id, date_time):
    cursor.execute("""
        SELECT *
        FROM StudentPrograms
        WHERE SP_Student_TAF_Key = ?
        AND ProgramID = ?
        AND ProgramDateTime = ?
    """, (data, program_id, date_time))
    return cursor.fetchone()

def grab_program_event_id(cursor, program_name):
    cursor.execute("""
    SELECT ProgramID
    FROM ProgramsEvents
    WHERE ProgramAcronym = ? 
    """, program_name)
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