from threading import Thread, Semaphore
from datetime import datetime
import time
import random

# Some constants
NUM_DOCTORS = 2
NUM_CHAIRS = 2
TREATMENT_DURATION = 2

# Semaphores for waiting room
waiting_room_mutex = Semaphore(value=1)                                #binary semaphore(Waiting room's lock)
waiting_room_free_chairs = Semaphore(value=NUM_CHAIRS)                  #counting semaphore

doctors_mutex = Semaphore(value=1)                                      #binary semaphore for doctors status(shared data)
free_doctor_rooms = Semaphore(value=0)                                  #counting semaphore

# Shared data
'''Since we are not able to access the values of semaphores,
   we define these variable to be just a copy of our counting semaphores '''
number_of_free_doctors = 0              #It will become NUM_DOCTORS after initializing the doctor threads
number_of_free_chairs = NUM_CHAIRS

# A list of doctors in the building
doctors = []

class DoctorsBuilding:
    def __init__(self, waiting_room_chairs : int, number_of_doctors : int):
        self.waiting_room_chairs = waiting_room_chairs
        self.number_of_doctors = number_of_doctors

        print('The building is now open!')
        print('Number of doctors in the building: {0}'.format(self.number_of_doctors))
        print('Number of chairs in the waiting room: {0}'.format(self.waiting_room_chairs))
        print('---------------------------------------------------------------------------')

        #Initializing the doctor threads
        for i in range(NUM_DOCTORS):
            new_doctor = Doctor(doctor_name=i)
            doctors.append(new_doctor)
            new_doctor.start()


class Doctor(Thread):
    def __init__(self, doctor_name : int):
        Thread.__init__(self)
        self.doctor_name = doctor_name
        self.is_busy = Semaphore(value=0)                               # A binary semaphore for each doctor
        self.status = 'FREE'                                            # Firstly he is free when he enters the building

    def run(self) -> None:
        while(True):
            print('Doctor {0} is now free!'.format(self.doctor_name))
            free_doctor_rooms.release()                                 # At first, makes himself free
            self.is_busy.acquire()                                      # He waits till a patient enters his room
            print('Doctor {0} is now treating {1}.'.format(self.doctor_name, self.current_patient.name))
            self.treat(doctor_room_entry_time=int(round(time.time() * 1000)))
            print('<< {0} is done! He is leaving the building.(exit time: {1})'.format(self.current_patient.name, datetime.now().strftime("%H:%M:%S")))
            doctors_mutex.acquire()                                     # Since we want to change the status of the doctor
            self.set_status('FREE')
            self.current_patient.in_doctor_room.release()               # Doctor tell his patiet that he can leave the room
            doctors_mutex.release()


    def set_patient(self, current_patient):
        self.current_patient = current_patient
    def set_status(self, status : str):
        self.status = status
    def get_status(self):
        return self.status

    def treat(self, doctor_room_entry_time : int) -> None:
        '''This is for treatment, it takes TREATMENT_DURATION to execute. '''
        current_time = int(round(time.time() * 1000))
        while(current_time - doctor_room_entry_time < TREATMENT_DURATION * 1000):
            current_time = int(round(time.time() * 1000))

class Patient(Thread):
    def __init__(self, name, entry_time):
        Thread.__init__(self)
        self.name = str(name)
        self.entry_time = int(entry_time)
        self.waiting_room_mutex = waiting_room_mutex
        self.waiting_room_free_chairs = waiting_room_free_chairs
        self.free_doctor_rooms = free_doctor_rooms
        self.in_doctor_room = Semaphore(value=0)

    def run(self) -> None:
        global number_of_free_chairs
        global number_of_free_doctors

        time.sleep(self.entry_time)

        waiting_room_mutex.acquire()                        #wait until it gets the waiting room lock
        if (number_of_free_chairs == 0):
            print('Waiting room is full, {0} is leaving.'.format(self.name))
            waiting_room_mutex.release()                    #release the lock immediatly
        else:
            print('>> {0} entered the building and is looking for a seat.(entry time: {1})'.format(self.name, datetime.now().strftime("%H:%M:%S")))
            waiting_room_free_chairs.acquire()              #wait for finding a free chair to seat on
            print('{0} sat down on a chair in the waiting room.'.format(self.name))
            number_of_free_chairs -= 1

            if (number_of_free_doctors > 0):
                free_doctor_rooms.acquire()                 #wait for a free doctor
                number_of_free_doctors -= 1
                waiting_room_free_chairs.release()
                number_of_free_chairs += 1
                waiting_room_mutex.release()
            else:
                waiting_room_mutex.release()
                free_doctor_rooms.acquire()                 #wait for a free doctor
                number_of_free_doctors -= 1
                waiting_room_free_chairs.release()
                number_of_free_chairs += 1

            doctors_mutex.acquire()
            for current_doctor in doctors:
                if (current_doctor.get_status() == 'FREE'):             #if doctor i is free
                    current_doctor.set_status(status='BUSY')            #is not free anymore
                    current_doctor.set_patient(self)
                    self.set_doctor(current_doctor)
                    print('{0} finally enterd doctor {1} room ({2})'.format(self.name, current_doctor.doctor_name, datetime.now().strftime("%H:%M:%S")))
                    break

            doctors_mutex.release()
            current_doctor.is_busy.release()
            self.in_doctor_room.acquire()

    def set_doctor(self, current_doctor : Doctor):
        self.current_doctor = current_doctor


if __name__ == '__main__':
    patients = [
        Patient(name='User1', entry_time=1),
        Patient(name='User2', entry_time=1),
        Patient(name='User3', entry_time=1),
        Patient(name='User4', entry_time=1),
        Patient(name='User5', entry_time=1),
        Patient(name='User6', entry_time=3),
        Patient(name='User7', entry_time=3),
        Patient(name='User8', entry_time=10)]

    DB = DoctorsBuilding(waiting_room_chairs=NUM_CHAIRS, number_of_doctors=NUM_DOCTORS)

    list(map(lambda x: x.start(), patients))    #start all the threads

