# Referencial de Requisitos Não Funcionais para Testes de Aplicações Web

## 1. Desempenho e eficiência
RNF-001 — Tempo de resposta da aplicação

As operações da aplicação devem apresentar tempos de resposta compatíveis com os limites estabelecidos para cada funcionalidade, considerando condições normais de utilização.
- APIs: tempo de resposta máximo de 2 segundos para operações convencionais.
- Consultas complexas e operações de processamento devem possuir limites específicos.
- A medição deve considerar, preferencialmente, o percentil 95 (p95), evitando que médias ocultem requisições lentas.
Testes: integração e desempenho.

RNF-002 — Desempenho de carregamento das páginas

A aplicação web deve atender aos seguintes indicadores Core Web Vitals:
Indicador	Critério de aceitação
LCP — carregamento do conteúdo principal	≤ 2,5 s
INP — resposta às interações	≤ 200 ms
CLS — estabilidade visual	≤ 0,1

Os indicadores devem ser avaliados no percentil 75, separando dispositivos móveis e desktops. 
Google for Developers+1


Testes: desempenho e interface (E2E).

RNF-003 — Capacidade de processamento

A aplicação deve suportar uma carga de utilização simultânea definida conforme a capacidade operacional esperada, mantendo os limites de tempo de resposta estabelecidos.
- Definir quantidade de usuários simultâneos.
- Definir taxa esperada de requisições por segundo.
- Avaliar comportamento em condições de pico.
- Identificar degradação progressiva e pontos de saturação.
Testes: carga, estresse e escalabilidade.

RNF-004 — Gerenciamento de recursos

O consumo de recursos computacionais deve permanecer dentro dos limites definidos para o ambiente de execução.
- Monitorar utilização de memória RAM.
- Monitorar utilização de CPU.
- Identificar vazamentos de memória.
- Verificar encerramento adequado de conexões e recursos.
- Avaliar comportamento sob carga prolongada.
Testes: desempenho, integração e estresse.

## 2. Segurança e privacidade
RNF-005 — Armazenamento seguro de credenciais

As senhas devem ser armazenadas utilizando algoritmos específicos para derivação de hash de senhas, com salt individual e parâmetros de custo adequados.
- Não permitir armazenamento de senhas em texto puro.
- Não utilizar SHA-256 isoladamente para armazenamento de senhas.
- Priorizar Argon2id, bcrypt ou PBKDF2, conforme a política de segurança adotada.
- Garantir que a verificação de credenciais não exponha informações sensíveis.
Testes: unitários e integração. 
OWASP Cheat Sheet Series


RNF-006 — Segurança das comunicações

Todas as comunicações externas que transportem informações sensíveis devem utilizar HTTPS com configuração TLS segura.
- Rejeitar conexões inseguras quando HTTPS for obrigatório.
- Verificar validade dos certificados.
- Impedir transmissão de credenciais em conexões HTTP.
- Verificar redirecionamento HTTP para HTTPS.
Testes: integração e segurança.

RNF-007 — Autenticação e gerenciamento de sessão

O mecanismo de autenticação deve garantir a integridade, confidencialidade e validade das sessões dos usuários.
- Impedir acesso a recursos protegidos sem autenticação.
- Invalidar sessões após logout.
- Controlar expiração de sessões.
- Impedir reutilização de sessões inválidas ou expiradas.
- Evitar exposição de tokens em URLs.
- Quando utilizados cookies para autenticação, verificar as configurações HttpOnly, Secure e SameSite adequadas ao fluxo de autenticação.
Testes: unitários e integração.

RNF-008 — Controle de acesso

A aplicação deve implementar controle de acesso baseado em papéis e permissões (RBAC), garantindo que cada usuário acesse somente os recursos autorizados.
- Impedir acesso não autorizado a endpoints.
- Impedir operações incompatíveis com as permissões do usuário.
- Verificar autorização tanto na interface quanto no servidor.
- Impedir acesso indevido a registros pertencentes a outros usuários, quando aplicável.
- Garantir que a alteração de papéis e permissões produza efeito conforme a política de sessão definida.
Testes: unitários e integração.

RNF-009 — Proteção contra vulnerabilidades web

A aplicação deve implementar mecanismos de proteção contra vulnerabilidades comuns em aplicações web, considerando as recomendações OWASP.

