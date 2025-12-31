Trong ticket .docs/1-implementation-plans/017-support-a2ui-protocol-plan.md và .docs/1-implementation-plans/018-support-dynamic-frontend-components-plan.md đã giúp agent có thể tạo các component và render về frontend app.

Các plan đã triển khai tại đây:
- .docs/1-implementation-plans/017-support-a2ui-protocol-plan.md
- .docs/1-implementation-plans/018-support-dynamic-frontend-components-plan.md

Tuy nhiên hiện tại đây là render một chiều từ agent đến frontend, mà chưa có cơ chế để tiếp nhận dữ liệu từ frontend gửi ngược lên agent. Ví dụ khi user nhấn vào một **Button* từ frontend, thì phải có cơ chế gửi message đó về agent để xử lý tiếp.


## Objective

- Bổ sung việc xử lý dữ liệu chiều ngược lại từ frontend đến agent cho các component
- Tìm hiểu cách làm cho đúng protocol a2ui, use context7
- Hoặc tìm hiểu sâu ở đây https://a2ui.org/specification/v0.9-a2ui/#the-protocol-schemas
- Ngoài ra cũng có một số ví dụ tham khảo: https://github.com/google/A2UI/blob/main/samples/agent/adk/restaurant_finder/agent_executor.py
- Cập nhật cho a2ui-loop agent trước để test xem ổn ko, sẽ cập nhật các agent khác sau.