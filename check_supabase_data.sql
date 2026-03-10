-- ตรวจสอบข้อมูลใน Supabase
-- รันใน Supabase SQL Editor

-- 1. ดูว่ามีตารางอะไรบ้าง
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- 2. ดูข้อมูลในตาราง users
SELECT 'USERS TABLE:' as info, COUNT(*) as count FROM users
UNION ALL
SELECT 'Sample users:', '' as info, 0 as count
UNION ALL
SELECT 'ID | Username | Email', '' as info, 0 as count
UNION ALL
SELECT CONCAT(id::text, ' | ', username, ' | ', email) as info, 0 as count 
FROM users 
LIMIT 5;

-- 3. ดูข้อมูลในตาราง products
SELECT 'PRODUCTS TABLE:' as info, COUNT(*) as count FROM products
UNION ALL
SELECT 'Sample products:', '' as info, 0 as count
UNION ALL
SELECT 'ID | Name | Price | Size', '' as info, 0 as count
UNION ALL
SELECT CONCAT(id::text, ' | ', name, ' | ', price::text, ' | ', size_category) as info, 0 as count 
FROM products 
LIMIT 5;

-- 4. ตรวจสอบว่ามีข้อมูลจาก local database หรือไม่
-- (เปรียบเทียบกับที่เห็นใน local: 5 users, 7 products)
