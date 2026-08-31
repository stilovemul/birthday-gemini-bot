import asyncio
import json
import logging
import time
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from core.config import YANDEX_OAUTH_TOKEN, TELEGRAM_USER_ID, MSK_TZ
from modules.smart_home.client import (
    get_user_info,
    set_device_on_off,
    toggle_device_by_name,
    turn_off_all_lights,
    execute_scenario,
    build_smart_home_card
)
from modules.birthdays.storage import (
    get_sorted_birthdays,
    add_birthday,
    delete_birthday,
    format_date_entry,
    format_age_word
)
from modules.smart_reminders.storage import (
    get_active_reminders,
    add_reminder,
    mark_as_done,
    delete_reminder
)
from modules.food_tracker.storage import (
    get_daily_summary,
    log_meal,
    delete_meal,
    get_user_calorie_goal,
    set_user_calorie_goal
)
from modules.weather_synoptic.service import (
    get_weather_report,
    fetch_weather_wttr
)
from modules.weather_synoptic.storage import get_user_weather_config
from modules.loan_calculator.calculator import (
    calculate_annuity_loan,
    calculate_early_repayment_savings
)

logger = logging.getLogger("MiniAppRouter")
router = APIRouter()


class DeviceToggleRequest(BaseModel):
    device_id: Optional[str] = None
    name: Optional[str] = None
    state: bool


class ScenarioRequest(BaseModel):
    scenario_id: str


class BirthdayAddRequest(BaseModel):
    name: str
    date: str
    note: Optional[str] = ""


class BirthdayDeleteRequest(BaseModel):
    id: str


class ReminderAddRequest(BaseModel):
    text: str
    target_dt_str: Optional[str] = None
    target_display: Optional[str] = None


class ReminderActionRequest(BaseModel):
    id: str


class FoodAddRequest(BaseModel):
    dish_name: str
    calories: int
    protein: float = 0.0
    fat: float = 0.0
    carbs: float = 0.0
    weight_g: Optional[int] = None


class FoodDeleteRequest(BaseModel):
    id: str


class LoanCalcRequest(BaseModel):
    amount: float
    rate: float
    months: int
    early_monthly: float = 0.0


@router.get("/api/dashboard/data")
async def get_dashboard_aggregated_data():
    """Aggregates real-time data for Smart Home, Weather, Birthdays, Tasks, and KBZhU in 1 call."""
    now_msk = datetime.now(MSK_TZ)
    user_id = TELEGRAM_USER_ID

    # 1. Smart Home Topology & Status
    sh_data = {
        "connected": False,
        "climate": [],
        "security_alerts": [],
        "door_states": [],
        "active_devices": [],
        "devices": [],
        "scenarios": [],
        "active_count": 0
    }
    try:
        raw_info = await get_user_info(YANDEX_OAUTH_TOKEN)
        if raw_info:
            sh_data["connected"] = True
            rooms = {r["id"]: r["name"] for r in raw_info.get("rooms", [])}
            devices_list = []
            
            for d in raw_info.get("devices", []):
                d_id = d.get("id")
                d_name = d.get("name", "")
                r_name = rooms.get(d.get("room"), "Дом")
                d_type = d.get("type", "")
                
                # Check on_off capability
                is_on = False
                has_on_off = False
                for cap in d.get("capabilities", []):
                    if cap.get("type") == "devices.capabilities.on_off":
                        has_on_off = True
                        c_state = cap.get("state") or {}
                        is_on = bool(c_state.get("value", False))
                
                # Check climate & sensor properties
                temp_val = None
                hum_val = None
                is_leak = False
                is_opened = False
                
                for prop in d.get("properties", []):
                    p_state = prop.get("state") or {}
                    p_val = p_state.get("value")
                    inst = prop.get("parameters", {}).get("instance", "")
                    
                    if inst == "temperature" and p_val is not None:
                        temp_val = round(float(p_val), 1)
                    elif inst == "humidity" and p_val is not None:
                        hum_val = round(float(p_val))
                    elif inst == "water_leak" and p_val == "leak":
                        is_leak = True
                    elif inst == "open" and p_val == "opened":
                        is_opened = True

                if temp_val is not None:
                    sh_data["climate"].append({
                        "room": r_name,
                        "device": d_name,
                        "temperature": temp_val,
                        "humidity": hum_val
                    })

                if is_leak:
                    sh_data["security_alerts"].append(f"🚨 Протечка воды: {r_name} ({d_name})")

                if "openable" in d_type or ("sensor" in d_type and ("двер" in d_name.lower() or "вход" in d_name.lower())):
                    sh_data["door_states"].append({
                        "name": d_name,
                        "room": r_name,
                        "is_opened": is_opened
                    })

                if is_on:
                    sh_data["active_devices"].append({"id": d_id, "name": d_name, "room": r_name})

                devices_list.append({
                    "id": d_id,
                    "name": d_name,
                    "room": r_name,
                    "type": d_type,
                    "is_on": is_on,
                    "has_on_off": has_on_off
                })

            sh_data["devices"] = devices_list
            sh_data["active_count"] = len(sh_data["active_devices"])
            sh_data["scenarios"] = [
                {"id": s.get("id"), "name": s.get("name")}
                for s in raw_info.get("scenarios", [])
            ]
    except Exception as e:
        logger.warning(f"Dashboard smart home fetch error: {e}")

    # 2. Weather Data
    weather_info = {
        "city": "Санкт-Петербург",
        "district": "Приморский р-н",
        "temp": "СПб",
        "text": ""
    }
    try:
        w_cfg = get_user_weather_config(user_id)
        city = w_cfg.get("city", "Санкт-Петербург")
        district = w_cfg.get("district", "Приморский р-н")
        lat = w_cfg.get("lat", 59.9950)
        lon = w_cfg.get("lon", 30.2200)
        ok, w_text = await get_weather_report(city, district, lat, lon)
        weather_info["text"] = w_text if ok else "Погода загружается..."
        weather_info["city"] = city
        weather_info["district"] = district
    except Exception as e:
        logger.warning(f"Dashboard weather fetch error: {e}")

    # 3. Birthdays
    birthdays_data = []
    try:
        b_list = get_sorted_birthdays()
        for b in b_list:
            birthdays_data.append({
                "id": b["id"],
                "name": b["name"],
                "day": b["day"],
                "month": b["month"],
                "year": b.get("year"),
                "date_display": format_date_entry(b),
                "days_left": b["days_left"],
                "turning_age": b.get("turning_age"),
                "age_display": format_age_word(b["turning_age"]) if b.get("turning_age") else "",
                "note": b.get("note", "")
            })
    except Exception as e:
        logger.warning(f"Dashboard birthdays error: {e}")

    # 4. Reminders
    reminders_data = []
    try:
        r_list = get_active_reminders(user_id)
        for r in r_list:
            reminders_data.append({
                "id": r["id"],
                "text": r["text"],
                "target_display": r.get("target_display", ""),
                "created_at": r.get("created_at", "")
            })
    except Exception as e:
        logger.warning(f"Dashboard reminders error: {e}")

    # 5. Food & KBZhU
    food_data = {}
    try:
        food_data = get_daily_summary(user_id)
    except Exception as e:
        logger.warning(f"Dashboard food summary error: {e}")

    return {
        "server_time_msk": now_msk.strftime("%d.%m.%Y, %H:%M:%S"),
        "date_today_msk": now_msk.strftime("%Y-%m-%d"),
        "smart_home": sh_data,
        "weather": weather_info,
        "birthdays": birthdays_data,
        "reminders": reminders_data,
        "food": food_data
    }


