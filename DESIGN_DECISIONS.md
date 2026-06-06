# Zimbro — Decisões de Design

Este documento documenta as decisões de design tomadas durante a criação do Zimbro.

## 1. Por que mocks falam a língua causal?

**Decisão**: Mocks em Zimbro falam a língua causal do Absinto, não parecem mocks de função JavaScript/Python.

**Justificativa**:

1. **Coerência com a filosofia do Absinto**: Absinto é sobre causalidade, não sobre chamadas de função. Mocks devem refletir isso.

2. **Testa comportamento, não implementação**: Mock causal declara efeito causal, não retorno de função. Isso alinha com a filosofia de Zimbro de testar relações causais, não implementação.

3. **Integração com o grafo causal**: Mocks causais se integram naturalmente com o grafo causal do Absinto. Eles podem registrar efeitos causais que são rastreados pelo grafo.

**Exemplo**:

```zim
# ❌ Mock de função (não-Zimbro)
mock PaymentGateway.process:
    returns {status: "success"}

# ✅ Mock causal (Zimbro)
mock PaymentGateway:
    when called_with(amount: > 0)
        then_causes Payment.processed
        then_returns {status: "success"}
```

## 2. Por que três modos de execução?

**Decisão**: Zimbro suporta três modos de execução: simulate, replay, continuous.

**Justificativa**:

1. **simulate**: Modo padrão para testes unitários. Simula execução sem efeitos colaterais. Ideal para testes rápidos e isolados.

2. **replay**: Para testes de integração que precisam replay de eventos reais. Permite testar com dados reais de produção em ambiente de teste.

3. **continuous**: Para monitoramento contínuo em produção. Permite validar que invariantes e relações causais continuam válidas em tempo real.

**Exemplo**:

```zim
# Simulate mode
test "Order creation":
    simulate
    causes Order.created causes Payment.processed

# Replay mode
test "Order creation replay":
    replay from "order_creation_events.json"
    causes Order.created causes Payment.processed

# Continuous mode
test "Order creation continuous":
    continuous
    causes Order.created causes Payment.processed
    always
```

## 3. Por que testes parametrizados?

**Decisão**: Zimbro suporta testes parametrizados com múltiplos casos.

**Justificativa**:

1. **Evita duplicação**: Permite testar o mesmo comportamento com diferentes inputs sem duplicar código.

2. **Legibilidade**: Torna claro que os testes estão testando o mesmo comportamento com diferentes parâmetros.

3. **Manutenção**: Facilita manutenção - mudanças no teste se aplicam a todos os casos.

**Exemplo**:

```zim
parametrize "Status transitions":
    parameters: [from_status, to_status]
    cases: [
        {from_status: "pending", to_status: "confirmed"},
        {from_status: "confirmed", to_status: "processing"},
        {from_status: "processing", to_status: "shipped"},
        {from_status: "shipped", to_status: "delivered"},
    ]
    
    causes Order.status == from_status causes Order.status == to_status
    within 2s
```

## 4. Por que snapshot testing?

**Decisão**: Zimbro suporta snapshot testing para entidades e estruturas de dados.

**Justificativa**:

1. **Detecta mudanças inesperadas**: Permite detectar mudanças na estrutura de dados que não foram intencionais.

2. **Útil para APIs**: Ideal para testar respostas de API que devem permanecer consistentes.

3. **Integração com entidades**: Funciona naturalmente com o sistema de entidades do Absinto.

**Exemplo**:

```zim
test "Order entity snapshot":
    snapshot Order.to_dict() as "order_snapshot"
```

## 5. Por que modificadores causais?

**Decisão**: Zimbro suporta modificadores causais: within, always, eventually, given.

**Justificativa**:

1. **Expressividade**: Permite expressar restrições temporais e condicionais de forma declarativa.

2. **Coerência com Absinto**: Modificadores seguem a mesma filosofia declarativa do Absinto.

3. **Flexibilidade**: Permite testar diferentes aspectos de relações causais (tempo, persistência, precondições).

**Exemplo**:

```zim
causes Order.created causes Payment.processed
    within 5s
    given Customer.active == true
```

## 6. Por que não testar funções?

**Decisão**: Zimbro não testa funções nem implementação. Testa relações causais, estados de entidades, invariantes e propagação.

**Justificativa**:

1. **Coerência com Absinto**: Absinto é sobre declaração de intenção e comportamento, não implementação.

2. **Testes mais robustos**: Testes que testam comportamento em vez de implementação são menos propensos a quebrar com refatoração.

3. **Foco no que importa**: O que importa é se o sistema se comporta corretamente, não como ele é implementado internamente.

**Exemplo**:

```zim
# ❌ Testar função (não-Zimbro)
test "calculate_total returns correct value":
    assert calculate_total(items) == 100.00

# ✅ Testar comportamento causal (Zimbro)
test "Order total calculation":
    causes Order.items_added causes Order.total == expected_total
```

## 7. Por que hooks de lifecycle?

**Decisão**: Zimbro suporta hooks de lifecycle: before, after, beforeEach, afterEach.

**Justificativa**:

1. **Paridade com Jest/Pytest**: Oferece as mesmas capacidades de setup/teardown.

2. **Organização**: Permite organizar setup e teardown de forma clara.

3. **Reutilização**: Permite reutilizar setup/teardown entre testes.

**Exemplo**:

```zim
suite OrderProcessing:
    before:
        mock DatabaseCapability:
            then_returns mock_db
    
    after:
        clear_mocks()
    
    beforeEach:
        reset_entity_states()
    
    afterEach:
        cleanup_test_data()
```

## 8. Por que filtragem por tags e nomes?

**Decisão**: Zimbro suporta filtragem de testes por tags e padrões de nome.

**Justificativa**:

1. **Organização**: Permite organizar testes em categorias (unit, integration, e2e).

2. **Execução seletiva**: Permite executar apenas testes relevantes para o contexto.

3. **Paridade com Jest/Pytest**: Oferece as mesmas capacidades de filtragem.

**Exemplo**:

```bash
zimbro run --tags integration
zimbro run --name "Order*"
```

## 9. Por que paralelismo?

**Decisão**: Zimbro suporta execução paralela de testes.

**Justificativa**:

1. **Performance**: Permite executar testes mais rápido em máquinas multi-core.

2. **Escalabilidade**: Permite escalar execução de testes em grandes suites.

3. **Paridade com Jest/Pytest**: Oferece as mesmas capacidades de paralelismo.

**Exemplo**:

```bash
zimbro run --parallel --workers 4
```

## 10. Por que watch mode?

**Decisão**: Zimbro suporta watch mode para re-execução automática de testes.

**Justificativa**:

1. **Productivity**: Permite desenvolvimento iterativo rápido.

2. **Feedback imediato**: Fornece feedback imediato quando código muda.

3. **Paridade com Jest/Pytest**: Oferece as mesmas capacidades de watch mode.

**Exemplo**:

```bash
zimbro run --watch
```

## Conclusão

Todas as decisões de design do Zimbro foram tomadas para:

1. Manter coerência com a filosofia do Absinto
2. Oferecer paridade funcional com Jest/Pytest
3. Focar em testar comportamento causal, não implementação
4. Ser expressivo e declarativo

Zimbro não é Jest ou Pytest com outro nome. É uma biblioteca de testes que fala a língua do Absinto.
