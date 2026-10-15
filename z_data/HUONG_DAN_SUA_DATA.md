# Hướng Dẫn Sửa Dữ Liệu Benchmark Cho IRIS (`z_data`)

Tài liệu tóm tắt ngắn gọn các điểm cần điều chỉnh trong thư mục `d:\iris\z_data`.

---

## 1. Tổng quan tình trạng 3 file

| File | Tình trạng | Cần làm gì? |
| :--- | :---: | :--- |
| **`build_info.csv`** | ✅ **Chuẩn 100%** | **Giữ nguyên**, không cần sửa gì thêm. |
| **`project_info.csv`** | ❌ **Cần sửa Header** | Đổi sang chuẩn 12 cột để script không bị lỗi `IndexError` và `KeyError`. |
| **`fix_info.csv`** | ⚠️ **Cần sửa Data** | Đổi **12 dòng** đang trỏ vào `src/test` sang method thực tế trong `src/main`. |

---

## 2. Chi tiết sửa `project_info.csv`

### Vấn đề:
Code của IRIS (`scripts/fetch_one.py` và `src/iris.py`) đọc file theo **thứ tự cột cố định (index)** và tìm cột `fix_commit_ids`. Header 5 cột hiện tại sẽ làm crash code.

### Cách sửa:
Đổi dòng header đầu tiên thành chuẩn 12 cột:
```csv
id,project_slug,cve_id,cwe_id,cwe_name,github_username,github_repository_name,github_tag,github_url,advisory_id,buggy_commit_id,fix_commit_ids
```

### Quy tắc điền dữ liệu (Các cột chính):
* Cột 1 (`id`): Điền số thứ tự `1, 2, 3...`
* Cột 2 (`project_slug`): Tên slug của dự án.
* Cột 3 (`cve_id`): Mã lỗi/VIC.
* Cột 4 (`cwe_id`): Mã CWE (ví dụ `CWE-022`, `CWE-079`...).
* Cột 9 (`github_url`): URL repo GitHub.
* Cột 11 (`buggy_commit_id`): **Mã commit SHA của VIC** (chính là `vic_id` của bạn).
* Cột 12 (`fix_commit_ids`): Điền mã commit vá lỗi (hoặc điền lại mã commit VIC nếu chưa có).
* *Các cột còn lại (`cwe_name`, `github_username`, `github_repository_name`, `github_tag`, `advisory_id`): Có thể để trống giữa các dấu phẩy.*

### Ví dụ mẫu 1 dòng:
```csv
1,perwendel__spark_CVE-2018-9159_2.7.1,CVE-2018-9159,CWE-022,,perwendel,spark,,https://github.com/perwendel/spark,,27018872d83fe425c89b417b09e7f7fd2d2a9c8c,27018872d83fe425c89b417b09e7f7fd2d2a9c8c
```

---

## 3. Chi tiết sửa `fix_info.csv`

### Vấn đề:
Trong module chấm điểm (`evaluation_pipeline.py:L207`), IRIS có câu lệnh:
```python
if "src/test" in file_name:
    continue  # Bỏ qua hoàn toàn file test!
```
Nếu bạn để method trong `src/test/java/...`, IRIS sẽ **bỏ qua**, dẫn đến điểm Recall luôn là `False` (0%).

### Danh sách 12 dòng cần đổi từ `src/test` sang `src/main`:

| Dòng | `project_slug` | File hiện tại (Bị bỏ qua) | Cần đổi sang |
| :---: | :--- | :--- | :--- |
| **3** | `perwendel__spark_CVE-2016-9177_2.5.1` | `src/test/.../StaticFilesTest.java` | File/method bị lỗi trong `src/main/...` |
| **4** | `vert-x3__vertx-web_CVE-2018-12542_3.5.3.CR1` | `vertx-web/src/test/.../StaticHandlerTest.java` | File/method bị lỗi trong `src/main/...` |
| **9** | `asf__james-project_CVE-2022-22931_3.6.0` | `server/.../src/test/.../SieveFileRepositoryTest.java` | File/method bị lỗi trong `src/main/...` |
| **10** | `asf__james-project_CVE-2022-22931_3.6.0` | `server/.../src/test/.../SieveFileRepositoryTest.java` | File/method bị lỗi trong `src/main/...` |
| **11** | `whitesource__curekit_CVE-2022-23082_1.1.3` | `src/test/.../FileSecurityUtilsTests.java` | File/method bị lỗi trong `src/main/...` |
| **16** | `jenkinsci__workflow-cps-global-lib-plugin_CVE-2022-25174...` | `src/test/.../SCMSourceRetrieverTest.java` | File/method bị lỗi trong `src/main/...` |
| **17** | `hibernate__hibernate-validator_CVE-2019-10219...` | `engine/src/test/.../SafeHtmlValidatorTest.java` | File/method bị lỗi trong `src/main/...` |
| **18** | `nahsra__antisamy_CVE-2022-29577_1.6.6.1` | `src/test/.../AntiSamyTest.java` | File/method bị lỗi trong `src/main/...` |
| **19** | `rhuss__jolokia_CVE-2018-1000129_1.4.0` | `agent/jvm/src/test/.../JolokiaHttpHandlerTest.java` | File/method bị lỗi trong `src/main/...` |
| **22** | `xwiki__xwiki-commons_CVE-2023-36471_14.10.5` | `.../src/test/.../SecureHTMLElementSanitizerTest.java` | File/method bị lỗi trong `src/main/...` |
| **25** | `asf__commons-text_CVE-2022-42889_1.9` | `src/test/.../StringLookupFactoryTest.java` | File/method bị lỗi trong `src/main/...` |

> **Lưu ý:** Chỉ cần trỏ đúng vào **file, class và method nghiệp vụ** nằm trong `src/main/java/...` mà luồng dữ liệu lỗi đi qua.
