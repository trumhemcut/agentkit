BUG
---

Khi ở chế độ canvas mode, user có thể chọn text trong artifact panel, sau đó nhấn nút "Chat with agent" để yêu cầu Agent thay đổi đoạn selected text.

## Expected behavior

- Agent sẽ generated một đoạn text mới
- Đoạn text mới này sẽ thay đúng đoạn selected text mà user đã chọn trước đó.
- Selected text vẫn được highlight cho đến khi nhận được các event liên quan đến artifact partial update.

## Bug description

- Luôn replace ở vị trí đầu tiên, không đúng vị trí của selected text.
- Và các lỗi tiềm năng khác.

## Tasks

- Hiểu sâu về cơ chế hoạt động hiện tại
- Hiểu lỗi
- Suggest fix để đạt dc expected behavior.