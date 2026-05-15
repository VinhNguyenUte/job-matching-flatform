from google.genai import types

from app.common.clients.gemini import gemini_client
from app.common.schemas.job import JobParsedSchema


class JDEmbeddingService:
    @staticmethod
    def contextualize_job(job: JobParsedSchema) -> str:
        priority_map = {1: "bat buoc", 2: "uu tien", 3: "diem cong", 4: "khong bat buoc"}
        parts = [
            f"Vi tri tuyen dung: {job.title}.",
            f"Cong ty: {job.company.name}.",
            f"Mo ta cong viec: {job.description_raw or ''}",
        ]

        if job.skills:
            parts.append(
                "Ky nang: "
                + ", ".join(
                    f"{item.name} ({priority_map.get(item.priority_level, 'bat buoc')})"
                    for item in job.skills
                )
                + "."
            )

        if job.tools:
            parts.append(
                "Cong cu: "
                + ", ".join(
                    f"{item.name} ({priority_map.get(item.priority_level, 'bat buoc')})"
                    for item in job.tools
                )
                + "."
            )

        if job.languages:
            parts.append(
                "Ngoai ngu: "
                + ", ".join(
                    f"{item.name} {item.proficiency_level or ''}".strip()
                    for item in job.languages
                )
                + "."
            )

        if job.mindsets:
            parts.append("Mindset: " + ", ".join(job.mindsets) + ".")

        if job.benefits:
            parts.append("Phuc loi: " + ", ".join(item.name for item in job.benefits) + ".")

        if job.requirements_summary:
            parts.append(f"Tom tat yeu cau: {job.requirements_summary}")

        return "\n".join(parts)

    @staticmethod
    async def generate_embedding(text: str) -> list[float]:
        response = gemini_client.models.embed_content(
            model="gemini-embedding-2",
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=768),
        )
        return response.embeddings[0].values
