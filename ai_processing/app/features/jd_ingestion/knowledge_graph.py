from app.features.jd_ingestion.schemas import KnowledgeGraphContext, KnowledgeGraphEdge, NamedEntity, NERResult


class JDTemporaryKnowledgeGraph:
    @staticmethod
    def build(ner: NERResult) -> KnowledgeGraphContext:
        nodes: list[NamedEntity] = []
        edges: list[KnowledgeGraphEdge] = []
        job_node = NamedEntity(
            name=ner.job_title or "job",
            entity_type="job",
            label="target_job",
            confidence=1.0,
        )
        nodes.append(job_node)

        if ner.company_name:
            company_node = NamedEntity(name=ner.company_name, entity_type="company", label="hiring_company")
            nodes.append(company_node)
            edges.append(KnowledgeGraphEdge(source=company_node.name, relation="HIRES_FOR", target=job_node.name))

        JDTemporaryKnowledgeGraph._append_relations(nodes, edges, job_node.name, "REQUIRES", ner.skills)
        JDTemporaryKnowledgeGraph._append_relations(nodes, edges, job_node.name, "USES", ner.tools)
        JDTemporaryKnowledgeGraph._append_relations(nodes, edges, job_node.name, "NEEDS_LANGUAGE", ner.languages)
        JDTemporaryKnowledgeGraph._append_relations(nodes, edges, job_node.name, "OFFERS", ner.benefits)
        JDTemporaryKnowledgeGraph._append_relations(nodes, edges, job_node.name, "LOCATED_IN", ner.locations)
        JDTemporaryKnowledgeGraph._append_relations(nodes, edges, job_node.name, "VALUES", ner.mindsets)

        context_text = "\n".join(f"{edge.source} {edge.relation} {edge.target}" for edge in edges)
        return KnowledgeGraphContext(nodes=nodes, edges=edges, context_text=context_text)

    @staticmethod
    def _append_relations(
        nodes: list[NamedEntity],
        edges: list[KnowledgeGraphEdge],
        source: str,
        relation: str,
        targets: list[NamedEntity],
    ) -> None:
        for target in targets:
            nodes.append(target)
            edges.append(KnowledgeGraphEdge(source=source, relation=relation, target=target.name))
