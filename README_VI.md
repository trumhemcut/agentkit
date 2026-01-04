# AgentKit

**Trợ lý AI đa tác nhân hiện đại với LangGraph & AG-UI**

> 🌐 **Tiếng Việt** | [English](README.md)

Xây dựng ứng dụng AI mạnh mẽ với streaming thời gian thực, các thành phần UI tương tác, và điều phối đa tác nhân.

![Giao diện Chat AgentKit](chat_screen.png)

## ✨ Tính Năng

- **🎛️ Giao thức A2UI**: Agent tạo các thành phần UI tương tác (checkbox, form, button) trong chat
- **🎨 Chế độ Canvas**: Không gian làm việc toàn màn hình cho quy trình làm việc phức tạp
- **🔄 Điều phối Đa tác nhân**: Quản lý quy trình làm việc được hỗ trợ bởi LangGraph
- **⚡ Streaming Thời gian thực**: Giao thức AG-UI với phản hồi tức thì từ agent
- **💬 Quản lý Thread**: Lưu trữ các cuộc hội thoại với SQLite/PostgreSQL
- **🎯 Stack Hiện đại**: NextJS + Shadcn UI + FastAPI + LangGraph
- **🔌 Hỗ trợ Đa LLM**: Ollama, Azure OpenAI, Gemini và nhiều hơn
- **🛡️ Type-Safe**: TypeScript cho frontend, Python type hints cho backend
- **📊 Khả năng Quan sát**: Tích hợp LangFuse (tùy chọn)

## 🚀 Bắt Đầu

### Yêu Cầu

1. **Python 3.10+** và **Node.js 18+**
2. **Ollama** (hoặc cấu hình Azure OpenAI/Gemini):
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama pull qwen:7b
   ```

### Cài Đặt Backend

```bash
cd backend

# Tạo môi trường ảo
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Cài đặt dependencies
pip install -r requirements.txt

# Cấu hình môi trường (tùy chọn)
cp .env.example .env
# Chỉnh sửa .env cho Azure OpenAI, Gemini, hoặc PostgreSQL

# Chạy database migrations
python migrate.py

# Khởi động server
python main.py
```

✅ Backend chạy tại `http://localhost:8000`

### Cài Đặt Frontend

```bash
cd frontend

# Cài đặt dependencies
npm install

# Khởi động development server
npm run dev
```

✅ Frontend chạy tại `http://localhost:3000`

## 🗄️ Cấu Hình Database

**SQLite** (mặc định - không cần cấu hình):
```bash
DATABASE_URL=sqlite+aiosqlite:///./agentkit.db
```

**PostgreSQL** (cho production):
```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/agentkit
```

Chạy migrations sau khi thay đổi cấu hình:
```bash
python migrate.py
```

## 🔌 Cấu Hình LLM Provider

Chỉnh sửa file `.env` trong thư mục backend:

**Ollama** (mặc định):
```bash
DEFAULT_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen:7b
```

**Azure OpenAI**:
```bash
DEFAULT_PROVIDER=azure-openai
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-5-mini
```

**Gemini**:
```bash
DEFAULT_PROVIDER=gemini
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-2.5-flash
```

## 🏗️ Kiến Trúc

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Frontend  │◄────────│   AG-UI      │────────►│   Backend   │
│  (NextJS)   │  SSE    │   Protocol   │  HTTP   │  (FastAPI)  │
└─────────────┘         └──────────────┘         └─────────────┘
                                                          │
                                                          ▼
                                                   ┌─────────────┐
                                                   │  LangGraph  │
                                                   │   Agents    │
                                                   └─────────────┘
                                                          │
                                                          ▼
                                                   ┌─────────────┐
                                                   │  LLM Provider│
                                                   │  (Ollama/   │
                                                   │   Azure/    │
                                                   │   Gemini)   │
                                                   └─────────────┘
```

**Stack Backend**:
- FastAPI + LangGraph + Giao thức AG-UI
- SQLAlchemy (async) + SQLite/PostgreSQL
- Ollama/Azure OpenAI/Gemini

**Stack Frontend**:
- NextJS 14 + TypeScript + Shadcn UI
- AG-UI client cho event streams
- LocalStorage cho lưu trữ thread

## 📚 Tài Liệu

- [Kiến trúc Đa tác nhân](agents.md)
- [Cài đặt Database](backend/DATABASE.md)
- [Giao thức A2UI](backend/A2UI_README.md)
- [Chế độ Canvas](backend/CANVAS_README.md)
- [Kế hoạch Triển khai](.docs/1-implementation-plans/)
- [Cơ sở Kiến thức](.docs/2-knowledge-base/)

## 🛠️ Phát Triển

### Cấu Trúc Dự Án

```
agentkit/
├── backend/              # Backend FastAPI + LangGraph
│   ├── agents/          # Các agent implementations
│   ├── graphs/          # Quy trình LangGraph workflows
│   ├── api/             # REST endpoints
│   ├── database/        # SQLAlchemy models & migrations
│   ├── llm/             # Tích hợp LLM provider
│   ├── protocols/       # Triển khai giao thức AG-UI
│   └── main.py          # Entry point
├── frontend/            # Frontend NextJS
│   ├── app/            # App router pages
│   ├── components/     # React components
│   ├── services/       # API client
│   └── types/          # TypeScript types
└── .docs/              # Tài liệu
```

### API Endpoints

**Chat**: `POST /api/chat` - Stream phản hồi từ agent
**Threads**: `GET/POST /api/threads` - Quản lý cuộc hội thoại
**Messages**: `GET /api/threads/{id}/messages` - Lấy lịch sử thread
**Health**: `GET /health` - Trạng thái server

### Thêm Agent Mới

1. Tạo agent trong `backend/agents/`
2. Định nghĩa graph trong `backend/graphs/`
3. Đăng ký trong `backend/agents/agent_registry.py`
4. Cập nhật frontend components nếu cần

Xem [agents.md](agents.md) để biết hướng dẫn chi tiết.

## 🧪 Testing

**Backend**:
```bash
cd backend
pytest
```

**Frontend**:
```bash
cd frontend
npm test
```

## 📝 Giấy Phép

Giấy phép MIT - xem file LICENSE để biết chi tiết

## 🤝 Đóng Góp

Chào mừng mọi đóng góp! Vui lòng đọc hướng dẫn đóng góp trước.

## 🌟 Ủng Hộ Dự Án

Nếu bạn thấy AgentKit hữu ích, hãy cho chúng tôi một ngôi sao ⭐️
