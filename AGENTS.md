# Repository Guidelines — Shootly

## O que é este projeto

Shootly é um SaaS de gestão para fotógrafos autônomos de arquitetura e
interiores no Brasil. O fotógrafo usa o sistema para gerenciar todo o
fluxo de um job: orçamento → contrato → seleção de fotos pelo cliente →
entrega → cobrança. O cliente do fotógrafo interage via portais públicos
(sem login) acessados por UUID token.

**Público-alvo (ICP):** fotógrafo autônomo, MEI ou ME, que atende
escritórios de arquitetura e construtoras, trabalha sozinho ou com um
editor parceiro, e acumula as funções de vendedor, fotógrafo, editor e
cobrador ao mesmo tempo.

**MVP — 5 features:**
1. Orçamento com templates
2. Contrato com assinatura digital própria (Lei 14.063/2020)
3. Portal de seleção de fotos pelo cliente
4. Portal de entrega com identidade visual do fotógrafo
5. Bloqueio de acesso às fotos até confirmação do pagamento

---

## Estrutura do projeto

```
core/           → settings, urls.py principal, wsgi, asgi
accounts/       → User customizado (auth por email, sem username)
plans/          → Plano e assinatura SaaS (Asaas como gateway)
clients/        → Cliente do fotógrafo
orcamentos/     → Servico (templates), Orcamento, OrcamentoItem
jobs/           → Job (máquina de estados central), ArquivoFoto
deliveries/     → Selecao, SelecaoItem, PortalEntrega
contracts/      → Contrato (assinatura própria com IP + hash SHA-256)
payments/       → Pagamento (split Asaas, gatilho manual ou webhook)
templates/      → Templates HTML base e por app
staticfiles/    → Assets coletados (não editar diretamente)
```

---

## Decisões técnicas já tomadas (não reverter sem discussão)

**Gateway de pagamento:** Asaas — único provedor pra tudo:
- Assinatura do SaaS (fotografo → Shootly)
- Split de pagamento job (cliente do fotógrafo → fotógrafo)
- Sub-conta do fotógrafo: `User.asaas_account_id` + `asaas_account_status`
- Enquanto sub-conta em aprovação: modo manual (`Pagamento.confirmado_por = "MANUAL"`)
- Quando aprovada: webhook libera automaticamente (`confirmado_por = "WEBHOOK"`)
- O endpoint `/webhooks/asaas/` substitui o `/webhooks/zouti/` que existia antes

**Assinatura digital:** implementação própria, sem provedor externo no MVP.
`Contrato.assinar()` registra nome, CPF, IP, timestamp e hash SHA-256 do
conteúdo. Válido pela Lei 14.063/2020.

**Storage de arquivos:** local (FileField/ImageField padrão do Django) no
MVP. Migração futura para Cloudflare R2 — só muda `DEFAULT_FILE_STORAGE`,
nenhum model precisa ser alterado.

**Frontend:** Django templates + HTMX para interatividade leve. Alpine.js
apenas onde HTMX não resolve (galeria de seleção de fotos no portal
público). Sem React, sem Vue, sem build step.

**Portais públicos:** acessados via `<uuid:token>` sem autenticação.
Prefixo `/p/` na URL os separa visualmente do painel autenticado.

---

## Estado atual do projeto

| Fase | Status |
|---|---|
| Models + migrations (6 apps) | ✅ concluído |
| Testes da camada de dados | ✅ concluído |
| Estrutura de URLs | ✅ concluído |
| Views — painel do fotógrafo (Fase 4) | ✅ concluído |
| Perfil da empresa + modelos de contrato (Fase 5a/5b) | 🔵 próximo |
| Marca d'água — config + aplicação Pillow (Fase 5c) | 🔵 próximo |
| Portal de seleção do cliente — Alpine.js (Fase 5d) | 🔵 próximo |
| Portal de entrega do cliente (Fase 5e) | 🔵 próximo |
| Lista de contratos no painel (Fase 5f) | 🔵 próximo |
| Integração Asaas — pagamento real (Fase 6) | ⬜ aguardando |
| Templates visuais orçamento/contrato (Fase 7) | ⬜ aguardando |
| Contratos recorrentes (Fase 8) | ⬜ aguardando |
| CRM + precificação + multi-usuário (Fase 9) | ⬜ aguardando |
| E-mails e notificações | ⬜ aguardando |
| Segurança e hardening | ⬜ aguardando |
| Deploy e produção | ⬜ aguardando |

