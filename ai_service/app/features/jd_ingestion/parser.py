from google.genai import types

from app.common.config import settings
from app.common.clients.gemini import gemini_client
from app.common.schemas.job import JobParsedSchema


class JDParsingService:
    @staticmethod
    async def parse_job_description(raw_content: str) -> JobParsedSchema:
        prompt = f"""
        Bạn là chuyên gia bóc tách dữ liệu Job Description.
        Hãy chuyển nội dung tuyển dụng dưới đây thành JSON đúng schema đã chỉ định.

        Quy tắc:
        - Trả về đúng schema JSON.
        - Nếu thiếu dữ liệu thì dùng null, chuỗi rỗng hoặc mảng rỗng phù hợp.
        - min_experience phải là số năm kinh nghiệm dạng float, ví dụ 6 tháng = 0.5.
        - Cố gắng tách kỹ locations, skills, tools, languages, benefits.
        - requirements_summary là phần tóm tắt ngắn gọn các yêu cầu chính.
        - extended_attributes chỉ dùng cho các trường hữu ích nhưng không ánh xạ trực tiếp.

        Nội dung JD:
        {raw_content}
        """

        response = gemini_client.models.generate_content(
            model=settings.AI_GENERATION_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=JobParsedSchema,
                temperature=0.1,
            ),
        )
        return JobParsedSchema.model_validate_json(response.text)
