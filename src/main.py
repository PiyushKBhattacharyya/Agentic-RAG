from __future__ import annotations
import argparse
from rich import print
from .pipeline import Pipeline


def main():
    parser = argparse.ArgumentParser(description="Agentic RAG demo: Invoice → PO matcher")
    parser.add_argument("--query", type=str, default="Why was invoice INV-123 flagged?", help="User question")
    args = parser.parse_args()

    pipe = Pipeline()
    result = pipe.handle(args.query)

    print("\n[bold cyan]Result:[/bold cyan]")
    print(result)


if __name__ == "__main__":
    main()