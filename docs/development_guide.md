# Development Guide

Guide for contributing new features to Light Agent without frameworks.

---

## 1. Antes de Começar

### 1.1 Verificar Código Existente

**Sempre verifique se já existe código similar:**

```bash
# Buscar funcionalidade similar
rg "similar_function_name" lightagent/ --type py

# Verificar se módulo já existe
rg "from lightagent.agent" lightagent/ --type py | head -20

# Verificar ferramentas similares
rg "class.*Tool" lightagent/agent/tools/ --type py

# Verificar dataclasses/models similares
rg "class.*State|class.*Model" lightagent/ --type py

# Verificar funções utilitárias
rg "^def " lightagent/utils/ --type py

# Verificar arquivos existentes
fd "my_feature" lightagent/
```

### 1.2 Duplicação de Código

| Situação | Ação |
|----------|------|
| 80%+ código similar | Extrair para função/classe compartilhada |
| Lógica similar, tipos diferentes | Usar generics |
| Padrões de config repetidos | Criar classe de configuração |

---

## 2. Criar Branch

```bash
# Sempre criar branch para novas features
git checkout -b feature/my-new-feature

# Ou para bugfixes
git checkout -b bugfix/issue-description

# Ou para documentação
git checkout -b docs/update-section
```

---

## 3. Estrutura de Arquivos

```
lightagent/agent/
├── my_feature/
│   ├── __init__.py
│   ├── models.py          # Pydantic models, dataclasses
│   ├── core.py            # Main logic
│   └── utils.py           # Helper functions
├── tools/
│   └── my_tool.py         # Se a feature adicionar uma ferramenta
└── tests/
    └── test_my_feature.py # Unit tests
```

---

## 4. Princípios de Design OO

### 4.1 Quando Usar Classes

**Use classes para:**
- **Componentes stateful**: Objetos com estado mutável (ex: `AgentLoop`, `SessionManager`)
- **Encapsulamento**: Agrupar dados e comportamento relacionados (ex: `ToolRegistry`, `MemoryStore`)
- **Polimorfismo**: Múltiplas implementações de interface (ex: `LLMProvider`)
- **Builder/Factory**: Criação estruturada de objetos (ex: `AgentBuilder`)

**Prefira funções para:**
- Transformações puras (ex: `serialize_state`, `deserialize_state`)
- Utilitários stateless (ex: `safe_filename`, `truncate_string`)

### 4.2 Exemplos de Design

```python
# BOM: Responsabilidade focada
class AgentLoop:
    """Main agent execution loop."""
    
    def __init__(self, provider: LLMProvider, tools: ToolRegistry):
        self.provider = provider
        self.tools = tools
        self.messages: list[dict] = []

    async def run(self, user_input: str) -> str:
        """Execute single turn."""
        ...

# BOM: Dataclasses imutáveis para estado
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ThreadState:
    """Immutable thread state."""
    thread_id: str
    version: int
    messages: list[dict]
    created_at: datetime = field(default_factory=datetime.utcnow)

# BOM: Abstract base class para plugins
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, messages: list[dict]) -> LLMResponse:
        """Generate LLM response."""
        pass
```

### 4.3 Composição Sobre Herança

```python
# BOM: Composição
class AgentLoop:
    def __init__(self, provider: LLMProvider, memory: MemoryStore):
        self.provider = provider  # Has-a relationship
        self.memory = memory

# EVITAR: Hierarquias profundas de herança
class A: ...
class B(A): ...  # Preferir composição
class C(B): ...
```

### 4.4 Observer Pattern

**Use para desacoplar emissores de eventos de consumidores:**

```python
from lightagent.agent.observer import AgentObserver, AgentSubject, AgentEvent, AgentEventType

# Criar observer
class MyObserver(AgentObserver):
    @property
    def observer_id(self) -> str:
        return "my_observer"

    @property
    def observer_name(self) -> str:
        return "My Observer"

    async def on_event(self, event: AgentEvent) -> None:
        print(f"Received: {event.event_type}")

# Criar subject e attachar
subject = AgentSubject(name="MyAgent")
subject.attach(MyObserver())

# Emitir eventos
subject.emit(AgentEvent(
    event_type=AgentEventType.TASK_STARTED,
    source="agent_1",
    data={"task_id": "task_123"}
))
```

---

## 5. Convenções de Código

### 5.1 Nomenclatura

