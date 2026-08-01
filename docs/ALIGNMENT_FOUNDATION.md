# FLCAD Alignment Foundation

## Objetivo

O módulo de alinhamento deverá operar sobre referências
geométricas associativas, e não apenas sobre atores gráficos.

## Primeira sequência planejada

1. Alinhar eixo reconhecido a X, Y ou Z global.
2. Alinhar plano reconhecido a XY, XZ ou YZ global.
3. Alinhamento eixo + plano.
4. Alinhamento por três pontos.
5. Alinhamento entre duas entidades.
6. Best Fit por ICP.
7. Best Fit restrito a regiões selecionadas.

## Regras

- Toda transformação deve suportar Undo/Redo.
- Malha e referências dependentes devem se mover juntas.
- Dados reconhecidos e nominais devem permanecer rastreáveis.
- O usuário deve visualizar uma prévia antes de aplicar.
- A matriz 4x4 resultante deve ser armazenada no projeto.
