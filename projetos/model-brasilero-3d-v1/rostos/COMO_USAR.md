# Rostos animados (model-brasilero-3d-v1/rostos)

5 tipos de rosto, cada um com 5 animações de 5 quadros. O rosto é uma camada **transparente** por cima da
pele: o tom de pele continua vindo só do `skin.png`.

| Arquivo | Para que serve |
|---|---|
| `model-brasilero-3d-rostos.blend` | Boneco com o sistema de rostos (Blender 5.2+). Lê `//skin.png` e `//rostos_atlas.png` desta pasta. |
| `skin.png` | Igual ao skin da v1, mas com a área ROSTO pintada de pele lisa (o desenho do rosto agora vem do atlas). |
| `rostos_atlas.png` | Todos os quadros (1200x240, fundo transparente). **É este que você edita para mudar os rostos.** |
| `rostos_guia.png` | O atlas ampliado 4x, com tipo, animação e quadro marcados. Só referência. |
| `rostos.json` | Medidas do atlas e a conta para achar cada quadro (para jogo). |
| `web/model-brasilero-3d-rostos.glb` | Versão para jogo web (three.js, Babylon etc.), com skin e atlas embutidos. |
| `web/demo_web.html` | Abre com dois cliques no navegador, sem internet. Troca rosto, toca animações, pisca sozinho. |
| `previews/` | `rostos_grade.png` (todas as expressões) e `rostos_animados.gif`. |
| `scripts/` | Código que gerou tudo, para refazer ou ajustar. |

## Tipos e animações (tudo começa em 0)

- `tipo_rosto`: 0 Clássico, 1 Animado, 2 Focado, 3 Sardento, 4 Tranquilo
- `animacao`: 0 piscar um olho, 1 piscar os dois, 2 força, 3 dor, 4 felicidade
- `quadro`: 0 a 4. Quadros 0 e 4 = rosto padrão, 2 = expressão completa, 1 e 3 = transição (iguais).
- Velocidade: 10 quadros por segundo (a animação inteira dura meio segundo).

## No Blender

1. Abra `model-brasilero-3d-rostos.blend` e use o modo **Material Preview** (tecla Z).
2. Selecione o objeto **Rosto_Expressao** (filho da Cabeca). No painel lateral, aba **Object > Custom Properties**,
   mude `tipo_rosto` para trocar o rosto. `animacao` e `quadro` mostram uma expressão parada.
3. Para tocar uma animação: no **Action Editor** (Dope Sheet > Action Editor) escolha uma das ações
   `Rosto_piscada_um_olho`, `Rosto_piscada_dois_olhos`, `Rosto_forca`, `Rosto_dor`, `Rosto_felicidade` e aperte play.
   Cada ação ocupa os quadros 1 a 11 da cena (24 fps, cada quadro do rosto dura 2 quadros da cena).
4. O `tipo_rosto` não faz parte das ações, então qualquer animação funciona em qualquer tipo.

## No jogo web

O UV do rosto no `.glb` aponta para o primeiro quadro. Para mostrar outro, mude o deslocamento da textura do
material do objeto `Rosto_Expressao`:

```js
rosto.material.map.offset.set((tipo * 5 + quadro) / 25, animacao / 5);
```

O `demo_web.html` tem isso funcionando (funções `setRosto` e `tocarAnimacao`). As ações do Blender não vão para
o `.glb`: no jogo, a sequência 0,1,2,3,4 a 10 fps é feita no código, como na demo.

## Editar os rostos à mão

Abra `rostos_atlas.png` (Photopea, Krita, Aseprite...). Cada bloco de 240x240 é um tipo; dentro dele, linha =
animação, coluna = quadro, cada quadro 48x48. Pinte com lápis de 1 px sem suavização e deixe transparente onde
for pele. Salve por cima e aperte Alt+R no Blender. Para o jogo web, rode de novo `scripts/export_web.py`
(ou troque a imagem no código).

## Limites

- A borda do couro cabeludo cobre o alto da testa. Cabelos com franja comprida podem esconder as sobrancelhas.
- A cor da sobrancelha é fixa por tipo; não acompanha a cor do cabelo.
