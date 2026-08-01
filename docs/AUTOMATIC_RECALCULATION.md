# Recálculo automático — Genesis v0.6.3

## Funcionamento

Depois de selecionar as sementes e obter um resultado válido,
o usuário pode alterar:

- raio da expansão;
- variação angular;
- mínimo de pontos.

Com a opção `Recalcular automaticamente` ativada, o FLCAD
aguarda 450 ms após a última alteração e reutiliza as sementes
existentes.

Esse pequeno atraso evita executar vários cálculos enquanto o
usuário ainda está digitando ou ajustando o controle.

## Segurança

- não recalcula enquanto faltam sementes;
- não inicia um segundo cálculo durante um cálculo ativo;
- alterar a quantidade de sementes invalida a seleção atual;
- o botão `Recalcular` continua disponível para uso manual;
- a preferência é salva na memória do último comando.
