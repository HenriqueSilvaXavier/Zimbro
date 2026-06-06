# Zimbro — Biblioteca Oficial de Testes do Absinto

Zimbro é a biblioteca oficial de testes do Absinto. Ela testa relações causais, estados de entidades, invariantes e propagação. Não testa funções nem implementação.

## Filosofia

Zimbro segue a filosofia do Absinto: o programador declara intenção e comportamento, não implementação.

- **Testa relações causais**: "Does this action cause that effect?"
- **Testa estados de entidades**: "Is the entity in the expected state?"
- **Testa invariantes**: "Does this invariant hold?"
- **Testa propagação**: "Does causal propagation work correctly?"

**NÃO testa**:
- Funções
- Implementação interna
- Detalhes de código

Um teste que quebra por refatoração interna mas comportamento correto é um teste mal escrito em Zimbro.

## Sintaxe

### Teste Básico

```zim
suite OrderProcessing:
    test "Order creation causes Payment processing":
        simulate
        
        causes Order.created causes Payment.processed
        within 5s
        
        assert Order.status == "pending"
        assert Payment.status == "pending"
```

### Operadores Causais

#### causes
Testa que um evento causa outro.

```zim
causes Order.created causes Payment.processed
```

#### prevents
Testa que um evento previne outro.

```zim
prevents Customer.banned prevents Order.created
```

#### requires
Testa que um evento requer outro.

```zim
requires Payment.processed requires Order.confirmed
```

#### precedes
Testa que um evento precede outro temporalmente.

```zim
precedes Order.confirmed precedes Payment.processed
```

#### never
Testa que um evento nunca causa outro.

```zim
never Order.cancelled causes Payment.processed
```

### Modificadores

#### within
Restrição de tempo.

```zim
causes Order.created causes Payment.processed
    within 5s
```

#### always
Sempre verdade.

```zim
causes Customer.active causes Order.created
    always
```

#### eventually
Eventualmente verdade (com timeout opcional).

```zim
causes Payment.confirmed causes Fulfillment.started
    eventually 10s
```

#### given
Precondição.

```zim
causes Order.created causes Payment.processed
    given Customer.active == true
```

### Mocks

Mocks em Zimbro falam a língua causal do Absinto.

```zim
mock DatabaseCapability:
    when called_with(query: "SELECT * FROM orders")
        then_causes Order.loaded
        then_returns mock_orders

mock PaymentCapability:
    when called_with(amount: > 0)
        then_causes Payment.processed
        then_returns {status: "success"}

mock auth.login:
    when called_with(email: "test@example.com")
        then_causes Customer.authenticated
        then_returns {token: "mock_token"}
```

### Suites e Hooks

```zim
suite OrderProcessing:
    before:
        # Setup compartilhado
        mock DatabaseCapability:
            then_returns mock_db
    
    after:
        # Cleanup compartilhado
        clear_mocks()
    
    beforeEach:
        # Setup antes de cada teste
        reset_entity_states()
    
    afterEach:
        # Cleanup depois de cada teste
        clear_causal_graph()
    
    test "Order creation":
        causes Order.created causes Payment.processed
    
    test "Order cancellation":
        prevents Order.cancelled prevents Payment.processed
```

### Testes Assíncronos

```zim
async test "Async order processing":
    simulate
    
    await Order.create(customer_id: 1, total: 100)
    
    causes Order.created causes Payment.processed
    eventually 10s
    
    assert Order.status == "pending"
```

### Testes Parametrizados

```zim
parametrize "Order status transitions":
    parameters: [status, expected_next]
    cases: [
        {status: "pending", expected_next: "confirmed"},
        {status: "confirmed", expected_next: "processing"},
        {status: "processing", expected_next: "shipped"},
    ]
    
    causes Order.status == status causes Order.status == expected_next
```

### Snapshot Testing

```zim
test "Order entity snapshot":
    snapshot Order.to_dict() as "order_snapshot"
```

### Modos de Execução

#### simulate
Modo padrão. Simula a execução sem efeitos colaterais.

```zim
test "Order creation":
    simulate
    causes Order.created causes Payment.processed
```

#### replay
Replay de eventos gravados.

```zim
test "Order creation replay":
    replay from "order_creation_events.json"
    causes Order.created causes Payment.processed
```

#### continuous
Execução contínua para monitoramento.

```zim
test "Order creation continuous":
    continuous
    causes Order.created causes Payment.processed
    always
```

### Assertions

```zim
assert Order.status == "pending"
assert Payment.amount == 100.00
assert Customer.email == "test@example.com"
assert invariant NoPaymentWithoutOrder holds
assert propagation Order.status.cancelled to Payment.status.cancelled
```

## Execução

### Linha de Comando

```bash
# Executar todos os testes
zimbro run

# Executar com padrão específico
zimbro run --pattern "*.test.zim"

# Executar em paralelo
zimbro run --parallel --workers 4

# Executar com coverage
zimbro run --coverage

# Executar em watch mode
zimbro run --watch

# Filtrar por tags
zimbro run --tags integration

# Filtrar por nome
zimbro run --name "Order*"

# Modo verbose
zimbro run --verbose

# Timeout customizado
zimbro run --timeout 10s

# Modo de execução
zimbro run --mode simulate
zimbro run --mode replay
zimbro run --mode continuous
```

### Python API

```python
from zimbro import ZimbroRunner, create_runner

# Criar runner com configuração
runner = create_runner(
    pattern="*.zim",
    parallel=True,
    workers=4,
    coverage=True,
    watch=False,
    verbose=True,
    timeout=5.0,
    mode="simulate",
    tags=["integration"],
    names=["Order*"]
)

# Executar testes
exit_code = runner.run(test_dir=".")

# Watch mode
runner.watch(test_dir=".")

# Coverage
runner.coverage(test_dir=".")
```

