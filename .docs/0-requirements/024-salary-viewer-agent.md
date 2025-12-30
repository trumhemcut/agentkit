# Tạo 1 langraph agent với tên là `salary-viewer-agent`

Em này sẽ làm một số tác vụ vui vẻ và hài hước sau:

## Context:
- User sẽ hỏi agent kiểu anh là **Tổng tài** đây, cho hỏi lương của anh kỳ này tăng được bao nhiêu.
- Agent sẽ trả lời đây là thông tin bảo mật, để bắt đầu xác nhận bạn chính là tổng tài, và đã gửi OTP qua thiết bị của tổng tài, y/c tổng tài nhập số vào form OTP.  
  Agent dùng OTP input tool để hiển thị ở frontend để user nhập.
- Sau khi user nhập xong (bất kỳ số nào), nhấn verify, thì Agent sẽ tiếp tục luồng trả lời.  
  Agent sẽ trả lời là lương của anh là 5tr và được tăng 5% là được 5.25tr nhé :D

## Objective:
- Agent architecture với tool loop?

## Implement:
- Cả backend và frontend tương ứng
