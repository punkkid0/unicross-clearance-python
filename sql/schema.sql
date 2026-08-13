-- Payment Verification and Clearance System (thesis Ch 3.4.3)

CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(120) NOT NULL,
  role VARCHAR(30) NOT NULL DEFAULT 'student',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS students (
  id SERIAL PRIMARY KEY,
  user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  matric_no VARCHAR(40) UNIQUE,
  faculty VARCHAR(80) DEFAULT 'Faculty of Computing',
  department VARCHAR(80) DEFAULT 'Computer Science',
  is_indigene BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS departments (
  id SERIAL PRIMARY KEY,
  code VARCHAR(40) UNIQUE NOT NULL,
  name VARCHAR(80) NOT NULL
);

CREATE TABLE IF NOT EXISTS school_fee_payments (
  id SERIAL PRIMARY KEY,
  rrr VARCHAR(80) UNIQUE NOT NULL,
  student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  amount NUMERIC(12,2) NOT NULL,
  payment_method VARCHAR(40) DEFAULT 'paystack',
  status VARCHAR(20) NOT NULL DEFAULT 'successful',
  gateway_ref VARCHAR(80),
  notes TEXT,
  recorded_by INTEGER REFERENCES users(id),
  payment_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payments (
  id SERIAL PRIMARY KEY,
  student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  amount NUMERIC(12,2) NOT NULL,
  payment_type VARCHAR(40) DEFAULT 'school_fee',
  status VARCHAR(20) NOT NULL DEFAULT 'completed',
  rrr VARCHAR(80),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
  id SERIAL PRIMARY KEY,
  payment_id INTEGER REFERENCES payments(id) ON DELETE SET NULL,
  student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  provider VARCHAR(40) NOT NULL,
  reference VARCHAR(80) UNIQUE NOT NULL,
  amount NUMERIC(12,2) NOT NULL,
  status VARCHAR(20) NOT NULL,
  raw_payload TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clearance_requests (
  id SERIAL PRIMARY KEY,
  student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  receipt_path VARCHAR(255),
  receipt_hash VARCHAR(64),
  declared_amount NUMERIC(12,2) NOT NULL,
  payment_reference VARCHAR(80) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  auto_score INTEGER,
  auto_decision VARCHAR(20),
  auto_reasons TEXT,
  certificate_path VARCHAR(255),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clearance_units (
  id SERIAL PRIMARY KEY,
  request_id INTEGER NOT NULL REFERENCES clearance_requests(id) ON DELETE CASCADE,
  unit_code VARCHAR(40) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  reason TEXT,
  reviewed_by INTEGER REFERENCES users(id),
  reviewed_at TIMESTAMP,
  UNIQUE (request_id, unit_code)
);

CREATE TABLE IF NOT EXISTS audit_log (
  id SERIAL PRIMARY KEY,
  action VARCHAR(80) NOT NULL,
  user_id INTEGER REFERENCES users(id),
  details TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO departments (code, name) VALUES
  ('bursary', 'Bursary'),
  ('library', 'Library'),
  ('faculty', 'Faculty'),
  ('department', 'Department'),
  ('hostel', 'Hostel'),
  ('student_affairs', 'Student Affairs')
ON CONFLICT (code) DO NOTHING;
