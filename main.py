from fastapi import FastAPI, Form, Request, UploadFile, File, Response, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import Path  # ensure this is imported if not already
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import shutil
import os
from collections import defaultdict  # Add this import if not already present
import time
from fastapi.responses import PlainTextResponse

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates and Static Files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# PostgreSQL DB Connection
while True:
    try:
        con = psycopg2.connect(
            dbname='Fastapidb',
            user='postgres',
            password='6382501831u',
            host='localhost',
            port=5432,
            cursor_factory=RealDictCursor
        )
        print("✅ Database connected successfully")
        break
    except Exception as e:
        print("❌ Connection failed:", e)
        time.sleep(2)

# Routes

@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(response: Response, request: Request, username: str = Form(...), password: str = Form(...), role: str = Form(...)):
    try:
        with con.cursor() as cur:
            if role == "admin":
                cur.execute("SELECT * FROM Admin WHERE username = %s AND password = %s", (username, password))
                admin = cur.fetchone()
                if admin:
                    response = RedirectResponse("/adminhome", status_code=302)
                    response.set_cookie(key="username", value=username)
                    response.set_cookie(key="password", value=password)
                    response.set_cookie(key="role", value=role)
                    return response
                else:
                    return HTMLResponse("<h3>❌ Invalid Admin Credentials</h3>")
            elif role == "user":
                cur.execute("SELECT * FROM voters WHERE name = %s AND password = %s", (username, password))
                user = cur.fetchone()
                if user:
                    response = RedirectResponse("/userhome", status_code=302)
                    response.set_cookie(key="username", value=username)
                    response.set_cookie(key="password", value=password)
                    response.set_cookie(key="role", value=role)
                    return response
                else:
                    return HTMLResponse("<h3>❌ Invalid User Credentials</h3>")
            else:
                return HTMLResponse("<h3>❌ Invalid Role</h3>")
    except Exception as e:
        con.rollback()
        return HTMLResponse(f"<h3>⚠️ Login Error: {str(e)}</h3>")


@app.get("/adminhome", response_class=HTMLResponse)
async def admin_home(request: Request, username: str = Cookie(default=None)):
    try:
        with con.cursor() as cur:
            cur.execute("""
                SELECT c.id, c.name, c.party, c.symbol, c.position_id, p.positionname
                FROM candidates c
                JOIN position p ON c.position_id = p.id
            """)
            all_candidates = cur.fetchall()

        # Group candidates by position
        positions = defaultdict(list)
        for c in all_candidates:
            positions[c["positionname"]].append(c)

        return templates.TemplateResponse("adminhome.html", {
            "request": request,
            "username": username,
            "positions": positions,
            "voter_id": 1  # Replace with dynamic voter ID when needed
        })
    except Exception as e:
        return HTMLResponse(f"<h3>⚠️ Error loading admin home: {str(e)}</h3>")



@app.post("/submit-vote")
async def submit_vote(request: Request, username: str = Cookie(default=None)):
    try:
        # ✅ Get voter_id using username
        with con.cursor() as cur:
            cur.execute("SELECT id FROM voters WHERE name = %s", (username,))
            voter = cur.fetchone()
            if not voter:
                return PlainTextResponse("❌ Voter not found. Please login again.")

            voter_id = voter["id"]

        # ✅ Read form data
        form = await request.form()
        position_name = form.get("position")
        candidate_id = int(form.get("candidate"))

        with con.cursor() as cur:
            # ✅ Get position_id from candidate
            cur.execute("SELECT position_id FROM candidates WHERE id = %s", (candidate_id,))
            pos_result = cur.fetchone()
            if not pos_result:
                return PlainTextResponse("❌ Candidate not found.")

            position_id = pos_result["position_id"]

            # ✅ Check for duplicate vote
            cur.execute(
                "SELECT id FROM votes WHERE voter_id = %s AND position_id = %s",
                (voter_id, position_id)
            )
            existing_vote = cur.fetchone()
            if existing_vote:
                return PlainTextResponse("❌ You have already voted for this position.")

            # ✅ Insert vote
            cur.execute(
                "INSERT INTO votes (voter_id, candidate_id, position_id) VALUES (%s, %s, %s)",
                (voter_id, candidate_id, position_id)
            )
            con.commit()

        return PlainTextResponse("✅ Your vote has been recorded successfully.")

    except Exception as e:
        con.rollback()
        return PlainTextResponse(f"❌ Error submitting vote: {str(e)}")
    
