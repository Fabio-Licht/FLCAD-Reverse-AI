# Alignment Engine por plano — Genesis v0.7.0

## Seleção

Selecione exatamente:

- uma malha;
- um plano de referência.

Use Ctrl + clique curto na viewport ou selecione pela árvore.

## Modos

### Assentar e orientar

- XY com normal Z+ ou Z−;
- XZ com normal Y+ ou Y−;
- YZ com normal X+ ou X−.

O sistema orienta a normal e move a origem do plano até o plano
global correspondente:

- XY → Z = 0;
- XZ → Y = 0;
- YZ → X = 0.

### Somente orientar

Gira a peça ao redor da origem do plano, sem alterar a posição
dessa origem.

## Histórico

Undo e Redo transformam a malha e as referências dependentes
como uma única operação.

## Próxima etapa

O alinhamento Plano + Eixo eliminará o grau de liberdade de
rotação restante sobre a normal do plano.