Devem ser contempladas, no mínimo:
- SQL Injection (SQLi).
- Cross-Site Scripting (XSS).
- Cross-Site Request Forgery (CSRF).
- Insecure Direct Object Reference (IDOR).
- Falhas de autenticação e autorização.
- Exposição indevida de informações.
- Manipulação de parâmetros e dados de entrada.
Testes: integração e segurança.

RNF-010 — Proteção contra requisições abusivas

Endpoints públicos e sensíveis devem implementar mecanismos de limitação de requisições (Rate Limiting).
- Definir limites específicos para autenticação e recuperação de senha.
- Aplicar limites por endereço IP, usuário ou outro identificador apropriado.
- Retornar HTTP 429 quando o limite estabelecido for excedido.
- Garantir que a limitação seja aplicada de maneira consistente.
Testes: integração e segurança.

RNF-011 — Cabeçalhos de segurança HTTP

O servidor web deve fornecer os cabeçalhos de segurança definidos na política da aplicação.
- Content-Security-Policy (CSP).
- Strict-Transport-Security (HSTS).
- X-Content-Type-Options.
- Referrer-Policy.
- Outros cabeçalhos aplicáveis à arquitetura.
Testes: integração e segurança.

RNF-012 — Auditoria e rastreabilidade

As operações críticas devem gerar registros de auditoria contendo informações suficientes para identificar a operação realizada.
- Identificador do usuário responsável.
- Data e hora da operação.
- Tipo de operação.
- Identificação do registro afetado.
- Resultado da operação.
- Informações necessárias para rastreabilidade, sem exposição indevida de dados sensíveis.
Os registros devem possuir proteção contra alteração ou exclusão não autorizada.

Testes: unitários e integração.

RNF-013 — Privacidade e proteção de dados

O tratamento de dados pessoais deve observar os princípios e requisitos aplicáveis da Lei Geral de Proteção de Dados (LGPD).
- Impedir exposição indevida de dados pessoais.
- Garantir acesso aos dados conforme as permissões estabelecidas.
- Verificar mecanismos de anonimização e exclusão, quando aplicáveis.
- Impedir armazenamento desnecessário de informações sensíveis.
- Garantir que informações pessoais não sejam expostas em mensagens de erro ou logs.
Testes: unitários, integração e segurança.

## 3. Disponibilidade e confiabilidade
RNF-014 — Disponibilidade da aplicação

A aplicação deve manter disponibilidade mínima de 99,9% ao mês, desconsiderando as janelas de manutenção programadas, conforme a política de disponibilidade definida.

Testes: monitoramento e testes operacionais.

RNF-015 — Integridade e consistência dos dados

A aplicação deve preservar a integridade dos dados durante operações de inclusão, consulta, atualização e exclusão.
- Impedir persistência de dados inconsistentes.
- Garantir aplicação das restrições de integridade do banco de dados.
- Garantir atomicidade das operações transacionais.
- Impedir duplicidade quando houver restrições de unicidade.
- Garantir comportamento consistente diante de falhas durante transações.
Testes: unitários e integração.

RNF-016 — Tratamento de falhas

A aplicação deve tratar falhas internas e externas sem comprometer a integridade dos dados ou provocar interrupções desnecessárias.
- Tratar indisponibilidade do banco de dados.
- Tratar falhas de serviços externos.
- Garantir encerramento adequado de transações.
- Retornar mensagens e códigos HTTP apropriados.
- Não expor stack traces ou detalhes internos ao usuário.
- Garantir que falhas em serviços secundários não interrompam operações principais, quando tecnicamente possível.
Testes: unitários e integração.

RNF-017 — Backup e recuperação

O banco de dados deve possuir rotina automatizada de backup e procedimentos documentados de recuperação.
- Realizar backups diários.
- Manter retenção mínima de 30 dias.
- Garantir RTO (Recovery Time Objective) de até 4 horas.
- Verificar integridade dos arquivos de backup.
- Executar testes periódicos de restauração.
Testes: integração operacional e recuperação de desastres.

RNF-018 — Idempotência e segurança na repetição de operações

As operações que possam ser repetidas em razão de falhas de comunicação ou reenvio de requisições devem possuir comportamento definido para evitar efeitos duplicados indevidos.
- Impedir duplicidade de operações críticas.
- Garantir consistência após reenvio de requisições.
- Definir mecanismos de idempotência quando aplicáveis.
Testes: unitários e integração.