@app.get("/userhome", response_class=HTMLResponse)
async def admin_home(request: Request, username: str = Cookie(default=None)):
    try:
        with con.cursor() as cur:
            cur.execute("""
                SELECT c.id, c.name, c.party, c.symbol, c.position_id, p.positionname
                FROM candidates c
                JOIN position p ON c.position_id = p.id
            """)
            all_candidates = cur.fetchall()

        # Group candidates by position
        positions = defaultdict(list)
        for c in all_candidates:
            positions[c["positionname"]].append(c)

        return templates.TemplateResponse("userhome.html", {
            "request": request,
            "username": username,
            "positions": positions,
            "voter_id": 1  # Replace with dynamic voter ID when needed
        })
    except Exception as e:
        return HTMLResponse(f"<h3>⚠️ Error loading admin home: {str(e)}</h3>")
    
@app.post("/candidates")
async def add_candidate(
    firstname: str = Form(...),
    lastname: str = Form(...),
    position: str = Form(...),
    party: str = Form(...),
    symbol: UploadFile = File(...)
):
    try:
       # print("Received form:", firstname, lastname, position, party, symbol.filename)

        symbol_path = f"static/uploads/candidates/{symbol.filename}"
        os.makedirs(os.path.dirname(symbol_path), exist_ok=True)
        with open(symbol_path, "wb") as buffer:
            shutil.copyfileobj(symbol.file, buffer)

        fullname = f"{firstname} {lastname}"
        with con.cursor() as cur:
            print("Looking up position:", position)
            cur.execute("SELECT id FROM position WHERE LOWER(positionname) = LOWER(%s)", (position,))
            result = cur.fetchone()
            print("Position lookup result:", result)

            if result is None:
                return {"error": f"❌ Position '{position}' does not exist."}
            position_id = result['id']  # using dict cursor

            cur.execute("""
                INSERT INTO candidates (name, position_id, party, symbol)
                VALUES (%s, %s, %s, %s)
            """, (fullname, position_id, party, symbol_path))
            con.commit()
            print("✅ Candidate inserted:", fullname)
        return {"message": "✅ Candidate added successfully"}
    except Exception as e:
        con.rollback()
        print("❌ Exception occurred while inserting candidate:", e)
        return {"error": f"❌ Failed to add candidate: {str(e)}"}


