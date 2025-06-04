<div align="center">

</div>

<p align="center">
  <img src="https://img.shields.io/github/languages/code-size/robonamari/Dirlotix-py?style=flat" alt="Code Size">
  <img src="https://tokei.rs/b1/github/robonamari/Dirlotix-py?style=flat" alt="Total lines">
  <img src="https://img.shields.io/badge/python-%5E3.9-blue" alt="Python Versions">
  <img src="https://img.shields.io/github/license/robonamari/Dirlotix-py" alt="GitHub license">
</p>

---

<img src="/.github/banner.png" alt="بنر">
<p dir="rtl">

این پروژه یک برنامه مدیریت فایل تحت وب است که با Python و Flask ساخته شده است. این برنامه به کاربران امکان می دهد تا فایل های موجود در سرور را مرور و دانلود کنند، لیست دایرکتوری ها را مشاهده کنند و با انواع مختلف فایل ها تعامل داشته باشند. همچنین، این برنامه از قابلیت چندزبانه پشتیبانی می کند و به کاربران اجازه می دهد تنظیمات مختلفی مانند رنگ های تم، فونت ها و فاوآیکن را پیکربندی کنند.

## ویژگی ها

- مرور و مشاهده فایل ها و دایرکتوری ها.
- پشتیبانی از انواع مختلف فایل ها (تصاویر، ویدئوها، صدا، متن، PDF و موارد دیگر).
- جستجو و مرتب سازی فایل ها بر اساس نام، اندازه یا تاریخ آخرین تغییر.
- پشتیبانی از همه زبان های زنده با بارگذاری پویا از طریق فایل‌های YAML (بر اساس استاندارد [ISO 639-1](https://fa.wikipedia.org/wiki/%D9%81%D9%87%D8%B1%D8%B3%D8%AA_%DA%A9%D8%AF%D9%87%D8%A7%DB%8C_%D8%A7%DB%8C%D8%B2%D9%88_%DB%B1%E2%80%93%DB%B6%DB%B3%DB%B9)، شامل تقریباً 176 زبان).
- قابلیت تنظیم رنگ های تم، فونت ها و فاوآیکن.
- مدیریت خطاها و ریدایرکت برای خطاهای مختلف HTTP.

## تنظیمات میزبانی شخصی

<details>
<summary dir="rtl">4 مرحله برای میزبانی Dirlotix-py روی سرور شخصی</summary>

### 1. کلون کردن مخزن

```bash
git clone https://github.com/robonamari/Dirlotix-py
```

### 2. نصب پایتون و وابستگی ها

پایتون را نصب کنید، سپس وابستگی های مورد نیاز را نصب کنید:

```bash
pip install -r requirements.txt
```

### 3. تنظیم اسکریپت

1. نام **.env.example** را به **.env** تغییر دهید.
2. توضیحات کامل متغیرهای محیطی داخل فایل `.env` نوشته شده اند، آن ها را مطابق نیاز تکمیل کنید.
3. یک پوشه به نام `downloads` بسازید و هر فایل، پوشه یا هر چیزی که می‌خواهید برای دانلود قرار دهید داخل این پوشه بگذارید.

### 4. اجرای اسکریپت

```bash
python index.py
```

### انجام شد!

اسکریپت شما باید به طور کامل تنظیم شده و آماده اجرا باشد!

</details>
</p>
