# BRICKKIT - AI Co-Creation Platform

แพลตฟอร์มออกแบบเฟอร์นิเจอร์ด้วย AI ที่รองรับภาษาไทยและอังกฤษ

## 🚀 Features

- **AI Chat System** - ออกแบบเฟอร์นิเจอร์ด้วยภาษาธรรมชาติ (รองรับไทยและอังกฤษ)
- **Chat History** - บันทึกประวัติการสนทนาอัตโนมัติ
- **Product Catalog** - จัดการสินค้าขนาด S, M, L
- **User Authentication** - ระบบสมาชิกและความปลอดภัย
- **Order Management** - ระบบคำสั่งซื้อสินค้า
- **Responsive Design** - รองรับทุกขนาดหน้าจอ
- **Dark Mode** - รองรับธีมสลับกลางวัน/กลางคืน

## 📋 Requirements

- Python 3.8+
- Ollama (สำหรับ AI model)
- Git

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd "LLM Mick"
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\Activate.ps1
# Mac/Linux
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install and Setup Ollama

#### Windows:
```bash
# Download and install Ollama from https://ollama.ai
# After installation, pull the model:
ollama pull gemma3:4b
```

#### Mac/Linux:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull gemma3:4b
```

### 5. Start Ollama Server
```bash
ollama serve
```

### 6. Initialize Database
```bash
python seed_database.py
```

### 7. Start Application
```bash
python start.py
```

หรือใช้คำสั่งดั้งเดิม:
```bash
uvicorn llm:app --reload --host localhost --port 8000
```

## 🌐 Access Points

เมื่อเริ่มต้นแอปพลิเคชัน คุณสามารถเข้าถึงได้ที่:

- **Main Website**: http://localhost:8000
- **AI Studio**: http://localhost:8000/ai-studio
- **Size Categories**:
  - http://localhost:8000/size-s (ขนาดเล็ก)
  - http://localhost:8000/size-m (ขนาดกลาง)  
  - http://localhost:8000/size-l (ขนาดใหญ่)
- **Login**: http://localhost:8000/login
- **Checkout**: http://localhost:8000/checkout
- **Orders**: http://localhost:8000/orders

## 🤖 AI Features

### Thai Language Support
- ตอบสนองภาษาไทยโดยอัตโนมัติ
- ใช้คำลงท้ายที่สุภาพ (ครับ/ค่ะ)
- แนะนำสินค้าเป็นภาษาไทย

### Quick Prompts (ภาษาไทย)
- "เพิ่มชั้นวางของ" - เพิ่มชั้นวาง
- "ทำให้สูงขึ้น" - ปรับความสูง
- "เพิ่มสีเขียว" - เปลี่ยนสี

### Quick Prompts (English)
- "Add shelf" - เพิ่มชั้นวาง
- "Make taller" - ปรับความสูง
- "More green" - เปลี่ยนสี

## 📁 Project Structure

```
LLM Mick/
├── llm.py              # Main FastAPI application
├── models.py           # Database models
├── database.py         # Database configuration
├── config.py           # Application settings
├── seed_database.py    # Database seeding script
├── start.py           # Startup script
├── requirements.txt    # Python dependencies
├── .env               # Environment variables
├── ai-studio.html     # AI chat interface
├── index.html         # Main website
├── size-*.html        # Size category pages
├── login.html         # Login page
├── checkout.html      # Checkout page
├── orders.html        # Orders page
└── shared.js          # Shared JavaScript
```

## 🔧 Configuration

### Environment Variables (.env)
```env
DATABASE_URL=sqlite:///./brickkit.db
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
API_HOST=localhost
API_PORT=8000
DEBUG=True
SECRET_KEY=your-secret-key-here
```

## 🛡️ Security Features

- Password hashing with bcrypt
- User authentication system
- SQL injection protection (SQLAlchemy ORM)
- CORS configuration
- Input validation (Pydantic)

## 📊 Database Schema

- **Users** - ข้อมูลสมาชิก
- **Products** - ข้อมูลสินค้า (S, M, L)
- **ChatMessages** - ประวัติการแชท
- **Orders** - คำสั่งซื้อ
- **OrderItems** - รายการสินค้าในคำสั่งซื้อ

## 🎯 API Endpoints

### Authentication
- `POST /api/auth/register` - สมัครสมาชิก
- `POST /api/auth/login` - เข้าสู่ระบบ

### Chat
- `POST /api/chat` - สนทนากับ AI
- `GET /api/chat/history` - ดูประวัติการแชท
- `POST /api/chat/save` - บันทึกข้อความ

### Products
- `GET /api/products` - ดูสินค้าทั้งหมด
- `GET /api/products/{size}` - ดูสินค้าตามขนาด
- `POST /api/products` - เพิ่มสินค้าใหม่

## 🔍 Troubleshooting

### Ollama Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve

# Reinstall model
ollama pull gemma3:4b
```

### Database Issues
```bash
# Reset database
rm brickkit.db
python seed_database.py
```

### Port Conflicts
```bash
# Change port in .env
API_PORT=8001

# Or kill existing process
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

## 🚀 Deployment

### Production Setup
1. Set `DEBUG=False` in `.env`
2. Change `SECRET_KEY` to secure value
3. Use production database (PostgreSQL/MySQL)
4. Set up reverse proxy (nginx)
5. Configure SSL certificates

### Docker Deployment
```dockerfile
# Dockerfile example coming soon
```

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

หากพบปัญหา:
1. ตรวจสอบ requirements ให้ครบถ้วน
2. ตรวจสอบว่า Ollama ทำงานอยู่
3. ลอง restart แอปพลิเคชัน
4. ตรวจสอบ log สำหรับข้อผิดพลาด

---

**BRICKKIT** - ออกแบบเฟอร์นิเจอร์ด้วย AI รองรับภาษาไทย 🇹🇭
