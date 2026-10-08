# Guia de contribuição

Este repositório usa um fluxo acadêmico inspirado em práticas de mercado, com `issues`, `branches`, `pull requests`, `reviews` e `milestones`.

## Fluxo padrão

1. Escolha ou crie uma `issue` vinculada à sprint atual.
2. Confirme que a `issue` tem critérios de aceite claros.
3. Crie uma `branch` com o padrão adequado.
4. Faça commits pequenos e descritivos.
5. Abra um `pull request` relacionando a `issue`.
6. Solicite `review` de pelo menos uma pessoa.
7. Responda aos comentários e ajuste o que for necessário.
8. Faça o `merge` somente após a aprovação e a resolução das conversas.

## Padrão de branches

- `feature/<numero-issue>-descricao`: funcionalidade ou requisito.
- `docs/<numero-issue>-descricao`: documentação.
- `fix/<numero-issue>-descricao`: correção.
- `release/sprint-XX`: consolidação de sprint, quando exigida pelo professor.

As branches `develop` e `release/sprint-XX` são opcionais e devem ser usadas apenas quando a disciplina exigir um marco de integração separado.

## Commits

Use mensagens curtas e claras:

- `docs: update sprint report`
- `feat: add requirement description`
- `fix: correct validation evidence`
- `chore: organize project documents`

## Antes de abrir o pull request

Rode as mesmas verificações que o CI (`.github/workflows/ci.yml`) roda em todo `pull request`:

```bash
python -m pytest                                   # backend (instale antes: pip install -r requirements-dev.txt)
cd frontend && npm run lint && npm test && npm run build
```

- Mudou `app/db/models.py`? Crie a migração com `alembic revision --autogenerate -m "descricao"`: um teste falha se modelos e migrações divergirem.
- Criou dados de negócio novos? Inclua um teste mostrando que outra empresa (ou outro usuário) não os enxerga.
- Variável de ambiente nova? Documente no `.env.example`. Nunca coloque valores reais em arquivos versionados (ver [SECURITY.md](SECURITY.md)).

O `merge` só acontece com o CI verde e a aprovação de pelo menos uma pessoa.

## Pull requests

Todo `pull request` deve conter:

- Link da `issue` relacionada.
- Resumo da mudança.
- Como validar.
- Evidências, quando aplicável.
- Documentos alterados.

## Qualidade esperada

- Mudanças pequenas e revisáveis.
- Documentação atualizada.
- Evidências registradas.
- Histórico de colaboração preservado.
