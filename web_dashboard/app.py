from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import httpx

# Dashboard app
dashboard_app = FastAPI(
    title="Dashboard App",
    root_path="/dashboard"
)

# Sessions
dashboard_app.add_middleware(SessionMiddleware, secret_key="your-secret-key-change-in-production")

# Static
dashboard_app.mount("/static", StaticFiles(directory="web_dashboard/static"), name="static")

# Templates
templates = Jinja2Templates(directory="web_dashboard/templates")

# Main API base
API_BASE_URL = "http://localhost:8000"


# Redirect root → login
@dashboard_app.get("/")
async def root_redirect():
    return RedirectResponse(url="/dashboard/login")


# ----------------------------------
# LOGIN PAGE
# ----------------------------------
@dashboard_app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# ----------------------------------
# LOGIN POST (fully async)
# ----------------------------------
@dashboard_app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):

    async with httpx.AsyncClient() as client:
        auth_response = await client.post(
            f"{API_BASE_URL}/api/auth/login",
            json={"username": username, "password": password}
        )

    if auth_response.status_code != 200:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"}
        )

    auth_data = auth_response.json()
    token = auth_data.get("access_token")
    role = auth_data.get("role")
    nim = auth_data.get("nim")
    kode_dosen = auth_data.get("kode_dosen")

    request.session["token"] = token
    request.session["role"] = role
    request.session["username"] = username
    request.session["nim"] = nim
    request.session["kode_dosen"] = kode_dosen

    if role == "ADMIN":
        return RedirectResponse(url="/dashboard/admin", status_code=303)
    if role == "DOSEN":
        return RedirectResponse(url="/dashboard/dosen", status_code=303)
    if role == "MAHASISWA":
        return RedirectResponse(url="/dashboard/mahasiswa", status_code=303)

    return RedirectResponse(url="/dashboard/login", status_code=303)


# ----------------------------------
# LOGOUT
# ----------------------------------
@dashboard_app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/dashboard/login", status_code=303)


# ----------------------------------
# SESSION HELPERS
# ----------------------------------
def get_current_user_session(request: Request):
    token = request.session.get("token")
    role = request.session.get("role")
    username = request.session.get("username")
    nim = request.session.get("nim")
    kode_dosen = request.session.get("kode_dosen")

    if not token or not role:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return {
        "token": token,
        "role": role,
        "username": username,
        "nim": nim,
        "kode_dosen": kode_dosen
    }


def check_role(required_role: str, user: dict):
    if user["role"] != required_role and user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Access denied")
    return True


# ----------------------------------
# ADMIN DASHBOARD
# ----------------------------------
@dashboard_app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, user: dict = Depends(get_current_user_session)):
    check_role("ADMIN", user)
    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "user": user})


# ----------------------------------
# DOSEN DASHBOARD
# ----------------------------------
@dashboard_app.get("/dosen", response_class=HTMLResponse)
async def dosen_dashboard(request: Request, user: dict = Depends(get_current_user_session)):
    check_role("DOSEN", user)
    kode_dosen = request.session.get("kode_dosen")

    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {user['token']}"}

        # Get lecturer's schedule
        schedule_response = await client.get(f"{API_BASE_URL}/api/schedule/lecturer/{kode_dosen}", headers=headers)
        schedule_data = schedule_response.json() if schedule_response.status_code == 200 else []

    return templates.TemplateResponse(
        "dosen_dashboard.html",
        {
            "request": request,
            "user": user,
            "schedule_data": schedule_data
        }
    )


