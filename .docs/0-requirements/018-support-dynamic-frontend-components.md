Trong ticket .docs/1-implementation-plans/017-support-a2ui-protocol-plan.md, chúng ta đã implement cơ chế a2ui để tạo front-end components từ Agent.

Tuy nhiên a2ui agent hiện tại đang chỉ generate ra một static check box.

Hãy xây dựng a2ai agent có thể generate động ra các front-end components dựa trên câu prompt của end user, không hỗ trợ static nữa.

Danh sách components hỗ trợ:

- Checkbox

Có thể mở rộng sau thành nhiều component khác.

Kiến trúc: Xem xét dùng tool để tạo component (tương lai sẽ dùng MCP)