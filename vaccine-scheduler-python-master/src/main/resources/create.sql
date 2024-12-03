CREATE TABLE Caregivers (
    Username varchar(255),
    Salt BINARY(16),
    Hash BINARY(16),
    PRIMARY KEY (Username)
);

CREATE TABLE Availabilities (
    Time date,
    Username varchar(255) REFERENCES Caregivers,
    PRIMARY KEY (Time, Username)
);

CREATE TABLE Vaccines (
    Name varchar(255),
    Doses int,
    PRIMARY KEY (Name)
);

CREATE TABLE Patients (
    Username varchar(255),
    Salt Binary(16),
    Hash Binary(16),
    PRIMARY KEY (Username)
);

CREATE TABLE Reservations (
    Pname varchar(255),
    Cname varchar(255),
    Vname varchar(255),
    Time date,
    id INT,
    PRIMARY KEY (id),
    FOREIGN KEY (Pname) REFERENCES Patients(Username),
    FOREIGN KEY (Cname) REFERENCES Caregivers(Username),
    FOREIGN KEY (Vname) REFERENCES Vaccines(Name)
);



