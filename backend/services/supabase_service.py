from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

def init_supabase():
    """Initialize Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
    
    return create_client(url, key)

# ================== INITIALIZATION ==================
supabase = init_supabase()

# Create tables if they don't exist (call once during setup)
def setup_database():
    """Initialize database schema"""
    schema = """
    -- mothers table
    CREATE TABLE IF NOT EXISTS mothers (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL,
        phone TEXT UNIQUE,
        age INTEGER,
        gravida INTEGER,
        parity INTEGER,
        bmi FLOAT,
        location TEXT,
        preferred_language TEXT DEFAULT 'en',
        created_at TIMESTAMPTZ DEFAULT now()
    );

    -- visits table
    CREATE TABLE IF NOT EXISTS visits (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        mother_id UUID REFERENCES mothers(id) ON DELETE CASCADE,
        asha_id UUID,
        visit_date DATE,
        bp_sys INTEGER,
        bp_dia INTEGER,
        heart_rate INTEGER,
        sugar_level FLOAT,
        hemoglobin FLOAT,
        weight FLOAT,
        notes TEXT,
        created_at TIMESTAMPTZ DEFAULT now()
    );

    -- risk_assessments table
    CREATE TABLE IF NOT EXISTS risk_assessments (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        mother_id UUID REFERENCES mothers(id),
        risk_score FLOAT,
        risk_tags TEXT[],
        recommendation TEXT,
        status TEXT,
        created_at TIMESTAMPTZ DEFAULT now()
    );

    -- appointments table
    CREATE TABLE IF NOT EXISTS appointments (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        mother_id UUID REFERENCES mothers(id),
        facility TEXT,
        appointment_date TIMESTAMPTZ,
        assigned_asha UUID,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMPTZ DEFAULT now()
    );

    -- prescriptions table
    CREATE TABLE IF NOT EXISTS prescriptions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        mother_id UUID REFERENCES mothers(id),
        medication TEXT,
        dosage TEXT,
        start_date DATE,
        end_date DATE,
        schedule JSONB,
        created_at TIMESTAMPTZ DEFAULT now()
    );

    -- emergency_incidents table
    CREATE TABLE IF NOT EXISTS emergency_incidents (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        mother_id UUID REFERENCES mothers(id),
        symptoms TEXT[],
        severity TEXT,
        response JSONB,
        status TEXT,
        created_at TIMESTAMPTZ DEFAULT now()
    );

    -- asha_workers table
    CREATE TABLE IF NOT EXISTS asha_workers (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT,
        phone TEXT,
        assigned_area TEXT,
        created_at TIMESTAMPTZ DEFAULT now()
    );

    -- medication_reminders table
    CREATE TABLE IF NOT EXISTS medication_reminders (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        mother_id UUID REFERENCES mothers(id),
        reminders JSONB,
        status TEXT,
        created_at TIMESTAMPTZ DEFAULT now()
    );

    -- nutrition_plans table
    CREATE TABLE IF NOT EXISTS nutrition_plans (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        mother_id UUID REFERENCES mothers(id),
        plan TEXT,
        language TEXT,
        created_at TIMESTAMPTZ DEFAULT now()
    );
    """
    return schema