# coding-team

**Ngôn ngữ:** [English](README.md) · **Tiếng Việt**

**Vibe-code, nhưng đừng xây mù.** Biến một ý tưởng kể bằng lời đơn giản thành
một thay đổi nhỏ, có thể xem lại, với phạm vi rõ ràng, bằng chứng hữu ích, và
quyết định cuối cùng vẫn là của bạn.

`coding-team` là một framework công khai, độc lập, phiên bản "lite". Nó cung
cấp các thẻ vai trò (role cards), công việc có giới hạn, quy tắc bằng chứng và
các cổng phê duyệt của con người, có thể dùng cho một dự án mà không cần truy
cập sản phẩm riêng hay dịch vụ lưu trữ.

[Cài đặt](docs/installation.md) · [Phạm vi dự án](docs/project-scope.md) · [Xem luồng công việc](docs/workflow.md) · [Các vai trò](docs/roles.md) · [Thử ví dụ](docs/examples/validation-scenario.md) · [Định nghĩa](docs/definitions.md) · [Skills](docs/skills.md) · [Addons](docs/addons.md) · [Model pool](docs/model-pool-mapping.md) · [Adapters](docs/adapters.md)

> Bản tiếng Việt này là bản dịch giúp bạn đọc nhanh. Bản tiếng Anh
> ([README.md](README.md)) là bản gốc chính thức; nếu có khác biệt, hãy theo
> bản tiếng Anh.

## Tại sao nó giúp ích

Viết code bằng AI thì nhanh. Phần khó là biết agent đang thay đổi gì, khi nào
công việc đủ nhỏ để xem lại, thực tế đã kiểm tra những gì, và liệu nó đã sẵn
sàng để ship.

coding-team làm cho những quyết định đó trở nên nhìn thấy được:

- **Sprint → Batch → Task** giữ một mục tiêu lớn đủ nhỏ để điều khiển.
- **Thẻ vai trò** làm rõ ai sở hữu và giới hạn ở đâu.
- **Tối đa hai task cùng lúc** giữ công việc song song đủ nhỏ để xem lại (tài
  liệu gọi giới hạn này là WIP ≤ 2).
- **Cổng con người** bảo vệ các hành động không thể hoàn tác.
- **Test Engineer → Gatekeeper** đặt bằng chứng độc lập lên trước khi chấp
  nhận cuối cùng.

Kết quả là một con đường nhìn thấy được từ yêu cầu đến thay đổi đã xem lại —
không phải lời hứa tự chủ nhiều hơn. Quyết định cuối cùng vẫn thuộc về bạn.

## Xem trong một phút

Bắt đầu bằng một yêu cầu. Làm rõ giới hạn của nó, chạy kiểm tra tập trung, và
tạm dừng để bạn quyết định khi bằng chứng đã sẵn sàng hoặc chưa đầy đủ.

![Hình minh họa: một mục tiêu bằng lời đơn giản đi qua công việc có giới hạn, bằng chứng và quyết định ship của con người.](docs/examples/assets/coding-team-lite-loop.svg)

Hình minh họa này cho thấy vòng lặp công khai: yêu cầu → công việc có giới
hạn → bằng chứng → quyết định của bạn. [Hướng dẫn giao tiếp](docs/communication-style.md)
giữ ngôn ngữ rõ ràng mà không thay đổi các ràng buộc hay yêu cầu bằng chứng.

## Điều phối multiagent hoạt động thế nào

Framework có một **Lead**. Lead kiểm tra mục tiêu trước, xem độ lớn của công
việc và cái gì sẽ chứng minh nó xong. Sau đó Lead giao các task nhỏ cho các vai
trò phù hợp.

<picture>
  <source media="(max-width: 640px)" srcset="docs/examples/assets/coding-team-multiagent-mobile.svg">
  <img src="docs/examples/assets/coding-team-multiagent.svg" alt="Luồng vai trò Coding Team: bạn đưa ra mục tiêu, Lead kiểm tra độ lớn và giao việc, các builder thực hiện, Test Engineer kiểm tra công việc quan trọng, Gatekeeper quyết định và bạn phê duyệt việc xuất bản.">
</picture>

- **Bạn đưa ra mục tiêu:** kết quả, các giới hạn và những quyết định phải giữ
  lại cho bạn.
