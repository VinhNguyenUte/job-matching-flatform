from celery import shared_task
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.cv import CV
from app.models.job import Job
from app.models.match import Match
import google.generativeai as genai
from sqlalchemy import text
from app.core.config import settings

@shared_task(name="recommend_jobs_for_cv")
def recommend_jobs_for_cv(cv_id: int, top_k: int = 10):
    db: Session = SessionLocal()
    try:
        cv = db.query(CV).filter(CV.id == cv_id).first()
        if not cv or not cv.embedding:
            return {"status": "failed", "reason": "No embedding"}

        # Cosine Similarity query với PGVector
        query = text("""
            SELECT 
                j.id,
                j.title,
                j.company,
                j.location,
                j.salary,
                (1 - (j.embedding <=> :cv_embedding)) as similarity_score
            FROM jobs j
            WHERE j.embedding IS NOT NULL
            ORDER BY j.embedding <=> :cv_embedding
            LIMIT :top_k
        """)

        results = db.execute(query, {
            "cv_embedding": cv.embedding,
            "top_k": top_k
        }).fetchall()

        # Xóa matches cũ
        db.query(Match).filter(Match.cv_id == cv_id).delete()

        matches_created = 0
        for row in results:
            job_id = row[0]
            score = float(row[5]) * 100  # Convert to percentage

            # Tạo explanation bằng Gemini (tóm tắt)
            explanation = generate_match_explanation(cv, job_id, score)

            match = Match(
                user_id=cv.user_id,
                cv_id=cv_id,
                job_id=job_id,
                score=score,
                explanation=explanation
            )
            db.add(match)
            matches_created += 1

        db.commit()

        # Cập nhật match_score cao nhất cho CV
        if results:
            cv.match_score = int(results[0][5] * 100)
            db.commit()

        return {
            "status": "success",
            "cv_id": cv_id,
            "matches_created": matches_created,
            "top_score": float(results[0][5] * 100) if results else 0
        }

    except Exception as e:
        print(f"Recommendation error for CV {cv_id}: {e}")
        return {"status": "failed"}
    finally:
        db.close()


def generate_match_explanation(cv: CV, job_id: int, score: float) -> str:
    """Dùng Gemini tạo giải thích match"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        CV của ứng viên có kỹ năng: {cv.entities.get('skills', [])[:10] if cv.entities else 'N/A'}
        Job: ID {job_id}
        Match score: {score:.1f}%

        Viết một đoạn giải thích ngắn gọn (2-3 câu) bằng tiếng Việt tại sao CV này phù hợp với job này.
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return f"Match score {score:.1f}% - Có sự phù hợp về kỹ năng và kinh nghiệm."