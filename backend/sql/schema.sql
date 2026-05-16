CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS companies (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    parent_company_id UUID,
    name VARCHAR(255) NOT NULL,
    website TEXT,
    logo_url TEXT,
    industry VARCHAR(100),
    mission TEXT,
    size_range VARCHAR(50),
    description TEXT,
    is_global BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_companies_parent
        FOREIGN KEY (parent_company_id)
        REFERENCES companies(id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_id UUID,
    title VARCHAR(255) NOT NULL,
    business_unit VARCHAR(100),
    department VARCHAR(100),
    job_level VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    work_mode VARCHAR(50),
    job_type VARCHAR(50),
    vacancy_count INTEGER DEFAULT 1,
    min_experience NUMERIC,
    target_majors JSONB,
    education_level_required VARCHAR(100),
    academic_support BOOLEAN DEFAULT FALSE,
    working_hours TEXT,
    salary_min NUMERIC,
    salary_max NUMERIC,
    salary_unit VARCHAR(20) DEFAULT 'Month',
    currency VARCHAR(10) DEFAULT 'VND',
    salary_description TEXT,
    performance_review_frequency VARCHAR(255),
    uses_ai_in_hiring BOOLEAN DEFAULT FALSE,
    is_equal_opportunity BOOLEAN DEFAULT TRUE,
    application_deadline DATE,
    description_raw TEXT,
    embedding VECTOR(768),
    contact_person_name VARCHAR(255),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    contact_phone_ext VARCHAR(10),
    application_url TEXT,
    hiring_process JSONB,
    training_details JSONB,
    extended_attributes JSONB,
    source_url TEXT UNIQUE,
    posted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_jobs_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS cvs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    title VARCHAR(150),
    raw_text TEXT,
    parsed_data JSONB,
    embedding VECTOR(768),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cvs_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS skills (
    id BIGSERIAL PRIMARY KEY,
    public_id UUID DEFAULT gen_random_uuid() UNIQUE,
    name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS job_skills (
    job_id UUID NOT NULL,
    skill_id BIGINT NOT NULL,
    priority_level SMALLINT DEFAULT 1,
    PRIMARY KEY (job_id, skill_id),
    CONSTRAINT fk_job_skills_job
        FOREIGN KEY (job_id)
        REFERENCES jobs(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_job_skills_skill
        FOREIGN KEY (skill_id)
        REFERENCES skills(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tools (
    id BIGSERIAL PRIMARY KEY,
    public_id UUID DEFAULT gen_random_uuid() UNIQUE,
    name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS job_tools (
    job_id UUID NOT NULL,
    tool_id BIGINT NOT NULL,
    priority_level SMALLINT DEFAULT 1,
    note TEXT,
    PRIMARY KEY (job_id, tool_id),
    CONSTRAINT fk_job_tools_job
        FOREIGN KEY (job_id)
        REFERENCES jobs(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_job_tools_tool
        FOREIGN KEY (tool_id)
        REFERENCES tools(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS languages (
    id BIGSERIAL PRIMARY KEY,
    public_id UUID DEFAULT gen_random_uuid() UNIQUE,
    name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS job_languages (
    job_id UUID NOT NULL,
    language_id BIGINT NOT NULL,
    proficiency_level VARCHAR(50),
    priority_level SMALLINT DEFAULT 1,
    PRIMARY KEY (job_id, language_id),
    CONSTRAINT fk_job_languages_job
        FOREIGN KEY (job_id)
        REFERENCES jobs(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_job_languages_language
        FOREIGN KEY (language_id)
        REFERENCES languages(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS benefits (
    id BIGSERIAL PRIMARY KEY,
    public_id UUID DEFAULT gen_random_uuid() UNIQUE,
    name VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS job_benefits (
    job_id UUID NOT NULL,
    benefit_id BIGINT NOT NULL,
    note TEXT,
    PRIMARY KEY (job_id, benefit_id),
    CONSTRAINT fk_job_benefits_job
        FOREIGN KEY (job_id)
        REFERENCES jobs(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_job_benefits_benefit
        FOREIGN KEY (benefit_id)
        REFERENCES benefits(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS mindsets (
    id BIGSERIAL PRIMARY KEY,
    public_id UUID DEFAULT gen_random_uuid() UNIQUE,
    name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS job_mindsets (
    job_id UUID NOT NULL,
    mindset_id BIGINT NOT NULL,
    PRIMARY KEY (job_id, mindset_id),
    CONSTRAINT fk_job_mindsets_job
        FOREIGN KEY (job_id)
        REFERENCES jobs(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_job_mindsets_mindset
        FOREIGN KEY (mindset_id)
        REFERENCES mindsets(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS job_locations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id UUID NOT NULL,
    building VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100) DEFAULT 'Vietnam',
    CONSTRAINT fk_job_locations_job
        FOREIGN KEY (job_id)
        REFERENCES jobs(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS job_raw_logs (
    id BIGSERIAL PRIMARY KEY,
    public_id UUID DEFAULT gen_random_uuid() UNIQUE,
    source_url TEXT,
    raw_content TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(20) DEFAULT 'pending',
    content_hash VARCHAR(64) UNIQUE
);

CREATE TABLE IF NOT EXISTS applications (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    cv_id BIGINT NOT NULL,
    job_id UUID NOT NULL,
    status VARCHAR(30) DEFAULT 'applied',
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_applications_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_applications_cv
        FOREIGN KEY (cv_id)
        REFERENCES cvs(id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_applications_job
        FOREIGN KEY (job_id)
        REFERENCES jobs(id)
        ON DELETE CASCADE,
    CONSTRAINT uq_applications_user_job
        UNIQUE (user_id, job_id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_embedding
ON jobs
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_jobs_deadline
ON jobs(application_deadline);

CREATE INDEX IF NOT EXISTS idx_jobs_status
ON jobs(status);

CREATE INDEX IF NOT EXISTS idx_jobs_company
ON jobs(company_id);

CREATE INDEX IF NOT EXISTS idx_jobs_posted_at
ON jobs(posted_at);

CREATE INDEX IF NOT EXISTS idx_jobs_created_at
ON jobs(created_at);

CREATE INDEX IF NOT EXISTS idx_cvs_user
ON cvs(user_id);

CREATE INDEX IF NOT EXISTS idx_cvs_parsed_data
ON cvs
USING gin (parsed_data);

CREATE INDEX IF NOT EXISTS idx_cvs_embedding
ON cvs
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_applications_user
ON applications(user_id);

CREATE INDEX IF NOT EXISTS idx_applications_cv
ON applications(cv_id);

CREATE INDEX IF NOT EXISTS idx_applications_job
ON applications(job_id);

CREATE INDEX IF NOT EXISTS idx_applications_status
ON applications(status);

CREATE INDEX IF NOT EXISTS idx_applications_applied_at
ON applications(applied_at);
