import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import google.generativeai as genai


DEFAULT_GEMINI_MODEL = "gemini-3-flash-preview"

ROLE_KEYWORDS = [
    (r"\b(fullstack|full stack)\b", "Fullstack Web Developer"),
    (r"\bfrontend engineer\b", "Frontend Engineer"),
    (r"\bfront end\b", "Frontend Engineer"),
    (r"\bbackend engineer\b", "Backend Engineer"),
    (r"\bbackend\b", "Backend Engineer"),
    (r"\bandroid developer\b", "Android Developer"),
    (r"\bios developer\b", "iOS Developer"),
    (r"\bdevops\b", "DevOps Engineer"),
    (r"\bqa engineer\b", "QA Engineer"),
    (r"\bproduct manager\b|\bpm\b", "Product Manager"),
    (r"\bproduct designer\b|\bui/ux\b|\bux/ui\b", "Product Designer"),
    (r"\bnetwork\b", "Network Engineer"),
    (r"\bsystem administrator\b|\bsystem admin\b|\bquản trị hệ thống\b", "System Administrator"),
    (r"\bdata engineer\b|\bdata\b", "Data Engineer"),
]

LOCATION_LABELS = [
    r"địa điểm làm việc",
    r"địa điểm",
    r"location",
    r"work location",
]

CITY_HINTS = [
    "Hà Nội",
    "Hanoi",
    "Hồ Chí Minh",
    "TP.HCM",
    "HCM",
    "Đà Nẵng",
    "Da Nang",
    "Hải Phòng",
    "Hai Phong",
    "Cầu Giấy",
    "Tây Hồ",
    "Mễ Trì",
    "Tân Bình",
    "Tân Phú",
]

SENIORITY_KEYWORDS = [
    (r"\bintern\b|\binternship\b|\bthực tập\b|\btts\b", "Internship"),
    (r"\bfresher\b|\bjunior\b|\bentry level\b|\bentry-level\b", "Entry level"),
    (r"\bmiddle\b|\bmid\b|\bsenior\b|\bmid/senior\b|\bsenior/middle\b", "Mid-Senior level"),
    (r"\blead\b|\bprincipal\b|\bstaff\b", "Senior level"),
]

EMPLOYMENT_KEYWORDS = [
    (r"\bfull[- ]time\b", "Full-time"),
    (r"\bpart[- ]time\b", "Part-time"),
    (r"\bcontract\b|\bhợp đồng\b", "Contract"),
    (r"\binternship\b|\bthực tập\b|\btts\b", "Internship"),
]

JOB_FUNCTIONS = [
    (r"\bfrontend\b|\breact\b|\bnext\.js\b|\bui/ux\b|\bproduct designer\b", "Information Technology"),
    (r"\bbackend\b|\bgo\b|\brust\b|\bjava\b|\bnode\.js\b|\bandroid\b", "Information Technology"),
    (r"\bdata\b|\bai\b|\bautomation\b", "Information Technology"),
    (r"\bqa\b|\btest\b", "Quality Assurance"),
    (r"\bproduct manager\b|\bpm\b", "Product Management"),
]

INDUSTRY_HINTS = [
    (r"\bfintech\b|\btrading\b|\bcrypto\b|\brealtime\b", "Fintech"),
    (r"\bsaas\b", "Software Development"),
    (r"\be-commerce\b|\becommerce\b|\bshopify\b", "E-commerce"),
    (r"\bsoftware\s+development\b", "Software Development"),
    (r"\bit services\b|\binformation technology\b", "IT Services"),
]

api_key = os.getenv("GEMINI_API_KEY", "").strip()

def configure_gemini(api_key: str):
    if not api_key:
        raise ValueError("Thiếu GEMINI_API_KEY. Hãy set biến môi trường hoặc truyền --api-key.")
    genai.configure(api_key=api_key)


