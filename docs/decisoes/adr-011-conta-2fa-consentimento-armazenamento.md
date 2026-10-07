# ADR-011 — Recuperação de conta, verificação em duas etapas, consentimento e armazenamento privado

- **Status:** Aceito
- **Data:** 2026-10-07

## Contexto

Para um produto pago faltavam quatro peças:
- a pessoa não conseguia recuperar a própria senha (só o Admin redefinia);
- não havia segundo fator;
- não havia aceite registrado dos termos;
- anexos e exportações ficavam no disco de uma única máquina, o que impede rodar mais de uma instância.

## Decisão

1. **E-mail:** SMTP genérico (`app/core/mailer.py`). Sem `SMTP_HOST`, a mensagem só vai para o log. Falhas de envio nunca derrubam a requisição.
2. **Recuperação de senha:** token aleatório de uso único, válido por 1 hora, guardado só como SHA-256. Um pedido novo invalida os anteriores, e a resposta é igual exista ou não o e-mail. Redefinir desbloqueia a conta e revoga as sessões antigas.
3. **Verificação em duas etapas:** TOTP com tolerância de um passo de relógio e 8 códigos de recuperação de uso único (hash). O login com 2FA ativo devolve um token intermediário de 5 minutos, aceito só em `/auth/login/mfa`; códigos errados contam para o bloqueio. O segredo é criptografado com Fernet usando `ENCRYPTION_KEY`, separada da `SECRET_KEY` para que a troca prevista no SEC-5 não apague o 2FA de todos. O Admin pode desativar o 2FA de um membro que perdeu o acesso.
4. **Limite por IP:** janela deslizante em memória nas rotas de autenticação. `X-Forwarded-For` só é considerado com `TRUSTED_PROXY_HOPS`, usando a entrada adicionada pelo nosso proxy.
5. **Consentimento:** o cadastro exige o aceite; a versão (`app/core/legal.py`, espelhada em `frontend/src/legal.ts` e verificada por teste) e a data são gravadas no usuário. Quem não aceitou a versão vigente aceita no próximo acesso.
6. **Armazenamento:** interface única com dois backends, disco local (padrão, mesma estrutura de pastas de antes) e S3 compatível (Supabase Storage, AWS S3, R2). Os arquivos nunca são públicos.

## Consequências

- O limite por IP vale por instância. Com várias instâncias, cada uma aplica a própria janela; um limite global exigiria o Redis já provisionado.
- Os textos de termos e privacidade são minuta. Mudar o texto exige subir a versão nos dois arquivos, o que pede um novo aceite de todos.
- Os uploads não passam por antivírus.