## 4. Escalabilidade
RNF-019 — Escalabilidade horizontal

A arquitetura deve permitir a ampliação da capacidade de processamento por meio da adição de instâncias da aplicação.

Quando houver infraestrutura de escalabilidade automática, deve ser possível configurar o acionamento conforme limites de utilização de recursos.
- Monitorar utilização de CPU.
- Verificar acionamento das políticas de escalabilidade.
- Garantir funcionamento correto com múltiplas instâncias.
- Evitar dependência de estado exclusivamente armazenado em memória local da instância.
Testes: integração e carga.

RNF-020 — Concorrência e processamento simultâneo

A aplicação deve preservar a integridade e consistência das operações realizadas simultaneamente por diferentes usuários.
- Impedir condições de corrida (race conditions).
- Tratar atualizações concorrentes.
- Garantir integridade das transações.
- Controlar conflitos de atualização.
- Garantir isolamento adequado das operações.
Testes: unitários e integração com concorrência.

## 5. Usabilidade, acessibilidade e interface
RNF-021 — Responsividade

A interface deve adaptar-se adequadamente às diferentes resoluções de tela, sem perda de funcionalidades ou comprometimento da experiência de utilização.
- Smartphones: largura mínima de 360 px.
- Tablets: resoluções intermediárias.
- Desktops e monitores ultrawide: até 2560 px.
- Evitar rolagem horizontal não intencional.
- Evitar sobreposição ou ocultação de componentes.
Testes: interface (E2E) e compatibilidade visual.

RNF-022 — Acessibilidade

A aplicação deve atender ao nível AA das diretrizes WCAG 2.2.
- Navegação integral por teclado.
- Identificação adequada dos elementos da interface.
- Compatibilidade com leitores de tela.
- Contraste mínimo de 4,5:1 para texto convencional.
- Identificação e comunicação de erros nos formulários.
- Associação correta entre rótulos e campos.
- Foco visual perceptível.
- Uso adequado de elementos semânticos.
A adoção da WCAG 2.2 AA amplia a cobertura em relação à versão 2.1 originalmente citada. 
W3C+1


Testes: acessibilidade automatizada e manual.

RNF-023 — Feedback das operações

A interface deve fornecer feedback visual adequado durante a execução das operações.
- Exibir indicadores de carregamento para operações assíncronas superiores a 500 ms.
- Informar sucesso ou falha das operações.
- Impedir submissões duplicadas quando necessário.
- Preservar os dados preenchidos em caso de erros recuperáveis.
- Exibir mensagens compreensíveis ao usuário.
Testes: unitários de componentes e interface (E2E).

RNF-024 — Compatibilidade entre navegadores

A aplicação deve funcionar adequadamente nas duas últimas versões estáveis dos seguintes navegadores:
- Google Chrome.
- Mozilla Firefox.
- Apple Safari.
- Microsoft Edge.
Devem ser verificados os aspectos funcionais, visuais e de compatibilidade dos recursos utilizados.

Testes: compatibilidade e interface (E2E).

## 6. Interoperabilidade e portabilidade
RNF-025 — Padronização das APIs

As interfaces de comunicação devem utilizar padrões abertos e formatos estruturados de troca de dados.
- APIs RESTful, quando adotadas.
- Formato JSON para intercâmbio de dados.
- Utilização adequada dos métodos HTTP.
- Códigos HTTP compatíveis com os resultados das operações.
- Padronização das mensagens de erro.
- Validação dos contratos de entrada e saída.
Testes: unitários e integração.

RNF-026 — Compatibilidade de dados

Os dados transmitidos e recebidos pela aplicação devem respeitar os contratos definidos, evitando inconsistências de representação.
- Validar tipos de dados.
- Validar campos obrigatórios.
- Validar formatos de datas e horários.
- Validar codificação de caracteres.
- Tratar campos nulos e valores opcionais.
- Garantir compatibilidade entre versões de contratos, quando aplicável.
Testes: unitários e integração.

## 7. Manutenibilidade e observabilidade
RNF-027 — Cobertura de testes automatizados

O projeto deve manter cobertura mínima de 80% do código executável por testes automatizados.
- Cobertura de testes unitários.
- Cobertura de testes de integração.
- Identificação de trechos não testados.
- Execução automatizada dos testes no pipeline de CI/CD.
- Geração de relatórios de cobertura.
A cobertura deve ser acompanhada por módulo ou pacote, evitando que uma boa cobertura global esconda componentes críticos sem testes.