# ----------------------------------
# MAHASISWA DASHBOARD
# ----------------------------------
@dashboard_app.get("/mahasiswa", response_class=HTMLResponse)
async def mahasiswa_dashboard(request: Request, user: dict = Depends(get_current_user_session)):
    check_role("MAHASISWA", user)
    nim = request.session.get("nim")

    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {user['token']}"}

        # Get student's KRS
        krs_response = await client.get(f"{API_BASE_URL}/api/krs/{nim}", headers=headers)
        krs_data = krs_response.json() if krs_response.status_code == 200 else []

        # Get student's schedule
        schedule_response = await client.get(f"{API_BASE_URL}/api/schedule/student/{nim}", headers=headers)
        schedule_data = schedule_response.json() if schedule_response.status_code == 200 else []

        # Get student's IPK
        ipk_response = await client.get(f"{API_BASE_URL}/api/gpa/ipk/{nim}", headers=headers)
        ipk_data = ipk_response.json() if ipk_response.status_code == 200 else {"ipk": 0.0}

        # Get student's grades to calculate total SKS and MK count
        grades_response = await client.get(f"{API_BASE_URL}/api/grades/student/{nim}", headers=headers)
        grades_data = grades_response.json() if grades_response.status_code == 200 else []

        # Calculate total SKS and MK count
        total_sks = 0
        jumlah_mk = 0
        for grade in grades_data:
            # Only count passing grades (non-E)
            if grade.get('nilai_huruf') and grade['nilai_huruf'].upper() != 'E':
                total_sks += grade.get('sks', 0)
                jumlah_mk += 1

    return templates.TemplateResponse(
        "mahasiswa_dashboard.html",
        {
            "request": request,
            "user": user,
            "krs_data": krs_data,
            "schedule_data": schedule_data,
            "ipk": ipk_data.get("ipk", 0.0),
            "total_sks": total_sks,
            "jumlah_mk": jumlah_mk
        }
    )


# ----------------------------------
# PMB PAGE
# ----------------------------------
@dashboard_app.get("/pmb", response_class=HTMLResponse)
async def pmb_page(request: Request, user: dict = Depends(get_current_user_session)):
    check_role("ADMIN", user)

    async with httpx.AsyncClient() as client:
        res = await client.get(f"{API_BASE_URL}/api/pmb")

    data = res.json() if res.status_code == 200 else []

    return templates.TemplateResponse("pmb_data.html", {"request": request, "user": user, "pmb_data": data})


# ----------------------------------
# KRS PAGE (for ADMIN only)
# ----------------------------------
@dashboard_app.get("/krs", response_class=HTMLResponse)
async def krs_page(request: Request, user: dict = Depends(get_current_user_session)):
    check_role("ADMIN", user)

    async with httpx.AsyncClient() as client:
        res = await client.get(f"{API_BASE_URL}/api/krs")

    data = res.json() if res.status_code == 200 else []

    return templates.TemplateResponse("krs_data.html", {"request": request, "user": user, "krs_data": data})


# ----------------------------------
# SCHEDULE PAGE (for ADMIN only)
# ----------------------------------
@dashboard_app.get("/schedule", response_class=HTMLResponse)
async def schedule_page(request: Request, user: dict = Depends(get_current_user_session)):
    check_role("ADMIN", user)

    async with httpx.AsyncClient() as client:
        res = await client.get(f"{API_BASE_URL}/api/schedule")

    data = res.json() if res.status_code == 200 else []

    return templates.TemplateResponse("schedule_data.html", {"request": request, "user": user, "schedule_data": data})


# ----------------------------------
# GRADES PAGES
# ----------------------------------
@dashboard_app.get("/dosen/grades", response_class=HTMLResponse)
async def dosen_grades_page(request: Request, user: dict = Depends(get_current_user_session)):
    check_role("DOSEN", user)
    return templates.TemplateResponse("dosen/grades.html", {"request": request, "user": user})


@dashboard_app.get("/mahasiswa/grades", response_class=HTMLResponse)
async def mahasiswa_grades_page(request: Request, user: dict = Depends(get_current_user_session)):
    check_role("MAHASISWA", user)
    nim = user.get("nim", "")

    # Get the token from the session
    token = user.get("token", "")

    return templates.TemplateResponse("mahasiswa/grades.html", {
        "request": request,
        "user": user,
        "nim": nim,
        "token": token
    })


@dashboard_app.get("/dosen/grade_history", response_class=HTMLResponse)
async def dosen_grade_history_page(request: Request, user: dict = Depends(get_current_user_session)):
    check_role("DOSEN", user)
    return templates.TemplateResponse("dosen/grade_history.html", {"request": request, "user": user})
