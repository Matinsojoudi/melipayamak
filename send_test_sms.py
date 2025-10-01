#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
send_test_sms.py
مثال ارسال پیامک تستی با استفاده از متد SendByBaseNumber2 (REST)
نحوه استفاده:
    python send_test_sms.py
یا از داخل کد فراخوانی تابع send_test_sms(...)
"""

import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

# آدرس متد (REST) بر اساس مستنداتی که فرستادی:
SEND_BY_BASE_NUMBER2_URL = "http://api.payamak-panel.com/post/Send.asmx/SendByBaseNumber2"

# نگاشت خطاهای رایج (بر اساس مستنداتی که فرستادی)
ERROR_CODES = {
    "-10": "در میان متغییرهای ارسالی، لینک وجود دارد.",
    "-7": "خطا در شماره فرستنده (با پشتیبانی تماس بگیرید).",
    "-6": "خطای داخلی سیستم (با پشتیبانی تماس بگیرید).",
    "-5": "متن ارسالی با متغیرهای مشخص شده همخوانی ندارد.",
    "-4": "کد متن (bodyId) صحیح نیست یا تایید نشده.",
    "-3": "خط ارسالی در سیستم تعریف نشده است.",
    "-2": "محدودیت تعداد شماره (هر بار فقط یک شماره مجاز است).",
    "-1": "دسترسی برای استفاده از این وب‌سرویس غیرفعال است.",
    "0": "نام کاربری یا رمزعبور صحیح نیست.",
    "2": "اعتبار کافی نیست.",
    "6": "سامانه در حال بروزرسانی می‌باشد.",
    "7": "متن حاوی کلمه فیلتر شده‌است.",
    "10": "کاربر موردنظر فعال نمی‌باشد.",
    "11": "ارسال نشده.",
    "12": "مدارک کاربر کامل نمی‌باشد.",
    "16": "شماره گیرنده یافت نشد.",
    "17": "متن پیامک خالی می‌باشد.",
    "18": "شماره گیرنده نامعتبر است.",
    "35": "در REST: شماره گیرنده در لیست سیاه مخابرات است."
}

def parse_recid_from_xml(xml_bytes: bytes) -> str:
    """
    پاسخ وب‌سرویس معمولاً XML بازمی‌گرداند. این تابع متن (text) عنصر اول را برمی‌گرداند.
    """
    try:
        root = ET.fromstring(xml_bytes)
        # معمولا مقدار در متن عنصر اول است
        if root.text and root.text.strip():
            return root.text.strip()
        # گاهی برگشت داخل فرزندهاست، اولین فرزند را بردار
        first = next(iter(root), None)
        if first is not None and first.text:
            return first.text.strip()
    except Exception as e:
        return f"parse_error: {e}"
    return ""

def send_test_sms(username: str, password: str, to: str, body_id: int, variables: List[str]) -> Dict[str, Any]:
    """
    ارسال با SendByBaseNumber2
    variables: لیست متغیرها (به ترتیب قرارگیری در تمپلیت)، سپس با ';' ترکیب و به پارامتر text ارسال می‌شود.
    """
    # ترکیب متغیرها با ; طبق مستند
    text_param = ";".join(variables)
    params = {
        "username": username,
        "password": password,
        "text": text_param,
        "to": to,
        "bodyId": str(body_id),
    }
    try:
        resp = requests.get(SEND_BY_BASE_NUMBER2_URL, params=params, timeout=20)
    except Exception as e:
        return {"ok": False, "error": "request_failed", "detail": str(e)}
    if resp.status_code != 200:
        return {"ok": False, "error": "http_error", "status_code": resp.status_code, "content": resp.text}

    recid = parse_recid_from_xml(resp.content)
    # اگر recid عددی و طولانی (>15) بود یعنی موفق
    result: Dict[str, Any] = {"ok": True, "raw_recid": recid, "http_status": resp.status_code}
    # بررسی خطای مستند (کدهای منفی یا مقادیر مشخص)
    if recid in ERROR_CODES:
        result.update({"ok": False, "error_code": recid, "error_message": ERROR_CODES[recid]})
    else:
        # بعضی وقت‌ها recid عددی بازگشتی است؛ تبدیل اختیاری به int
        try:
            rint = int(recid)
            # طبق مستند: اگر عدد بیش از 15 رقم => ارسال موفق
            if len(str(abs(rint))) > 15:
                result["sent"] = True
                result["message"] = "ارسال موفق (recId دریافت شد)"
            else:
                # ممکن است مقداری کوتاه برگشته باشد (خطا یا کد وضعیت)
                result["sent"] = False
                # اگر کد خطا در mapping هست، بده
                if recid in ERROR_CODES:
                    result["error_code"] = recid
                    result["error_message"] = ERROR_CODES[recid]
                else:
                    result["warning"] = "recId کوتاه است — احتمالا خطا یا پاسخ ویژه"
        except Exception:
            # اگر قابل تبدیل نباشد، باز هم آن را برمی‌گردانیم
            result["sent"] = False
            result["warning"] = "recId غیرعددی یا غیرقابل‌تفسیر"
    return result

# --- مثال استفاده ---
if __name__ == "__main__":
    # مقادیرِ نمونه — اینها را با مقادیر واقعی‌ات عوض کن
    username = "your_username"
    password = "your_password"
    to = "09123456789"       # شماره گیرنده (یک شماره)
    body_id = 1234           # id تمپلیتِ تاییدشده در پنل

    variables = [
        "۱۲۳۴",               # مقدار جای {0} (کد تایید)
    ]

    res = send_test_sms(username, password, to, body_id, variables)
    print("نتیجه ارسال:")
    for k, v in res.items():
        print(f"  {k}: {v}")