def sanitize_filename(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return safe.strip("._-") or "output"


def extract_json_text(text: str):
    if not text:
        return None

    cleaned = text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except Exception:
        for pattern in (r"\{.*\}", r"\[.*\]"):
            match = re.search(pattern, cleaned, re.S)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    continue
    return None


def normalize_field(value, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return ", ".join(items) if items else default
    text = str(value).strip()
    return text if text else default


def first_label_value(text: str, labels) -> str:
    for label in labels:
        pattern = rf"(?:^|\n)\s*[^\S\r\n]*{label}\s*[:\-–]?\s*(.+)"
        match = re.search(pattern, text, re.I)
        if match:
            value = match.group(1).strip()
            if value:
                return value.split("\n", 1)[0].strip()
    return ""


def clean_text_lines(text: str):
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip().lstrip("*#>-•").strip()
        if line:
            lines.append(line)
    return lines


def guess_title(text: str) -> str:
    lines = clean_text_lines(text)
    for line in lines[:6]:
        if any(re.search(pattern, line, re.I) for pattern, _ in ROLE_KEYWORDS):
            return line[:120]

    for pattern, title in ROLE_KEYWORDS:
        if re.search(pattern, text, re.I):
            return title

    if lines:
        candidate = lines[0]
        if len(candidate) > 8:
            return candidate[:120]
    return ""


def guess_company(record: dict, text: str) -> str:
    author = normalize_field(record.get("author"))
    if author and len(author) >= 2:
        if not re.search(r"^\s*(hr|admin|recruiter|tuyển dụng)\b", author, re.I):
            return author

    bracket_match = re.search(r"\[([A-Za-z0-9._&\- ]{2,})\]", text)
    if bracket_match:
        return bracket_match.group(1).strip()

    company_patterns = [
        r"^\s*([A-Z0-9][A-Z0-9&()._/\- ]{2,})\s*(?:TUYỂN DỤNG|TUYEN DUNG|HIRING|TÌM|TIM|OPEN|RECRUITING)\b",
        r"^\s*([A-Z][A-Za-z0-9&()._/\- ]{2,})\s*(?:tuyển dụng|tuyen dung|hiring|recruiting)\b",
    ]
    for line in clean_text_lines(text)[:8]:
        for pattern in company_patterns:
            match = re.search(pattern, line, re.I)
            if match:
                company = match.group(1).strip("-:| ")
                if company:
                    return company
    return ""


def guess_location(text: str) -> str:
    for label in LOCATION_LABELS:
        value = first_label_value(text, [label])
        if value:
            return value

    for city in CITY_HINTS:
        if re.search(re.escape(city), text, re.I):
            return city
    return ""


def guess_seniority_level(text: str) -> str:
    for pattern, value in SENIORITY_KEYWORDS:
        if re.search(pattern, text, re.I):
            return value
    return ""


def guess_employment_type(text: str) -> str:
    for pattern, value in EMPLOYMENT_KEYWORDS:
        if re.search(pattern, text, re.I):
            return value
    return ""


def guess_job_function(text: str) -> str:
    for pattern, value in JOB_FUNCTIONS:
        if re.search(pattern, text, re.I):
            return value
    return "Information Technology" if re.search(r"\b(it|software|developer|engineer|code|backend|frontend|android|react|java)\b", text, re.I) else ""


def guess_industries(text: str) -> str:
    values = []
    for pattern, value in INDUSTRY_HINTS:
        if re.search(pattern, text, re.I):
            values.append(value)
    if values:
        deduped = []
        for value in values:
            if value not in deduped:
                deduped.append(value)
        return ", ".join(deduped)
    return ""


def merge_ai_and_fallbacks(record: dict, text: str, ai_data: dict) -> dict:
    ai_data = ai_data if isinstance(ai_data, dict) else {}
    merged = {
        "title": normalize_field(ai_data.get("title")) or guess_title(text),
        "company": normalize_field(ai_data.get("company")) or guess_company(record, text),
        "location": normalize_field(ai_data.get("location")) or guess_location(text),
        "link": normalize_field(ai_data.get("link"), "") or normalize_field(record.get("url"), "N/A"),
        "seniority_level": normalize_field(ai_data.get("seniority_level")) or guess_seniority_level(text),
        "employment_type": normalize_field(ai_data.get("employment_type")) or guess_employment_type(text),
        "job_function": normalize_field(ai_data.get("job_function")) or guess_job_function(text),
        "industries": normalize_field(ai_data.get("industries")) or guess_industries(text),
    }
    if not merged["link"]:
        merged["link"] = "N/A"
    return merged


def load_records(input_path: Path):
    data = json.loads(input_path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get("posts"), list):
            return data["posts"]
        if isinstance(data.get("results"), list):
            return data["results"]
        return [data]
    raise ValueError("File input phải là JSON list hoặc JSON object")


def pick_latest_input_file() -> Optional[Path]:
    candidates = sorted(Path(".").glob("output_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if candidates:
        return candidates[0]

    fallback = Path("fb_posts.json")
    if fallback.exists():
        return fallback

    return None


async def analyze_post_ai(text: str, model):
    if not text or len(text.strip()) < 10:
        return None

    prompt = f"""
Phân tích bài đăng Facebook sau và trích xuất dữ liệu thành JSON theo cấu trúc jobs.json.
1. title: Tên khóa học/Vị trí tuyển dụng.
2. company: Tên công ty/tổ chức.
3. location: Địa điểm làm việc/học tập.
4. seniority_level: Mức độ ("Internship", "Entry level", "Mid-Senior level", "Director", etc).
5. employment_type: Loại hình ("Internship", "Full-time", "Part-time", "Contract", etc).
6. job_function: Lĩnh vực ("Information Technology", "Sales", "Marketing", etc).
7. industries: Ngành ("Software Development", "IT Services", etc).
8. link: Link bài đăng (hoặc "N/A" nếu không có).

Chỉ trả về đúng 1 object JSON với đủ các khóa: title, company, location, seniority_level, employment_type, job_function, industries, link.
Nếu không chắc chắn, hãy để giá trị rỗng cho từng khóa nhưng vẫn phải giữ đúng cấu trúc object.

Nội dung:
{text}

Trả về duy nhất JSON thuần túy, không markdown, không giải thích thêm.
"""

    try:
        response = await asyncio.to_thread(model.generate_content, prompt)
        parsed = extract_json_text(getattr(response, "text", ""))
        if isinstance(parsed, list):
            parsed = parsed[0] if parsed else None
        return parsed if isinstance(parsed, dict) else None
    except Exception as e:
        print(f"Lỗi AI: {e!s}")
        return None


def format_to_jobs_json(record: dict, text: str, ai_data: dict) -> dict:
    """Transform analyzed data to jobs.json format"""
    merged = merge_ai_and_fallbacks(record, text, ai_data)
    job_entry = {
        "title": merged["title"],
        "company": merged["company"],
        "location": merged["location"],
        "post_time": record.get("scraped_at", datetime.now().isoformat())[:10],
        "link": merged["link"],
        "description": text,
        "seniority_level": merged["seniority_level"],
        "employment_type": merged["employment_type"],
        "job_function": merged["job_function"],
        "industries": merged["industries"]
    }
    return job_entry


async def analyze_records(records, model, limit: Optional[int] = None):
    results = []
    usable_records = records[:limit] if limit and limit > 0 else records

    for idx, record in enumerate(usable_records, 1):
        text = (
            record.get("text")
            or record.get("raw_text")
            or record.get("content")
            or ""
        ).strip()
        if not text:
            continue

        ai_data = await analyze_post_ai(text, model)
        record["raw_text"] = text
        record["scraped_at"] = record.get("scraped_at") or datetime.now().isoformat()
        
        # Format output as jobs.json structure
        job_entry = format_to_jobs_json(record, text, ai_data)
        results.append(job_entry)
        print(f"✓ Đã phân tích bài {idx}/{len(usable_records)}")
        await asyncio.sleep(0.25)

    return results


async def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    load_dotenv()
    parser = argparse.ArgumentParser(description="Phân tích JSON bài đăng Facebook bằng Gemini")
    parser.add_argument("--input", help="File JSON đầu vào từ fb_scraper.py")
    parser.add_argument("--output", help="File JSON đầu ra")
    parser.add_argument("--model", default=DEFAULT_GEMINI_MODEL, help="Tên model Gemini")
    parser.add_argument("--limit", type=int, default=0, help="Giới hạn số bài cần phân tích")
    parser.add_argument("--api-key", help="Gemini API key (nếu không dùng .env)")
    args = parser.parse_args()

    api_key = (args.api_key or os.getenv("GEMINI_API_KEY", "")).strip()
    configure_gemini(api_key)
    model = genai.GenerativeModel(args.model)

    input_path = Path(args.input) if args.input else pick_latest_input_file()
    if input_path is None:
        raise SystemExit(
            "Không tìm thấy file input. Hãy truyền --input hoặc đặt một file output_*.json / fb_posts.json trong thư mục hiện tại."
        )
    if not input_path.exists():
        raise SystemExit(f"Không tìm thấy file input: {input_path}")

    records = load_records(input_path)
    final_data = await analyze_records(records, model, args.limit)

    output_path = Path(args.output) if args.output else Path(f"analyzed_{sanitize_filename(input_path.stem)}.json")
    output_path.write_text(json.dumps(final_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Hoàn tất! File lưu tại: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