- **Lead kiểm tra trước khi giao:** Task đã rõ chưa? Một vai trò có thể sở hữu
  nó không? Nó đủ nhỏ không? Kiểm tra nào sẽ chứng minh nó hoạt động? Nếu chưa,
  Lead hỏi nhóm hoặc chia nhỏ công việc thành Sprint → Batch → Task.
- **Nhóm tham gia là tùy chọn:** Product Manager, System Architect, Advisor,
  Contradictor hoặc một Domain Advisor chỉ tham gia khi câu trả lời của họ có
  thể làm thay đổi task.
- **Các builder thực hiện:** Backend Engineer và Frontend Builder chỉ có thể
  làm cùng lúc khi file và dependency của họ không xung đột.
- **Kiểm tra theo mức rủi ro:** các builder chạy kiểm tra tập trung. Với công
  việc quan trọng hoặc rủi ro cao, Test Engineer kiểm tra kết quả, sau đó
  Gatekeeper chấp nhận, yêu cầu sửa hoặc chặn nó.
- **Cổng con người:** commit, push/merge, release và xuất bản công khai đều
  cần một lời "yes" rõ ràng. Sự im lặng, tin nhắn "đã phê duyệt" của agent, hay
  một test chạy qua — đều không phải là phê duyệt.

### Lead ước lượng độ lớn task thế nào

Framework công khai dùng một kiểm tra theo quy tắc, không phải một bộ ước lượng
tự động. Trước khi giao việc, Lead kiểm tra xem có đúng một người sở hữu, một
mối quan tâm, một kết quả và một lần chạy ngắn với điểm dừng rõ ràng. Nếu công
việc tương tự đã hoàn thành có thời gian đo được, Lead có thể dùng nó làm ước
lượng. Nếu không, Lead nói rằng ước lượng chưa biết và chia nhỏ task hoặc chạy
một bước tìm hiểu nhỏ. Sau khi task xong, ghi lại thời gian thực tế, kết quả và
vướng mắc để lần ước lượng sau có bằng chứng.

## Mức độ QA

| Đường QA | Trạng thái công khai | Khi nào dùng |
|---|---|---|
| **Normal QA** | `AVAILABLE` | Mặc định cho các thay đổi nhỏ, có giới hạn |
| **Risky QA** | `EXPERIMENTAL` | Bắt buộc khi một trigger rủi ro cao đã có hiệu lực |

Risky QA đã được thực hiện và có sẵn để dùng thử cẩn thận. Hướng dẫn công khai
của nó vẫn đang được đánh giá. Nó không tự động chuyển về Normal QA khi một
trigger rủi ro xuất hiện, và nó không làm thay đổi các cổng phê duyệt của con
người. Xem [ví dụ cơ bản](docs/examples/risky-qa-trial.md).

## Một task có giới hạn đầu tiên

```text
Goal: thêm một tính năng nhỏ
Boundary: chỉ chạm vào các file đã chỉ định
Proof: chạy kiểm tra tập trung và báo cáo các đường dẫn đã thay đổi
Stop: tạm dừng để xem lại trước khi commit hoặc release
```

Cài đặt adapter cho host của bạn, bắt đầu với một task có giới hạn và điều
chỉnh framework cho dự án của bạn. Phần core vẫn trung lập với host; các bản
gắn kết Codex, Cursor và Cline nằm trong `adapters/`. Xem [Phạm vi dự án](docs/project-scope.md)
để biết giới hạn của bản phát hành công khai.

---

## Cài đặt bằng một lệnh

Với hầu hết mọi người, lệnh nhập thân thiện sẽ tự phát hiện host có sẵn và có
thể chuẩn bị một dự án đầu tiên (tùy chọn). Nhấn Enter để bỏ qua câu hỏi về dự
án:

```bash
./install.sh
```

Nó cũng có thể thêm một con trỏ đến dự án đầu tiên của bạn (tùy chọn):

```bash
./install.sh --project /path/to/your/project
```

Nếu thư mục đó không tồn tại hoặc không thể cập nhật, quá trình cài đặt vẫn
hoàn tất và lệnh sẽ giải thích cách chuẩn bị nó sau.

Dành cho CI, script hoặc thiết lập hoàn toàn tường minh, bỏ qua mọi câu hỏi:

```bash
./install.sh --platform codex --no-questionnaire
```

## Bắt đầu một task từ chat của bạn

