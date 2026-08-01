# Reconhecimento cilíndrico interativo — Genesis v0.6.1

## Novo fluxo

1. Abrir `Reconhecer cilindro por região`.
2. Configurar raio, ângulo, sementes e mínimo de pontos.
3. Clicar em `Selecionar sementes`.
4. Selecionar os triângulos com a janela ainda aberta.
5. Acompanhar o contador de sementes no próprio painel.
6. Após um resultado válido, o painel de propriedades é aberto.

## Controles

- `Selecionar sementes`: inicia a captura na viewport;
- `Limpar sementes`: remove os cliques sem fechar o comando;
- `Cancelar`: encerra o reconhecimento;
- a janela permanece não modal durante a seleção.

## Próxima evolução

O mesmo painel poderá recalcular automaticamente com as mesmas
sementes quando raio ou ângulo forem alterados, sem exigir nova
seleção.
