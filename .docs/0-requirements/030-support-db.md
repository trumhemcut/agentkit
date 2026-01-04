Backend hiện tại không có persistent layer, và frontend phải lưu trữ tạm thời bằng LocalStorage, vốn không phải là cách lưu trữ bền vững. Nên cần có một chiến lược lưu trữ bền vững.


## Mục tiêu

- Xây dựng một persistent architecture cho backend, hỗ trợ SQLite cho môi trường Dev, và postgres cho môi trường production.
- Frontend sẽ chỉ cache và offline friendly dùng zustand
- Chỉ cần Service Layer, không cần repository layer vì dự án khá gọn nhẹ. Tổ chức folder structure chuẩn theo standard.
- DB Migration versioned trong code base này
- Xây dựng các API bổ sung

## Nguyên tắc

- Giữ nguyên sự ổn định đang có, do đó ưu tiên không thay đổi các endpoint của backend
- Server là nguồn dữ liệu chính, frontend chỉ cache dữ liệu gần đây.
- Backend thay đổi trước, frontend thay đổi sau
- Test backend phải dùng pytest
- Chỉ hỗ trợ cho 2 model là Thread và Message trước, sẽ bổ sung các model khác sau.
- Phải dùng 100% async cho database
- Phải dùng Pydantic model

## Strategy

- Giai đoạn 1: frontend vẫn đọc trong localstorage như hiện tại, nhưng khi tạo message, sẽ call lên server để lưu trữ. (Chấp nhận duplicate, ticket sau sẽ xử lý tiếp). Khi fetch vẫn là ở frontend, không lấy dữ liệu từ API (mặc dù API đã có)
