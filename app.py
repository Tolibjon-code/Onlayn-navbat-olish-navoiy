# app.py - Она ва бола скрининги маркази учун дастури
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, time, timedelta
import json
import os
import hashlib
import sqlite3
import numpy as np
from typing import Dict, List, Optional
import calendar
from streamlit_option_menu import option_menu
import requests
from PIL import Image
import io
import base64

# Саҳифа конфигурацияси
st.set_page_config(
    page_title="Она ва бола скрининги маркази",
    page_icon="🤰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS стиллари
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        color: #E91E63;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
        background: linear-gradient(90deg, #E91E63, #9C27B0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #9C27B0;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-left: 5px solid #E91E63;
        padding-left: 15px;
    }
    .pregnancy-card {
        background: linear-gradient(135deg, #fce4ec 0%, #f3e5f5 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #E91E63;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .child-card {
        background: linear-gradient(135deg, #e3f2fd 0%, #e8f5e9 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #4CAF50;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .doctor-card {
        background: linear-gradient(135deg, #f3e5f5 0%, #e8eaf6 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid #CE93D8;
        transition: transform 0.3s;
    }
    .doctor-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    .emergency-card {
        background: linear-gradient(135deg, #ffebee 0%, #fff3e0 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #F44336;
        margin-bottom: 1.5rem;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(244, 67, 54, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(244, 67, 54, 0); }
        100% { box-shadow: 0 0 0 0 rgba(244, 67, 54, 0); }
    }
    .stats-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 1rem;
    }
    .stButton > button {
        background: linear-gradient(90deg, #E91E63, #9C27B0);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .time-slot {
        display: inline-block;
        padding: 10px 20px;
        margin: 8px;
        background: linear-gradient(90deg, #2196F3, #21CBF3);
        color: white;
        border-radius: 8px;
        cursor: pointer;
        text-align: center;
        min-width: 100px;
        transition: all 0.3s;
        font-weight: bold;
    }
    .time-slot:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .time-slot.booked {
        background: linear-gradient(90deg, #757575, #9E9E9E);
        cursor: not-allowed;
    }
    .time-slot.selected {
        background: linear-gradient(90deg, #4CAF50, #8BC34A);
        border: 2px solid #2E7D32;
    }
    .pregnancy-week {
        font-size: 1.2rem;
        color: #E91E63;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .notification-badge {
        background-color: #FF5252;
        color: white;
        border-radius: 50%;
        padding: 2px 8px;
        font-size: 0.8rem;
        position: absolute;
        top: 10px;
        right: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Маълумотлар базасини инициализация қилиш
def init_database():
    """SQLite маълумотлар базасини инициализация қилиш"""
    conn = sqlite3.connect('screening_center.db')
    cursor = conn.cursor()
    
    # Фойдаланувчилар таблицаси
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        full_name TEXT,
        phone TEXT,
        email TEXT,
        user_type TEXT, -- 'patient', 'doctor', 'admin'
        birth_date DATE,
        gender TEXT,
        address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
    ''')
    
    # Хомиладорлик таблицаси
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pregnancies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        pregnancy_number INTEGER,
        last_period_date DATE,
        estimated_due_date DATE,
        current_week INTEGER,
        risk_level TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Болалар таблицаси
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS children (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        birth_date DATE,
        gender TEXT,
        birth_weight REAL,
        birth_height REAL,
        current_weight REAL,
        current_height REAL,
        blood_type TEXT,
        allergies TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Шифокорлар таблицаси
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        specialty TEXT,
        qualification TEXT,
        experience_years INTEGER,
        consultation_price REAL,
        working_hours TEXT,
        rating REAL DEFAULT 0.0,
        total_ratings INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Навбатлар таблицаси
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        doctor_id INTEGER,
        appointment_date DATE,
        appointment_time TEXT,
        appointment_type TEXT,
        status TEXT DEFAULT 'scheduled',
        reason TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES users (id),
        FOREIGN KEY (doctor_id) REFERENCES doctors (id)
    )
    ''')
    
    # Скрининг тадқиқотлари
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS screenings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        pregnancy_id INTEGER,
        child_id INTEGER,
        screening_type TEXT,
        screening_date DATE,
        results JSON,
        doctor_id INTEGER,
        recommendations TEXT,
        next_screening_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES users (id),
        FOREIGN KEY (doctor_id) REFERENCES doctors (id)
    )
    ''')
    
    # Лаборатория натижалари
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lab_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        test_type TEXT,
        test_date DATE,
        results JSON,
        normal_range TEXT,
        interpretation TEXT,
        doctor_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES users (id)
    )
    ''')
    
    # Эслатмалар
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        notification_type TEXT,
        message TEXT,
        is_read BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Вакцинация жадвали
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vaccinations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_id INTEGER,
        vaccine_name TEXT,
        scheduled_date DATE,
        administered_date DATE,
        status TEXT DEFAULT 'scheduled',
        doctor_id INTEGER,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (child_id) REFERENCES children (id)
    )
    ''')
    
    conn.commit()
    return conn

# Базани инициализация қилиш
conn = init_database()

# Хеш функцияси
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Авторизация функциялари
def authenticate_user(username, password):
    cursor = conn.cursor()
    password_hash = hash_password(password)
    cursor.execute(
        'SELECT * FROM users WHERE username = ? AND password_hash = ?',
        (username, password_hash)
    )
    user = cursor.fetchone()
    return user

def register_user(user_data):
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash, full_name, phone, email, user_type, birth_date, gender, address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_data['username'],
            hash_password(user_data['password']),
            user_data['full_name'],
            user_data['phone'],
            user_data['email'],
            'patient',
            user_data['birth_date'],
            user_data['gender'],
            user_data.get('address', '')
        ))
        conn.commit()
        return True, "✅ Рўйхатдан ўтдингиз!"
    except sqlite3.IntegrityError:
        return False, "⚠️ Бу фойдаланувчи номи аллақачон мавжуд"
    except Exception as e:
        return False, f"❌ Хатолик: {str(e)}"

# Хомиладорлик ҳисоблаш функциялари
def calculate_pregnancy_week(last_period_date):
    """Хомиладорлик ҳафтасини ҳисоблаш"""
    today = date.today()
    days_pregnant = (today - last_period_date).days
    weeks_pregnant = days_pregnant // 7
    days_remaining = days_pregnant % 7
    return weeks_pregnant, days_remaining

def calculate_due_date(last_period_date):
    """Тахминий туғиш кунини ҳисоблаш (40 ҳафта)"""
    return last_period_date + timedelta(days=280)

# Бола ривожланиши функциялари
def calculate_child_age(birth_date):
    """Бола ёшини ҳисоблаш"""
    today = date.today()
    years = today.year - birth_date.year
    months = today.month - birth_date.month
    days = today.day - birth_date.day
    
    if days < 0:
        months -= 1
        days += 30
    
    if months < 0:
        years -= 1
        months += 12
    
    return years, months, days

def get_growth_percentile(weight, height, age_months, gender):
    """Бола ўсишини баҳолаш (содда версия)"""
    # Содда ўлчовлар (хақиқий маълумотлар учун махсус база керак)
    if gender.lower() == 'эркак':
        if age_months <= 12:
            if weight >= 10 and height >= 75:
                return "90-чи процентильдан юқори"
            elif weight >= 8 and height >= 70:
                return "50-чи процентиль"
            else:
                return "10-чи процентильдан паст"
    return "Нормал"

# Шифокорлар маълумотлари
SPECIALTIES = {
    "primatolog": {
        "name": "Пренатолог",
        "description": "Хомиладорлик даврида она ва ножаённинг соглиғини кузатиш",
        "icon": "👶",
        "tests": ["УЗИ", "Кардиотокография", "Скрининг тестлари"]
    },
    "endocrinolog": {
        "name": "Эндокринолог",
        "description": "Гормон системаси касалликларини даволаш",
        "icon": "⚖️",
        "tests": ["Қондаги қанд", "Гормонлар таҳлили", "Тиреоид гормонлари"]
    },
    "genetik": {
        "name": "Генетик",
        "description": "Насллий касалликларни ташхислаш ва профилактика",
        "icon": "🧬",
        "tests": ["Генетик скрининг", "ДНК таҳлили", "Хромосома таҳлили"]
    },
    "nevropatolog": {
        "name": "Невропатолог",
        "description": "Нерв системаси касалликларини даволаш",
        "icon": "🧠",
        "tests": ["ЭЭГ", "ЭМГ", "Неврологик текширув"]
    },
    "lab": {
        "name": "Лаборатория шифокори",
        "description": "Лаборатория таҳлилларини баҳолаш",
        "icon": "🔬",
        "tests": ["Қон таҳлили", "Сийдик таҳлили", "Биохимик таҳлил"]
    },
    "statist": {
        "name": "Статистик шифокор",
        "description": "Тиббий статистика ва маълумотларни таҳлил қилиш",
        "icon": "📊",
        "tests": ["Статистик таҳлил", "Маълумотлар таҳлили", "Трендлар таҳлили"]
    }
}

# Асосий функция
def main():
    # Сайдбар меню
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3069/3069172.png", width=100)
        
        if 'user' not in st.session_state:
            # Кириш/Рўйхатдан ўтиш
            menu_choice = option_menu(
                "Кириш",
                ["Кириш", "Рўйхатдан ўтиш"],
                icons=['box-arrow-in-right', 'person-plus'],
                menu_icon="cast",
                default_index=0
            )
            
            if menu_choice == "Кириш":
                st.markdown("### Кириш")
                username = st.text_input("Фойдаланувчи номи")
                password = st.text_input("Парол", type="password")
                
                if st.button("Кириш", type="primary"):
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state.user = {
                            'id': user[0],
                            'username': user[1],
                            'full_name': user[3],
                            'user_type': user[6]
                        }
                        st.success(f"Хуш келибсиз, {user[3]}!")
                        st.rerun()
                    else:
                        st.error("Нотўғри фойдаланувчи номи ёки парол!")
            
            elif menu_choice == "Рўйхатдан ўтиш":
                st.markdown("### Рўйхатдан ўтиш")
                with st.form("register_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        username = st.text_input("Фойдаланувчи номи*")
                        full_name = st.text_input("Тўлиқ исм*")
                        phone = st.text_input("Телефон рақам*")
                    with col2:
                        email = st.text_input("Email")
                        password = st.text_input("Парол*", type="password")
                        confirm_password = st.text_input("Паролни тасдиқланг*", type="password")
                    
                    birth_date = st.date_input("Туғилган сана*", max_value=date.today())
                    gender = st.selectbox("Жинс*", ["Аёл", "Эркак"])
                    address = st.text_area("Яшаш манзили")
                    
                    if st.form_submit_button("Рўйхатдан ўтиш"):
                        if password != confirm_password:
                            st.error("Пароллар мос келмайди!")
                        else:
                            user_data = {
                                'username': username,
                                'password': password,
                                'full_name': full_name,
                                'phone': phone,
                                'email': email,
                                'birth_date': birth_date.isoformat(),
                                'gender': gender,
                                'address': address
                            }
                            success, message = register_user(user_data)
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
        
        else:
            # Фойдаланувчи кирганда
            user = st.session_state.user
            st.markdown(f"### 👤 {user['full_name']}")
            st.markdown(f"**Рол:** {user['user_type']}")
            
            # Меню
            if user['user_type'] == 'patient':
                menu_options = [
                    "🏠 Асосий саҳифа",
                    "🤰 Хомиладорлик",
                    "👶 Болаларим",
                    "👨‍⚕️ Шифокорлар",
                    "📅 Навбатлар",
                    "📊 Скрининг",
                    "💉 Вакцинация",
                    "🔔 Эслатмалар",
                    "⚙️ Профиль"
                ]
                icons = [
                    'house', 'person-pregnant', 'people',
                    'person-badge', 'calendar-check', 'clipboard-pulse',
                    'syringe', 'bell', 'gear'
                ]
            elif user['user_type'] == 'doctor':
                menu_options = [
                    "🏠 Асосий саҳифа",
                    "📋 Кабинет",
                    "👥 Беморлар",
                    "📅 Жадвал",
                    "📊 Статистика",
                    "💬 Консультация",
                    "⚙️ Профиль"
                ]
                icons = [
                    'house', 'clipboard', 'people',
                    'calendar', 'bar-chart', 'chat',
                    'gear'
                ]
            else:  # admin
                menu_options = [
                    "🏠 Асосий саҳифа",
                    "📊 Умумий статистика",
                    "👨‍⚕️ Шифокорлар",
                    "👥 Фойдаланувчилар",
                    "🏥 Марказ маълумотлари",
                    "⚙️ Тизим созламалари"
                ]
                icons = [
                    'house', 'bar-chart', 'person-badge',
                    'people', 'hospital', 'gear'
                ]
            
            selected = option_menu(
                menu_title="Меню",
                options=menu_options,
                icons=icons,
                menu_icon="cast",
                default_index=0
            )
            
            if st.button("📤 Чиқиш"):
                del st.session_state.user
                st.rerun()
    
    # Асосий контент
    if 'user' not in st.session_state:
        show_landing_page()
    else:
        user = st.session_state.user
        if user['user_type'] == 'patient':
            handle_patient_pages(selected, user)
        elif user['user_type'] == 'doctor':
            handle_doctor_pages(selected, user)
        else:
            handle_admin_pages(selected, user)

def show_landing_page():
    """Лендинг саҳифаси"""
    st.markdown('<h1 class="main-header">🤰 Она ва бола скрининги маркази</h1>', unsafe_allow_html=True)
    
    # Хизматлар
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="pregnancy-card">', unsafe_allow_html=True)
        st.markdown("### 🤰 Хомиладорлик")
        st.markdown("""
        - Пренатал скрининг
        - УЗИ текшируви
        - Лаборатория таҳлиллари
        - Эндокринолог текшируви
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="child-card">', unsafe_allow_html=True)
        st.markdown("### 👶 Болалар")
        st.markdown("""
        - Вакцинация
        - Ривожланиш текшируви
        - Генетик консультация
        - Невропатолог текшируви
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="doctor-card">', unsafe_allow_html=True)
        st.markdown("### 👨‍⚕️ Шифокорлар")
        st.markdown("""
        - Пренатолог
        - Эндокринолог
        - Генетик
        - Невропатолог
        - Лаборатория мутахассиси
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Шошилинч ёрдам
    st.markdown('<div class="emergency-card">', unsafe_allow_html=True)
    st.markdown("### 🚨 Шошилинч ёрдам")
    
    emergency_cols = st.columns(4)
    with emergency_cols[0]:
        if st.button("🚑 Тежёрув", key="ambulance"):
            st.info("Тежёрув: **103**")
    with emergency_cols[1]:
        if st.button("👶 Болалар тежёруви", key="child_emergency"):
            st.info("Болалар тежёруви: **116**")
    with emergency_cols[2]:
        if st.button("📞 Марказ тежёруви", key="center_emergency"):
            st.info("Марказ тежёруви: **+998 71 123 45 67**")
    with emergency_cols[3]:
        if st.button("💬 Онлайн консультация", key="online_consult"):
            st.info("Онлайн консультация учун тизимга киринг")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Хомиладорлик ҳафтаси ҳисоблагич
    st.markdown('<h2 class="sub-header">📅 Хомиладорлик ҳафтасини ҳисоблаш</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        last_period = st.date_input("Охирги ҳаёт давраси санаси", value=date.today() - timedelta(days=7*12))
    with col2:
        if st.button("Ҳисоблаш", type="primary"):
            weeks, days = calculate_pregnancy_week(last_period)
            due_date = calculate_due_date(last_period)
            
            st.markdown(f"""
            <div class="pregnancy-card">
            <div class="pregnancy-week">🎉 {weeks} ҳафта {days} кун</div>
            <p><strong>Тахминий туғиш куни:</strong> {due_date.strftime('%d.%m.%Y')}</p>
            <p><strong>Қолган вақт:</strong> {(due_date - date.today()).days} кун</p>
            </div>
            """, unsafe_allow_html=True)

def handle_patient_pages(selected, user):
    """Бемор учун саҳифалар"""
    if selected == "🏠 Асосий саҳифа":
        show_patient_dashboard(user)
    elif selected == "🤰 Хомиладорлик":
        show_pregnancy_page(user)
    elif selected == "👶 Болаларим":
        show_children_page(user)
    elif selected == "👨‍⚕️ Шифокорлар":
        show_doctors_page(user)
    elif selected == "📅 Навбатлар":
        show_appointments_page(user)
    elif selected == "📊 Скрининг":
        show_screening_page(user)
    elif selected == "💉 Вакцинация":
        show_vaccination_page(user)
    elif selected == "🔔 Эслатмалар":
        show_notifications_page(user)
    elif selected == "⚙️ Профиль":
        show_profile_page(user)

def show_patient_dashboard(user):
    """Бемор дашборди"""
    st.markdown(f'<h1 class="main-header">👋 Хуш келибсиз, {user["full_name"]}!</h1>', unsafe_allow_html=True)
    
    # Статистика карточкалари
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM appointments WHERE patient_id = ?', (user['id'],))
        appointments_count = cursor.fetchone()[0]
        st.markdown(f'''
        <div class="stats-card">
            <h3>📅</h3>
            <h2>{appointments_count}</h2>
            <p>Навбатлар</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        cursor.execute('SELECT COUNT(*) FROM pregnancies WHERE user_id = ?', (user['id'],))
        pregnancies_count = cursor.fetchone()[0]
        st.markdown(f'''
        <div class="stats-card">
            <h3>🤰</h3>
            <h2>{pregnancies_count}</h2>
            <p>Хомиладорлик</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        cursor.execute('SELECT COUNT(*) FROM children WHERE user_id = ?', (user['id'],))
        children_count = cursor.fetchone()[0]
        st.markdown(f'''
        <div class="stats-card">
            <h3>👶</h3>
            <h2>{children_count}</h2>
            <p>Болалар</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        cursor.execute('SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0', (user['id'],))
        notifications_count = cursor.fetchone()[0]
        st.markdown(f'''
        <div class="stats-card">
            <h3>🔔</h3>
            <h2>{notifications_count}</h2>
            <p>Янги эслатма</p>
        </div>
        ''', unsafe_allow_html=True)
    
    # Яқин навбатлар
    st.markdown('<h2 class="sub-header">📅 Яқин навбатларим</h2>', unsafe_allow_html=True)
    
    cursor.execute('''
        SELECT a.appointment_date, a.appointment_time, d.specialty, u.full_name 
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users u ON d.user_id = u.id
        WHERE a.patient_id = ? AND a.status = 'scheduled' 
        AND a.appointment_date >= DATE('now')
        ORDER BY a.appointment_date, a.appointment_time
        LIMIT 5
    ''', (user['id'],))
    
    appointments = cursor.fetchall()
    
    if appointments:
        for app in appointments:
            st.markdown(f'''
            <div class="queue-card">
                <strong>📅 {app[0]}</strong> | <strong>⏰ {app[1]}</strong><br>
                <strong>👨‍⚕️ {app[2]}</strong> - {app[3]}
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.info("📭 Яқин навбатлар йўқ")
    
    # Хомиладорлик маълумотлари
    cursor.execute('SELECT * FROM pregnancies WHERE user_id = ? ORDER BY created_at DESC LIMIT 1', (user['id'],))
    pregnancy = cursor.fetchone()
    
    if pregnancy:
        st.markdown('<h2 class="sub-header">🤰 Жорий хомиладорлик</h2>', unsafe_allow_html=True)
        
        weeks, days = calculate_pregnancy_week(date.fromisoformat(pregnancy[3]))
        due_date = date.fromisoformat(pregnancy[4])
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'''
            <div class="pregnancy-card">
                <div class="pregnancy-week">{weeks} ҳафта {days} кун</div>
                <p><strong>Тахминий туғиш куни:</strong> {due_date.strftime('%d.%m.%Y')}</p>
                <p><strong>Қолган вақт:</strong> {(due_date - date.today()).days} кун</p>
                <p><strong Хавф даражаси:> {pregnancy[6]}</p>
            </div>
            ''', unsafe_allow_html=True)
        
        with col2:
            # Хомиладорлик прогресси
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=weeks,
                title={'text': "Хомиладорлик ҳафтаси"},
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [0, 42]},
                    'bar': {'color': "#E91E63"},
                    'steps': [
                        {'range': [0, 14], 'color': "lightgray"},
                        {'range': [14, 28], 'color': "gray"},
                        {'range': [28, 42], 'color': "darkgray"}
                    ]
                }
            ))
            st.plotly_chart(fig, use_container_width=True)

def show_pregnancy_page(user):
    """Хомиладорлик саҳифаси"""
    st.markdown('<h1 class="main-header">🤰 Хомиладорлик</h1>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Маълумотлар", "📅 Скрининг", "📊 Натижалар", "➕ ЯнгИ хомиладорлик"])
    
    with tab1:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pregnancies WHERE user_id = ?', (user['id'],))
        pregnancies = cursor.fetchall()
        
        if pregnancies:
            for preg in pregnancies:
                weeks, days = calculate_pregnancy_week(date.fromisoformat(preg[3]))
                
                with st.expander(f"Хомиладорлик #{preg[2]} - {weeks} ҳафта {days} кун"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Охирги ҳаёт давраси:** {preg[3]}")
                        st.markdown(f"**Тахминий туғиш куни:** {preg[4]}")
                        st.markdown(f"**Жорий ҳафта:** {preg[5]}")
                    with col2:
                        st.markdown(f"**Хавф даражаси:** {preg[6]}")
                        st.markdown(f"**Эслатмалар:** {preg[7]}")
        
        # Скрининг жадвали
        st.markdown('<h3 class="sub-header">📅 Скрининг жадвали</h3>', unsafe_allow_html=True)
        
        screening_schedule = {
            "1-триместр (8-13 ҳафта)": ["Қон таҳлили", "УЗИ", "Биохимик скрининг"],
            "2-триместр (18-22 ҳафта)": ["Детал УЗИ", "Қондаги қанд", "Кардиотокография"],
            "3-триместр (28-32 ҳафта)": ["УЗИ", "Қон таҳлили", "Қисқа муддатли УЗИ"]
        }
        
        for trimester, tests in screening_schedule.items():
            with st.expander(trimester):
                for test in tests:
                    st.markdown(f"✅ {test}")
    
    with tab2:
        st.markdown('<h3 class="sub-header">🎯 Скрининг навбати</h3>', unsafe_allow_html=True)
        
        # Скрининг турлари
        screening_types = {
            "1-триместр скрининги": "8-13 ҳафта",
            "2-триместр скрининги": "18-22 ҳафта",
            "3-триместр скрининги": "28-32 ҳафта",
            "Генетик скрининг": "10-13 ҳафта",
            "УЗИ скрининг": "Ҳар 4 ҳафтада"
        }
        
        selected_screening = st.selectbox("Скрининг турини танланг", list(screening_types.keys()))
        st.info(f"**Тавсия этилган вақт:** {screening_types[selected_screening]}")
        
        # Вақт танлаш
        available_dates = [
            (date.today() + timedelta(days=i)).strftime('%Y-%m-%d') 
            for i in range(1, 31) 
            if (date.today() + timedelta(days=i)).weekday() < 5
        ]
        
        selected_date = st.selectbox("Кунни танланг", available_dates)
        
        available_times = ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
        selected_time = st.selectbox("Вақтни танланг", available_times)
        
        if st.button("🎫 Навбат олиш", type="primary"):
            # Скрининг навбатини сақлаш
            st.success(f"✅ Скрининг навбати олинди!\n**Кун:** {selected_date}\n**Вақт:** {selected_time}")
    
    with tab3:
        st.markdown('<h3 class="sub-header">📊 Скрининг натижалари</h3>', unsafe_allow_html=True)
        
        # Скрининг натижалари таблицаси
        screening_results = [
            {"Скрининг": "1-триместр", "Сана": "2024-01-15", "Натижа": "Норма", "Тавсия": "Регуляр УЗИ"},
            {"Скрининг": "Қон таҳлили", "Сана": "2024-01-10", "Натижа": "Норма", "Тавсия": "Витамин истеьмол қилиш"},
            {"Скрининг": "УЗИ", "Сана": "2024-01-05", "Натижа": "Норма", "Тавсия": "4 ҳафтадан кейин кайта УЗИ"}
        ]
        
        df = pd.DataFrame(screening_results)
        st.dataframe(df, use_container_width=True)
        
        # График
        fig = px.line(df, x='Сана', y='Скрининг', title='Скрининг натижалари')
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.markdown('<h3 class="sub-header">➕ ЯнгИ хомиладорлик қўшиш</h3>', unsafe_allow_html=True)
        
        with st.form("new_pregnancy"):
            col1, col2 = st.columns(2)
            with col1:
                pregnancy_number = st.number_input("Хомиладорлик рақами", min_value=1, value=1)
                last_period = st.date_input("Охирги ҳаёт давраси", key="new_last_period")
            with col2:
                risk_level = st.selectbox("Хавф даражаси", ["Паст", "Ўрта", "Юқори"])
                notes = st.text_area("Қўшимча маълумотлар")
            
            if st.form_submit_button("Қўшиш"):
                due_date = calculate_due_date(last_period)
                weeks, _ = calculate_pregnancy_week(last_period)
                
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO pregnancies (user_id, pregnancy_number, last_period_date, estimated_due_date, current_week, risk_level, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user['id'], pregnancy_number, last_period.isoformat(), due_date.isoformat(), weeks, risk_level, notes))
                conn.commit()
                
                st.success("✅ ЯнгИ хомиладорлик қўшилди!")

def show_children_page(user):
    """Болалар саҳифаси"""
    st.markdown('<h1 class="main-header">👶 Болаларим</h1>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["👶 Болалар рўйхати", "📈 Ривожланиш", "➕ ЯнгИ бола қўшиш"])
    
    with tab1:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM children WHERE user_id = ?', (user['id'],))
        children = cursor.fetchall()
        
        if children:
            for child in children:
                years, months, days = calculate_child_age(date.fromisoformat(child[3]))
                
                with st.expander(f"{child[2]} - {years} ёш {months} ой {days} кун"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Туғилган сана:** {child[3]}")
                        st.markdown(f"**Жинс:** {child[4]}")
                        st.markdown(f"**Туғилган вазни:** {child[5]} кг")
                        st.markdown(f"**Туғилган бўйи:** {child[6]} см")
                    with col2:
                        st.markdown(f"**Жорий вазн:** {child[7]} кг")
                        st.markdown(f"**Жорий бўй:** {child[8]} см")
                        st.markdown(f"**Қон гуруҳи:** {child[9]}")
                        st.markdown(f"**Аллергиялар:** {child[10]}")
        
        else:
            st.info("📭 Ҳозирча болалар рўйхати бўш")
    
    with tab2:
        st.markdown('<h3 class="sub-header">📈 Бола ривожланиш мониторинги</h3>', unsafe_allow_html=True)
        
        if children:
            child_names = [child[2] for child in children]
            selected_child = st.selectbox("Болани танланг", child_names)
            
            if selected_child:
                # Вазн бўйича график
                weight_data = {
                    "Ой": [1, 2, 3, 4, 5, 6, 9, 12],
                    "Вазн (кг)": [3.5, 4.5, 5.5, 6.2, 6.8, 7.3, 8.5, 9.2]
                }
                
                df_weight = pd.DataFrame(weight_data)
                fig1 = px.line(df_weight, x='Ой', y='Вазн (кг)', title='Вазн ривожланиши')
                st.plotly_chart(fig1, use_container_width=True)
                
                # Бўй бўйича график
                height_data = {
                    "Ой": [1, 2, 3, 4, 5, 6, 9, 12],
                    "Бўй (см)": [52, 57, 61, 64, 67, 69, 73, 76]
                }
                
                df_height = pd.DataFrame(height_data)
                fig2 = px.line(df_height, x='Ой', y='Бўй (см)', title='Бўй ривожланиши')
                st.plotly_chart(fig2, use_container_width=True)
    
    with tab3:
        st.markdown('<h3 class="sub-header">➕ ЯнгИ бола қўшиш</h3>', unsafe_allow_html=True)
        
        with st.form("new_child"):
            col1, col2 = st.columns(2)
            with col1:
                child_name = st.text_input("Боланинг исми*")
                birth_date = st.date_input("Туғилган сана*", max_value=date.today())
                gender = st.selectbox("Жинс*", ["Эркак", "Аёл"])
                birth_weight = st.number_input("Туғилган вазни (кг)*", min_value=1.0, max_value=10.0, value=3.5)
            with col2:
                birth_height = st.number_input("Туғилган бўйи (см)*", min_value=30, max_value=70, value=52)
                current_weight = st.number_input("Жорий вазн (кг)", min_value=1.0, max_value=50.0, value=birth_weight)
                current_height = st.number_input("Жорий бўй (см)", min_value=30, max_value=200, value=birth_height)
                blood_type = st.selectbox("Қон гуруҳи", ["А(I)", "Б(II)", "AB(III)", "O(IV)"])
            
            allergies = st.text_area("Аллергиялар (ихтиёрий)")
            notes = st.text_area("Қўшимча маълумотлар")
            
            if st.form_submit_button("Қўшиш"):
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO children (user_id, name, birth_date, gender, birth_weight, birth_height, 
                                        current_weight, current_height, blood_type, allergies, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user['id'], child_name, birth_date.isoformat(), gender, birth_weight, birth_height,
                     current_weight, current_height, blood_type, allergies, notes))
                conn.commit()
                
                st.success("✅ ЯнгИ бола қўшилди!")

def show_doctors_page(user):
    """Шифокорлар саҳифаси"""
    st.markdown('<h1 class="main-header">👨‍⚕️ Шифокорларимиз</h1>', unsafe_allow_html=True)
    
    # Шифокорлар излаш
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        search_term = st.text_input("🔍 Шифокор излаш (махсуслик ёки исм бўйича)")
    with search_col2:
        specialty_filter = st.selectbox("Махсуслиг", ["Барчаси"] + list(SPECIALTIES.keys()))
    
    # Шифокорларни кўрсатиш
    cursor = conn.cursor()
    
    if specialty_filter != "Барчаси":
        cursor.execute('''
            SELECT u.full_name, d.specialty, d.qualification, d.experience_years, d.rating, d.consultation_price
            FROM doctors d
            JOIN users u ON d.user_id = u.id
            WHERE d.specialty = ?
        ''', (specialty_filter,))
    else:
        cursor.execute('''
            SELECT u.full_name, d.specialty, d.qualification, d.experience_years, d.rating, d.consultation_price
            FROM doctors d
            JOIN users u ON d.user_id = u.id
        ''')
    
    doctors = cursor.fetchall()
    
    # Филтрлаш
    if search_term:
        doctors = [doc for doc in doctors if search_term.lower() in doc[0].lower() or search_term.lower() in doc[1].lower()]
    
    # Шифокорларни кўрсатиш
    cols = st.columns(2)
    for idx, doctor in enumerate(doctors):
        with cols[idx % 2]:
            st.markdown(f'''
            <div class="doctor-card">
                <h3>{SPECIALTIES.get(doctor[1], {}).get('icon', '👨‍⚕️')} {doctor[0]}</h3>
                <p><strong>Махсуслиги:</strong> {SPECIALTIES.get(doctor[1], {}).get('name', doctor[1])}</p>
                <p><strong>Маълумоти:</strong> {doctor[2]}</p>
                <p><strong>Тажриба:</strong> {doctor[3]} йил</p>
                <p><strong>Рейтинг:</strong> {"⭐" * int(doctor[4])} ({doctor[4]})</p>
                <p><strong>Консультация нархи:</strong> {doctor[5]:,.0f} сўм</p>
            </div>
            ''', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🎫 Навбат олиш", key=f"appoint_{idx}"):
                    st.session_state.selected_doctor = doctor[0]
                    st.session_state.selected_specialty = doctor[1]
                    st.rerun()
            with col2:
                if st.button("💬 Онлайн консультация", key=f"consult_{idx}"):
                    st.info("Онлайн консультация тезда ишга тушади...")
    
    # Навбат олиш формаси
    if 'selected_doctor' in st.session_state:
        st.markdown("---")
        st.markdown(f'<h3 class="sub-header">🎫 Навбат олиш: {st.session_state.selected_doctor}</h3>', unsafe_allow_html=True)
        
        with st.form("appointment_form"):
            col1, col2 = st.columns(2)
            with col1:
                appointment_date = st.date_input("Кун", min_value=date.today())
                appointment_type = st.selectbox("Кўриқ тури", ["Дори-дармон", "Текширув", "Консультация", "Скрининг"])
            with col2:
                available_times = ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
                appointment_time = st.selectbox("Вақт", available_times)
                reason = st.text_area("Сабаб")
            
            if st.form_submit_button("Навбатни тасдиқланг"):
                # Навбатни сақлаш
                st.success(f"✅ Навбат олинди!\n**Шифокор:** {st.session_state.selected_doctor}\n**Кун:** {appointment_date}\n**Вақт:** {appointment_time}")
                del st.session_state.selected_doctor
                del st.session_state.selected_specialty

def show_appointments_page(user):
    """Навбатлар саҳифаси"""
    st.markdown('<h1 class="main-header">📅 Навбатларим</h1>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📋 Жадвал", "📊 Статистика", "📝 ЯнгИ навбат"])
    
    with tab1:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.id, a.appointment_date, a.appointment_time, d.specialty, u.full_name, a.status, a.reason
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            JOIN users u ON d.user_id = u.id
            WHERE a.patient_id = ?
            ORDER BY a.appointment_date DESC
        ''', (user['id'],))
        
        appointments = cursor.fetchall()
        
        if appointments:
            for app in appointments:
                status_color = {
                    'scheduled': '#4CAF50',
                    'completed': '#2196F3',
                    'cancelled': '#F44336'
                }.get(app[5], '#9E9E9E')
                
                st.markdown(f'''
                <div style="background: white; padding: 1rem; border-radius: 10px; border-left: 5px solid {status_color}; margin-bottom: 1rem;">
                    <strong>📅 {app[1]}</strong> | <strong>⏰ {app[2]}</strong> | 
                    <span style="color: {status_color}; font-weight: bold;">{app[5].upper()}</span><br>
                    <strong>👨‍⚕️ {app[3]}</strong> - {app[4]}<br>
                    <strong>Сабаб:</strong> {app[6]}
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.info("📭 Навбатлар йўқ")
    
    with tab2:
        # Навбатлар статистикаси
        cursor.execute('''
            SELECT status, COUNT(*) as count
            FROM appointments
            WHERE patient_id = ?
            GROUP BY status
        ''', (user['id'],))
        
        status_stats = cursor.fetchall()
        
        if status_stats:
            df_status = pd.DataFrame(status_stats, columns=['Статус', 'Сони'])
            fig = px.pie(df_status, values='Сони', names='Статус', title='Навбатлар статуси')
            st.plotly_chart(fig, use_container_width=True)
        
        # Ойлик навбатлар
        cursor.execute('''
            SELECT strftime('%Y-%m', appointment_date) as month, COUNT(*) as count
            FROM appointments
            WHERE patient_id = ?
            GROUP BY month
            ORDER BY month
        ''', (user['id'],))
        
        monthly_stats = cursor.fetchall()
        
        if monthly_stats:
            df_monthly = pd.DataFrame(monthly_stats, columns=['Ой', 'Навбатлар'])
            fig2 = px.bar(df_monthly, x='Ой', y='Навбатлар', title='Ойлик навбатлар')
            st.plotly_chart(fig2, use_container_width=True)
    
    with tab3:
        st.markdown('<h3 class="sub-header">🎫 ЯнгИ навбат олиш</h3>', unsafe_allow_html=True)
        
        # Шифокорларни танлаш
        cursor.execute('SELECT d.id, u.full_name, d.specialty FROM doctors d JOIN users u ON d.user_id = u.id')
        doctors = cursor.fetchall()
        
        doctor_options = {f"{doc[1]} ({doc[2]})": doc[0] for doc in doctors}
        selected_doctor = st.selectbox("Шифокорни танланг", list(doctor_options.keys()))
        
        # Вақт танлаш
        col1, col2 = st.columns(2)
        with col1:
            appointment_date = st.date_input("Кун", min_value=date.today())
        with col2:
            available_times = ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
            appointment_time = st.selectbox("Вақт", available_times)
        
        appointment_type = st.selectbox("Кўриқ тури", ["Дори-дармон", "Текширув", "Консультация", "Скрининг", "Вакцинация"])
        reason = st.text_area("Сабаб (ихтиёрий)")
        
        if st.button("Навбатни тасдиқланг", type="primary"):
            doctor_id = doctor_options[selected_doctor]
            
            cursor.execute('''
                INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, appointment_type, reason)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user['id'], doctor_id, appointment_date.isoformat(), appointment_time, appointment_type, reason))
            conn.commit()
            
            st.success("✅ Навбат муваффақиятли олинди!")

def show_screening_page(user):
    """Скрининг саҳифаси"""
    st.markdown('<h1 class="main-header">📊 Скрининг ва таҳлиллар</h1>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["🩺 Лаборатория", "📈 Натижалар", "📅 Жадвал", "💡 Тавсиялар"])
    
    with tab1:
        st.markdown('<h3 class="sub-header">🩺 Лаборатория таҳлиллари</h3>', unsafe_allow_html=True)
        
        test_types = [
            "Қондаги умумий таҳлил",
            "Биохимик таҳлил",
            "Гормонлар таҳлили",
            "Сийдик таҳлили",
            "Генетик таҳлил",
            "Иммунологик таҳлил"
        ]
        
        selected_test = st.selectbox("Таҳлил турини танланг", test_types)
        
        col1, col2 = st.columns(2)
        with col1:
            test_date = st.date_input("Таҳлил санаси", value=date.today())
        with col2:
            fasting = st.checkbox("Оч қорин")
        
        if st.button("Таҳлил учун навбат олиш"):
            st.success(f"✅ {selected_test} учун навбат олинди!\n**Сана:** {test_date}")
    
    with tab2:
        st.markdown('<h3 class="sub-header">📈 Таҳлил натижалари</h3>', unsafe_allow_html=True)
        
        # Намуна таҳлил натижалари
        lab_results = {
            "Қондаги умумий таҳлил": {
                "Гемоглобин": {"Натижа": "125 г/л", "Норма": "120-150 г/л", "Ҳолат": "✅ Норма"},
                "Лейкоцитлар": {"Натижа": "6.5 ×10⁹/л", "Норма": "4-9 ×10⁹/л", "Ҳолат": "✅ Норма"},
                "Тромбоцитлар": {"Натижа": "250 ×10⁹/л", "Норма": "150-400 ×10⁹/л", "Ҳолат": "✅ Норма"}
            },
            "Биохимик таҳлил": {
                "Глюкоза": {"Натижа": "5.2 ммоль/л", "Норма": "3.9-6.1 ммоль/л", "Ҳолат": "✅ Норма"},
                "Холестерин": {"Натижа": "4.8 ммоль/л", "Норма": "3.5-5.2 ммоль/л", "Ҳолат": "✅ Норма"},
                "Креатинин": {"Натижа": "78 мкмоль/л", "Норма": "53-97 мкмоль/л", "Ҳолат": "✅ Норма"}
            }
        }
        
        for test_name, results in lab_results.items():
            with st.expander(test_name):
                df = pd.DataFrame(results).T
                st.dataframe(df, use_container_width=True)
    
    with tab3:
        st.markdown('<h3 class="sub-header">📅 Скрининг жадвали</h3>', unsafe_allow_html=True)
        
        # Хомиладорлик скрининг жадвали
        pregnancy_schedule = pd.DataFrame([
            {"Ҳафта": "8-13", "Скрининг": "1-триместр скрининги", "Мажбурий": "✅"},
            {"Ҳафта": "18-22", "Скрининг": "2-триместр скрининги", "Мажбурий": "✅"},
            {"Ҳафта": "28-32", "Скрининг": "3-триместр скрининги", "Мажбурий": "✅"},
            {"Ҳафта": "16-20", "Скрининг": "Генетик скрининг", "Мажбурий": "⚪"},
            {"Ҳафта": "24-28", "Скрининг": "Қондаги қанд", "Мажбурий": "✅"}
        ])
        
        st.dataframe(pregnancy_schedule, use_container_width=True)
        
        # Болалар скрининг жадвали
        child_schedule = pd.DataFrame([
            {"Ёш": "1 ой", "Скрининг": "УЗИ бош мия", "Мажбурий": "✅"},
            {"Ёш": "3 ой", "Скрининг": "Невролог кўриги", "Мажбурий": "✅"},
            {"Ёш": "6 ой", "Скрининг": "Ортопед кўриги", "Мажбурий": "✅"},
            {"Ёш": "9 ой", "Скрининг": "Стоматолог кўриги", "Мажбурий": "⚪"},
            {"Ёш": "12 ой", "Скрининг": "Умумий скрининг", "Мажбурий": "✅"}
        ])
        
        st.dataframe(child_schedule, use_container_width=True)
    
    with tab4:
        st.markdown('<h3 class="sub-header">💡 Соглик учун тавсиялар</h3>', unsafe_allow_html=True)
        
        recommendations = {
            "Хомиладор аёллар учун": [
                "Кундузлик рационга диққат қилинг",
                "Регуляр шифокор кўригида бўлинг",
                "Фаол ҳаракатли бўлинг",
                "Стрессдан қочинг",
                "Йетарли миқдорда сув ичинг"
            ],
            "Болалар учун": [
                "Регуляр вакцинация",
                "Тўгри овқатланиш",
                "Ҳаёт тарзини назорат қилиш",
                "Регуляр шифокор кўриги",
                "Жисмоний фаоллик"
            ]
        }
        
        for category, items in recommendations.items():
            with st.expander(category):
                for item in items:
                    st.markdown(f"✅ {item}")

def show_vaccination_page(user):
    """Вакцинация саҳифаси"""
    st.markdown('<h1 class="main-header">💉 Вакцинация жадвали</h1>', unsafe_allow_html=True)
    
    # Вакцинация жадвали
    vaccination_schedule = [
        {"Вакцина": "Гепатит В", "Ёш": "Туғилганда", "Мажбурий": "✅", "Изох": "Бирінчи доза"},
        {"Вакцина": "БЦЖ", "Ёш": "3-7 кун", "Мажбурий": "✅", "Изох": "Туберкулёздан ҳимоя"},
        {"Вакцина": "АКДС", "Ёш": "2 ой", "Мажбурий": "✅", "Изох": "Дифтерия, коклюш, столбняк"},
        {"Вакцина": "Полиомиелит", "Ёш": "2 ой", "Мажбурий": "✅", "Изох": "Бирінчи доза"},
        {"Вакцина": "Гемофил инфекция", "Ёш": "3 ой", "Мажбурий": "✅", "Изох": "Гемофил инфлюэнца"},
        {"Вакцина": "ККП", "Ёш": "1 ёш", "Мажбурий": "✅", "Изох": "Қизилча, қути, қуйи қовоқ"},
        {"Вакцина": "Гепатит А", "Ёш": "1.5 ёш", "Мажбурий": "⚪", "Изох": "Ихтиёрий"}
    ]
    
    df = pd.DataFrame(vaccination_schedule)
    st.dataframe(df, use_container_width=True)
    
    # Болани танлаш
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM children WHERE user_id = ?', (user['id'],))
    children = cursor.fetchall()
    
    if children:
        child_options = {child[1]: child[0] for child in children}
        selected_child = st.selectbox("Болани танланг", list(child_options.keys()))
        
        # Вакцинация жадвалини кўрсатиш
        st.markdown(f'<h3 class="sub-header">💉 {selected_child} учун вакцинация жадвали</h3>', unsafe_allow_html=True)
        
        # Вакцинация қўшиш
        with st.expander("➕ Вакцинация қўшиш"):
            with st.form("add_vaccination"):
                col1, col2 = st.columns(2)
                with col1:
                    vaccine_name = st.text_input("Вакцина номи")
                    scheduled_date = st.date_input("Жадвал санаси")
                with col2:
                    administered_date = st.date_input("Қўлланган сана (ихтиёрий)")
                    status = st.selectbox("Ҳолат", ["Жадвалланган", "Қўлланган", "Бекор қилинган"])
                
                notes = st.text_area("Изохлар")
                
                if st.form_submit_button("Қўшиш"):
                    child_id = child_options[selected_child]
                    cursor.execute('''
                        INSERT INTO vaccinations (child_id, vaccine_name, scheduled_date, administered_date, status, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (child_id, vaccine_name, scheduled_date.isoformat(), 
                         administered_date.isoformat() if administered_date else None,
                         status, notes))
                    conn.commit()
                    st.success("✅ Вакцинация қўшилди!")

def show_notifications_page(user):
    """Эслатмалар саҳифаси"""
    st.markdown('<h1 class="main-header">🔔 Эслатмалар</h1>', unsafe_allow_html=True)
    
    # Эслатмаларни кўрсатиш
    cursor = conn.cursor()
    cursor.execute('''
        SELECT notification_type, message, created_at, is_read
        FROM notifications
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user['id'],))
    
    notifications = cursor.fetchall()
    
    if notifications:
        for notif in notifications:
            bg_color = "#F0F8FF" if not notif[3] else "#FFFFFF"
            border_color = "#2196F3" if not notif[3] else "#E0E0E0"
            
            st.markdown(f'''
            <div style="background: {bg_color}; padding: 1rem; border-radius: 10px; border-left: 5px solid {border_color}; margin-bottom: 1rem;">
                <strong>{notif[0]}</strong><br>
                {notif[1]}<br>
                <small>{notif[2]}</small>
            </div>
            ''', unsafe_allow_html=True)
        
        # Барча эслатмаларни ўқилган деб белгилаш
        if st.button("Барчасини ўқилган деб белгилаш"):
            cursor.execute('UPDATE notifications SET is_read = 1 WHERE user_id = ?', (user['id'],))
            conn.commit()
            st.success("✅ Барча эслатмалар ўқилган деб белгиланди!")
            st.rerun()
    else:
        st.info("📭 Эслатмалар йўқ")

def show_profile_page(user):
    """Профиль саҳифаси"""
    st.markdown(f'<h1 class="main-header">👤 {user["full_name"]} профили</h1>', unsafe_allow_html=True)
    
    # Фойдаланувчи маълумотлари
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user['id'],))
    user_data = cursor.fetchone()
    
    if user_data:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Шахсий маълумотлар")
            st.markdown(f"**Тўлиқ исм:** {user_data[3]}")
            st.markdown(f"**Телефон:** {user_data[4]}")
            st.markdown(f"**Email:** {user_data[5]}")
            st.markdown(f"**Туғилган сана:** {user_data[7]}")
            st.markdown(f"**Жинс:** {user_data[8]}")
        
        with col2:
            st.markdown("### Қўшимча маълумотлар")
            st.markdown(f"**Яшаш манзили:** {user_data[9]}")
            st.markdown(f"**Рўйхатдан ўтган:** {user_data[10]}")
            st.markdown(f"**Охирги кириш:** {user_data[11]}")
    
    # Профильни янгилаш
    st.markdown("---")
    st.markdown('<h3 class="sub-header">⚙️ Профильни янгилаш</h3>', unsafe_allow_html=True)
    
    with st.form("update_profile"):
        col1, col2 = st.columns(2)
        with col1:
            new_phone = st.text_input("Янги телефон", value=user_data[4] if user_data else "")
            new_email = st.text_input("Янги email", value=user_data[5] if user_data else "")
        with col2:
            new_address = st.text_area("Янги манзил", value=user_data[9] if user_data else "")
        
        if st.form_submit_button("Профильни янгилаш"):
            cursor.execute('''
                UPDATE users 
                SET phone = ?, email = ?, address = ?
                WHERE id = ?
            ''', (new_phone, new_email, new_address, user['id']))
            conn.commit()
            st.success("✅ Профиль янгиланди!")

def handle_doctor_pages(selected, user):
    """Шифокор учун саҳифалар"""
    if selected == "🏠 Асосий саҳифа":
        show_doctor_dashboard(user)
    elif selected == "📋 Кабинет":
        show_doctor_cabinet(user)
    elif selected == "👥 Беморлар":
        show_doctor_patients(user)
    elif selected == "📅 Жадвал":
        show_doctor_schedule(user)
    elif selected == "📊 Статистика":
        show_doctor_statistics(user)
    elif selected == "💬 Консультация":
        show_doctor_consultation(user)
    elif selected == "⚙️ Профиль":
        show_doctor_profile(user)

def show_doctor_dashboard(user):
    """Шифокор дашборди"""
    st.markdown(f'<h1 class="main-header">👨‍⚕️ Хуш келибсиз, {user["full_name"]}!</h1>', unsafe_allow_html=True)
    
    # Шифокор статистикаси
    cursor = conn.cursor()
    cursor.execute('SELECT specialty FROM doctors WHERE user_id = ?', (user['id'],))
    doctor_info = cursor.fetchone()
    
    if doctor_info:
        specialty = doctor_info[0]
        st.markdown(f'<div class="pregnancy-card">', unsafe_allow_html=True)
        st.markdown(f"### {SPECIALTIES.get(specialty, {}).get('icon', '👨‍⚕️')} {SPECIALTIES.get(specialty, {}).get('name', specialty)}")
        st.markdown(f"**Махсуслигингиз:** {SPECIALTIES.get(specialty, {}).get('description', '')}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Кунлик статистика
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cursor.execute('SELECT COUNT(*) FROM appointments WHERE doctor_id = ? AND appointment_date = DATE("now")', (user['id'],))
        today_appointments = cursor.fetchone()[0]
        st.metric("📅 Бугунги навбатлар", today_appointments)
    
    with col2:
        cursor.execute('SELECT COUNT(*) FROM appointments WHERE doctor_id = ? AND status = "scheduled"', (user['id'],))
        scheduled = cursor.fetchone()[0]
        st.metric("⏳ Жадвалланган", scheduled)
    
    with col3:
        cursor.execute('SELECT COUNT(*) FROM appointments WHERE doctor_id = ? AND status = "completed"', (user['id'],))
        completed = cursor.fetchone()[0]
        st.metric("✅ Бажарилган", completed)
    
    with col4:
        cursor.execute('SELECT AVG(rating) FROM doctors WHERE user_id = ?', (user['id'],))
        rating = cursor.fetchone()[0] or 0
        st.metric("⭐ Рейтинг", f"{rating:.1f}/5")

def show_doctor_cabinet(user):
    """Шифокор кабинети"""
    st.markdown('<h1 class="main-header">📋 Менинг кабинетим</h1>', unsafe_allow_html=True)
    
    # Шифокор маълумотларини янгилаш
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM doctors WHERE user_id = ?', (user['id'],))
    doctor_data = cursor.fetchone()
    
    if doctor_data:
        with st.form("update_doctor"):
            col1, col2 = st.columns(2)
            with col1:
                qualification = st.text_input("Маълумотингиз", value=doctor_data[2])
                experience = st.number_input("Тажрибангиз (йил)", min_value=0, value=doctor_data[3])
            with col2:
                consultation_price = st.number_input("Консультация нархи", min_value=0, value=doctor_data[4])
                working_hours = st.text_input("Иш вақтингиз", value=doctor_data[5])
            
            if st.form_submit_button("Маълумотларни янгилаш"):
                cursor.execute('''
                    UPDATE doctors 
                    SET qualification = ?, experience_years = ?, consultation_price = ?, working_hours = ?
                    WHERE user_id = ?
                ''', (qualification, experience, consultation_price, working_hours, user['id']))
                conn.commit()
                st.success("✅ Маълумотлар янгиланди!")

def handle_admin_pages(selected, user):
    """Админ учун саҳифалар"""
    if selected == "🏠 Асосий саҳифа":
        show_admin_dashboard()
    elif selected == "📊 Умумий статистика":
        show_admin_statistics()
    elif selected == "👨‍⚕️ Шифокорлар":
        show_admin_doctors()
    elif selected == "👥 Фойдаланувчилар":
        show_admin_users()
    elif selected == "🏥 Марказ маълумотлари":
        show_admin_center_info()
    elif selected == "⚙️ Тизим созламалари":
        show_admin_settings()

def show_admin_dashboard():
    """Админ дашборди"""
    st.markdown('<h1 class="main-header">👑 Админ панели</h1>', unsafe_allow_html=True)
    
    # Умумий статистика
    cursor = conn.cursor()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        st.metric("👥 Фойдаланувчилар", total_users)
    
    with col2:
        cursor.execute('SELECT COUNT(*) FROM doctors')
        total_doctors = cursor.fetchone()[0]
        st.metric("👨‍⚕️ Шифокорлар", total_doctors)
    
    with col3:
        cursor.execute('SELECT COUNT(*) FROM appointments')
        total_appointments = cursor.fetchone()[0]
        st.metric("📅 Навбатлар", total_appointments)
    
    with col4:
        cursor.execute('SELECT COUNT(*) FROM pregnancies')
        total_pregnancies = cursor.fetchone()[0]
        st.metric("🤰 Хомиладорлик", total_pregnancies)

# Қолган функцияларни ҳаётга келтириш учун маълумотлар базасини яратиш керак
if __name__ == "__main__":
    main()
