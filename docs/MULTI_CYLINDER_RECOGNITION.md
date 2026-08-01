# Multi-reconhecimento de cilindros — Genesis v0.6.6

## Objetivo

Reconhecer diversos cilindros e criá-los em uma única operação.

## Fluxo

1. Ative `Multi-reconhecimento: acumular vários cilindros`.
2. Selecione as sementes do primeiro cilindro.
3. Avalie ou recalcule o resultado.
4. Clique em `Adicionar resultado ao lote`.
5. Repita o processo para os demais cilindros.
6. Clique em `Criar lote`.

## Criação

O lote usa as opções lembradas do último comando de criação:

- comprimento limitado ou estendido;
- fator de extensão;
- criação de eixo;
- criação de ponto central.

Padrões lineares e circulares não são aplicados ao lote, pois
cada item já representa um cilindro reconhecido individualmente.

## Histórico

Todo o lote entra como uma única operação de Undo/Redo.
