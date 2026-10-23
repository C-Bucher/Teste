# Mapa do frontend

Explica cada pasta e arquivo do frontend. Fica aqui em `docs/` de propósito:
o frontend é o produto que vai para o cliente e não leva nenhuma nota dentro dele.

## `frontend`

**Função:** Frontend: as telas do sistema em React + TypeScript, com Vite (compila e serve), Tailwind (estilo) e Vitest (testes). O código está em src; as bibliotecas instaladas estão em node_modules.

- `.gitignore`: O que o Git ignora dentro do frontend (node_modules, dist etc.).
- `eslint.config.js`: Regras do ESLint: aponta erros e más práticas no código TypeScript/React.
- `index.html`: Página HTML única do site. O React desenha todas as telas dentro do elemento div#root.
- `package-lock.json`: Versões exatas instaladas de cada dependência. Gerado pelo npm; não editar à mão.
- `package.json`: Lista de dependências do frontend e os comandos npm (dev, build, lint, test).
- `postcss.config.js`: Configuração do PostCSS: aplica o Tailwind e o autoprefixer ao CSS.
- `public/`: Arquivos que o site entrega como estão, sem processar (ícone da aba e ícones SVG).
- `README.md`: README do frontend (texto do modelo do Vite).
- `src/`: Código-fonte do frontend. App.tsx define as rotas, api.ts conversa com o servidor, types.ts tem os tipos e as subpastas separam as peças por tipo.
- `tailwind.config.js`: Configuração do Tailwind CSS: onde procurar classes e as cores e fontes do tema.
- `tsconfig.app.json`: Configuração do TypeScript para o código em src.
- `tsconfig.json`: Configuração raiz do TypeScript; aponta para os dois arquivos abaixo.
- `tsconfig.node.json`: Configuração do TypeScript para os arquivos de configuração (vite.config etc.).
- `vite.config.ts`: Configuração do Vite (ferramenta que roda e compila o frontend): usa o plugin do React.
- `vitest.config.ts`: Configuração dos testes do frontend (Vitest): ambiente de navegador simulado e arquivo de preparação.
- `node_modules/`: bibliotecas de terceiros instaladas pelo npm (não é código nosso; `npm install` recria).
- `dist/`: site compilado por `npm run build`; é o que vai para produção. Apagado e refeito a cada build.

## `frontend/public`

**Função:** Arquivos que o site entrega como estão, sem processar (ícone da aba e ícones SVG).

- `favicon.svg`: Ícone da aba do navegador.
- `icons.svg`: Conjunto de ícones em SVG servido como está.

## `frontend/src`

**Função:** Código-fonte do frontend. App.tsx define as rotas, api.ts conversa com o servidor, types.ts tem os tipos e as subpastas separam as peças por tipo.

- `api.test.ts`: Testa o cliente da API: token, renovação e o bloqueio por assinatura inativa.
- `api.ts`: Cliente HTTP (axios) da API: coloca o token em cada pedido, renova o token quando vence e volta ao login se não conseguir.
- `App.css`: Estilos do modelo inicial do Vite. Não é importado por nenhuma tela; o visual real está em index.css.
- `App.tsx`: Mapa de rotas do site: cada endereço abre uma tela. As rotas privadas conferem login, escopo (empresa/pessoal) e módulo permitido.
- `assets/`: Imagens que o código pode importar. Hoje só tem as figuras do modelo inicial do Vite.
- `components/`: Componentes reutilizados em várias telas: estrutura (Layout), painel da IA, janelas de confirmação e seções de Configurações e Minha Conta.
- `context/`: Contextos do React: os avisos temporários (toast) e a confirmação de ações. Qualquer tela pode usar.
- `hooks/`: Hooks (lógica reaproveitável do React). Hoje só usePermissions, que informa os módulos liberados ao usuário.
- `index.css`: Estilos globais: importa o Tailwind e define as cores, fontes e efeitos (vidro) usados em todas as telas.
- `legal.ts`: Versão dos termos de uso no frontend. Precisa ser igual à de app/core/legal.py (um teste confere).
- `main.tsx`: Ponto de entrada do frontend: monta o App e envolve com os provedores de avisos (toast) e de confirmação.
- `pages/`: As telas do sistema, uma por arquivo (Login, Dashboard, Kanban, Financeiro, Hub Pessoal, Bancos, IA etc.).
- `test/`: Preparação comum dos testes do frontend.
- `types.ts`: Tipos TypeScript dos dados que vêm da API e a função errorMessage para ler mensagens de erro.
- `utils/`: Funções utilitárias pequenas, sem tela.

## `frontend/src/assets`

**Função:** Imagens que o código pode importar. Hoje só tem as figuras do modelo inicial do Vite.

- `hero.png`: Imagem de exemplo do modelo inicial do Vite.
- `react.svg`: Logo do React (modelo inicial do Vite).
- `vite.svg`: Logo do Vite (modelo inicial do Vite).

## `frontend/src/components`

**Função:** Componentes reutilizados em várias telas: estrutura (Layout), painel da IA, janelas de confirmação e seções de Configurações e Minha Conta.