| Tipo | Convenção | Exemplo |
|------|-----------|---------|
| Modules | `snake_case` | `thread_store.py` |
| Classes | `PascalCase` | `ThreadStore` |
| Functions | `snake_case` | `load_thread()` |
| Constants | `UPPER_SNAKE` | `MAX_RETRIES` |
| Variables | `snake_case` | `thread_id` |

### 5.2 Ordem de Imports

```python
# Standard library
import json
from datetime import datetime
from typing import Any, Dict, Optional

# Third party
from pydantic import BaseModel

# Local
from lightagent.agent.base import Tool
```

---

## 6. Padrões Comuns

### 6.1 Pydantic Models

```python
from pydantic import BaseModel
from datetime import datetime

class MyModel(BaseModel):
    name: str
    value: int
    created_at: datetime = datetime.utcnow()
```

### 6.2 Operações Async

```python
import asyncio
from typing import Optional

async def fetch_data(self, query: str) -> Optional[dict]:
    await asyncio.sleep(0.1)
    return {"result": query}
```

### 6.3 Tratamento de Erros

```python
class MyError(Exception):
    """Custom error for this feature."""

async def risky_operation(self) -> str:
    try:
        result = await potentially_failing_call()
        return result
    except SpecificError as e:
        raise MyError("Helpful message") from e
```

### 6.4 Consistência de Idioma

**SEMPRE responda no idioma do usuário:**

```python
# BOM: Respostas no idioma correto
async def execute(self, **kwargs: Any) -> str:
    user_input = kwargs.get("input", "")
    is_portuguese = self._detect_language(user_input)
    
    if is_portuguese:
        return "Operação concluída com sucesso."
    else:
        return "Operation completed successfully."

# RUIM: Misturar idiomas
def bad_example():
    return "File saved with success. Ver arquivo em /path"
```

---

## 7. Criar Nova Ferramenta

```python
from lightagent.agent.tools.base import Tool
from typing import Any

class MyTool(Tool):
    """Brief description of what the tool does."""

    @property
    def name(self) -> str:
        return "my_tool_name"

    @property
    def description(self) -> str:
        return "What this tool does and when to use it."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "..."}
            },
            "required": ["param1"]
        }

    async def execute(self, **kwargs: Any) -> str:
        # Tool implementation
        return "Result string"
```

---

## 8. Testes

### 8.1 Estrutura de Testes

```
tests/
├── __init__.py              # Fixture globais
├── conftest.py              # Fixtures compartilhadas
├── agents/
│   ├── __init__.py
│   ├── test_agent_builder.py
│   ├── test_agent_loop.py
│   ├── test_subagent.py
│   ├── test_tool.py
│   └── test_tool_registry.py
├── providers/
│   ├── __init__.py
│   └── test_litellm_provider.py
└── skills/
    ├── __init__.py
    └── test_skills_loader.py
```
lightagent/tests/
├── __init__.py
├── conftest.py              # Fixtures compartilhadas
├── agents/
│   ├── __init__.py
│   ├── test_agent_builder.py
│   ├── test_agent_loop.py
│   ├── test_subagent.py
│   ├── test_tool.py
│   └── test_tool_registry.py
├── providers/
│   ├── __init__.py
│   └── test_litellm_provider.py
└── skills/
    ├── __init__.py
    └── test_skills_loader.py
```

### 8.2 pytest Configuration

O projeto usa `pytest` com `pytest-asyncio` para testes async:

```bash
# Executar todos os testes
uv run pytest tests/

# Executar com verbose
uv run pytest tests/ -v

# Executar teste específico
uv run pytest tests/agents/test_agent_builder.py::TestAgentBuilder::test_init -v
```

### 8.3 Fixtures Compartilhadas (conftest.py)

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def temp_workspace() -> Generator[str, Any, Any]:
    """Diretório temporário para testes."""
    with TemporaryDirectory() as tmp:
        yield tmp

@pytest.fixture
def mock_provider() -> MagicMock:
    """Provider LLM mockado."""
    provider = MagicMock(spec=LLMProvider)
    provider.generate = AsyncMock(
        return_value=LLMResponse(content="Mock response")
    )
    provider.get_default_model = MagicMock(return_value="test/model")
    return provider
```

### 8.4 Testes Async

Use `@pytest.mark.async` ou configure `pytest-asyncio`:

