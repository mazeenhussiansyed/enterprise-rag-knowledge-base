from __future__ import annotations

import argparse
import json
import urllib.error
from urllib.request import Request, urlopen

import gradio as gr


DEFAULT_API_URL = "http://127.0.0.1:8000"

DEFAULT_QUERY = (
    "When is multi-factor authentication required and which "
    "authentication methods can employees use?"
)

ROLE_CHOICES = [
    "all_employees",
    "it_admin",
    "manager",
    "security",
    "legal",
]


def _post_json(api_url: str, path: str, payload: dict[str, object]) -> dict:
    request = Request(
        url=f"{api_url.rstrip('/')}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(body).get("detail", body)
        except json.JSONDecodeError:
            detail = body
        raise RuntimeError(f"API returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Cannot reach the FastAPI service. Keep the API terminal running "
            "with: uvicorn enterprise_rag.api:app --host 127.0.0.1 --port 8000"
        ) from exc


def _format_citations(citations: list[dict[str, object]]) -> str:
    if not citations:
        return "No citations were returned."

    lines = ["## Evidence and citations"]

    for citation in citations:
        citation_id = citation.get("citation_id", "?")
        title = citation.get("title", "Untitled source")
        section = citation.get("section", "Unknown section")
        version = citation.get("version", "unknown")
        effective_date = citation.get("effective_date", "unknown")
        score = float(citation.get("relevance_score", 0.0))
        excerpt = str(citation.get("excerpt", "")).strip()

        lines.extend(
            [
                f"### [{citation_id}] {title} — {section}",
                (
                    f"Version **{version}** · Effective **{effective_date}** "
                    f"· Relevance **{score:.4f}**"
                ),
                f"> {excerpt}",
            ]
        )

    return "\n\n".join(lines)


def ask_policy(
    query: str,
    role: str,
    strategy: str,
    top_k: int | float,
    api_url: str,
) -> tuple[str, str]:
    cleaned_query = query.strip()

    if not cleaned_query:
        return (
            "## Enter a question\n\nPlease enter a policy question before submitting.",
            "",
        )

    payload = {
        "query": cleaned_query,
        "role": role,
        "strategy": strategy,
        "top_k": int(top_k),
    }

    try:
        response = _post_json(api_url, "/ask", payload)
    except RuntimeError as exc:
        return f"## Service unavailable\n\n{exc}", ""

    status = str(response.get("status", "unknown"))
    answer = str(response.get("answer", "No answer was returned."))
    confidence = float(response.get("confidence", 0.0))
    reason = str(response.get("reason", "unknown"))
    provider = str(response.get("provider", "unknown"))
    citations = response.get("citations", [])

    if not isinstance(citations, list):
        citations = []

    if status == "refused":
        answer_markdown = "\n\n".join(
            [
                "## Safe refusal",
                answer,
                f"**Reason:** `{reason}`",
                f"**Confidence:** `{confidence:.4f}`",
                f"**Provider:** `{provider}`",
            ]
        )
        return answer_markdown, (
            "No evidence was cited because the system safely refused to answer."
        )

    answer_markdown = "\n\n".join(
        [
            "## Grounded answer",
            answer,
            f"**Confidence:** `{confidence:.4f}`",
            f"**Reason:** `{reason}`",
            f"**Provider:** `{provider}`",
        ]
    )
    return answer_markdown, _format_citations(citations)


def build_demo(api_url: str) -> gr.Blocks:
    with gr.Blocks(title="Enterprise Policy RAG") as demo:
        gr.Markdown(
            """
# Enterprise Policy RAG

Ask questions about the governed enterprise-policy knowledge base.
Every answer is grounded in authorized evidence and includes source citations.
            """.strip()
        )

        with gr.Row():
            with gr.Column(scale=3):
                query = gr.Textbox(
                    label="Policy question",
                    placeholder="Ask a question about an enterprise policy...",
                    value=DEFAULT_QUERY,
                    lines=3,
                )
            with gr.Column(scale=1):
                role = gr.Dropdown(
                    choices=ROLE_CHOICES,
                    value="all_employees",
                    label="Your role",
                )
                strategy = gr.Radio(
                    choices=["hybrid", "vector", "bm25"],
                    value="hybrid",
                    label="Retrieval strategy",
                )
                top_k = gr.Slider(
                    minimum=1,
                    maximum=5,
                    value=3,
                    step=1,
                    label="Evidence chunks",
                )

        submit = gr.Button("Ask the knowledge base", variant="primary")

        answer = gr.Markdown(
            "## Ready\n\nEnter a question and select **Ask the knowledge base**."
        )
        citations = gr.Markdown()

        gr.Examples(
            examples=[
                [
                    (
                        "When is multi-factor authentication required and which "
                        "authentication methods can employees use?"
                    ),
                    "all_employees",
                    "hybrid",
                    3,
                ],
                [
                    (
                        "What controls apply to privileged administrator accounts "
                        "and elevation windows?"
                    ),
                    "it_admin",
                    "hybrid",
                    3,
                ],
                [
                    (
                        "What cyber insurance and liability clauses are required "
                        "in vendor contracts?"
                    ),
                    "legal",
                    "hybrid",
                    3,
                ],
                [
                    "What meals are served in the company cafeteria?",
                    "all_employees",
                    "hybrid",
                    3,
                ],
            ],
            inputs=[query, role, strategy, top_k],
            label=(
                "Example scenarios — the final example intentionally demonstrates "
                "a safe refusal."
            ),
        )

        def submit_question(
            entered_query: str,
            entered_role: str,
            entered_strategy: str,
            entered_top_k: int | float,
        ) -> tuple[str, str]:
            return ask_policy(
                entered_query,
                entered_role,
                entered_strategy,
                entered_top_k,
                api_url,
            )

        submit.click(
            fn=submit_question,
            inputs=[query, role, strategy, top_k],
            outputs=[answer, citations],
        )

        query.submit(
            fn=submit_question,
            inputs=[query, role, strategy, top_k],
            outputs=[answer, citations],
        )

        gr.Markdown(
            """
---
**Safety behavior:** if the authorized policy evidence is insufficient,
the system refuses instead of inventing an answer.
            """.strip()
        )

    return demo


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Launch the local Enterprise Policy RAG chat demonstration."
    )
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()

    demo = build_demo(args.api_url)
    demo.launch(
        server_name=args.host,
        server_port=args.port,
        show_error=True,
        theme=gr.themes.Soft(),
        css=".gradio-container { max-width: 1100px !important; }",
    )


if __name__ == "__main__":
    main()