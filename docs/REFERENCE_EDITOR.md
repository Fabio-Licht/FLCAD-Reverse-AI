# Editor permanente de referências — Genesis v0.4.9

## Acesso

Dê duplo clique em um cilindro na árvore do projeto.

Caso a entidade seja uma instância, o editor localiza o cilindro
mestre e reabre as propriedades do padrão completo.

## Dados editáveis

- diâmetro nominal;
- centro X, Y e Z;
- vetor I, J e K;
- inclinação e azimute;
- comprimento e extensão;
- quantidade e parâmetros do padrão linear ou circular;
- criação de eixos e pontos centrais.

## Atualização

Ao confirmar, o padrão anterior e suas referências derivadas são
substituídos pelo novo conjunto em uma única etapa de Undo/Redo.

## Próxima etapa

O reconhecimento cilíndrico por duas sementes será implementado
para reduzir a influência do triângulo inicial na estimativa de
diâmetro, centro e direção.