```python
import pytest
from lightagent.agent.loop import AgentLoop

class TestAgentLoop:
    @pytest.mark.asyncio
    async def test_run_simple_response(
        self,
        mock_provider: MagicMock,
        temp_workspace: str
    ) -> None:
        """Teste de execução simples."""
        loop = AgentLoop(
            provider=mock_provider,
            memory=MemoryStore(temp_workspace),
            tools=ToolRegistry(),
        )
        result = await loop.run("Hello")
        assert result == "Mock response"
```

### 8.5 Testes de Ferramentas (Tools)

```python
from typing import Any
from lightagent.agent.tools.base import Tool

class MyTestTool(Tool):
    @property
    def name(self) -> str:
        return "my_test_tool"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Input"}
            },
            "required": ["input"]
        }

    async def execute(self, **kwargs: Any) -> str:
        return f"processed: {kwargs.get('input')}"
```

### 8.6 Mocking de Dependências

```python
from unittest.mock import patch, MagicMock

class TestMyFeature:
    def test_with_mocked_settings(self) -> None:
        """Mock de configurações."""
        with patch("lightagent.config.settings") as mock_settings:
            mock_settings.effective_base_dir = Path("/tmp")
            # Test implementation
```

### 8.7 Convenções de Testes

| Tipo | Padrão |
|------|---------|
| Arquivos | `test_*.py` |
| Classes | `Test*` |
| Funções | `test_*` |
| Fixtures | `conftest.py` |
| Async | `@pytest.mark.asyncio` |

### 8.8 Exemplo Completo

```python
"""Tests for AgentBuilder."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

from lightagent.agent.builder import AgentBuilder
from lightagent.agent.tools.registry import ToolRegistry
from lightagent.providers.base import LLMProvider


class TestAgentBuilder:
    """Tests for AgentBuilder class."""

    def test_init(self) -> None:
        """Test initialization with defaults."""
        builder = AgentBuilder()
        assert builder._provider is None
        assert isinstance(builder._tools, ToolRegistry)

    def test_with_provider(self) -> None:
        """Test setting provider."""
        builder = AgentBuilder()
        result = builder.with_provider(model="ollama/llama3")
        assert result is builder
        assert builder._provider is not None

    def test_build_chain(self) -> None:
        """Test fluent builder pattern."""
        with TemporaryDirectory() as tmp:
            agent = (
                AgentBuilder()
                .with_workspace(Path(tmp))
                .with_provider(model="test/model")
                .build()
            )
            assert agent is not None
```

---

## 9. Verificações

### 9.1 Lint e Type Check

```bash
# Run linter
uv run ruff check lightagent/

# Run type checker
uv run pyright lightagent/
```

### 9.2 Checklist Pré-Commit

- [ ] Code passa `ruff check`
- [ ] Code passa `pyright`
- [ ] Tests passam (`uv run pytest tests/`)
- [ ] Novas features têm testes unitários
- [ ] Bugs corrigidos têm testes de regressão
- [ ] Sem `as any`, `@ts-ignore`, ou supressão de tipos
- [ ] Docstrings em APIs públicas
- [ ] Imports organizados
- [ ] Código verificado para duplicação
- [ ] Design OO justificado
- [ ] Respostas em idioma consistente

---

## 10. Formato de Commit

```
<type>(<scope>): <description>

Types:
- feat: Nova feature
- fix: Bug fix
- docs: Documentação
- style: Estilo de código
- refactor: Reestruturação
- test: Testes
- chore: Manutenção

Examples:
feat(agent): add new thread serialization
fix(tools): resolve memory leak in approval tool
docs(readme): update usage instructions
```

---

## 11. Push e PR

```bash
# Push branch
git push -u origin feature/my-feature

# Create PR
gh pr create --title "feat: Add my feature" --body "Description..."
```

---

## Quick Reference

```bash
# 1. Verificar código existente
rg "similar" lightagent/ --type py

# 2. Criar branch
git checkout -b feature/new-feature

# 3. Criar testes para a nova feature
#    - Adicionar em tests/<module>/
#    - Seguir padrão: test_*.py

# 4. Desenvolver (seguir convenções OO)

# 5. Testar
uv run pytest tests/ -v

# 6. Verificar
uv run ruff check lightagent/
uv run pyright lightagent/

# 7. Commitar
git add .
git commit -m "feat(scope): description"
```
