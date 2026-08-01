# Seleção protegida da viewport — Genesis v0.6.7

## Problema corrigido

O botão esquerdo era usado simultaneamente para rotacionar e
selecionar. Ao terminar um arraste, o picker podia interpretar
o gesto como clique e selecionar um objeto acidentalmente.

## Novo comportamento

- arrastar com o botão esquerdo: rotacionar a vista;
- Ctrl + clique esquerdo curto: selecionar ou desmarcar objeto;
- Ctrl + arraste: continua sendo navegação e não seleciona;
- seleção pela árvore: continua funcionando normalmente.

## Tolerância

O gesto só é considerado clique quando o cursor se desloca no
máximo 5 pixels entre pressionar e soltar. Acima disso, o FLCAD
considera que houve manipulação da vista.

## Modos afetados

A regra vale para seleção normal, exclusão e seleção de
referências para alinhamento. Os comandos de reconhecimento
continuam usando seus próprios modos explícitos de captura.
