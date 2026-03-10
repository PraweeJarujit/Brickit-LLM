-- Simple Supabase Setup - No conflicts
-- Run this step by step

-- Step 1: Check what tables exist
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

-- Step 2: Create users table (if not exists)
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Step 3: Create products table (if not exists)
CREATE TABLE IF NOT EXISTS products (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    size_category VARCHAR(10) NOT NULL,
    stock_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Step 4: Insert test data (only if tables are empty)
INSERT INTO users (username, email) 
SELECT 'test', 'test@gmail.com' 
WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'test@gmail.com');

INSERT INTO users (username, email) 
SELECT 'Mickey', 'Mickey@gmail.com' 
WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'Mickey@gmail.com');

INSERT INTO products (name, price, size_category, stock_count) 
SELECT 'Modern Office Chair', 299.99, 'M', 10 
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name = 'Modern Office Chair');

INSERT INTO products (name, price, size_category, stock_count) 
SELECT 'Standing Desk', 599.99, 'L', 5 
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name = 'Standing Desk');

INSERT INTO products (name, price, size_category, stock_count) 
SELECT 'Drawer Organizer', 49.99, 'S', 20 
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name = 'Drawer Organizer');

-- Step 5: Verify data
SELECT 'Users:' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'Products:', COUNT(*) FROM products;
