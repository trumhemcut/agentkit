Trang chat chính app/page.tsx cần hỗ trợ canvas mode. 

Khi canvas mode được enable / bật:
- Collapse sidebar
- ChatContainer thu hẹp lại chỉ còn 1/3 chiều rộng
- Artifact Pannel chiếm 2/3 chiều rộng

Khi render:
- Dựa vào loại event mà render.
- Đối với ChatContainer sẽ nhận stream như hiện tại với event là TEXT_MESSAGE_START, TEXT_MESSAGE_CONTENT và TEXT_MESSAGE_END. 
- Đối với Artifact Pannel sẽ nhận stream với event là EventType.CUSTOM, và các name là artifact_streaming_start, artifact_streaming, artifact_created, artifact_updated và sẽ hiển thị dữ liệu chunk by chunk in realtime.

Refactor:
- Chỉ có một chat thread duy nhất, không phân biệt chat thread hay canvas thread.
- Việc trả về artifact hay không là do agent quyết định, không phải frontend app quyết định.
