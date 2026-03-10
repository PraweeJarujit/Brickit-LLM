-- Working Supabase Setup - Use only existing columns
-- Step 1: Check current table structure
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'products' AND table_schema = 'public'
ORDER BY ordinal_position;

-- Step 2: Check current table structure for users
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users' AND table_schema = 'public'
ORDER BY ordinal_position;

-- Step 3: Insert data using ONLY existing columns
-- Insert users (use only username and email)
INSERT INTO users (username, email) VALUES 
('test', 'test@gmail.com')
ON CONFLICT (email) DO NOTHING;

INSERT INTO users (username, email) VALUES 
('Mickey', 'Mickey@gmail.com')
ON CONFLICT (email) DO NOTHING;

-- Insert products (use only name, price, size_category)
INSERT INTO products (name, price, size_category) VALUES 
('Modern Office Chair', 299.99, 'M')
ON CONFLICT DO NOTHING;

INSERT INTO products (name, price, size_category) VALUES 
('Standing Desk', 599.99, 'L')
ON CONFLICT DO NOTHING;

INSERT INTO products (name, price, size_category) VALUES 
('Drawer Organizer', 49.99, 'S')
ON CONFLICT DO NOTHING;

-- Step 4: Verify data was inserted
SELECT 'Users:' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'Products:', COUNT(*) FROM products;
