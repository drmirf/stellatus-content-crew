"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_topic():
    """Sample topic for testing."""
    return "Como usar os ciclos lunares para planejar suas metas de negócios"


@pytest.fixture
def sample_content():
    """Sample content for testing."""
    return """# Como usar os ciclos lunares para planejar suas metas de negócios

A lua tem sido uma guia para a humanidade desde tempos imemoriais. Agricultores plantavam seguindo
suas fases, navegadores usavam sua luz para orientação, e diversas culturas desenvolveram calendários
baseados em seus ciclos.

## A Lua Nova: Tempo de Planejamento

A lua nova representa novos começos. Este é o momento ideal para definir novas metas, iniciar
projetos e plantar as sementes de suas intenções para o ciclo que se inicia.

## A Lua Crescente: Tempo de Ação

Com a lua crescente, a energia aumenta. É hora de colocar seus planos em prática, fazer
reuniões importantes e avançar com iniciativas.

## A Lua Cheia: Tempo de Colheita

A lua cheia traz iluminação e culminação. Avalie seus progressos, celebre conquistas e
faça ajustes necessários em sua estratégia.

## A Lua Minguante: Tempo de Reflexão

A fase minguante convida ao recolhimento e reflexão. Analise o que funcionou, descarte
o que não serve mais e prepare-se para o próximo ciclo.
"""
