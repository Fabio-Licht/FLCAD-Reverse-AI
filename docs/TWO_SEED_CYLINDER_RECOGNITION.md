# Reconhecimento cilíndrico por duas sementes — Genesis v0.5.0

## Motivação

Uma única célula da malha pode apresentar ruído, inclinação,
desgaste ou proximidade de bordas. Isso pode deslocar o centro
e alterar o diâmetro estimado.

## Fluxo

1. O usuário escolhe uma ou duas sementes.
2. Cada clique gera uma expansão conectada independente.
3. As regiões são combinadas e os pontos duplicados removidos.
4. Um ajuste cilíndrico preliminar é calculado com o conjunto.
5. O refinamento preserva os componentes conectados a qualquer
   semente.
6. O cilindro final é recalculado sobre a região refinada.

## Regras

- As sementes precisam pertencer à mesma malha.
- Recomenda-se clicar em regiões afastadas da mesma parede.
- O modo de uma semente continua disponível.
- Os pontos clicados e a quantidade de sementes são guardados
  nos metadados da referência.
