Salary reviewer agent đã implemtn luồng cơ bản theo requirement ở đây : .docs/0-requirements/024-salary-viewer-agent.md và plan ở đây .docs/1-implementation-plans/024-salary-viewer-agent-plan.md. Tuy nhiên, agent này chỉ mới stream opt về front-end mà không có nhận handler từ frontend về lại backend.

Sau đó, đã implement thêm tính năng nhận handling events từ front-end ở đây: .docs/1-implementation-plans/025-handling-events-for-components-plan.md

Hãy implement thêm tính năng nhận handling events từ frontend cho salary reviewer, khi user nhấn nút Verify thì backend hãy thông báo qua chat echo số otp mà user đã nhập mã otp tương ứng.