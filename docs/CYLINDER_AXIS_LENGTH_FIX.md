# Correção de comprimento — Genesis v0.5.4

## Problema

Ao editar um cilindro estendido, o comprimento já multiplicado
era reutilizado como comprimento-base. O fator de extensão era
aplicado novamente, fazendo o cilindro e principalmente o eixo
crescerem a cada edição.

Exemplo do erro anterior:

- comprimento reconhecido: 10 mm;
- extensão: 3×;
- primeira criação: 30 mm;
- primeira edição: 90 mm;
- segunda edição: 270 mm.

## Correção

O FLCAD agora separa permanentemente:

- `recognized_length`: comprimento-base reconhecido na malha;
- `display_length`: comprimento visual final;
- `extension_factor`: fator aplicado apenas uma vez.

Ao reabrir o editor, o cálculo sempre parte de
`recognized_length`, impedindo crescimento acumulativo.

## Compatibilidade

Para cilindros criados antes da v0.5.4, o comprimento-base é
reconstruído dividindo o comprimento atual pelo fator salvo.
