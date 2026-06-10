# 資源使用紀錄

本專案刻意隔離在 `/home/mark/workspace/taica_proj`。

## 最近一次執行

- UTC 時間：2026-06-10T12:08:43.167421+00:00
- 指令：`python3 -m ragshield.cli run-demo`
- 網路：只有在公開資料集 CSV 尚未快取時，才會使用 Hugging Face datasets-server HTTPS API。
- GPU：未使用。
- Port：預設不佔用任何 port。選配靜態報告服務只會在程序執行期間使用指定 port。
- 檔案寫入：僅寫入本專案目錄內的 `data/`、`reports/` 與本資源紀錄。
- 輸出：
  - json: `/home/mark/workspace/taica_proj/reports/final_validation.json`
  - markdown: `/home/mark/workspace/taica_proj/reports/final_validation.md`
  - html: `/home/mark/workspace/taica_proj/reports/final_validation.html`
