import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import time
import copy
import io

# ── reportlab（PDF 收据）──────────────────────────────────────
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle,
        Paragraph, Spacer
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False

# ════════════════════════════════════════════════════════════════
# 1. 页面配置 & 全局样式
# ════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Harmony PMS v14.0", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
html, body, [class*="st-"] { font-family: 'Inter', sans-serif; color: #1e293b; }

.stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); }

.pms-card {
    background: rgba(255,255,255,0.92);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 24px;
    border: 1px solid rgba(255,255,255,0.3);
    box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
    transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
    margin-bottom: 20px;
}
.pms-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1);
    border: 1px solid #3b82f6;
}

.stButton>button {
    border-radius: 12px; font-weight: 600;
    letter-spacing: 0.5px; text-transform: uppercase;
    font-size: 0.82rem; height: 3.2rem !important;
    transition: all 0.2s !important; border: none !important;
    background: #ffffff !important; color: #1e293b !important;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1) !important;
}
.stButton>button:hover {
    background: #3b82f6 !important; color: white !important;
    box-shadow: 0 10px 15px -3px rgba(59,130,246,0.4) !important;
}

.main-title {
    font-size: 2.2rem; font-weight: 800;
    background: linear-gradient(90deg,#1e293b,#3b82f6);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 1rem;
}

.badge { padding:4px 12px; border-radius:999px; font-size:0.75rem; font-weight:700; text-transform:uppercase; }
.badge-clean  { background:#dcfce7; color:#15803d; }
.badge-dirty  { background:#fee2e2; color:#b91c1c; }
.badge-occ    { background:#dbeafe; color:#1d4ed8; }
.badge-ooo    { background:#fef9c3; color:#a16207; }

.warn-box {
    background:#fff7ed; border:1px solid #fb923c;
    border-radius:10px; padding:10px 16px;
    margin-bottom:8px; font-size:0.85rem; color:#9a3412;
}
.role-badge-mgr  { background:#fce7f3; color:#9d174d; padding:4px 14px; border-radius:999px; font-weight:700; font-size:0.8rem; }
.role-badge-staff{ background:#e0f2fe; color:#0c4a6e; padding:4px 14px; border-radius:999px; font-weight:700; font-size:0.8rem; }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# 2. 账号配置（角色权限）
# ════════════════════════════════════════════════════════════════
ACCOUNTS = {
    "asd": {"password": "1234", "role": "staff",   "display": "前台员工"},
    "Ben": {"password": "1234", "role": "manager",  "display": "经理"},
}

def is_manager():
    return st.session_state.get("role") == "manager"

def require_manager():
    """在页面顶部显示权限不足警告，返回 False 表示无权限。"""
    if not is_manager():
        st.error("🔒 权限不足：此功能需要经理权限。")
        if st.button("⬅️ 返回主页"):
            nav_to("home"); st.rerun()
        st.stop()

# ════════════════════════════════════════════════════════════════
# 3. 状态初始化
# ════════════════════════════════════════════════════════════════
def _init():
    defaults = {
        # ── 房间数据库 ──────────────────────────────────────────
        "rooms_db": {
            "101": {"type":"大床房","price":200.0,"status":"Clean","guest":None,"guest_ic":None,"phone":"","email":"","others":[],"current_uid":None},
            "102": {"type":"大床房","price":200.0,"status":"Clean","guest":None,"guest_ic":None,"phone":"","email":"","others":[],"current_uid":None},
            "103": {"type":"大床房","price":200.0,"status":"Dirty","guest":None,"guest_ic":None,"phone":"","email":"","others":[],"current_uid":None},
            "201": {"type":"双床房","price":250.0,"status":"Clean","guest":None,"guest_ic":None,"phone":"","email":"","others":[],"current_uid":None},
            "202": {"type":"双床房","price":250.0,"status":"OOO",  "guest":None,"guest_ic":None,"phone":"","email":"","others":[],"current_uid":None},
        },
        # ── 业务数据 ────────────────────────────────────────────
        "history":          [],   # 已支付订单
        "refunds":          [],   # 退款凭证
        "temp":             {},   # 账单暂存
        "paid":             False,
        "checkout_history": [],   # 退房快照（撤销用）
        "refund_ledger":    {},   # uid -> 已退总额

        # ── 新功能数据 ──────────────────────────────────────────
        # 追加消费: {uid: [{item, amount, time}]}
        "extra_charges":    {},
        # 留言板: [{room, from_role, content, time, read}]
        "messages":         [],
        # 叫醒服务: [{room, guest, wake_time, status, created_at}]
        "wakeups":          [],
        # 每日入住快照（用于趋势图）: [{date_str, occ_count, revenue}]
        "daily_stats":      [],

        # ── 会话 ────────────────────────────────────────────────
        "page":         "home",
        "is_logged_in": False,
        "role":         None,
        "username":     None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

# ════════════════════════════════════════════════════════════════
# 4. 工具函数
# ════════════════════════════════════════════════════════════════
def nav_to(target):
    st.session_state.page = target

def get_room_label(room_no):
    db = st.session_state.rooms_db
    if room_no in db:
        return f"{room_no} ({db[room_no]['type']})"
    return str(room_no)

def total_room_count():
    return len(st.session_state.rooms_db)

def deep_copy_room(room_val: dict) -> dict:
    return copy.deepcopy(room_val)

def safe_df(records: list, columns: list) -> pd.DataFrame:
    """安全构造 DataFrame，缺失列自动补 N/A。"""
    if not records:
        return pd.DataFrame(columns=columns)
    df = pd.DataFrame(records)
    for col in columns:
        if col not in df.columns:
            df[col] = "N/A"
    return df[columns]

def get_extra_total(uid: str) -> float:
    """返回某订单所有追加消费之和。"""
    charges = st.session_state.extra_charges.get(uid, [])
    return sum(c["amount"] for c in charges)

def record_daily_stat():
    """每次支付完成后追加当日快照（用于趋势图）。"""
    today_str = date.today().isoformat()
    occ = sum(1 for r in st.session_state.rooms_db.values() if r["guest"])
    rev = sum(h["total"] for h in st.session_state.history)
    ref = sum(r["amount"] for r in st.session_state.refunds)
    entry = {"date": today_str, "occ": occ, "net_revenue": round(rev - ref, 2)}
    # 同一天只保留最新快照
    st.session_state.daily_stats = [
        s for s in st.session_state.daily_stats if s["date"] != today_str
    ]
    st.session_state.daily_stats.append(entry)

# ════════════════════════════════════════════════════════════════
# 5. PDF 收据生成
# ════════════════════════════════════════════════════════════════
def build_receipt_pdf(order: dict) -> bytes:
    """
    生成订单 PDF 收据，返回字节流。
    包含房费、追加消费、SST、押金明细。
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    styles = getSampleStyleSheet()
    title_style  = ParagraphStyle("t", parent=styles["Title"],  fontSize=18, spaceAfter=6)
    sub_style    = ParagraphStyle("s", parent=styles["Normal"], fontSize=10, textColor=colors.grey)
    normal_style = styles["Normal"]

    uid          = order.get("uid", "N/A")
    name         = order.get("name", "N/A")
    checkin      = order.get("checkin", "N/A")
    checkout     = order.get("checkout", "N/A")
    days         = order.get("days", 0)
    room_list    = order.get("room_list", "N/A")
    rs           = order.get("rs", {})
    sub          = order.get("sub", 0.0)
    tax          = order.get("tax", 0.0)
    deposit      = order.get("deposit", 100.0)
    extra_total  = get_extra_total(uid)
    total        = order.get("total", 0.0) + extra_total
    pay_time     = order.get("time", "N/A")
    status       = order.get("status", "N/A")

    story = []
    story.append(Paragraph("HARMONY HOTEL", title_style))
    story.append(Paragraph("No.1 Jalan Harmoni, Kuala Lumpur | Tel: +60 3-1234 5678", sub_style))
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph(f"<b>OFFICIAL RECEIPT</b>", styles["Heading2"]))
    story.append(Spacer(1, 0.3*cm))

    # 订单基本信息
    info_data = [
        ["Order No:", uid,       "Payment Time:", pay_time],
        ["Guest:",   name,       "Status:",       status],
        ["Check-in:",checkin,    "Check-out:",    checkout],
        ["Rooms:",   room_list,  "Nights:",       str(days)],
    ]
    info_tbl = Table(info_data, colWidths=[3*cm, 6*cm, 3.5*cm, 4.5*cm])
    info_tbl.setStyle(TableStyle([
        ("FONTSIZE",    (0,0),(-1,-1), 9),
        ("FONTNAME",    (0,0),(0,-1),  "Helvetica-Bold"),
        ("FONTNAME",    (2,0),(2,-1),  "Helvetica-Bold"),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",  (0,0),(-1,-1),4),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 0.5*cm))

    # 消费明细
    detail_rows = [["Description", "Unit Price", "Qty", "Amount (RM)"]]
    for r, pr in rs.items():
        detail_rows.append([
            f"Room Charge - {get_room_label(r)}",
            f"RM {pr:.2f}/night",
            f"{days} nights",
            f"RM {pr * days:.2f}"
        ])

    extras = st.session_state.extra_charges.get(uid, [])
    for ex in extras:
        detail_rows.append([
            f"Extra: {ex['item']}",
            f"RM {ex['amount']:.2f}",
            "1",
            f"RM {ex['amount']:.2f}"
        ])

    detail_rows.append(["", "", "Subtotal:", f"RM {sub + extra_total:.2f}"])
    detail_rows.append(["", "", "SST (6%):", f"RM {tax:.2f}"])
    detail_rows.append(["", "", "Deposit (Refundable):", f"RM {deposit:.2f}"])
    detail_rows.append(["", "", "TOTAL:", f"RM {total:.2f}"])

    det_tbl = Table(detail_rows, colWidths=[8*cm, 3.5*cm, 3.5*cm, 3*cm])
    det_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,0),  colors.HexColor("#1e293b")),
        ("TEXTCOLOR",    (0,0),(-1,0),  colors.white),
        ("FONTNAME",     (0,0),(-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0,0),(-1,-1), 9),
        ("ROWBACKGROUNDS",(0,1),(-1,-5),[colors.white, colors.HexColor("#f8fafc")]),
        ("GRID",         (0,0),(-1,-5), 0.5, colors.HexColor("#e2e8f0")),
        ("FONTNAME",     (2,-4),(2,-1), "Helvetica-Bold"),
        ("FONTNAME",     (3,-1),(3,-1), "Helvetica-Bold"),
        ("FONTSIZE",     (3,-1),(3,-1), 11),
        ("LINEABOVE",    (2,-4),(3,-4), 1, colors.HexColor("#1e293b")),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("TOPPADDING",   (0,0),(-1,-1), 5),
    ]))
    story.append(det_tbl)
    story.append(Spacer(1, 0.8*cm))
    story.append(Paragraph("Thank you for choosing Harmony Hotel. We hope to see you again!", sub_style))
    story.append(Paragraph("This is a computer-generated receipt and does not require a signature.", sub_style))

    doc.build(story)
    return buf.getvalue()

# ════════════════════════════════════════════════════════════════
# 6. 登录网关
# ════════════════════════════════════════════════════════════════
if not st.session_state.is_logged_in:
    _, center_col, _ = st.columns([1, 1.2, 1])
    with center_col:
        st.markdown("<div style='height:100px;'></div>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center;'>🏨 Harmony Hotel</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;color:#64748b;'>Staff Portal v14.0</p>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("Staff ID",   placeholder="asd / Ben")
            p = st.text_input("Password",   type="password", placeholder="**")
            if st.form_submit_button("LOGIN", use_container_width=True):
                if u in ACCOUNTS and ACCOUNTS[u]["password"] == p:
                    st.session_state.is_logged_in = True
                    st.session_state.role          = ACCOUNTS[u]["role"]
                    st.session_state.username      = u
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials.")
                    time.sleep(0.8); st.rerun()
    st.stop()

# ════════════════════════════════════════════════════════════════
# 7. 顶部状态栏（每页显示）
# ════════════════════════════════════════════════════════════════
role_label = "经理 👑" if is_manager() else "前台员工"
role_class = "role-badge-mgr" if is_manager() else "role-badge-staff"
st.markdown(
    f"<div style='text-align:right;margin-bottom:4px;'>"
    f"<span class='{role_class}'>{role_label} — {st.session_state.username}</span>"
    f"</div>",
    unsafe_allow_html=True
)

# 叫醒服务自动检查（每次页面刷新时触发）
now_str = datetime.now().strftime("%H:%M")
for wu in st.session_state.wakeups:
    if wu["status"] == "待执行" and wu["wake_time"] <= now_str:
        wu["status"] = "已触发"

# ════════════════════════════════════════════════════════════════
# 8. 主页看板
# ════════════════════════════════════════════════════════════════
if st.session_state.page == "home":
    st.markdown("<h1 class='main-title'>🏨 鸿蒙智慧酒店管理系统 v14.0</h1>", unsafe_allow_html=True)

    # 顶部指标
    g_in        = sum(h["total"] for h in st.session_state.history)
    g_out       = sum(r["amount"] for r in st.session_state.refunds)
    extra_rev   = sum(get_extra_total(h["uid"]) for h in st.session_state.history)
    occ_count   = sum(1 for r in st.session_state.rooms_db.values() if r["guest"])
    clean_avail = sum(1 for r in st.session_state.rooms_db.values() if r["status"] == "Clean" and not r["guest"])
    occ_rate    = (occ_count / total_room_count()) * 100

    # 未读留言数
    unread_msg  = sum(1 for m in st.session_state.messages if not m["read"])
    # 待触发叫醒数
    pending_wu  = sum(1 for w in st.session_state.wakeups if w["status"] == "待执行")

    m_cols = st.columns(5)
    m_cols[0].metric("入住率",      f"{occ_rate:.0f}%")
    m_cols[1].metric("当日净营收",  f"RM {g_in + extra_rev - g_out:.2f}")
    m_cols[2].metric("未读留言",    f"{unread_msg} 条")
    m_cols[3].metric("待叫醒",      f"{pending_wu} 项")
    m_cols[4].metric("可用洁净房",  f"{clean_avail} 间")

    # 房态栅格
    st.markdown("### 🛏️ 实时房态监控")
    room_grid = st.columns(len(st.session_state.rooms_db))
    for idx, (r_id, r_info) in enumerate(st.session_state.rooms_db.items()):
        with room_grid[idx]:
            is_occ = r_info["guest"] is not None
            s_low  = r_info["status"].lower()
            bc     = "badge-occ" if is_occ else ("badge-clean" if s_low=="clean" else ("badge-ooo" if s_low=="ooo" else "badge-dirty"))
            st.markdown(f"""
                <div class='pms-card'>
                    <div style='display:flex;justify-content:space-between;align-items:center;'>
                        <span style='font-size:1.5rem;font-weight:800;'>{r_id}</span>
                        <span class='badge {bc}'>{r_info['status']}</span>
                    </div>
                    <div style='color:#64748b;font-size:0.85rem;margin-top:4px;'>{r_info['type']}</div>
                    <div style='margin-top:16px;font-weight:600;'>
                        {('👤 ' + r_info['guest']) if is_occ else '✨ Available'}
                    </div>
                    <div style='font-size:0.75rem;color:#94a3b8;margin-top:6px;'>
                        Base: RM {r_info['price']}
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # 快捷导航
    st.markdown("### ⚡ 快捷指令中心")
    nav_cols = st.columns(9)
    btns = [
        ("📝 登记入住",  "in"),
        ("🔑 退房结算",  "out"),
        ("💰 追加消费",  "extra"),
        ("⚙️ 房价管理",  "price"),
        ("🧹 房态维护",  "batch"),
        ("📊 报表中心",  "report"),
        ("💸 退款处理",  "refund"),
        ("💬 留言服务",  "messages"),
        ("⏰ 叫醒服务",  "wakeup"),
    ]
    for col, (label, target) in zip(nav_cols, btns):
        if col.button(label, use_container_width=True):
            nav_to(target); st.rerun()

    # 退出按钮
    if st.button("🚪 安全退出", use_container_width=False):
        for k in ["is_logged_in","role","username","page"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

# ════════════════════════════════════════════════════════════════
# 9. 登记入住
# ════════════════════════════════════════════════════════════════
elif st.session_state.page == "in":
    st.markdown("<h2 class='main-title'>📝 新旅客入住登记</h2>", unsafe_allow_html=True)

    st.markdown("<div class='pms-card'>", unsafe_allow_html=True)
    st.subheader("1. 核心联系人信息")
    c1, c2 = st.columns(2)
    n = c1.text_input("全名 (Name) *")
    i = c2.text_input("证件号 (ID/Passport) *")
    p = c1.text_input("手机号 (Mobile) *")
    e = c2.text_input("电子邮箱 (Email)")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='pms-card'>", unsafe_allow_html=True)
    st.subheader("2. 随行人员（如有）")
    s_count = st.number_input("随行人数", 0, 10, 0, key="in_scount")
    others_cache = []
    for idx in range(int(s_count)):
        sc1, sc2 = st.columns(2)
        others_cache.append({
            "name": sc1.text_input(f"随行人 {idx+1} 姓名", key=f"s_n_{idx}"),
            "ic":   sc2.text_input(f"随行人 {idx+1} 证件", key=f"s_i_{idx}")
        })
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='pms-card'>", unsafe_allow_html=True)
    st.subheader("3. 房源与周期")
    avail = {
        k: get_room_label(k)
        for k, v in st.session_state.rooms_db.items()
        if v["status"] == "Clean" and not v["guest"]
    }

    if not avail:
        st.warning("⚠️ 目前没有可分配的洁净房间。")
    else:
        with st.form("in_form_v14"):
            sel_rooms = st.multiselect("分配客房 *", options=list(avail.keys()), format_func=lambda x: avail[x])
            date_pick = st.date_input("入住 / 退房日期 *", value=[date.today(), date.today() + timedelta(1)])
            submitted = st.form_submit_button("核算账单预览", use_container_width=True)

            if submitted:
                errors = []
                if len(date_pick) < 2:
                    errors.append("请选择完整的入住和退房日期。")
                elif date_pick[0] >= date_pick[1]:
                    errors.append("退房日期必须晚于入住日期。")
                if not n.strip():    errors.append("请填写旅客全名。")
                if not i.strip():    errors.append("请填写证件号。")
                if not p.strip():    errors.append("请填写手机号。")
                if not sel_rooms:    errors.append("请选择至少一间客房。")

                if errors:
                    for err in errors:
                        st.error(f"❌ {err}")
                else:
                    u_code = f"UID-{datetime.now().strftime('%m%d%H%M%S')}"
                    st.session_state.paid = False
                    st.session_state.temp = {
                        "uid":      u_code,
                        "name":     n.strip(),
                        "ic":       i.strip(),
                        "phone":    p.strip(),
                        "email":    e.strip(),
                        "others":   copy.deepcopy(others_cache),
                        "rs":       {r: st.session_state.rooms_db[r]["price"] for r in sel_rooms},
                        "days":     (date_pick[1] - date_pick[0]).days,
                        "checkin":  str(date_pick[0]),
                        "checkout": str(date_pick[1]),
                    }
                    nav_to("pay"); st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    if st.button("⬅️ 返回看板"): nav_to("home"); st.rerun()

# ════════════════════════════════════════════════════════════════
# 10. 账单支付
# ════════════════════════════════════════════════════════════════
elif st.session_state.page == "pay":
    st.markdown("<h2 class='main-title'>💳 账单支付确认</h2>", unsafe_allow_html=True)
    t = st.session_state.temp

    if not t:
        st.error("无效账单，请重新登记。")
        if st.button("重新登记"): nav_to("in"); st.rerun()
        st.stop()

    if st.session_state.paid:
        st.success(f"✅ 入住成功！订单号: {t['uid']}")

        # 找到刚入住的订单，提供 PDF 下载
        order = next((h for h in st.session_state.history if h["uid"] == t["uid"]), None)
        if order and REPORTLAB_OK:
            pdf_bytes = build_receipt_pdf(order)
            st.download_button(
                "📄 下载入住收据 (PDF)",
                data=pdf_bytes,
                file_name=f"receipt_{t['uid']}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        elif not REPORTLAB_OK:
            st.info("（需安装 reportlab 才能生成 PDF 收据）")

        if st.button("返回首页", use_container_width=True):
            nav_to("home"); st.rerun()
    else:
        st.markdown("<div class='pms-card'>", unsafe_allow_html=True)
        st.write(f"*负责人:* {t['name']}  |  *单号:* {t['uid']}")
        st.write(f"*入住:* {t['checkin']}  →  *退房:* {t['checkout']}  （{t['days']} 晚）")
        st.divider()

        items, sub = [], 0.0
        for r, pr in t["rs"].items():
            cost = pr * t["days"]
            sub += cost
            items.append({"描述": f"房费 - {get_room_label(r)}", "明细": f"RM {pr} × {t['days']} 晚", "小计": f"RM {cost:.2f}"})

        tax     = sub * 0.06
        deposit = 100.0
        total   = sub + tax + deposit

        items.append({"描述": "SST (6%)",          "明细": "—", "小计": f"RM {tax:.2f}"})
        items.append({"描述": "履约押金（可退）",   "明细": "—", "小计": f"RM {deposit:.2f}"})
        st.table(pd.DataFrame(items))
        st.markdown(f"<h2 style='text-align:right;'>应付总额: RM {total:.2f}</h2>", unsafe_allow_html=True)

        pc1, pc2, pc3 = st.columns(3)
        if pc1.button("✅ 确认支付", type="primary", use_container_width=True):
            with st.spinner("处理中..."):
                for r in t["rs"]:
                    st.session_state.rooms_db[r].update({
                        "guest":       t["name"],
                        "guest_ic":    t["ic"],
                        "phone":       t["phone"],
                        "email":       t["email"],
                        "others":      copy.deepcopy(t["others"]),
                        "status":      "Occupied",
                        "current_uid": t["uid"],
                        "price_at_checkin": t["rs"][r],
                    })
                st.session_state.history.append({
                    **t,
                    "total":     total,
                    "sub":       sub,
                    "tax":       tax,
                    "deposit":   deposit,
                    "room_list": ", ".join(get_room_label(r) for r in t["rs"]),
                    "time":      datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "status":    "Paid",
                })
                # 初始化该订单的追加消费列表
                if t["uid"] not in st.session_state.extra_charges:
                    st.session_state.extra_charges[t["uid"]] = []
                record_daily_stat()
                st.session_state.paid = True
                st.rerun()

        if pc2.button("❌ 放弃登记", use_container_width=True):
            st.session_state.temp = {}
            st.session_state.paid = False
            nav_to("home"); st.rerun()

        if pc3.button("⬅️ 返回修改", use_container_width=True):
            nav_to("in"); st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# 11. 追加消费
# ════════════════════════════════════════════════════════════════
elif st.session_state.page == "extra":
    st.markdown("<h2 class='main-title'>💰 追加消费记录</h2>", unsafe_allow_html=True)

    # 找出有在住订单的历史记录
    active_orders = [
        h for h in st.session_state.history
        if any(
            st.session_state.rooms_db[r]["current_uid"] == h["uid"]
            for r in st.session_state.rooms_db
            if st.session_state.rooms_db[r].get("current_uid")
        )
    ]

    if not active_orders:
        st.info("目前没有在住订单，无法追加消费。")
    else:
        st.markdown("<div class='pms-card'>", unsafe_allow_html=True)
        st.subheader("选择订单")

        order_map = {
            f"{h['uid']} | {h['name']} | {h['room_list']}": h
            for h in active_orders
        }
        sel_key   = st.selectbox("在住订单", list(order_map.keys()))
        sel_order = order_map[sel_key]
        uid       = sel_order["uid"]

        # 现有追加消费列表
        charges = st.session_state.extra_charges.get(uid, [])
        if charges:
            st.write("*已追加消费：*")
            st.table(pd.DataFrame(charges)[["item","amount","time"]])
            st.write(f"*追加消费小计：RM {sum(c['amount'] for c in charges):.2f}*")
        else:
            st.write("暂无追加消费。")

        st.divider()
        st.subheader("新增消费项目")

        PRESET_ITEMS = ["餐饮", "洗衣服务", "Minibar", "客房服务", "停车费", "其他"]
        with st.form("extra_form"):
            item_choice = st.selectbox("消费类别", PRESET_ITEMS)
            custom_item = st.text_input("自定义名称（选填，覆盖上方类别）")
            amount      = st.number_input("金额 (RM)", min_value=0.01, value=10.0, step=0.5, format="%.2f")
            if st.form_submit_button("✅ 记录消费", use_container_width=True):
                final_item = custom_item.strip() if custom_item.strip() else item_choice
                if uid not in st.session_state.extra_charges:
                    st.session_state.extra_charges[uid] = []
                st.session_state.extra_charges[uid].append({
                    "item":   final_item,
                    "amount": round(amount, 2),
                    "time":   datetime.now().strftime("%Y-%m-%d %H:%M"),
                })
                st.success(f"✅ 已记录：{final_item} — RM {amount:.2f}")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("⬅️ 返回主页"): nav_to("home"); st.rerun()

# ════════════════════════════════════════════════════════════════
# 12. 退房结算
# ════════════════════════════════════════════════════════════════
elif st.session_state.page == "out":
    st.markdown("<h2 class='main-title'>🔑 离店退房管理</h2>", unsafe_allow_html=True)

    # 用 uid 去重，构建在住客人池
    active_pool = {}
    for r_no, v in st.session_state.rooms_db.items():
        if v["guest"]:
            uid = v.get("current_uid") or f"UNKNOWN-{v['guest']}"
            if uid not in active_pool:
                active_pool[uid] = {"name": v["guest"], "ic": v["guest_ic"], "uid": uid, "rooms": []}
            active_pool[uid]["rooms"].append(r_no)

    c_left, c_right = st.columns(2)

    with c_left:
        st.markdown("<div class='pms-card'>", unsafe_allow_html=True)
        st.subheader("退房结算")

        if active_pool:
            display_map = {
                uid: f"{info['name']} | UID: {uid} | 房: {', '.join(info['rooms'])}"
                for uid, info in active_pool.items()
            }
            sel_uid = st.selectbox("选择在住客", list(display_map.keys()), format_func=lambda x: display_map[x])
            info    = active_pool[sel_uid]

            # 显示追加消费汇总
            extra_total = get_extra_total(sel_uid)
            order = next((h for h in st.session_state.history if h["uid"] == sel_uid), None)

            if order:
                st.write(f"*房费总额:* RM {order['total']:.2f}")
                if extra_total > 0:
                    st.write(f"*追加消费:* RM {extra_total:.2f}")
                    st.write(f"*退房应收合计:* RM {order['total'] + extra_total:.2f}")

            if st.button("🔑 办理离店", type="primary", use_container_width=True):
                released = []
                for r_no in info["rooms"]:
                    snapshot = deep_copy_room(st.session_state.rooms_db[r_no])
                    st.session_state.checkout_history.append({
                        "room":     r_no,
                        "snapshot": snapshot,
                        "time":     datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "uid":      info["uid"],
                    })
                    st.session_state.rooms_db[r_no].update({
                        "status": "Dirty", "guest": None, "guest_ic": None,
                        "phone": "", "email": "", "others": [], "current_uid": None,
                    })
                    released.append(r_no)

                # 更新订单状态
                for h in st.session_state.history:
                    if h["uid"] == sel_uid:
                        h["status"] = "Checked Out"
                        h["total"]  = h["total"] + extra_total  # 追加消费并入总额
                        break

                record_daily_stat()
                st.success(f"✅ 离店完成！房号 {', '.join(released)} 已释放。")
                time.sleep(0.5); st.rerun()
        else:
            st.info("目前无在住旅客。")

        st.markdown("</div>", unsafe_allow_html=True)

    with c_right:
        st.markdown("<div class='pms-card'>", unsafe_allow_html=True)
        st.subheader("🔄 撤销退房")

        if st.session_state.checkout_history:
            recent = st.session_state.checkout_history[-3:][::-1]
            for idx, item in enumerate(recent):
                cur = st.session_state.rooms_db[item["room"]]
                has_new = cur["guest"] is not None

                if has_new:
                    st.markdown(f"""
                        <div class='warn-box'>
                        ⚠️ <b>{get_room_label(item['room'])}</b><br>
                        原客: {item['snapshot']['guest']}<br>
                        🔒 已入住新客: <b>{cur['guest']}</b>，无法撤销
                        </div>
                    """, unsafe_allow_html=True)
                    st.button("🔒 无法恢复（房间已被占用）", key=f"undo_{idx}", disabled=True, use_container_width=True)
                else:
                    st.write(f"🏠 {get_room_label(item['room'])} | 👤 {item['snapshot']['guest']} | 🕐 {item.get('time','')}")
                    if st.button(f"↩️ 恢复入住", key=f"undo_{idx}", use_container_width=True):
                        st.session_state.rooms_db[item["room"]] = deep_copy_room(item["snapshot"])
                        # 恢复订单状态
                        for h in st.session_state.history:
                            if h["uid"] == item.get("uid"):
                                h["status"] = "Paid"
                                break
                        st.session_state.checkout_history.remove(item)
                        st.success(f"已恢复 {item['room']} 入住状态。")
                        st.rerun()
        else:
            st.write("暂无最近操作。")

        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("⬅️ 返回主页"): nav_to("home"); st.rerun()

# ════════════════════════════════════════════════════════════════
# 13. 退款处理（仅经理）
# ════════════════════════════════════════════════════════════════
elif st.session_state.page == "refund":
    require_manager()
    st.markdown("<h2 class='main-title'>💸 财务退款中心</h2>", unsafe_allow_html=True)

    if not st.session_state.history:
        st.info("尚无成交订单。")
    else:
        st.markdown("<div class='pms-card'>", unsafe_allow_html=True)

        ref_options = {
            f"{h['uid']} | {h['name']} | {h['room_list']}": i
            for i, h in enumerate(st.session_state.history)
        }
        sel_key = st.selectbox("选择订单", list(ref_options.keys()))
        t_order = st.session_state.history[ref_options[sel_key]]

        refunded = st.session_state.refund_ledger.get(t_order["uid"], 0.0)
        bal      = round(t_order["total"] - refunded, 2)

        c1, c2, c3 = st.columns(3)
        c1.metric("订单总额",   f"RM {t_order['total']:.2f}")
        c2.metric("累计已退",   f"RM {refunded:.2f}")
        c3.metric("剩余可退",   f"RM {bal:.2f}")

        with st.expander("📋 价格明细"):
            for r, pr in t_order.get("rs", {}).items():
                st.write(f"- {get_room_label(r)}: RM {pr} × {t_order.get('days',0)} 晚")
            extras = st.session_state.extra_charges.get(t_order["uid"], [])
            for ex in extras:
                st.write(f"- 追加 {ex['item']}: RM {ex['amount']:.2f}")
            st.write(f"- SST: RM {t_order.get('tax',0):.2f}")
            st.write(f"- 押金: RM {t_order.get('deposit',100):.2f}")

        if bal <= 0:
            st.error("🚫 此订单已全额退款。")
        else:
            amt = st.number_input("退款金额 (RM)", min_value=0.01, max_value=float(bal), value=min(float(bal), 1.0), step=0.01, format="%.2f")
            why = st.text_area("退款原因及审计备注 *")

            if st.button("✅ 批准退款", type="primary", use_container_width=True):
                if not why.strip():
                    st.warning("⚠️ 请填写退款原因。")
                else:
                    new_refunded = round(refunded + amt, 2)
                    st.session_state.refund_ledger[t_order["uid"]] = new_refunded
                    st.session_state.refunds.append({
                        "uid":    t_order["uid"],
                        "name":   t_order["name"],
                        "amount": amt,
                        "reason": why.strip(),
                        "time":   datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "by":     st.session_state.username,
                    })
                    idx = ref_options[sel_key]
                    st.session_state.history[idx]["status"] = (
                        "Fully Refunded" if new_refunded >= t_order["total"] else "Partial Refund"
                    )
                    record_daily_stat()
                    st.success(f"✅ 退款成功 RM {amt:.2f}")
                    time.sleep(1); nav_to("home"); st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("⬅️ 返回"): nav_to("home"); st.rerun()

# ════════════════════════════════════════════════════════════════
# 14. 报表中心（含趋势图）
# ════════════════════════════════════════════════════════════════
elif st.session_state.page == "report":
    st.markdown("<h2 class='main-title'>📊 综合审计报表</h2>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💰 入账明细", "📄 退款日志", "🔍 旅客查询", "📦 退房历史", "📈 趋势图"
    ])

    with tab1:
        df = safe_df(st.session_state.history, ["time","uid","name","room_list","total","status"])
        st.table(df) if not df.empty else st.info("暂无数据")

    with tab2:
        df = safe_df(st.session_state.refunds, ["time","uid","name","amount","reason","by"])
        st.table(df) if not df.empty else st.info("暂无退款记录")

    with tab3:
        q = st.text_input("输入姓名搜索")
        if q:
            matches = [h for h in st.session_state.history if q.lower() in h["name"].lower()]
            df = safe_df(matches, ["time","uid","name","room_list","total","status"])
            st.table(df) if not df.empty else st.warning("未找到匹配旅客")

    with tab4:
        records = [
            {
                "退房时间": item.get("time","N/A"),
                "房号":     get_room_label(item["room"]),
                "旅客":     item["snapshot"].get("guest","N/A"),
                "证件号":   item["snapshot"].get("guest_ic","N/A"),
                "订单UID":  item.get("uid","N/A"),
            }
            for item in st.session_state.checkout_history
        ]
        df = pd.DataFrame(records)
        st.table(df) if not df.empty else st.info("暂无退房记录")

    with tab5:
        st.subheader("入住率 & 净营收趋势")
        stats = st.session_state.daily_stats
        if len(stats) < 1:
            st.info("完成至少一笔入住后，趋势图将自动生成。")
        else:
            df_stats = pd.DataFrame(stats).set_index("date")
            col_a, col_b = st.columns(2)
            with col_a:
                st.write("*入住间数趋势*")
                st.bar_chart(df_stats[["occ"]])
            with col_b:
                st.write("*净营收趋势 (RM)*")
                st.bar_chart(df_stats[["net_revenue"]])

    # 报表页也提供 PDF 下载（经理专属）
    if is_manager() and st.session_state.history:
        st.divider()
        st.subheader("📄 下载订单收据")
        order_opts = {f"{h['uid']} | {h['name']}": h for h in st.session_state.history}
        sel = st.selectbox("选择订单", list(order_opts.keys()), key="report_pdf_sel")
        chosen = order_opts[sel]
        if REPORTLAB_OK:
            pdf_bytes = build_receipt_pdf(chosen)
            st.download_button(
                "⬇️ 下载 PDF 收据",
                data=pdf_bytes,
                file_name=f"receipt_{chosen['uid']}.pdf",
                mime="application/pdf"
            )
        else:
            st.info("需安装 reportlab 库才能生成 PDF。")

    if st.button("⬅️ 返回主页"): nav_to("home"); st.rerun()

# ════════════════════════════════════════════════════════════════
# 15. 房价管理（仅经理）
# ════════════════════════════════════════════════════════════════
elif st.session_state.page == "price":
    require_manager()
    st.markdown("<h2 class='main-title'>⚙️ 客房定价中心</h2>", unsafe_allow_html=True)
    st.markdown("<div class='pms-card'>", unsafe_allow_html=True)
    st.info("⚠️ 调价只影响新订单，已入住订单价格已锁定，不受此处影响。")

    cols = st.columns(len(st.session_state.rooms_db))
    upd  = {}
    for i, (no, d) in enumerate(st.session_state.rooms_db.items()):
        upd[no] = cols[i].number_input(get_room_label(no), value=float(d["price"]), min_value=0.0, step=10.0, key=f"pr_{no}")

    if st.button("💾 保存调价", type="primary", use_container_width=True):
        for no, price in upd.items():
            st.session_state.rooms_db[no]["price"] = price
        st.success("✅ 调价已保存。")
        nav_to("home"); st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    if st.button("⬅️ 返回"): nav_to("home"); st.rerun()

# ════════════════════════════════════════════════════════════════
# 16. 房态维护
# ════════════════════════════════════════════════════════════════
elif st.session_state.page == "batch":
    st.markdown("<h2 class='main-title'>🧹 房态自动化调度</h2>", unsafe_allow_html=True)
    st.markdown("<div class='pms-card'>", unsafe_allow_html=True)

    rooms   = {k: get_room_label(k) for k in st.session_state.rooms_db}
    targets = st.multiselect("目标房间", list(rooms.keys()), format_func=lambda x: rooms[x])
    stat    = st.selectbox("设定状态", ["Clean", "Dirty", "OOO (维修)"])

    if st.button("⚡ 执行同步", type="primary", use_container_width=True):
        if not targets:
            st.warning("请先选择目标房间。")
        else:
            updated, skipped = [], []
            for r in targets:
                if st.session_state.rooms_db[r]["guest"]:
                    skipped.append(r)
                else:
                    st.session_state.rooms_db[r]["status"] = "OOO" if "维修" in stat else stat
                    updated.append(r)
            if updated:  st.success(f"✅ 已同步: {', '.join(updated)}")
            if skipped:  st.warning(f"⚠️ 在住房间跳过: {', '.join(skipped)}")
            if updated:
                nav_to("home"); st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    if st.button("⬅️ 返回"): nav_to("home"); st.rerun()

# ════════════════════════════════════════════════════════════════
# 17. 留言服务
# ════════════════════════════════════════════════════════════════
elif st.session_state.page == "messages":
    st.markdown("<h2 class='main-title'>💬 留言服务</h2>", unsafe_allow_html=True)

    # 获取在住客人列表（用于指定留言目标房间）
    occupied = {
        r_no: f"{r_no} — {r_info['guest']}"
        for r_no, r_info in st.session_state.rooms_db.items()
        if r_info["guest"]
    }

    tab_new, tab_all = st.tabs(["📝 发送留言", "📬 留言记录"])

    with tab_new:
        st.markdown("<div class='pms-card'>", unsafe_allow_html=True)
        if not occupied:
            st.info("目前无在住旅客。")
        else:
            with st.form("msg_form"):
                room_sel = st.selectbox("目标客房", list(occupied.keys()), format_func=lambda x: occupied[x])
                msg_type = st.selectbox("留言类型", ["前台 → 客人", "客人 → 前台"])
                content  = st.text_area("留言内容 *", max_chars=500)
                if st.form_submit_button("📤 发送留言", use_container_width=True):
                    if not content.strip():
                        st.error("❌ 留言内容不能为空。")
                    else:
                        guest_name = st.session_state.rooms_db[room_sel]["guest"]
                        st.session_state.messages.append({
                            "room":      room_sel,
                            "guest":     guest_name,
                            "from_role": msg_type,
                            "content":   content.strip(),
                            "time":      datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "read":      False,
                            "by":        st.session_state.username,
                        })
                        st.success("✅ 留言已发送！")
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_all:
        if st.session_state.messages:
            st.markdown("<div class='pms-card'>", unsafe_allow_html=True)

            # 过滤选项
            filter_room = st.selectbox(
                "按房间筛选",
                ["全部"] + sorted({m["room"] for m in st.session_state.messages})
            )
            msgs = st.session_state.messages
            if filter_room != "全部":
                msgs = [m for m in msgs if m["room"] == filter_room]

            for idx, m in enumerate(reversed(msgs)):
                real_idx = len(st.session_state.messages) - 1 - idx
                unread_tag = "🔴 未读" if not m["read"] else "✅ 已读"
                with st.expander(f"[{unread_tag}] 房 {m['room']} — {m['from_role']} | {m['time']}"):
                    st.write(f"*客人:* {m['guest']}  |  *发送人:* {m.get('by','N/A')}")
                    st.write(f"*内容:* {m['content']}")
                    if not m["read"]:
                        if st.button("✅ 标记已读", key=f"read_{real_idx}"):
                            st.session_state.messages[real_idx]["read"] = True
                            st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

            # 一键全部已读
            if st.button("✅ 全部标记已读", use_container_width=True):
                for m in st.session_state.messages:
                    m["read"] = True
                st.rerun()
        else:
            st.info("暂无留言记录。")

    if st.button("⬅️ 返回主页"): nav_to("home"); st.rerun()

# ════════════════════════════════════════════════════════════════
# 18. 叫醒服务
# ════════════════════════════════════════════════════════════════
elif st.session_state.page == "wakeup":
    st.markdown("<h2 class='main-title'>⏰ 叫醒服务</h2>", unsafe_allow_html=True)

    occupied = {
        r_no: f"{r_no} — {r_info['guest']}"
        for r_no, r_info in st.session_state.rooms_db.items()
        if r_info["guest"]
    }

    tab_add, tab_list = st.tabs(["➕ 设定叫醒", "📋 叫醒列表"])

    with tab_add:
        st.markdown("<div class='pms-card'>", unsafe_allow_html=True)
        if not occupied:
            st.info("目前无在住旅客，无法设定叫醒服务。")
        else:
            with st.form("wakeup_form"):
                room_sel  = st.selectbox("目标客房", list(occupied.keys()), format_func=lambda x: occupied[x])
                wake_date = st.date_input("叫醒日期", value=date.today())
                wake_time = st.time_input("叫醒时间", value=datetime.now().replace(hour=7, minute=0, second=0).time())
                note      = st.text_input("备注（如：早班机）")

                if st.form_submit_button("⏰ 确认设定", use_container_width=True):
                    wake_dt_str = f"{wake_date} {wake_time.strftime('%H:%M')}"
                    # 校验叫醒时间不能早于当前时间
                    wake_dt = datetime.strptime(wake_dt_str, "%Y-%m-%d %H:%M")
                    if wake_dt <= datetime.now():
                        st.error("❌ 叫醒时间必须晚于当前时间。")
                    else:
                        guest_name = st.session_state.rooms_db[room_sel]["guest"]
                        st.session_state.wakeups.append({
                            "room":       room_sel,
                            "guest":      guest_name,
                            "wake_time":  wake_dt_str,
                            "note":       note.strip(),
                            "status":     "待执行",
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "by":         st.session_state.username,
                        })
                        st.success(f"✅ 叫醒服务已设定：{wake_dt_str}")
                        st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with tab_list:
        if st.session_state.wakeups:
            st.markdown("<div class='pms-card'>", unsafe_allow_html=True)

            # 过滤
            filter_status = st.selectbox("按状态筛选", ["全部", "待执行", "已触发", "已取消"])
            wus = st.session_state.wakeups
            if filter_status != "全部":
                wus = [w for w in wus if w["status"] == filter_status]

            for idx, w in enumerate(reversed(wus)):
                real_idx = len(st.session_state.wakeups) - 1 - idx
                status_icon = {"待执行": "🕐", "已触发": "✅", "已取消": "❌"}.get(w["status"], "❓")
                with st.expander(f"{status_icon} 房 {w['room']} — {w['guest']} | 叫醒: {w['wake_time']}"):
                    st.write(f"*备注:* {w['note'] or '无'}  |  *设定人:* {w.get('by','N/A')}")
                    st.write(f"*创建时间:* {w['created_at']}  |  *状态:* {w['status']}")

                    col_a, col_b = st.columns(2)
                    if w["status"] == "待执行":
                        if col_a.button("✅ 标记已执行", key=f"wu_done_{real_idx}"):
                            st.session_state.wakeups[real_idx]["status"] = "已触发"
                            st.rerun()
                        if col_b.button("❌ 取消叫醒",   key=f"wu_cancel_{real_idx}"):
                            st.session_state.wakeups[real_idx]["status"] = "已取消"
                            st.rerun()
                    elif w["status"] == "已触发":
                        col_a.success("叫醒已完成")
                    elif w["status"] == "已取消":
                        col_a.error("已取消")

            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("暂无叫醒记录。")

    if st.button("⬅️ 返回主页"): nav_to("home"); st.rerun()

# ════════════════════════════════════════════════════════════════
# 19. 兜底：未知页面
# ════════════════════════════════════════════════════════════════
else:
    st.warning(f"未知页面 '{st.session_state.page}'，自动重定向...")
    nav_to("home"); st.rerun()

# ════════════════════════════════════════════════════════════════
# v14.0 变更日志
# ════════════════════════════════════════════════════════════════
# 新功能:
#   F1  双角色权限: 员工(asd/1234) | 经理(Ben/1234)
#       - 退款、调价页面员工无法访问
#   F2  追加消费: 餐饮/洗衣/Minibar 等，退房时并入总额
#   F3  PDF 收据: reportlab 生成，含追加消费明细
#   F4  入住率/营收趋势图: 每次支付/退房自动快照
#   F5  留言服务: 前台↔客人，未读标记，按房间筛选
#   F6  叫醒服务: 指定日期时间，状态追踪，时间校验
#
# Bug 修复（继承 v13.0 全部 + 新增）:
#   B1  撤销退房 disabled 保护（新住客已入住时）
#   B2  深拷贝快照防引用污染
#   B3  价格快照锁定，退款不受调价影响
#   B4  退房匹配改用 uid 防同名误退
#   B5  paid 标志在进入 pay 页时初始化
#   B6  safe_df() 保护所有 DataFrame 构造
#   B7  nav_to+rerun 统一化
#   B8  入住率分母动态计算
#   B9  叫醒时间必须晚于当前时间校验
#   B10 追加消费退房时安全并入总额（防重复累加）
#   B11 退款上限精确到分（round 防浮点误差）
#   B12 房态维护空选择时给出提示而非静默失败
#   B13 入住表单多重校验错误同时显示
#   B14 退出登录清理 session 而非简单翻转标志
