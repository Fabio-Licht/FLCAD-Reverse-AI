# FLCAD Pattern Engine — Genesis v0.4.8

## Objetivo

Criar padrões associativos a partir de uma referência mestre.

A primeira implementação atende cilindros reconhecidos, mas o
motor matemático foi separado da interface para ser reutilizado
futuramente por pontos, eixos, planos, curvas, superfícies e
sólidos.

## Padrão linear

Entradas:

- centro e direção da entidade mestre;
- vetor de translação;
- espaçamento;
- quantidade total.

A quantidade inclui o mestre.

## Padrão circular

Entradas:

- centro e direção da entidade mestre;
- origem do eixo central;
- vetor do eixo central;
- passo angular;
- quantidade total;
- manter ou rotacionar a orientação das instâncias.

## Rastreabilidade

As instâncias guardam metadados:

- pattern_id;
- pattern_type;
- pattern_role;
- pattern_index;
- pattern_parameter;
- pattern_quantity;
- pattern_master_id;
- pattern_settings.

O mestre mantém os dados reconhecidos da malha. As demais
entidades são marcadas como instâncias nominais.

## Próximas evoluções

- pré-visualização completa do padrão antes da criação;
- grupo hierárquico na árvore;
- edição associativa do padrão após a criação;
- desvincular instância;
- validação de cada instância contra a malha;
- padrões retangulares e por curva.
