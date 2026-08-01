# Correção da seleção pela viewport — Genesis v0.7.2

A seleção pela tela agora usa `vtkCellPicker`, mais adequado
para malhas, planos e referências pequenas. Caso ele não encontre
uma célula, o sistema tenta `vtkPropPicker`.

O ator capturado é convertido explicitamente para o objeto da
cena e a seleção usa o mesmo método da árvore. Isso mantém:

- viewport e árvore sincronizadas;
- destaque por tipo;
- seleção múltipla;
- Ctrl + clique curto;
- arraste reservado para rotação.
