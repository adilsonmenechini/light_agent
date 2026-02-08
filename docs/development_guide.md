# Development Guide

Guide for contributing new features to Light Agent without frameworks.

---

## 1. Antes de Começar

### 1.1 Verificar Código Existente

**Sempre verifique se já existe código similar:**

```bash
# Buscar funcionalidade similar
rg "similar_function_name" light_agent/ --type py

# Verificar se módulo já existe
rg "from light_agent.agent" light_agent/ --type py | head -20

# Verificar ferramentas similares
rg "class.*Tool" light_agent/agent/tools/ --type py

# Verificar dataclasses/models similares
rg "class.*State|class.*Model" light_agent/ --type py

# Verificar funções utilitárias
rg "^def " light_agent/utils/ --type py

# Verificar arquivos existentes
fd "my_feature" light_agent/
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
light_agent/agent/
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
from light_agent.agent.observer import AgentObserver, AgentSubject, AgentEvent, AgentEventType

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
from light_agent.agent.base import Tool
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
from light_agent.agent.tools.base import Tool
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

```python
import pytest

class TestMyFeature:
    def test_basic_functionality(self):
        result = my_function("input")
        assert result == "expected"

    async def test_async_functionality(self):
        result = await async_function()
        assert result is not None
```

---

## 9. Verificações

### 9.1 Lint e Type Check

```bash
# Run linter
uv run ruff check light_agent/

# Run type checker
uv run pyright light_agent/
```

### 9.2 Checklist Pré-Commit

- [ ] Code passa `ruff check`
- [ ] Code passa `pyright`
- [ ] Tests passam (`pytest`)
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
rg "similar" light_agent/ --type py

# 2. Criar branch
git checkout -b feature/new-feature

# 3. Desenvolver (seguir convenções OO)

# 4. Testar
pytest light_agent/

# 5. Verificar
uv run ruff check light_agent/
uv run pyright light_agent/

# 6. Commitar
git add .
git commit -m "feat(scope): description"
```