---

## Máquina de estados do Job

O `Job.status` é a entidade central do sistema. Toda ação de negócio
muda o status. Nunca mude o status diretamente — use os métodos dos
models relacionados (ex: `Contrato.assinar()`, `Selecao.concluir()`,
`Pagamento.confirmar()`):

```
ORCAMENTO_APROVADO
  → CONTRATO_PENDENTE (quando job é criado)
  → CONTRATO_ASSINADO (via Contrato.assinar())
  → EM_PRODUCAO (fotógrafo marca manualmente)
  → AGUARDANDO_SELECAO (quando Selecao é criada)
  → SELECAO_CONCLUIDA (via Selecao.concluir())
  → EM_EDICAO (fotógrafo marca manualmente)
  → AGUARDANDO_PAGAMENTO (quando PortalEntrega é criada)
  → ENTREGUE (via Pagamento.confirmar())
  → CONCLUIDO (fotógrafo fecha o job)
```

---

## Convenções de código

- 4 espaços de indentação
- `snake_case` para funções e variáveis, `PascalCase` para classes e models
- `choices` como constantes de classe dentro do model (não como tuplas soltas)
- FK via `settings.AUTH_USER_MODEL`, nunca importando `User` diretamente
- Views thin — lógica de negócio nos métodos dos models ou em `services.py`
- URL names com namespace: `clients:list`, `jobs:detail`, etc.
- Commits no padrão Conventional Commits:
  `feat(app): descrição` / `fix(app): descrição` / `test(app): descrição`
- Todo PR deve incluir: resultado de `python manage.py check`, resultado
  de `python manage.py test`, e migration notes se models mudaram

---

## Segurança — regras obrigatórias

- **Toda view autenticada** usa `LoginRequiredMixin` (CBV) ou
  `@login_required` (FBV) — sem exceção
- **Toda query no painel** filtra por `fotografo=request.user` para
  prevenir IDOR (um fotógrafo nunca pode ver dados de outro)
- **Webhook Asaas** valida header de assinatura antes de processar
  qualquer dado — nunca confiar só no POST
- **Upload de arquivo** valida extensão, mimetype e tamanho máximo
- **Variáveis sensíveis** sempre via `.env` e `python-decouple`:
  `DJANGO_SECRET_KEY`, `ASAAS_API_KEY`, `ASAAS_WEBHOOK_SECRET`,
  `DEBUG`, credenciais de banco
- `PortalEntrega` nasce sempre com `status = "BLOQUEADO"` — nunca
  inicializar como liberado
- `link_token` sempre UUID4 — nunca expor PKs sequenciais em URLs públicas

---

## URLs — mapa completo

