#!/usr/bin/env python3
"""
MongoDB Query Optimizer - Main Entry Point

An intelligent MongoDB performance analysis tool that identifies slow queries
and provides AI-powered optimization recommendations using Large Language Models.

Usage:
    python mongo-optimiser-agent.py

Configuration:
    Copy .env.example to .env and configure your settings.

Requirements:
    - OpenRouter API key
    - MongoDB instance (local Docker or remote)
    - Python 3.8+
"""

from mongo_optimiser.main import run

if __name__ == "__main__":
    run()
