# Roadmap

## in development
- [ ] Não existe histórico append-only de alterações; a auditoria conserva apenas o estado atual e metadados da última alteração.
- [ ] implementar MFA usando aplicativo autenticador
- [ ] rate limiting distribuído por padrão.
- [ ] pouca documentação de hardening para produção
- [ ] há algumas abstrações incompletas ou não utilizadas
    - [ ] como schemas de reset de senha
    - [ ] além de mapeamento de erros baseado em análise textual das mensagens do banco.
- [x] o logout revoga apenas o refresh token; o access token permanece válido até expirar.
- [x] recuperação de senha implementada ou revogação por sessão/família.
- [x] CORS configurável
- [x] headers de segurança e configuração explícita de HTTPS, configurada diretamente no servidor
- [x] A CI não exige cobertura, não executa cobertura no pipeline e não cobre alguns cenários importantes, como revogação imediata de access token no logout e headers de segurança
- [x] Há inconsistências de porta
- [x] Descrição incorreta de secret opcional
- [x] ausência de Docker

## in concept
- [ ] O endpoint de bootstrap pode ser usado para assumir o primeiro administrador em banco vazio.