- `AICfoDrawer.tsx`: Painel lateral do CFO Virtual: chat com a IA disponível em qualquer tela.
- `AuditLogSection.tsx`: Seção de auditoria (Configurações): lista quem fez o quê e quando, com filtros.
- `AuthCard.tsx`: Cartão central e estilos dos campos usados nas telas de login, recuperação de senha e 2FA.
- `ConfirmModal.tsx`: Janela de confirmação (título, mensagem, botões confirmar e cancelar).
- `CtcParamsSection.tsx`: Seção de Configurações para ajustar os multiplicadores do CTC e as horas mensais.
- `IntegrationsStatus.tsx`: Lista o status das integrações (IA, pagamentos, e-mail, bancos etc.). Usada em Configurações e no Onboarding.
- `Layout.tsx`: Estrutura das telas privadas: menu lateral, barra superior com busca e notificações, troca entre empresa e pessoal e painel da IA.
- `PermissionMatrix.tsx`: Tabela de permissões: marca quais módulos cada cargo (Gerente, Funcionário) pode acessar.
- `SubscriptionBanner.tsx`: Faixa fina no topo avisando que o teste grátis está acabando ou que há pagamento em atraso.
- `SystemAccessSection.tsx`: Gestão de acessos ao sistema: criar usuário, trocar cargo, redefinir senha, desativar e remover o 2FA.
- `TwoFactorSection.tsx`: Seção de Minha Conta para ligar e desligar o 2FA e guardar os códigos de recuperação.

## `frontend/src/context`

**Função:** Contextos do React: os avisos temporários (toast) e a confirmação de ações. Qualquer tela pode usar.

- `ConfirmContext.ts`: Define o contexto e o hook useConfirm: qualquer tela abre uma pergunta de confirmação e recebe sim ou não.
- `ConfirmProvider.tsx`: Provedor da confirmação: mostra a janela de confirmação e devolve a resposta à tela que perguntou.
- `ToastContext.ts`: Define o contexto e o hook useToast (success, error, info, warning) para exibir avisos temporários.
- `ToastProvider.tsx`: Provedor dos avisos (toast): mostra os recados no canto da tela e os remove sozinhos.

## `frontend/src/hooks`

**Função:** Hooks (lógica reaproveitável do React). Hoje só usePermissions, que informa os módulos liberados ao usuário.

- `usePermissions.ts`: Hook que busca (uma vez, com cache) quais módulos o usuário pode acessar. Usado pelo menu e pelas rotas.

## `frontend/src/pages`

**Função:** As telas do sistema, uma por arquivo (Login, Dashboard, Kanban, Financeiro, Hub Pessoal, Bancos, IA etc.).

- `Bancos.tsx`: Tela de Bancos (empresa e pessoal): importa extrato OFX/CSV, conecta o banco, lista transações, concilia com lançamentos e define regras de categoria.
- `Checkout.tsx`: Tela de pagamento da assinatura: leva à página do provedor (Asaas), onde o cartão é digitado.
- `Configuracoes.tsx`: Configurações em 8 abas: empresa, plano de contas, centros de custo, calendário, CTC, cargos, conexões de API e auditoria.
- `Dashboard.tsx`: Painel inicial da empresa: indicadores financeiros, DRE, fluxo de caixa e últimas transações.
- `Exportacao.tsx`: Exportação de relatórios (Excel, PDF, CSV e JSON) e histórico do que já foi exportado.
- `Financeiro.tsx`: Financeiro em 3 abas: lançamentos (com comprovante), DRE e fluxo de caixa de 90 dias.
- `Fornecedores.tsx`: Cadastro de fornecedores: listar (em cartões ou lista), criar, editar e excluir.
- `GestaoEquipe.tsx`: Gestão de equipe: colaboradores com contrato, salário, CTC e custo por hora; e, só para o administrador, a gestão de acessos ao sistema.
- `HubPessoal.tsx`: Hub Pessoal em 11 abas: visão geral, extrato, contas e cartões, orçamento, metas, dívidas, assinaturas, divisão de despesas, análise, timeboxes/OKRs e CFO pessoal (IA).
- `IAEmpresarial.tsx`: IA da empresa em 3 abas: CFO Virtual (chat), conciliação bancária por IA e gerador de orçamentos.
- `Kanban.tsx`: Quadro Kanban de projetos: colunas, cartões, cronômetro por tarefa, custo por tarefa e comentários.
- `Legal.tsx`: Termos de uso, política de privacidade e a tela de aceite dos termos.
- `Login.tsx`: Tela de login (com passo de 2FA quando ativo), com atalhos para os usuários de demonstração.
- `MinhaConta.tsx`: Minha Conta: trocar a senha, ligar o 2FA, exportar os próprios dados e excluir a conta.
- `Onboarding.tsx`: Assistente de primeira configuração do administrador em 3 passos: dados da empresa, permissões dos cargos e conexões de API.
- `Plans.tsx`: Tela de planos e preços, com alternância mensal e anual.
- `RecuperarSenha.tsx`: Telas de Esqueci a senha (pede o e-mail) e Redefinir senha (usa o link recebido por e-mail).
- `Register.tsx`: Cadastro em 2 passos: dados da pessoa e da empresa, depois escolha do plano; exige aceitar os termos.
- `screens.test.tsx`: Testes das telas principais (login, termos, banner de assinatura, recuperação de senha etc.).
- `Subscription.tsx`: Assinatura: plano atual, faturas, consumo do plano (IA, bancos) e cancelamento.

## `frontend/src/test`

**Função:** Preparação comum dos testes do frontend.

- `setup.ts`: Preparação dos testes do frontend: ativa os comparadores do Testing Library e limpa a tela e o localStorage depois de cada teste.

## `frontend/src/utils`

**Função:** Funções utilitárias pequenas, sem tela.

- `defer.ts`: Função defer: adia o carregamento de dados para logo depois da montagem da tela, evitando erro de atualização de estado dentro de efeito.
