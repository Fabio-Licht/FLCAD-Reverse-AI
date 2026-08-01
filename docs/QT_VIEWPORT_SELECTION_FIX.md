# Seleção pela viewport via Qt — Genesis v0.7.4

## Problema

Em algumas combinações de PyVistaQt e VTK, os observadores
`LeftButtonPressEvent` e `LeftButtonReleaseEvent` não recebiam
os eventos da viewport. Por isso, a seleção funcionava pela
árvore, mas não pela tela.

## Correção

O FLCAD agora instala um filtro de eventos diretamente no
widget Qt da viewport.

Fluxo:

- Ctrl + clique curto é detectado pelo Qt;
- a coordenada Y é convertida para o sistema do VTK;
- o sistema tenta `vtkCellPicker`;
- se necessário, tenta `vtkPropPicker`;
- o ator é vinculado ao objeto lógico e à árvore.

O filtro retorna o evento para o QtInteractor, preservando a
rotação normal por arraste.
