# Hướng Dẫn Chạy Benchmark Toàn Bộ 25 Datapoints VIC Trên IRIS

Tài liệu này hướng dẫn chi tiết cách chạy benchmark cho **25 datapoints** trong thư mục `z_data` bằng **Docker (khuyên dùng để cách ly môi trường hoàn toàn)** hoặc chạy trực tiếp trên Windows Native.

---

## 🐳 PHẦN 0: Chạy Benchmark Bằng Docker (Khuyên Dùng Nhất - Isolated Environment)

Sử dụng Docker giúp giải quyết triệt để vấn đề xung đột JDK (8, 11, 17) và thiếu các công cụ build đặc thù (Apache Ant, Gradle 6.8). Mọi thứ được gói gọn trong container Ubuntu 22.04 chuẩn của IRIS.

### Bước 1: Khởi động Docker Desktop
1. Nhấn phím `Windows`, tìm và mở ứng dụng **Docker Desktop**.
2. Đợi biểu tượng Docker ở thanh taskbar hiển thị màu xanh (**Engine running**).
3. Kiểm tra bằng lệnh trong PowerShell:
   ```powershell
   docker ps
   ```

### Bước 2: Build Image IRIS Benchmark
Tại thư mục gốc `d:\iris`, chạy lệnh:
```powershell
docker compose build
```
*(Lệnh này sẽ tự động build image `iris:latest` với đầy đủ JDK 8, 11, 17, Maven 3.2/3.5/3.9, Gradle 6.8/7.6/8.9, Apache Ant và CodeQL Linux bundle v2.23.2).*

### Bước 3: Khởi chạy Container
Chạy lệnh:
```powershell
docker compose run --rm iris
```
*Lưu ý:* Container đã được cấu hình tự động mount thư mục `z_data/`, `output/` và file `.env` từ máy Windows của bạn vào container. Bất kỳ kết quả hay database nào tạo ra đều được lưu ngay lập tức về máy Windows host.

### Bước 4: Chạy Benchmark trong Container
Khi bạn đã ở trong cửa sổ dòng lệnh Linux của container (`root@...:/iris#`), bạn dùng lệnh `python3`:
```bash
python3 scripts/run_vic_benchmark.py --llm gemini-3.5-flash-lite --run-id vic_eval --num-threads 2
```
*(Nếu muốn dùng lệnh `python` ngắn gọn, bạn chỉ cần gõ 1 lệnh tạo shortcut: `ln -s /usr/bin/python3 /usr/bin/python`)*.

* Hoặc chạy thử nghiệm trên 1 dự án cụ thể (ví dụ project `mpxj` dùng Ant):
  ```bash
  python3 scripts/run_vic_benchmark.py --filter mpxj --llm gemini-3.5-flash-lite --run-id vic_eval
  ```

---

## PHẦN 0.1: Chạy Native Trực Tiếp Trên Windows (Thay Thế Nếu Không Dùng Docker)

Để môi trường chạy sạch sẽ, không ảnh hưởng đến Python cài đặt trên máy:

1. **Tạo virtual environment**:
   ```powershell
   python -m venv .venv
   ```

