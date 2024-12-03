from model.Vaccine import Vaccine
from model.Caregiver import Caregiver
from model.Patient import Patient
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql
import datetime
import random


'''
objects to keep track of the currently logged-in user
Note: it is always true that at most one of currentCaregiver and currentPatient is not null
        since only one user can be logged-in at a time
'''
current_patient = None

current_caregiver = None


def create_patient(tokens):
    if len(tokens) != 3:
        print("Failed to create user.")
        return
    
    username = tokens[1]
    password = tokens[2]

    if(username_exists_patient(username)):
        print("Username taken, try again.")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)
    
    # create the caregiver
    patient = Patient(username, salt=salt, hash=hash)

    # save to caregiver information to our database
    try:
        patient.save_to_db()
    except pymssql.Error as e:
        print("Create patient failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Create patient failed.")
        print(e)
        return
    print("Created user ", username)

    pass

def username_exists_patient(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Patients WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def create_caregiver(tokens):
    # create_caregiver <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_caregiver(username):
        print("Username taken, try again!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the caregiver
    caregiver = Caregiver(username, salt=salt, hash=hash)

    # save to caregiver information to our database
    try:
        caregiver.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)


def username_exists_caregiver(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Caregivers WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def login_patient(tokens):
    # login_caregiver <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_patient
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    patient = None
    try:
        patient = Patient(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if patient is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_patient = patient
    pass


def login_caregiver(tokens):
    # login_caregiver <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_caregiver
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    caregiver = None
    try:
        caregiver = Caregiver(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if caregiver is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_caregiver = caregiver


def search_caregiver_schedule(tokens):
    # Output the username for the caregiver that are available for the date ordered
    # output the vaccine name and number of available doeses for the vaccine
    global current_caregiver

    if(current_caregiver is None and current_patient is None):
        print("Please login first")
        return

    date = tokens[1].split("-")
 

    if(len(date[0]) != 2 or len(date[1]) != 2 or len(date[2]) < 4 or int(date[0]) < 1 or int(date[0]) > 31 or int(date[1]) < 1 or int(date[1]) > 12):
        print("Please try again")
        return
    
    date_str = f"{date[2]}-{date[1]}-{date[0]}"

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)
   
    availabilities = """SELECT DISTINCT Username
                            FROM Availabilities
                            WHERE Time = %s
                            ORDER BY Username ASC;
                        """
                    
    vacines = "SELECT * FROM Vaccines;"
    try:
        cursor.execute(availabilities, date_str)
        for caregiver in cursor:
            print(caregiver['Username'])
            
        cursor.execute(vacines)
        for vacine in cursor:
            print(f"{vacine['Name']} {vacine['Doses']}")
        
    except pymssql.Error as e:
        raise e
    finally:
        cm.close_connection()
    return None
    



def reserve(tokens):
    #Patients perform to reserve an appointment
    #Caregivers can only see one patient per day
    global current_patient
    
    if(current_patient is None):
        print("Please login first")
        return
    
    date = tokens[1].split("-")
 
    if(len(date[0]) != 2 or len(date[1]) != 2 or len(date[2]) < 4 or int(date[0]) < 1 or int(date[0]) > 31 or int(date[1]) < 1 or int(date[1]) > 12):
        print("Please try again")
        return
    
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict = True)
    
    get_caregiver = """
                    SELECT C.Username
                        FROM Caregivers as C, Availabilities as A
                        WHERE A.Time = %s AND
                        A.Username = C.Username AND
                        C.Username NOT IN (
                            SELECT Cname
                                FROM Reservations
                                WHERE Time = %s
                            )
                        ORDER BY C.Username ASC
                    """
    
    get_num_vaccine = """
                    SELECT Doses
                        FROM Vaccines
                        WHERE Name = %s;
                    """
    
    get_reservation_ids = """
                            SELECT id
                              FROM Reservations;
                        """
    
    update_reservation = """
                            INSERT INTO Reservations 
                             VALUES (%s, %s, %s, %s, %s);
                        """
    try:
        cursor.execute(get_caregiver, (tokens[1], tokens[1]))
        caregiver = cursor.fetchone()
        
        if(caregiver is None):
            print("No results found")
            return 
        
        cursor.execute(get_num_vaccine, tokens[2])
        amount_left_vaccine = cursor.fetchone()
        
        if (amount_left_vaccine is None or amount_left_vaccine['Doses'] == 0):
            print("Not enough available doses")
            return
        
        cursor.execute(get_reservation_ids)
        existing_ids = [row[0] for row in cursor]
        
        rand_id = random.randint(0,10**100)
        while rand_id in existing_ids:
            rand_id = random.randint(0, 10**100)
        
        date_str = f"{date[2]}-{date[1]}-{date[0]}"
        the_tuple = (current_patient.username, caregiver['Username'], tokens[2], date_str, rand_id)
        
        cursor.execute(update_reservation, the_tuple)
        conn.commit()
        
        print(f"Appointment ID {rand_id}, Caregiver username {caregiver['Username']}")
    except pymssql.Error as e:
        raise e
    finally:
        cm.close_connection()
    return None
    



def upload_availability(tokens):
    #  upload_availability <date>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        d = datetime.datetime(year, month, day)
        current_caregiver.upload_availability(d)
    except pymssql.Error as e:
        print("Upload Availability Failed")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please enter a valid date!")
        return
    except Exception as e:
        print("Error occurred when uploading availability")
        print("Error:", e)
        return
    print("Availability uploaded!")


def cancel(tokens):
    global current_caregiver

    if(current_caregiver is None and current_patient is None):
        print("Please login first")
        return
    
    if(len(tokens) < 2 or len(tokens) > 2):
        print("Enter a valid reservation ID")
        return
    
    check_appointment_exists = """
                            SELECT id
                            FROM Reservations;
                            """
    delete_appointment = """
                        DELETE FROM Reservations WHERE id = %s;
                        """
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict = True)
    
    try:
        cursor.execute(check_appointment_exists)
        first_id = cursor.fetchall()
        if(first_id is None):
            print("There are no Appointments")
            return
        
        appointments = [row['id'] for row in cursor]
        
        if(int(tokens[1]) not in appointments):
            print("There is no such Appointment")
            print("These are the exsisting appointments")
            print(f" - {first_id[0]['id']}")
            for id in appointments:
                print(" - ", id)
            return
        
        cursor.execute(delete_appointment, tokens[1])
        print("Successfully deleted the appointment: ", tokens[1])
        
    except pymssql.Error as e:
        raise e
    finally:
        cm.close_connection()
    return

def add_doses(tokens):
    #  add_doses <vaccine> <number>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    #  check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    vaccine_name = tokens[1]
    doses = int(tokens[2])
    vaccine = None
    try:
        vaccine = Vaccine(vaccine_name, doses).get()
    except pymssql.Error as e:
        print("Error occurred when adding doses")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when adding doses")
        print("Error:", e)
        return

    # if the vaccine is not found in the database, add a new (vaccine, doses) entry.
    # else, update the existing entry by adding the new doses
    if vaccine is None:
        vaccine = Vaccine(vaccine_name, doses)
        try:
            vaccine.save_to_db()
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    else:
        # if the vaccine is not null, meaning that the vaccine already exists in our table
        try:
            vaccine.increase_available_doses(doses)
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    print("Doses updated!")


def show_appointments(tokens):
    global current_caregiver
    global current_patient
    
    person = ''
    
    if(current_patient is not None):
        person = 'Cname'
    elif(current_caregiver is not None):
        person = 'Vname'
    else:
        print("Please login first")
        return
    
    get_appointments = f"""
                    SELECT id, Vname, Time, {person}
                        FROM Reservations;
                    """
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict = True)
    
    try:
        cursor.execute(get_appointments, person)
        for r in cursor:
            print(f"{r['id']} {r['Vname']} {r['Time']} {r[person]}")
    except pymssql.Error as e:
        raise e
    finally:
        cm.close_connection()
    return


