# Heartbeat Tasks

This file is checked every 30 minutes by your lightagent agent.
Use it for recurring tasks that need periodic attention.

## Active Tasks

<!-- Adicione suas tarefas periódicas abaixo -->

## Completed

<!-- Mova tarefas concluídas para cá ou delete-as -->

## Exemplos de Tarefas

### Monitoramento
- [ ] Check system health: `uptime`, `df -h`
- [ ] Verificar serviços críticos: `systemctl --type=service --state=running`

### Revisão Diária
- [ ] Review application logs for errors
- [ ] Check disk usage: `df -h && du -sh /var/*`

### Lembretes
- [ ] Backup database (daily at 2AM)
- [ ] Review pending PRs

## Como Gerenciar

- **Adicionar**: Use `edit_file` para append novas tarefas
- **Remover**: Use `edit_file` para remover tarefas concluídas
- **Reescrever**: Use `write_file` para reescrever toda a lista

Mantenha o arquivo pequeno para minimizar uso de tokens.