### Painel autenticado (LoginRequired em tudo)
```
/clientes/                          clients:list
/clientes/novo/                     clients:create
/clientes/<pk>/                     clients:detail
/clientes/<pk>/editar/              clients:edit
/clientes/<pk>/excluir/             clients:delete
/servicos/                          orcamentos:servico_list
/servicos/novo/                     orcamentos:servico_create
/servicos/<pk>/editar/              orcamentos:servico_edit
/servicos/<pk>/excluir/             orcamentos:servico_delete
/orcamentos/                        orcamentos:list
/orcamentos/novo/                   orcamentos:create
/orcamentos/<pk>/                   orcamentos:detail
/orcamentos/<pk>/editar/            orcamentos:edit
/orcamentos/<pk>/excluir/           orcamentos:delete
/orcamentos/<pk>/enviar/            orcamentos:send
/jobs/                              jobs:list
/jobs/<pk>/                         jobs:detail
/jobs/<pk>/editar/                  jobs:edit
/jobs/<pk>/contrato/gerar/          contracts:generate
/jobs/<pk>/contrato/                contracts:detail
/jobs/<pk>/fotos/                   deliveries:foto_list
/jobs/<pk>/fotos/upload/            deliveries:foto_upload
/jobs/<pk>/selecao/criar/           deliveries:selecao_create
/jobs/<pk>/entrega/criar/           deliveries:portal_create
/jobs/<pk>/pagamento/               payments:detail
/jobs/<pk>/pagamento/criar/         payments:create
/jobs/<pk>/pagamento/confirmar/     payments:confirm_manual
/jobs/<pk>/status/                  jobs:status_update
/fotos/<foto_pk>/delete/            deliveries:foto_delete
/contratos/                         contracts:list
/configuracoes/perfil/              accounts:perfil
/configuracoes/marca-dagua/         accounts:marca_dagua
/configuracoes/modelos-contrato/              contracts:modelo_list
/configuracoes/modelos-contrato/novo/         contracts:modelo_create
/configuracoes/modelos-contrato/<pk>/editar/  contracts:modelo_edit
/configuracoes/modelos-contrato/<pk>/excluir/ contracts:modelo_delete
```

### Portais públicos (sem login, via UUID token)
```
/p/orcamento/<token>/               orcamentos:public_view
/p/orcamento/<token>/aprovar/       orcamentos:public_approve
/p/orcamento/<token>/recusar/       orcamentos:public_reject
/p/contrato/<token>/                contracts:public_view
/p/contrato/<token>/assinar/        contracts:public_sign
/p/selecao/<token>/                 deliveries:public_selecao
/p/entrega/<token>/                 deliveries:public_portal
```

### Webhooks
```
/webhooks/asaas/                    payments:webhook_asaas (csrf_exempt)
/webhooks/zouti/                    plans:zouti_webhook (existente, assinatura SaaS)
```

---

## PRDs disponíveis

Os documentos abaixo descrevem o que já foi implementado e como. Consulte
antes de alterar qualquer área coberta por eles:

- `docs/prd/shootly-prd-fases.md` — models e migrations (Fases 0-8)
- `docs/prd/shootly-prd-testes.md` — testes da camada de dados (Fases 0-9)
- `docs/prd/shootly-prd-urls.md` — estrutura de URLs (Fases 0-8)

---

## Comandos úteis

```bash
# Ambiente
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Mac/Linux
pip install -r requirements.txt

# Desenvolvimento
python manage.py migrate
python manage.py runserver      # http://127.0.0.1:8000

# Qualidade
python manage.py check          # obrigatório antes de qualquer commit
python manage.py test           # rodar todos os testes
python manage.py check --deploy # checagem de segurança (antes do deploy)

# Migrations
python manage.py makemigrations <app>
python manage.py showmigrations

# Verificar URLs
python manage.py shell -c "from django.urls import reverse; print(reverse('jobs:list'))"
```

---

## Gaps de segurança conhecidos (a corrigir na Fase 11)

- `Contrato.assinar()` permite ser chamado duas vezes, sobrescrevendo a
  assinatura original sem erro (documentado no teste
  `test_assinar_called_twice_currently_overwrites_without_warning`)
- `Pagamento.confirmar()` não trava contra dupla confirmação
- Views ainda usam `TemplateView` placeholder — `LoginRequiredMixin`
  será adicionado quando as views reais forem escritas (Fase 4)
- Webhook Asaas aceita qualquer POST enquanto for placeholder —
  validação de assinatura entra na Fase 8

---

## O que NÃO fazer

- Não criar views sem `LoginRequiredMixin` no painel autenticado
- Não expor PKs sequenciais em URLs de portais públicos (usar `link_token`)
- Não hardcodar API keys ou secrets no código
- Não alterar o `Job.status` diretamente — usar os métodos dos models
- Não criar nova URL sem adicioná-la ao mapa acima
- Não instalar biblioteca de frontend pesada (React, Vue, Webpack)
- Não migrar storage sem testar localmente primeiro