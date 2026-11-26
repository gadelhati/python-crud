# Production Hardening

**Projeto:** Python CRUD  
**Arquivo:** `docs/PRODUCTION_HARDENING.md`  
**Objetivo:** estabelecer os requisitos de segurança específicos para implantação e operação do Python CRUD em produção.

## 1. Premissas de infraestrutura

A aplicação será implantada em um servidor previamente configurado conforme o padrão definido no repositório [basic-configuration/devops](https://github.com/gadelhati/basic-configuration/tree/main/devops).

Este documento não reproduz os procedimentos de hardening do sistema operacional e da infraestrutura. Considera que esses controles são tratados pelo padrão de referência.

O Python CRUD deve respeitar essa configuração e não introduzir exposição adicional de serviços, privilégios ou portas.

## 2. Configuração da aplicação

- [ ] Executar com configuração de produção, sem modo de debug.
- [ ] Utilizar variáveis de ambiente para configurações sensíveis.
- [ ] Não versionar arquivos `.env`, credenciais ou chaves privadas.
- [ ] Utilizar segredos JWT fortes, exclusivos e independentes.
- [ ] Restringir permissões de leitura dos arquivos de configuração.
- [ ] Não expor stack traces, caminhos internos ou informações sensíveis nas respostas.
- [ ] Desabilitar ou proteger Swagger, ReDoc e OpenAPI conforme a necessidade operacional.

## 3. Autenticação e autorização

- [ ] Utilizar armazenamento seguro de senhas, com algoritmo apropriado e salt individual.
- [ ] Validar assinatura, expiração, tipo e claims obrigatórios dos JWTs.
- [ ] Manter access token e refresh token com finalidades distintas.
- [ ] Verificar revogação dos tokens.
- [ ] Validar `auth_version` em todas as rotas protegidas.
- [ ] Invalidar sessões anteriores após redefinição de senha.
- [ ] Aplicar princípio do menor privilégio.
- [ ] Validar permissões no backend em todas as operações protegidas.
- [ ] Impedir elevação indevida de privilégios e delegação de permissões não autorizadas.
- [ ] Restringir e auditar o procedimento de bootstrap administrativo.

## 4. Recuperação de senha e proteção contra abuso

- [ ] Utilizar tokens aleatórios, armazenando somente seus hashes.
- [ ] Garantir validade limitada e utilização única dos tokens.
- [ ] Utilizar HTTPS nos links de recuperação.
- [ ] Retornar respostas genéricas para evitar enumeração de contas.
- [ ] Não registrar tokens ou links de recuperação nos logs.
- [ ] Utilizar SMTP autenticado e transporte seguro.
- [ ] Aplicar rate limiting em login, refresh, recuperação de senha e bootstrap.
- [ ] Utilizar armazenamento compartilhado para rate limiting quando houver múltiplas instâncias.

## 5. Comunicação e exposição da API

- [ ] Utilizar HTTPS em todas as comunicações externas.
- [ ] Restringir o acesso direto à porta interna da aplicação.
- [ ] Permitir somente origens CORS explicitamente autorizadas.
- [ ] Restringir métodos e headers conforme a necessidade da API.
- [ ] Configurar corretamente os headers encaminhados pelo reverse proxy.
- [ ] Confiar em informações `X-Forwarded-*` somente de proxies autorizados.
- [ ] Avaliar headers de segurança HTTP e limites de requisição.
- [ ] Avaliar proteção CSRF quando a autenticação utilizar cookies enviados automaticamente pelo navegador.

A terminação TLS, firewall e exposição de portas devem seguir o padrão de infraestrutura adotado.

## 6. Banco de dados

- [ ] Utilizar PostgreSQL com credenciais exclusivas para a aplicação.
- [ ] Não utilizar usuário superuser para as operações da API.
- [ ] Restringir conexões ao banco à rede e aos serviços autorizados.
- [ ] Não expor a porta do PostgreSQL publicamente.
- [ ] Utilizar transações nas operações que exigem atomicidade.
- [ ] Manter constraints, foreign keys e índices adequados.
- [ ] Utilizar Alembic para controlar alterações de estrutura.
- [ ] Revisar migrações antes de executá-las em produção.
- [ ] Não utilizar `create_all()` como substituto das migrações.
- [ ] Realizar backup antes de alterações estruturais relevantes.
- [ ] Testar periodicamente a restauração dos backups.

## 7. Containers e implantação

Quando utilizado Docker:

- [ ] Utilizar imagens com versões fixadas.
- [ ] Executar a aplicação com usuário não privilegiado.
- [ ] Não utilizar `privileged: true`.
- [ ] Não incluir segredos nas imagens.
- [ ] Não copiar arquivos `.env` para a imagem.
- [ ] Restringir portas publicadas e utilizar redes internas.
- [ ] Definir limites de CPU e memória.
- [ ] Manter imagens e dependências atualizadas.
- [ ] Avaliar vulnerabilidades das imagens utilizadas.

A configuração do sistema operacional, Docker Engine e serviços de infraestrutura permanece sob responsabilidade do padrão `basic-configuration`.

## 8. Logs, auditoria e monitoramento

- [ ] Registrar eventos de autenticação e autorização.
- [ ] Registrar operações administrativas e alterações relevantes.
- [ ] Registrar erros e falhas operacionais sem expor informações sensíveis.
- [ ] Não registrar senhas, JWTs, tokens de recuperação ou credenciais.
- [ ] Monitorar disponibilidade, erros HTTP, conexões com o banco e falhas de envio de e-mail.
- [ ] Proteger os registros contra alteração e exclusão indevidas.

**Auditoria:** o registro do estado atual e dos metadados da última alteração não equivale a um histórico completo. Caso seja necessário rastreamento histórico confiável, implementar auditoria append-only, com controle de acesso e proteção contra adulteração.

## 9. Dependências e qualidade

Antes de cada release:

- [ ] Executar Ruff.
- [ ] Executar testes unitários e de integração.
- [ ] Executar testes de segurança.
- [ ] Verificar vulnerabilidades nas dependências.
- [ ] Revisar alterações de autenticação e autorização.
- [ ] Revisar migrações Alembic.
- [ ] Verificar ausência de segredos no repositório.

Comandos de referência:

```bash
ruff check .
pytest -v
pip-audit
```

## 10. Checklist de liberação

A implantação somente deve ser autorizada após a validação dos requisitos obrigatórios.

| Verificação | Critério |
|---|---|
| Configuração | Segredos e variáveis de produção definidos |
| Autenticação | JWT e refresh token validados |
| Sessões | Revogação e invalidação funcionando |
| Autorização | Privilégios e permissões validados |
| Recuperação | Tokens temporários e de uso único |
| Rate limiting | Endpoints sensíveis protegidos |
| CORS | Origens explicitamente autorizadas |
| HTTPS | Comunicação externa protegida |
| PostgreSQL | Acesso restrito e credenciais exclusivas |
| Migrações | Alembic validado |
| Backup | Restauração testada |
| Logs | Ausência de credenciais e tokens |
| Testes | Suíte automatizada aprovada |
| Containers | Execução com privilégios mínimos, quando aplicável |

## 11. Revisão periódica

Revisar periodicamente:

- Vulnerabilidades nas dependências.
- Usuários e privilégios administrativos.
- Configurações CORS e autenticação.
- Segredos e credenciais.
- Registros de auditoria.
- Integridade e restauração dos backups.
- Configurações de implantação.

Mudanças na infraestrutura devem continuar sendo tratadas pelo padrão [basic-configuration/devops](https://github.com/gadelhati/basic-configuration/tree/main/devops).

---

**Controle do documento**

| Campo | Valor |
|---|---|
| Documento | Production Hardening |
| Projeto | Python CRUD |
| Revisão | Inicial |
| Status | Proposta para validação |
| Referência de infraestrutura | `basic-configuration/devops` |