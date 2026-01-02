This is just Frontend works.
----
## Đối với chế độ desktop, khung chat hiện tại chiếm 100% (a không chắc lắm, em kiểm tra lại) khoảng không gian dành cho chat container. Theo tham chiếu của Gemini tại đây .docs/0-requirements/images/gemini-chatting.png thì Chat history và Chat Input chỉ chiếm một phần của không gian chat container thôi (có thể khoảng 50%?). Chắc là để giúp mắt tập trung tốt hơn.

## Ngoài ra, Message trả về của Agent không có border luôn, để tạo cảm giác đọc 1 đoạn text từ Agent từ nhiên hơn. Gợi mở không gian thoải mái.

## Cải tạo khung chat (ChatInput)

- Chat Input nên lớn hơn để có thể chứa dấu "+" để upload files, Tools để "Create Image", hoặc 1 tool nào đó trong tương lai
- Nút Send nên canh phải ở cùng hàng với nút "+" và nút "Tools", kiểu giống Gemini

## Vị trí mặc định khi chưa chat

Tham khảo .docs/0-requirements/images/gemini-default.png ở đây, khi chưa có chat nào, thì khung chat nên ở giữa màn hình để chat dễ hơn.