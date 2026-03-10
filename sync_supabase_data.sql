-- Sync ข้อมูลจาก Local ไป Supabase
-- รันใน Supabase SQL Editor

-- 1. Insert users ที่ยังไม่มีใน Supabase
INSERT INTO users (username, email) 
SELECT 'test', 'test@gmail.com' 
WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'test@gmail.com');

INSERT INTO users (username, email) 
SELECT 'test1', 'test1@gmail.com' 
WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'test1@gmail.com');

INSERT INTO users (username, email) 
SELECT 'test2', 'test2@gmail.com' 
WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'test2@gmail.com');

INSERT INTO users (username, email) 
SELECT 'test3', 'test3@gmail.com' 
WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'test3@gmail.com');

INSERT INTO users (username, email) 
SELECT 'Mickey', 'Mickey@gmail.com' 
WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'Mickey@gmail.com');

-- 2. Insert products ที่ยังไม่มีใน Supabase
INSERT INTO products (name, price, size_category) 
SELECT 'Modern Office Chair', 299.99, 'M' 
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name = 'Modern Office Chair');

INSERT INTO products (name, price, size_category) 
SELECT 'Standing Desk', 599.99, 'L' 
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name = 'Standing Desk');

INSERT INTO products (name, price, size_category) 
SELECT 'Drawer Organizer', 49.99, 'S' 
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name = 'Drawer Organizer');

INSERT INTO products (name, price, size_category) 
SELECT 'Storage Cube Set', 89.99, 'M' 
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name = 'Storage Cube Set');

INSERT INTO products (name, price, size_category) 
SELECT 'Monitor Stand', 39.99, 'S' 
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name = 'Monitor Stand');

INSERT INTO products (name, price, size_category) 
SELECT 'Office Lamp', 79.99, 'M' 
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name = 'Office Lamp');

-- 3. ตรวจสอบผลลัพธ์
SELECT 'USERS AFTER SYNC:' as info, COUNT(*) as count FROM users
UNION ALL
SELECT 'PRODUCTS AFTER SYNC:', COUNT(*) FROM products;
