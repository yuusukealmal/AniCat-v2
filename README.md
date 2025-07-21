# AniCat-v2

AniCat-v2 為一個 [Anime1.me](https://anime1.me/) 的下載器。

## 功能

- 支援多連結輸入
- 支援下載進度條

## 使用方法

1. 建立環境

   ```
   pip install -r requirements.txt
   ```

2. 在`url.txt`中輸入 [Anime1.me](https://anime1.me/) 的動畫連結

   - 支援的連結格式

     - 單季連結：`https://anime1.me/category/...`
     - 單集連結：：`https://anime1.me/...`
     - 支援多連結 **`以行為間隔`**
     - 範例

       ```
       https://anime1.me/category/2021年冬季/關於我轉生變成史萊姆這檔事-第二季
       https://anime1.me/15651
       ```

3. 執行 Python

   ```
   python anime1.py
   ```
