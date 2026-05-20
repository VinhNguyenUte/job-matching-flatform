from app.features.jd_ingestion.schemas import IngestJobRequest, NormalizedJobInput


class JDInputAdapter:
    @staticmethod
    def normalize(item: IngestJobRequest) -> NormalizedJobInput:
        raw_text = JDInputAdapter._clean(item.description) or JDInputAdapter._clean(item.text)
        if not raw_text:
            raise ValueError("Missing JD raw text. Provide either 'description' or 'text'.")

        source_url = JDInputAdapter._clean(item.link) or JDInputAdapter._clean(item.url)
        source_type = JDInputAdapter._detect_source_type(item)
        posted_at = (
            JDInputAdapter._clean(item.post_time)
            or JDInputAdapter._clean(item.timestamp)
            or JDInputAdapter._clean(item.scraped_at)
        )

        source_metadata = {
            "source_type": source_type,
            "post_id": item.post_id,
            "author": item.author,
            "likes": item.likes,
            "comments_count": item.comments_count,
            "shares": item.shares,
            "comments": item.comments,
            "scraped_at": item.scraped_at,
            "original_url": item.url,
            "original_link": item.link,
        }
        source_metadata = {key: value for key, value in source_metadata.items() if value not in (None, "", [])}

        return NormalizedJobInput(
            raw_text=raw_text,
            source_type=source_type,
            source_url=source_url,
            posted_at=posted_at,
            title=JDInputAdapter._clean(item.title),
            company=JDInputAdapter._clean(item.company),
            location=JDInputAdapter._clean(item.location),
            source_author=JDInputAdapter._clean(item.author),
            external_id=JDInputAdapter._clean(item.post_id),
            source_metadata=source_metadata,
        )

    @staticmethod
    def _detect_source_type(item: IngestJobRequest) -> str:
        if item.text and (item.post_id or "facebook.com" in (item.url or "").lower()):
            return "facebook"
        if item.description:
            return "linkedin"
        return "generic_jd"

    @staticmethod
    def _clean(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None