@router.post("/api/smart_home/toggle")
async def api_toggle_device(req: DeviceToggleRequest):
    if req.device_id:
        ok, msg = await set_device_on_off(YANDEX_OAUTH_TOKEN, req.device_id, req.state)
        return {"success": ok, "message": msg}
    elif req.name:
        ok, msg, dev = await toggle_device_by_name(YANDEX_OAUTH_TOKEN, req.name, req.state)
        return {"success": ok, "message": msg}
    raise HTTPException(status_code=400, detail="Missing device_id or name")


@router.post("/api/smart_home/all_off")
async def api_all_off():
    ok, msg, count = await turn_off_all_lights(YANDEX_OAUTH_TOKEN)
    return {"success": ok, "message": msg, "turned_off_count": count}


@router.post("/api/smart_home/scenario")
async def api_scenario(req: ScenarioRequest):
    ok, msg = await execute_scenario(YANDEX_OAUTH_TOKEN, req.scenario_id)
    return {"success": ok, "message": msg}


@router.post("/api/birthdays/add")
async def api_add_birthday(req: BirthdayAddRequest):
    ok, msg, entry = add_birthday(req.name, req.date, req.note or "")
    if ok:
        return {"success": True, "message": msg, "entry": entry}
    raise HTTPException(status_code=400, detail=msg)


@router.post("/api/birthdays/delete")
async def api_delete_birthday(req: BirthdayDeleteRequest):
    ok, msg = delete_birthday(req.id)
    return {"success": ok, "message": msg}


@router.post("/api/reminders/add")
async def api_add_reminder(req: ReminderAddRequest):
    target_dt = datetime.now(MSK_TZ)
    if req.target_dt_str:
        try:
            target_dt = datetime.fromisoformat(req.target_dt_str).replace(tzinfo=MSK_TZ)
        except Exception:
            pass
    entry = add_reminder(
        user_id=TELEGRAM_USER_ID,
        text=req.text,
        target_dt=target_dt,
        target_display=req.target_display or target_dt.strftime("%d.%m в %H:%M")
    )
    return {"success": True, "entry": entry}


@router.post("/api/reminders/done")
async def api_done_reminder(req: ReminderActionRequest):
    mark_as_done(req.id)
    return {"success": True}


@router.post("/api/reminders/delete")
async def api_delete_reminder(req: ReminderActionRequest):
    ok = delete_reminder(req.id)
    return {"success": ok}


@router.post("/api/food/add")
async def api_add_food(req: FoodAddRequest):
    entry = log_meal(
        user_id=TELEGRAM_USER_ID,
        dish_name=req.dish_name,
        calories=req.calories,
        protein=req.protein,
        fat=req.fat,
        carbs=req.carbs,
        weight_g=req.weight_g
    )
    return {"success": True, "entry": entry}


@router.post("/api/food/delete")
async def api_delete_food(req: FoodDeleteRequest):
    ok = delete_meal(TELEGRAM_USER_ID, req.id)
    return {"success": ok}


@router.post("/api/loan/calculate")
async def api_calc_loan(req: LoanCalcRequest):
    try:
        schedule = calculate_annuity_loan(req.amount, req.rate, req.months)
        early_res = calculate_early_repayment_savings(req.amount, req.rate, req.months, req.early_monthly)
        return {
            "success": True,
            "monthly_payment": schedule.get("monthly_payment", 0),
            "total_payout": schedule.get("total_payout", 0),
            "total_interest": schedule.get("total_overpayment", 0),
            "early": early_res
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/app", response_class=HTMLResponse)
async def serve_mini_app():
    from modules.webapp.dashboard_html import TMA_DASHBOARD_HTML
    return HTMLResponse(content=TMA_DASHBOARD_HTML)