def logout(tokens):
    global current_caregiver
    global current_patient
    if(current_patient is None and current_caregiver is None):
        print("Please login first")
        return
    if(current_caregiver is not None):
        current_caregiver = None
    elif(current_patient is not None):
        current_patient = None
    print("Successfully logged out")
    
    return


def start():
    stop = False
    print()
    print(" *** Please enter one of the following commands *** ")
    print("> create_patient <username> <password>")  # //TODO: implement create_patient (Part 1)
    print("> create_caregiver <username> <password>")
    print("> login_patient <username> <password>")  # // TODO: implement login_patient (Part 1)
    print("> login_caregiver <username> <password>")
    print("> search_caregiver_schedule <date>")  # // TODO: implement search_caregiver_schedule (Part 2)
    print("> reserve <date> <vaccine>")  # // TODO: implement reserve (Part 2)
    print("> upload_availability <date>")
    print("> cancel <appointment_id>")  # // TODO: implement cancel (extra credit)
    print("> add_doses <vaccine> <number>")
    print("> show_appointments")  # // TODO: implement show_appointments (Part 2)
    print("> logout")  # // TODO: implement logout (Part 2)
    print("> Quit")
    print()
    while not stop:
        response = ""
        print("> ", end='')

        try:
            response = str(input())
        except ValueError:
            print("Please try again!")
            break

        response = response.lower()
        tokens = response.split(" ")
        if len(tokens) == 0:
            ValueError("Please try again!")
            continue
        operation = tokens[0]
        if operation == "create_patient":
            create_patient(tokens)
        elif operation == "create_caregiver":
            create_caregiver(tokens)
        elif operation == "login_patient":
            login_patient(tokens)
        elif operation == "login_caregiver":
            login_caregiver(tokens)
        elif operation == "search_caregiver_schedule":
            search_caregiver_schedule(tokens)
        elif operation == "reserve":
            reserve(tokens)
        elif operation == "upload_availability":
            upload_availability(tokens)
        elif operation == "cancel":
            cancel(tokens)
        elif operation == "add_doses":
            add_doses(tokens)
        elif operation == "show_appointments":
            show_appointments(tokens)
        elif operation == "logout":
            logout(tokens)
        elif operation == "quit":
            print("Bye!")
            stop = True
        else:
            print("Invalid operation name!")


if __name__ == "__main__":
    '''
    // pre-define the three types of authorized vaccines
    // note: it's a poor practice to hard-