## Exemplos Completos

### Exemplo 1: Teste de Causalidade Básico

```zim
suite BasicCausality:
    test "Customer active causes order creation":
        simulate
        
        given Customer.active == true
        causes Customer.active causes Order.created
        within 5s
        
        assert Order.customer_id == customer.id
```

### Exemplo 2: Teste de Invariante

```zim
suite InvariantTests:
    test "No payment without order":
        simulate
        
        never Payment.created before Order.confirmed
        assert invariant NoPaymentWithoutOrder holds
```

### Exemplo 3: Teste de Propagação

```zim
suite PropagationTests:
    test "Status cancellation propagates":
        simulate
        
        mock Order:
            when status == "cancelled"
                then_causes Payment.status == "cancelled"
                then_causes Fulfillment.status == "cancelled"
        
        causes Order.status == "cancelled" causes Payment.status == "cancelled"
        causes Order.status == "cancelled" causes Fulfillment.status == "cancelled"
        
        assert propagation Order.status.cancelled to [Payment, Fulfillment]
```

### Exemplo 4: Teste com Mocks

```zim
suite MockTests:
    test "Payment with mocked gateway":
        simulate
        
        mock PaymentGateway:
            when called_with(amount: > 0)
                then_causes Payment.processed
                then_returns {status: "success", transaction_id: "txn_123"}
        
        causes PaymentGateway.process(amount: 100) causes Payment.processed
        assert Payment.status == "success"
        assert Payment.transaction_id == "txn_123"
```

### Exemplo 5: Teste Assíncrono

```zim
suite AsyncTests:
    async test "Async order processing":
        simulate
        
        await Customer.create(email: "test@example.com")
        await Order.create(customer_id: customer.id, total: 100)
        
        causes Order.created causes Payment.processed
        eventually 10s
        
        assert Order.status == "pending"
        assert Payment.status == "pending"
```

### Exemplo 6: Teste Parametrizado

```zim
suite ParametrizedTests:
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

### Exemplo 7: Suite Completa com Hooks

```zim
suite CompleteOrderFlow:
    before:
        mock DatabaseCapability:
            then_returns mock_db
        mock PaymentGateway:
            then_returns {status: "success"}
    
    after:
        clear_mocks()
        clear_causal_graph()
    
    beforeEach:
        reset_entity_states()
        create_test_customer()
    
    afterEach:
        cleanup_test_data()
    
    test "Order creation flow":
        simulate
        
        causes Customer.active causes Order.created
        causes Order.created causes Payment.processed
        causes Payment.processed causes Fulfillment.started
        
        assert Order.status == "pending"
        assert Payment.status == "pending"
        assert Fulfillment.status == "pending"
    
    test "Order cancellation flow":
        simulate
        
        prevents Order.cancelled prevents Payment.processed
        causes Order.cancelled causes Payment.refunded
        
        assert Order.status == "cancelled"
        assert Payment.status == "refunded"
```

## Decisões de Design

### Por que mocks falam a língua causal?

Mocks em Zimbro não são mocks de função JavaScript/Python. Eles falam a língua causal do Absinto porque:

1. **Coerência com a filosofia**: Absinto é sobre causalidade, não sobre chamadas de função
2. **Testa comportamento, não implementação**: Mock causal declara efeito causal, não retorno de função
3. **Integração com o grafo causal**: Mocks causais se integram naturalmente com o grafo causal do Absinto

Exemplo:

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

### Por que três modos de execução?

1. **simulate**: Modo padrão para testes unitários. Simula execução sem efeitos colaterais.
2. **replay**: Para testes de integração que precisam replay de eventos reais.
3. **continuous**: Para monitoramento contínuo em produção.

### Por que testes parametrizados?

Testes parametrizados permitem testar o mesmo comportamento com diferentes inputs sem duplicar código. Isso é especialmente útil para transições de estado, validações de input, etc.

### Por que snapshot testing?

Snapshot testing permite verificar que a estrutura de dados não muda inesperadamente. Útil para APIs, entidades complexas, etc.

## Integração com Absinto

Zimbro se integra com o sistema causal do Absinto:

- Usa o `CausalGraph` para rastrear relações causais
- Usa o `CausalEngine` para validar causalidade
- Usa o sistema de entidades para consultar estados
- Usa invariantes declarados no código Absinto

## Paridade com Jest/Pytest

Zimbro oferece paridade funcional com Jest e Pytest:

| Feature | Jest/Pytest | Zimbro |
|---------|-------------|--------|
| Test runner | ✓ | ✓ |
| Suite grouping | describe/test | suite/test |
| Lifecycle hooks | before/after/beforeEach/afterEach | before/after/beforeEach/afterEach |
| Assertions | expect/assert | assert |
| Async tests | async/await | async/await |
| Parametrized tests | test.each | parametrize |
| Snapshot testing | toMatchSnapshot | snapshot |
| Coverage | --coverage | --coverage |
| Watch mode | --watch | --watch |
| Parallel tests | --maxWorkers | --parallel --workers |
| Filtering | --testNamePattern | --name, --tags |
| Verbose output | --verbose | --verbose |

Mas tudo reexpresso na sintaxe e filosofia do Absinto.

## Conclusão

Zimbro é a biblioteca oficial de testes do Absinto. Ela testa relações causais, estados de entidades, invariantes e propagação. Não testa funções nem implementação.

Mocks em Zimbro falam a língua causal do Absinto, não parecem mocks de JavaScript/Python.

Zimbro oferece paridade com Jest/Pytest, mas tudo reexpresso na sintaxe e filosofia do Absinto.