Framework đóng gói một **process pack** nhỏ gồm các skill. Skill đầu vào công
khai là `plain-task-start`: nó biến một yêu cầu bằng lời đơn giản thành một thẻ
bốn dòng — **Goal (Mục tiêu), Scope (Phạm vi), Proof (Bằng chứng), Stop (Dừng)**
— trước khi bất kỳ file nào bị thay đổi.

Nó nằm sẵn trong repository tại `skills/process/plain-task-start/` và được nạp
từ `CODING_TEAM_ROOT` của bạn, nên không cần cài thêm gì. Chỉ cho agent đến
đường dẫn của skill:

```text
Dùng skills/process/plain-task-start/ để chuyển yêu cầu này thành một task card:
Thêm công tắc dark-mode vào trang cài đặt
```

Agent trả lời bằng thẻ trong cùng cuộc chat, rồi dừng để bạn xem lại.

```text
Goal: thêm công tắc dark-mode vào trang cài đặt
Scope: chỉ src/settings/*
Proof: công tắc đổi màu xem trước trên /settings
Stop: sau khi kiểm tra xem trước, trước khi commit
```

Thẻ chỉ là dữ liệu đầu vào để lập kế hoạch — nó không thực hiện, không phê
duyệt và không thay thế việc xem lại của con người. Xem [Skills](docs/skills.md)
cho toàn bộ pack.

## Cài đặt nâng cao và phần mở rộng tường minh

Bộ cài chuẩn liên kết adapter đã chọn và hỗ trợ QA có điều kiện:

```bash
./scripts/install-coding-team.sh --platform codex
```

Chỉ có một đường dẫn cài đặt công khai. Model map và addon là các phần mở rộng
tường minh; xem [Cài đặt](docs/installation.md).

## Đây là cái gì

| Lớp | Nó làm gì |
|---|---|
| **Core** | Các vai trò, cổng và giới hạn hoạt động giống nhau trên Codex, Cursor hoặc Cline |
| **Skills** | Các pack engineering / quality / process / design đi kèm |
| **Adapters** | Gắn kết runtime cho Codex, Cursor, Cline |
| **Addons** | Hỗ trợ ra quyết định PM Lean — mặc định TẮT, chỉ khi được gọi rõ |

## Định tuyến hoạt động thế nào

Định tuyến quyết định model nào làm task nào. Nói đơn giản: sắp xếp task theo
loại, chọn năng lực mà loại đó cần, rồi dùng model mà host của bạn đã phê duyệt
cho năng lực đó. Luồng kỹ thuật dùng đúng các thuật ngữ của framework, được định
nghĩa bên dưới.

1. Lead sắp xếp mỗi task theo loại (framework gọi đây là **nature**: một tra cứu
   chỉ-đọc, một bản xây có giới hạn, một thay đổi rủi ro cao cần con người trước,
   v.v. — bộ đầy đủ là N0–N5 cộng thêm Consult và Docs; xem [Định nghĩa](docs/definitions.md)).
2. Loại đó chọn một **tier**: năng lực cần thiết, chẳng hạn tra cứu rẻ, builder
   ổn định hoặc đánh giá cao cấp. Một tier là ý định, không phải một model hay
   một nhà cung cấp.
3. Lead dùng định danh model (gọi là **slug**) mà host của bạn đã phê duyệt
   trong `model-pool.map.md` khi có tồn tại.
4. Thiếu slug → lấy cái tốt nhất tiếp theo; ghi lại `planned → actual` (không
   bao giờ chặn việc bắt đầu).

Một dòng: **Cao cấp ra quyết định. Tiết kiệm xây dựng. Rẻ cho tìm kiếm/tài liệu. Cổng con người cho rủi ro không thể hoàn tác.**

## Chuyên gia tên miền (`[Domain]-Advisor`)

Không có vai trò Talent-Care cố định. Khi cần đánh giá chuyên môn, Lead **hỏi
tên miền (domain)**, rồi ánh xạ:

| Hiển thị | Instance ID |
|---|---|
| Talent-Advisor | `talent-advisor` |
| Strategic-Advisor | `strategic-advisor` |
| Security-Advisor | `security-advisor` |
| … | `{domain}-advisor` |

Bản mẫu: `core/roles/domain-advisor.md` · Quy tắc: `core/domain-advisors.md` · Tài liệu vai trò: [docs/roles.md](docs/roles.md).

## Giấy phép

MIT cho các file của framework. Thông báo bên thứ ba: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
