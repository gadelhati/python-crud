# Roadmap

## in development
- [x] o logout revoga apenas o refresh token; o access token permanece válido até expirar.
- [ ] implementar MFA usando aplicativo autenticador
- [ ] recuperação de senha implementada ou revogação por sessão/família.
- [x] CORS configurável
- [x] headers de segurança e configuração explícita de HTTPS, configurada diretamente no servidor
- [ ] rate limiting distribuído por padrão.
- [ ] há algumas abstrações incompletas ou não utilizadas
    - [ ] como schemas de reset de senha
    - [ ] além de mapeamento de erros baseado em análise textual das mensagens do banco.
- [ ] Não existe histórico append-only de alterações; a auditoria conserva apenas o estado atual e metadados da última alteração.
- [x] A CI não exige cobertura, não executa cobertura no pipeline e não cobre alguns cenários importantes, como revogação imediata de access token no logout e headers de segurança
- [x] Há inconsistências de porta
- [ ] Descrição incorreta de secret opcional
- [ ] ausência de Docker
- [ ] pouca documentação de hardening para produção

## in concept
- [ ] O endpoint de bootstrap pode ser usado para assumir o primeiro administrador em banco vazio.