@app.post("/voters")
async def add_voter(
    aadhhaarno: str = Form(...),
    name: str = Form(...),
    mailid: str = Form(...),
    password: str = Form(...),
    age: int = Form(...),
    address: str = Form(...),
    gender: str = Form(...),
    photo: UploadFile = File(...)
):
    try:
        photo_path = f"static/uploads/voters/{photo.filename}"
        os.makedirs(os.path.dirname(photo_path), exist_ok=True)
        with open(photo_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)

        with con.cursor() as cur:
            cur.execute("""
                INSERT INTO voters (aadhhaarno, name, mailid, password, age, address, gender, photo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (aadhhaarno, name, mailid, password, age, address, gender, photo_path))
            con.commit()
        return {"message": "✅ Voter added successfully"}
    except Exception as e:
        con.rollback()
        return {"error": f"❌ Failed to add voter: {str(e)}"}


@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, username: str = Cookie(default=None), password: str = Cookie(default=None)):
    try:
        with con.cursor() as cur:
            cur.execute("SELECT * FROM voters WHERE name = %s AND password = %s", (username, password))
            user = cur.fetchone()
            if user:
                return templates.TemplateResponse("profile.html", {"request": request, "user": user})
            else:
                return HTMLResponse("<h3>❌ User not found</h3>")
    except Exception as e:
        return HTMLResponse(f"<h3>⚠️ Error fetching profile: {str(e)}</h3>")

@app.get("/voterlist", response_class=HTMLResponse)
async def voters_list(request: Request):
    try:
        with con.cursor() as cur:
            cur.execute("SELECT * FROM voters")
            voters = cur.fetchall()
        return templates.TemplateResponse("voterlist.html", {"request": request, "voters": voters})
    except Exception as e:
        return HTMLResponse(f"<h3>Error: {str(e)}</h3>")


@app.get("/voter/edit/{voter_id}", response_class=HTMLResponse)
async def edit_voter_page(request: Request, voter_id: int):
    with con.cursor() as cur:
        cur.execute("SELECT * FROM voters WHERE id = %s", (voter_id,))
        voter = cur.fetchone()
    return templates.TemplateResponse("edit_voter.html", {"request": request, "voter": voter})

@app.post("/voter/edit/{voter_id}")
async def update_voter(
    voter_id: int,
    aadhhaarno: str = Form(...),
    name: str = Form(...),
    mailid: str = Form(...),
    password: str = Form(...),
    age: int = Form(...),
    address: str = Form(...),
    gender: str = Form(...),
    photo: UploadFile = File(None)
):
    try:
        with con.cursor() as cur:
            if photo:
                photo_path = f"static/uploads/voters/{photo.filename}"
                os.makedirs(os.path.dirname(photo_path), exist_ok=True)
                with open(photo_path, "wb") as buffer:
                    shutil.copyfileobj(photo.file, buffer)
                cur.execute("""
                    UPDATE voters SET aadhhaarno=%s, name=%s, mailid=%s, password=%s,
                    age=%s, address=%s, gender=%s, photo=%s WHERE id=%s
                """, (aadhhaarno, name, mailid, password, age, address, gender, photo_path, voter_id))
            else:
                cur.execute("""
                    UPDATE voters SET aadhhaarno=%s, name=%s, mailid=%s, password=%s,
                    age=%s, address=%s, gender=%s WHERE id=%s
                """, (aadhhaarno, name, mailid, password, age, address, gender, voter_id))
            con.commit()
        return RedirectResponse(url="/voterlist", status_code=302)
    except Exception as e:
        con.rollback()
        return HTMLResponse(f"<h3>Failed to update voter: {str(e)}</h3>")

@app.get("/voter/delete/{voter_id}")
async def delete_voter(voter_id: int):
    try:
        with con.cursor() as cur:
            cur.execute("DELETE FROM voters WHERE id = %s", (voter_id,))
            con.commit()
        return RedirectResponse(url="/voterlist", status_code=302)
    except Exception as e:
        con.rollback()
        return HTMLResponse(f"<h3>Failed to delete voter: {str(e)}</h3>")



@app.get("/candidatelist", response_class=HTMLResponse)
async def candidate_list(request: Request):
    try:
        with con.cursor() as cur:
            cur.execute("SELECT * FROM candidates")
            candidates = cur.fetchall()

            cur.execute("SELECT id, positionname FROM position")
            positions = cur.fetchall()

        return templates.TemplateResponse(
            "candidatelist.html",
            {
                "request": request,
                "candidates": candidates,
                "position": positions  # ✅ Pass this to the template
            }
        )
    except Exception as e:
        return HTMLResponse(f"<h3>Error fetching candidates: {str(e)}</h3>")


@app.get("/candidate/view/{candidate_id}", response_class=HTMLResponse)
async def view_candidate(request: Request, candidate_id: int = Path(...)):
    try:
        with con.cursor() as cur:
            cur.execute("SELECT * FROM candidates WHERE id = %s", (candidate_id,))
            candidate = cur.fetchone()
            if not candidate:
                return HTMLResponse("<h3>❌ Candidate not found</h3>")
        return templates.TemplateResponse("view_candidate.html", {"request": request, "candidate": candidate})
    except Exception as e:
        return HTMLResponse(f"<h3>⚠️ Error fetching candidate: {str(e)}</h3>")



@app.get("/candidate/edit/{candidate_id}", response_class=HTMLResponse)
async def edit_candidate_page(request: Request, candidate_id: int):
    try:
        with con.cursor() as cur:
            cur.execute("SELECT * FROM candidates WHERE id = %s", (candidate_id,))
            candidate = cur.fetchone()
        return templates.TemplateResponse("edit_candidate.html", {"request": request, "candidate": candidate})
    except Exception as e:
        return HTMLResponse(f"<h3>Error loading edit form: {str(e)}</h3>")


@app.post("/candidate/edit/{candidate_id}")
async def update_candidate(
    candidate_id: int,
    name: str = Form(...),
    position: str = Form(...),
    party: str = Form(...),
    symbol: UploadFile = File(None)
):
    try:
        with con.cursor() as cur:
            if symbol:
                symbol_path = f"static/uploads/candidates/{symbol.filename}"
                os.makedirs(os.path.dirname(symbol_path), exist_ok=True)
                with open(symbol_path, "wb") as buffer:
                    shutil.copyfileobj(symbol.file, buffer)
                cur.execute("""
                    UPDATE candidates SET name = %s, position = %s, party = %s, symbol = %s WHERE id = %s
                """, (name, position, party, symbol_path, candidate_id))
            else:
                cur.execute("""
                    UPDATE candidates SET name = %s, position = %s, party = %s WHERE id = %s
                """, (name, position, party, candidate_id))
            con.commit()
        return RedirectResponse(url="/candidatelist", status_code=302)
    except Exception as e:
        con.rollback()
        return HTMLResponse(f"<h3>Failed to update candidate: {str(e)}</h3>")


@app.get("/candidate/delete/{candidate_id}")
async def delete_candidate(candidate_id: int):
    try:
        with con.cursor() as cur:
            cur.execute("DELETE FROM candidates WHERE id = %s", (candidate_id,))
            con.commit()
        return RedirectResponse(url="/candidatelist", status_code=302)
    except Exception as e:
        con.rollback()
        return HTMLResponse(f"<h3>Failed to delete candidate: {str(e)}</h3>")



@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        with con.cursor() as cur:
            # Summary counts
            cur.execute("SELECT COUNT(*) FROM position")
            positions_count = cur.fetchone()["count"]

            cur.execute("SELECT COUNT(*) FROM candidates")
            candidates_count = cur.fetchone()["count"]

            cur.execute("SELECT COUNT(*) FROM voters")
            total_voters = cur.fetchone()["count"]

            cur.execute("SELECT COUNT(DISTINCT voter_id) FROM votes")
            voters_voted = cur.fetchone()["count"]

            # Tally per candidate per position
            cur.execute("""
                SELECT p.positionname, c.name AS candidate_name, COUNT(v.id) AS vote_count
                FROM votes v
                JOIN candidates c ON v.candidate_id = c.id
                JOIN position p ON c.position_id = p.id
                GROUP BY p.positionname, c.name
                ORDER BY p.positionname
            """)
            results = cur.fetchall()

            tally = defaultdict(lambda: {"labels": [], "votes": []})
            for row in results:
                position = row["positionname"]
                tally[position]["labels"].append(row["candidate_name"])
                tally[position]["votes"].append(row["vote_count"])

            # Structure to pass to Chart.js
            chart_data = dict(tally)

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "positions_count": positions_count,
            "candidates_count": candidates_count,
            "total_voters": total_voters,
            "voters_voted": voters_voted,
            "positions": list(chart_data.keys()),
            "chart_data": chart_data
        })
    except Exception as e:
        return HTMLResponse(f"<h3>⚠️ Error loading dashboard: {str(e)}</h3>")

@app.get("/logout")
async def logout():
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("username")
    response.delete_cookie("password")
    response.delete_cookie("role")
    return response
