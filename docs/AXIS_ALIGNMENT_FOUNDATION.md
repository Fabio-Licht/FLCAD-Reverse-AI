# Fundação do alinhamento por eixo — Genesis v0.5.3

## Fluxo

1. Ativar `Selecionar objetos`.
2. Selecionar uma malha.
3. Selecionar um cilindro ou eixo de referência.
4. Abrir `Alinhamento`.
5. Escolher X+, Y+, Z+, X−, Y− ou Z−.

A rotação é calculada pelo Geometry Engine e acontece em torno
do centro do cilindro ou da origem do eixo.

## Dependências visuais

A malha, a referência selecionada e as referências cujo
`source_object_id` depende delas são transformadas juntas.

## Histórico

O alinhamento suporta Undo/Redo.

## Limitação desta primeira fundação

A v0.5.3 aplica a matriz aos atores da cena. A etapa futura de
`Bake Transform` incorporará a matriz definitivamente aos
pontos da malha e atualizará os valores lógicos das referências,
preparando exportação e encadeamento completo de alinhamentos.