2. **Kích hoạt virtual environment**:
   * Trên **PowerShell**:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
     *(Nếu gặp lỗi PowerShell ExecutionPolicy, chạy lệnh: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` rồi chạy lại lệnh trên)*.
   * Trên **CMD**:
     ```cmd
     .\.venv\Scripts\activate.bat
     ```

3. **Cài đặt thư viện từ `requirements.txt`**:
   ```bash
   pip install -r requirements.txt
   ```

---

## PHẦN 1: Cấu hình Gemini API Key

Bạn có thể cung cấp API Key bằng **1 trong 2 cách** sau:

### Cách 1: Dùng file `.env` (Khuyên dùng - Rất tiện lợi)
Tạo một file tên là `.env` ngay tại thư mục gốc của dự án (`d:\iris\.env`):
```env
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
*(Hệ thống đã được cấu hình để tự động nạp `GEMINI_API_KEY` hoặc `GOOGLE_API_KEY` từ file `.env` này)*.

### Cách 2: Set biến môi trường trong Terminal
Nếu không muốn tạo file `.env`, bạn có thể set trực tiếp trên cửa sổ dòng lệnh trước khi chạy:
* **Trên PowerShell**:
  ```powershell
  $env:GOOGLE_API_KEY = "AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  ```
* **Trên Command Prompt (CMD)**:
  ```cmd
  set GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  ```

> 💡 **Mẹo**: Nếu bạn đã chạy `pip install -r requirements.txt` ở **Phần 0**, thư viện Google Generative AI và Dotenv đã được cài đặt đầy đủ.

---

## PHẦN 2: Cách Chạy Benchmark Cho Toàn Bộ 25 Datapoint

Hiện tại có **2 phương pháp chạy**:

### Cách 1: Chạy TỰ ĐỘNG toàn bộ bằng 1 lệnh duy nhất (Khuyên dùng)
Tôi đã viết sẵn script [scripts/run_vic_benchmark.py](file:///d:/iris/scripts/run_vic_benchmark.py). Script này sẽ tự động đọc danh sách 25 dự án trong `z_data/project_info.csv`, lần lượt:
1. Tải mã nguồn (`fetch_one.py`).
2. Biên dịch & tạo CodeQL Database (`build_codeql_dbs.py`).
3. Bóc tách packages nội bộ (`get_packages_codeql.py`).
4. Chạy phân tích IRIS với Gemini (`src/iris.py`).
5. In bảng tổng kết trạng thái thành công/thất bại khi hoàn tất.

#### Lệnh thực hiện:
```bash
# Chạy toàn bộ 25 dự án với Gemini 3.5 Flash Lite:
python scripts/run_vic_benchmark.py --llm gemini-3.5-flash-lite --run-id vic_eval
```

#### Các tùy chọn hữu ích khác của script:
* **Chạy thử 1 hoặc vài dự án cụ thể**:
  ```bash
  python scripts/run_vic_benchmark.py --filter spark
  ```
* **Bỏ qua khâu fetch/build nếu DB đã tạo sẵn**:
  ```bash
  python scripts/run_vic_benchmark.py --skip-fetch --skip-build-db --llm gemini-3.5-flash-lite
  ```

---

### Cách 2: Chạy Thủ Công (Manual) Từng Dự Án (Từng Bước)

Phương pháp này dành cho khi bạn muốn kiểm tra kỹ lưỡng, debug hoặc chạy thử nghiệm trên từng dự án cụ thể. 

Quy trình chuẩn gồm **4 bước**:

#### Bước 1: Tải source và checkout commit VIC
Lệnh này sẽ clone repo từ GitHub và checkout đúng commit lỗi tương ứng (lưu vào `z_data/project-sources/<project_slug>`):
```powershell
python scripts/fetch_one.py <project_slug>
```
*Ví dụ*:
```powershell
python scripts/fetch_one.py perwendel__spark_CVE-2018-9159_2.7.1
```

#### Bước 2: Tạo CodeQL Database
Biên dịch dự án và dựng cơ sở dữ liệu CodeQL (lưu vào `z_data/codeql-dbs/<project_slug>`):
```powershell
python scripts/build_codeql_dbs.py --project <project_slug>
```
*Ví dụ*:
```powershell
python scripts/build_codeql_dbs.py --project perwendel__spark_CVE-2018-9159_2.7.1
```

#### Bước 3: Trích xuất internal package (Namespace nội bộ)
Đọc file build (`pom.xml` / `build.gradle`) để xác định các namespace package của dự án, lưu vào `z_data/package-names/<project_slug>.txt`:
```powershell
python scripts/get_packages_codeql.py <project_slug>
```
*Ví dụ*:
```powershell
python scripts/get_packages_codeql.py perwendel__spark_CVE-2018-9159_2.7.1
```

#### Bước 4: Chạy IRIS phân tích Taint Flow với model `gemini-3.5-flash-lite`
Cú pháp tổng quát:
```powershell
python src/iris.py <project_slug> --query <query_name> --llm gemini-3.5-flash-lite --run-id vic_eval
```

* **Ví dụ với dự án Spark (CWE-022 -> query `cwe-022wLLM`)**:
  ```powershell
  python src/iris.py perwendel__spark_CVE-2018-9159_2.7.1 --query cwe-022wLLM --llm gemini-3.5-flash-lite --run-id vic_eval
  ```

* **Ví dụ với dự án cron-utils (CWE-094 -> query `cwe-094wLLM`)**:
  ```powershell
  python src/iris.py jmrozanec__cron-utils_CVE-2021-41269_9.1.5 --query cwe-094wLLM --llm gemini-3.5-flash-lite --run-id vic_eval
  ```

#### 💡 Các cờ tùy chọn hữu ích khi chạy thủ công `src/iris.py`:
* `--llm gemini-3.5-flash-lite`: Chỉ định sử dụng model Gemini 3.5 Flash Lite (bạn cũng có thể đổi sang `gemini-2.5-flash-lite`, `gemini-1.5-flash`, hoặc `gemini-1.5-pro`).
* `--run-id <tên_chạy>`: Đặt tên thư mục chứa kết quả (mặc định nên để `vic_eval`).
* `--overwrite`: Cho phép chạy đè và tính toán lại nếu thư mục output đã tồn tại từ lần chạy trước.
* `--overwrite-llm-cache`: Bắt buộc gọi lại API Gemini, bỏ qua cache LLM đã lưu từ trước.
* `--num-threads <số_luồng>`: Số luồng song song gọi API (mặc định là `8`). Nếu bị Rate Limit của API, bạn có thể giảm xuống `--num-threads 2` hoặc `4`.

---

## PHẦN 3: Danh Sách 25 Datapoints & Query Tương Ứng

| STT | `project_slug` | CWE | Query Tương Ứng |
| :---: | :--- | :---: | :---: |
| 1 | `perwendel__spark_CVE-2018-9159_2.7.1` | CWE-022 | `cwe-022wLLM` |
| 2 | `perwendel__spark_CVE-2016-9177_2.5.1` | CWE-022 | `cwe-022wLLM` |
| 3 | `vert-x3__vertx-web_CVE-2018-12542_3.5.3.CR1` | CWE-022 | `cwe-022wLLM` |
| 4 | `joniles__mpxj_CVE-2020-35460_8.3.4` | CWE-022 | `cwe-022wLLM` |
| 5 | `apache__flink_CVE-2020-17519_1.11.2` | CWE-022 | `cwe-022wLLM` |
| 6 | `kubernetes-client__java_CVE-2020-8570_client-java-parent-9.0.1` | CWE-022 | `cwe-022wLLM` |
| 7 | `asf__karaf_CVE-2022-22932_4.3.5` | CWE-022 | `cwe-022wLLM` |
| 8 | `asf__james-project_CVE-2022-22931_3.6.0-1` | CWE-022 | `cwe-022wLLM` |
| 9 | `asf__james-project_CVE-2022-22931_3.6.0-2` | CWE-022 | `cwe-022wLLM` |
| 10 | `whitesource__curekit_CVE-2022-23082_1.1.3` | CWE-022 | `cwe-022wLLM` |
| 11 | `DSpace__DSpace_CVE-2022-31195_5.10` | CWE-022 | `cwe-022wLLM` |
| 12 | `Graylog2__graylog2-server_CVE-2023-41044_5.1.2` | CWE-022 | `cwe-022wLLM` |
| 13 | `yamcs__yamcs_CVE-2023-45278_5.8.6` | CWE-022 | `cwe-022wLLM` |
| 14 | `yamcs__yamcs_CVE-2023-45277_5.8.6` | CWE-022 | `cwe-022wLLM` |
| 15 | `jenkinsci__workflow-cps-global-lib-plugin_CVE-2022-25174_544.vff04fa68714d` | CWE-078 | `cwe-078wLLM` |
| 16 | `hibernate__hibernate-validator_CVE-2019-10219_6.0.17.Final` | CWE-079 | `cwe-079wLLM` |
| 17 | `nahsra__antisamy_CVE-2022-29577_1.6.6.1` | CWE-079 | `cwe-079wLLM` |
| 18 | `rhuss__jolokia_CVE-2018-1000129_1.4.0` | CWE-079 | `cwe-079wLLM` |
| 19 | `DSpace__DSpace_CVE-2022-31192_5.10` | CWE-079 | `cwe-079wLLM` |
| 20 | `xwiki__xwiki-commons_CVE-2023-31126_14.10.3` | CWE-079 | `cwe-079wLLM` |
| 21 | `xwiki__xwiki-commons_CVE-2023-36471_14.10.5` | CWE-079 | `cwe-079wLLM` |
| 22 | `xwiki__xwiki-rendering_CVE-2023-37908_14.10.3` | CWE-079 | `cwe-079wLLM` |
| 23 | `jmrozanec__cron-utils_CVE-2021-41269_9.1.5` | CWE-094 | `cwe-094wLLM` |
| 24 | `asf__commons-text_CVE-2022-42889_1.9` | CWE-094 | `cwe-094wLLM` |
| 25 | `codecentric__spring-boot-admin_CVE-2022-46166_2.6.9` | CWE-094 | `cwe-094wLLM` |

---

## PHẦN 4: Xem Kết Quả Sau Khi Chạy

Kết quả của từng dự án được lưu trong thư mục:
`output/<project_slug>/<run_id>/`

1. **File đánh giá chi tiết của từng dự án (JSON)**:
   * Đường dẫn: `output/<project_slug>/<run_id>/<query>-final/results.json`
   * Chứa các chỉ số:
     * `execution_time_seconds`: Tổng thời gian thực thi (giây).
     * `token_usage`:
       * `prompt_tokens`: Tổng số input tokens gửi lên LLM.
       * `candidate_tokens`: Tổng số output tokens mô hình sinh ra.
       * `total_tokens`: Tổng tokens tiêu thụ.
     * `statistics`: Thống kê số lượng API candidates, sources, sinks, taint propagators.
     * `posthoc_filter_result`:
       * `num_paths`: Tổng số luồng Taint Flow tìm thấy.
       * `recall_method`: `True` nếu luồng đi qua đúng hàm lỗi trong `fix_info.csv` (True Positive).
       * `recall_file`: `True` nếu luồng đi qua đúng file bị lỗi.

2. **File tổng kết toàn bộ Benchmark**:
   * Đường dẫn: `output/benchmark_summary_<run_id>.json`
   * Bảng tổng hợp toàn bộ 25 dự án: tổng số dự án thành công, tổng thời gian chạy, tổng token tiêu thụ và tỉ lệ phát hiện đúng Ground Truth.

3. **Xem trực quan trên giao diện Web (Visualizer)**:
   * Chạy server:
     ```bash
     python visualizer/server.py
     ```
   * Mở trình duyệt tại: `http://localhost:8000` để xem trực quan từng bước lan truyền của luồng dữ liệu từ Source -> Sink.
