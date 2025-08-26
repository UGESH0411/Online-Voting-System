# 🗳️ Online Voting System

A **secure, transparent, and user-friendly online voting system** built using **FastAPI (Python)**, **PostgreSQL**, and **Jinja2 Templates**.
This project demonstrates how technology can ensure **fair elections** with **real-time vote tallying**, **role-based authentication**, and **transparent election management**.

---

##  Features

###  Voter

* Register with Aadhaar, photo, and personal details
* Login securely to cast vote
* View ongoing elections only within valid time windows
* Vote **only once per position**
* Profile management

###  Admin

* Manage voters (Add, Edit, Delete)
* Manage candidates with party details & symbols
* Create election positions with start & end times
* Monitor election progress
* View dashboard with **real-time analytics & vote tally**

###  Dashboard

* Total voters, positions, candidates
* Voter participation tracking
* Vote count visualization per candidate per position

---

##  Tech Stack

* **Backend**: FastAPI (Python)
* **Database**: PostgreSQL (psycopg2)
* **Frontend**: HTML, CSS, Bootstrap, Jinja2
* **Other Tools**: CORS Middleware, File Uploads

---

##  Database Schema

```sql
CREATE TABLE admin (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE voters (
    id SERIAL PRIMARY KEY,
    aadhhaarno VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    mailid VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    age INT CHECK (age >= 18),
    address TEXT,
    gender VARCHAR(10),
    photo TEXT
);

CREATE TABLE position (
    id SERIAL PRIMARY KEY,
    positionname VARCHAR(150) UNIQUE NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL
);

CREATE TABLE candidates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    position_id INT REFERENCES position(id) ON DELETE CASCADE,
    party VARCHAR(100),
    symbol TEXT
);

CREATE TABLE votes (
    id SERIAL PRIMARY KEY,
    voter_id INT REFERENCES voters(id) ON DELETE CASCADE,
    candidate_id INT REFERENCES candidates(id) ON DELETE CASCADE,
    position_id INT REFERENCES position(id) ON DELETE CASCADE,
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (voter_id, position_id)
);
```



##  Installation & Setup

1. **Clone Repo**

   ```bash
   git clone https://github.com/UGESH0411/Online-Voting-System.git
   cd online-voting-system
   ```

2. **Create Virtual Environment & Install Dependencies**

   ```bash
   python -m venv venv
   source venv/bin/activate   # on Linux/Mac
   venv\Scripts\activate      # on Windows
   pip install -r requirements.txt
   ```

3. **Setup Database**

   * Install PostgreSQL
   * Create a database `Fastapidb`
   * Run schema SQL (above) in pgAdmin/psql

4. **Configure Connection**
   Update your DB credentials inside `main.py`:

   python
   con = psycopg2.connect(
       dbname="Fastapidb",
       user="postgres",
       password="yourpassword",
       host="localhost",
       port=5432
   )

5. **Run the App**

   bash
   uvicorn main:app --reload
   


##  Screenshots (Add after running)

*  **Login Page**
*  **Admin Dashboard**
*  **Voter Profile**
*  **Voting Page**
*  **Election Results**


##  Future Improvements

*  Password hashing & JWT authentication
*  Responsive mobile-friendly UI
*  Email/OTP-based voter verification
*  Docker support for easy deployment

---

##  Author

Developed by **\[Ugesh K]**
    GitHub: [Ugesh K](https://github.com/UGESH0411)
    LinkedIn: \[https://www.linkedin.com/in/ugesh04/]