Testes: validação automatizada do pipeline.

RNF-028 — Monitoramento e observabilidade

A aplicação deve disponibilizar informações que permitam acompanhar sua saúde operacional e diagnosticar falhas.
- Métricas de disponibilidade.
- Tempo de resposta.
- Taxa de erros.
- Consumo de recursos.
- Identificação de falhas de integração.
- Registros estruturados de eventos.
- Rastreamento de requisições, quando aplicável.
Testes: integração e testes operacionais.

RNF-029 — Padronização e qualidade do código

O código-fonte deve atender aos padrões de qualidade e estilo definidos pelo projeto.
- Execução automatizada de ferramentas de análise estática.
- Identificação de problemas de estilo.
- Identificação de possíveis erros.
- Verificação de complexidade e problemas recorrentes.
- Bloqueio do pipeline em caso de violações classificadas como impeditivas.
Testes: análise estática e CI/CD.

RNF-030 — Reprodutibilidade do ambiente de testes

O ambiente de testes deve permitir a execução repetível e isolada dos testes automatizados.
- Isolamento dos dados utilizados nos testes.
- Preparação e limpeza do banco de dados.
- Controle de dependências externas.
- Configurações específicas para testes.
- Independência da ordem de execução dos testes.
- Possibilidade de execução automatizada em ambiente de CI/CD.
Testes: unitários e integração.

## 8. Matriz de aplicabilidade dos testes
Um ponto importante: nem todos os requisitos acima devem ser verificados pelo mesmo tipo de teste.

Esta é a classificação recomendada para orientar a implementação:
Tipo de teste	Objetivo	Exemplos
Unitário	Validar unidades isoladas de código	Validadores, serviços, regras, permissões
Integração	Validar comunicação entre componentes	ORM, banco, APIs, autenticação
Segurança	Identificar vulnerabilidades	SQLi, XSS, CSRF, RBAC
Desempenho	Medir capacidade e latência	Carga, estresse, concorrência
E2E	Validar fluxos completos	Login, formulários, navegação
Acessibilidade	Verificar conformidade da interface	WCAG, teclado, leitores de tela
Compatibilidade	Validar funcionamento em navegadores	Chrome, Firefox, Safari, Edge
Operacional	Validar infraestrutura e recuperação	Backup, restore, disponibilidade

9. Ajustes importantes em relação à lista original
Algumas informações precisavam de revisão antes de serem adotadas como requisitos:
Item original	Ajuste recomendado
SHA-256 para senhas	Substituir por Argon2id, bcrypt ou PBKDF2.
WCAG 2.1 AA	Adotar WCAG 2.2 AA como referência.
500 transações/s	Definir conforme capacidade e demanda reais.
10.000 usuários simultâneos	Não assumir sem dimensionamento e testes de carga.
CPU acima de 80% por 5 minutos	Definir uma única política de escalabilidade, baseada na infraestrutura.
CPU acima de 75% por 3 minutos	Evitar manter dois critérios conflitantes.
99,9% de disponibilidade	Validar por monitoramento operacional, não por testes unitários.
CDN obrigatória	Tratar como decisão arquitetural, não requisito universal.
SameSite=Strict	Definir conforme o fluxo de autenticação e integrações.
Cobertura de 80%	Acompanhar também cobertura de branches e criticidade dos módulos.
JavaScript desabilitado	Definir degradação graciosa somente se fizer parte dos requisitos de utilização.

Referências técnicas para fundamentar a suíte de testes:
- OWASP ASVS 5.0 — Requisitos de verificação de segurança.
- OWASP Web Security Testing Guide — metodologia de testes de segurança web.
- OWASP Password Storage Cheat Sheet — armazenamento seguro de senhas.
- W3C WCAG — acessibilidade.
- Core Web Vitals — desempenho da experiência web.

10. Como utilizar este referencial no projeto
Minha recomendação é manter os requisitos identificados e independentes das tecnologias utilizadas.

Cada requisito deve possuir:
- Identificador único (RNF-001).
- Descrição.
- Critério de aceitação.
- Prioridade (crítica, alta, média ou baixa).
- Tipo de teste aplicável.
- Casos de teste associados.
- Situação de implementação.