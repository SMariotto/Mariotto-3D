# Prompt para o Jarvis: personagem BRASILERO no jogo

Jarvis, você vai implementar no jogo o modelo do projeto **model-brasilero-3d**. Os modelos, texturas,
rostos e cabelos são feitos pela Sofia (outra IA, que trabalha com o Samuel no Blender). O seu trabalho é carregar,
montar e animar isso no jogo. Leia este documento inteiro antes de escrever código: ele explica o que cada arquivo é,
como as peças se encaixam, as fórmulas e as armadilhas.

---

## 1. Visão geral

O personagem é um menino jogador de futebol low-poly no estilo Nintendo 64: poucos polígonos, texturas pequenas,
pixels duros (sem filtro), cores em degraus. A personalização funciona em três camadas independentes:

| Camada | O que muda | Arquivo | Como troca no jogo |
|---|---|---|---|
| **Skin** | roupa (camisa, bermuda, chuteira) e tom de pele | `skin.png` 128x128 | troca a textura do material `Skin` |
| **Rosto** | 5 tipos de rosto x 5 animações x 5 quadros | `rostos_atlas.png` 1200x240 | muda o offset da textura do material `Rosto` |
| **Cabelo** | 7 cortes (malha) x 5 cores (textura) | malha `Cabelo` + `texturas/<corte>_<cor>.png` 64x64 | corte = troca a malha; cor = troca a textura |

Ainda **não existe esqueleto (rig)**. As peças do corpo são malhas rígidas separadas, todas em T-pose. O esqueleto
está planejado (ver seção 9).

## 2. Onde estão os arquivos

Raiz no computador do Samuel: `C:\Users\Samuel\Documents\3d-projects\projetos\model-brasilero-3d-v1\`

| Caminho | O que é |
|---|---|
| `rostos/skin.png` | skin padrão de teste (pele rosa, camisa verde, bermuda azul, chuteira preta) |
| `rostos/rostos_atlas.png` | atlas dos rostos (fundo transparente) |
| `rostos/rostos.json` | medidas do atlas, nomes dos tipos e animações, fórmula do offset |
| `rostos/web/demo_web.html` | demo three.js funcionando (troca rosto e toca animações). **Referência de implementação.** |
| `rostos/model-brasilero-3d-rostos-cranio-v2.blend` | personagem careca (sem cabelo), versão atual da cabeça |
| `cabelos-v4/<NN>-<corte>_<cor>.blend` | 35 versões completas no Blender (personagem + cabelo) |
| `cabelos-v4/web/<NN>-<corte>_<cor>.glb` | as mesmas 35 versões em glTF binário, **tudo embutido**. **É isso que o jogo usa hoje.** |
| `cabelos-v4/texturas/<corte>_<cor>.png` | 35 texturas de cabelo 64x64 |
| `template/layout.json` | coordenadas oficiais de cada área da skin |
| `template/mapa_template_1024.png`, `template/areas_128.png` | guias visuais do mapa da skin |
| `skins/` | skins feitas à parte (exemplo: `skin_capivara.png`, time inventado) |
| `skins/vestiario-pixel.html` | guia interativo de como pintar skins no Photopea |

As pastas `cabelos/`, `cabelos-v2/` e `cabelos-v3/` são versões antigas. **Use só `cabelos-v4`.**
A pasta `projetos/jogador-n64/` é o protótipo de origem e **não pode ir para o jogo**.

## 3. Sistema de coordenadas e escala

- No Blender: Z para cima, a frente do personagem olha para **-Y**, a esquerda do personagem é **+X**.
- O exportador glTF converte para Y para cima: no `.glb` o personagem olha para **+Z** e fica em pé em Y.
- Altura total aproximada: **0,45 unidades** (pé no 0, topo da cabeça em ~0,45). Para um personagem de ~1,4 m no
  jogo, escale o nó raiz por ~3,1. Escale o nó raiz, nunca as malhas uma por uma.
- Sufixo `.L` = lado esquerdo **do personagem**; `.R` = lado direito do personagem.

## 4. Objetos e materiais (nomes fixos, use estes nomes no código)

| Nó no glb | Material | Observação |
|---|---|---|
| `Cabeca` | `Skin` | rosto (malha da frente da cabeça). Pai de `Cranio`, `Rosto_Expressao` e `Cabelo` |
| `Cranio` | `Skin` | crânio (topo e parte de trás da cabeça) |
| `Rosto_Expressao` | `Rosto` | camada transparente com olhos, sobrancelhas e boca, 0,6 mm à frente do rosto |
| `Cabelo` | `Cabelo` | malha do corte atual |
| `Orelha.L/.R`, `Pescoco`, `Camisa_Tronco`, `Braco.L/.R`, `Mao.L/.R` | `Skin` | |
| `Bermuda`, `Perna.L/.R` | `Skin` | |
| `Chuteira.L/.R`, `Chuteira_Sola.L/.R`, `Chuteira_Cadarco.L/.R` | `Skin` | a sola inclui os cravos |

Configuração dos materiais no glb (o GLTFLoader do three.js já lê isso, mas confira):

| Material | alphaMode | Lados | Filtro | Cuidados |
|---|---|---|---|---|
| `Skin` | OPAQUE | dupla face | Nearest | um pixel transparente na skin aparece como a cor RGB que estiver nele |
| `Rosto` | BLEND | uma face | Nearest | `depthWrite = false` e `renderOrder = 1` para não brigar com o rosto de baixo |
| `Cabelo` | MASK (corte 0,5) | dupla face | Nearest | as partes transparentes são o degradê e a sombra |

**Regra de ouro das texturas (vale para skin, rostos e cabelo), no three.js:**
```js
tex.flipY = false;                     // convenção do glTF; se ficar true, a textura aparece de cabeça para baixo
tex.colorSpace = THREE.SRGBColorSpace;
tex.magFilter = THREE.NearestFilter;   // pixel duro, estilo N64
tex.minFilter = THREE.NearestFilter;
tex.generateMipmaps = false;           // mipmap borra e mistura áreas vizinhas do atlas
```
Se usar outra engine, o equivalente é: sem flip vertical, sRGB, filtro "point/nearest", sem mipmaps.

## 5. Skin (roupa e pele)

Um único `skin.png` de **128x128** veste o corpo todo. Cada área do PNG cai numa parte fixa do corpo (igual ao skin
do Minecraft). Coordenadas em pixels, origem no canto **superior esquerdo**:

| Área | x | y | l x a | Peça |
|---|---|---|---|---|
| ROSTO | 0 | 0 | 48x48 | frente do rosto (deve ficar em **pele lisa**: o desenho vem da camada `Rosto`) |
| CABECA_LADOS_TRAS | 48 | 0 | 48x24 | laterais da cabeça |
| COURO_CABELUDO | 48 | 24 | 48x24 | crânio (o `Cranio` usa o retângulo x52 y24 23x18, que **tem que ser pele**) |
| ORELHA_ESQ / _DIR | 96 / 112 | 0 | 16x12 | orelhas |
| PESCOCO | 96 | 12 | 32x8 | pescoço |
| MAO_ESQ / _DIR | 96 / 112 | 20 | 16x14 | mãos |
| CADARCO_ESQ / _DIR | 96 / 112 | 34 | 16x14 | língua e cadarço da chuteira |
| CAMISA_FRENTE | 0 | 48 | 40x40 | frente da camisa (esquerda da imagem = lado direito do personagem). O V cor de pele no alto é o decote |
| CAMISA_COSTAS | 40 | 48 | 40x40 | costas (como olhar de trás: texto e número não ficam espelhados) |
| BRACO_ESQ / _DIR | 80 | 48 / 58 | 48x10 | ombro à esquerda, punho à direita; x 80 a ~107 é manga, dali em diante é antebraço (pele) |
| BERMUDA_CINTURA | 80 | 68 | 48x20 | dá a volta no corpo; o meio (x 104) é a frente |
| BERMUDA_PERNA_ESQ / _DIR | 0 / 24 | 88 | 24x16 | pernas da bermuda |
| SOLA_ESQ / _DIR | 0 / 24 | 104 | 24x16 | sola |
| CRAVOS_ESQ / _DIR | 0 / 24 | 120 | 24x8 | todos os cravos de um pé |
| PERNA_ESQ / _DIR | 48 / 68 | 88 | 20x40 | pernas (pele; a parte de baixo pode virar meião) |
| CHUTEIRA_ESQ / _DIR | 88 / 108 | 88 | 20x26 | corpo da chuteira |

A lista oficial é `template/layout.json`. Leia dele em vez de copiar os números à mão.

**Aplicar uma skin no jogo:**
```js
const tex = await new THREE.TextureLoader().loadAsync('skins/skin_capivara.png');
setupPixelTexture(tex);                          // regra de ouro da seção 4
personagem.traverse(o => { if (o.isMesh && o.material.name === 'Skin') o.material.map = tex; });
```
Todas as peças com material `Skin` compartilham a mesma textura. Para vários jogadores com skins diferentes,
**clone o material** por jogador (`o.material = o.material.clone()`) antes de trocar o `map`.

**Validar uma skin antes de aceitar** (vale fazer no carregamento, principalmente se jogadores puderem enviar skins):
o PNG tem que ter exatamente 128x128; pixels transparentes dentro de áreas usadas viram cor errada (já aconteceu:
uma skin veio com os cravos 100% transparentes). Compare o canal alfa com `template/areas_128.png` e preencha ou
recuse. A área ROSTO e o retângulo x52 y24 23x18 têm que ser cor de pele.

**Trocar o tom de pele por código** (sem pintar outra skin): a pele usa uma cor única em toda a skin. Troque essa
cor exata por outra num canvas e gere a textura nova. Na skin padrão a pele é `rgb(242,160,172)`; numa skin feita
por outra pessoa, leia a cor do pixel (24,24), que fica no meio da área ROSTO.

## 6. Rostos animados

O rosto **não está na skin**. Ele é uma camada transparente (`Rosto_Expressao`) por cima da pele, com olhos,
sobrancelhas e boca. Onde não tem desenho, aparece a pele da skin, então qualquer rosto funciona com qualquer tom
de pele.

**Atlas `rostos_atlas.png` (1200x240):** quadros de 48x48 organizados em **25 colunas x 5 linhas**.
- 5 blocos lado a lado, um por **tipo de rosto** (cada bloco tem 240x240 = 5x5 quadros).
- Dentro do bloco: **linha = animação**, **coluna = quadro**.

| `tipo` | Nome | | `animacao` | Nome | | `quadro` | O que é |
|---|---|---|---|---|---|---|---|
| 0 | Clássico | | 0 | piscar um olho | | 0 | padrão |
| 1 | Animado | | 1 | piscar os dois olhos | | 1 | transição |
| 2 | Focado | | 2 | força | | 2 | expressão completa |
| 3 | Sardento | | 3 | dor | | 3 | transição (igual ao 1) |
| 4 | Tranquilo | | 4 | felicidade | | 4 | padrão (igual ao 0) |

**No glb, o UV de `Rosto_Expressao` aponta para o quadro (tipo 0, animação 0, quadro 0).** Para mostrar outro
quadro, desloque a textura:
```js
function setRosto(mat, tipo, animacao, quadro) {
  mat.map.offset.set((tipo * 5 + quadro) / 25, animacao / 5);
}
```
(Com `flipY = false`, `offset.y` positivo desce no atlas, que é o certo aqui. Está testado na `demo_web.html`.)

**Tocar uma animação:** 5 quadros a **10 quadros por segundo** (0,5 s no total). Sequência 0, 1, 2, 3, 4; no fim,
volte para `(tipo, 0, 0)`, o rosto parado. O `tipo` é do personagem e não muda durante a animação.
```js
function tocarRosto(p, animacao) { p.rosto = { animacao, inicio: agora() }; }
function atualizarRosto(p, t) {
  if (!p.rosto) return;
  const q = Math.floor((t - p.rosto.inicio) * 10);         // t em segundos
  if (q >= 5) { setRosto(p.matRosto, p.tipo, 0, 0); p.rosto = null; }
  else setRosto(p.matRosto, p.tipo, p.rosto.animacao, q);
}
```
- **Piscar sozinho:** a cada 2,2 a 4,7 s (aleatório), toque a animação 1, se nenhuma outra estiver tocando.
- **Sugestão de uso no jogo:** força (2) ao chutar forte ou disputar bola; dor (3) ao sofrer falta; felicidade (4)
  no gol; piscar um olho (0) como provocação ou comemoração.
- **Vários jogadores:** cada um precisa da **própria textura** no rosto, senão todos piscam juntos:
  `mat = mat.clone(); mat.map = mat.map.clone(); mat.map.needsUpdate = true;`.
- No Blender existem as Actions `Rosto_*` e as propriedades `tipo_rosto`, `animacao` e `quadro`, mas **isso não
  vai para o glb**. No jogo, a sequência é feita no código, como acima.

## 7. Cabelos

**7 cortes:** `01 liso-repartido`, `02 jogador-degrade`, `03 raspado`, `04 cacheado-curto`, `05 crespo-curto`,
`06 espetado-gel`, `07 mullet`.

**5 cores:** `loiro-natural`, `loiro-pintado` (platinado), `ruivo`, `preto`, `castanho`.

- **Cor** = só textura. As 5 texturas de um corte usam o mesmo UV; trocar a cor é trocar o `map` do material
  `Cabelo` por `cabelos-v4/texturas/<corte>_<cor>.png` (regra de ouro da seção 4 + `alphaTest = 0.5` + dupla face).
  Uma textura de cabelo de 64x64: a metade de cima pinta as mechas, a metade de baixo pinta a casca escura por
  baixo delas.
- **Corte** = troca de malha. Hoje cada um dos 35 glb é o personagem completo com um cabelo. Montagem recomendada
  no jogo: carregue um glb por corte (7 arquivos, por exemplo os `_castanho`), pegue o nó `Cabelo` de cada um e
  guarde como peça reaproveitável. No personagem, remova o `Cabelo` atual e prenda o novo como filho de `Cabeca`,
  **mantendo a transformação local** que veio no glb (todos foram feitos no mesmo espaço da cabeça).
- Deixe o código pronto para isso: "carregar base, prender cabelo,
  aplicar textura".

## 8. Como a Sofia produz e vai continuar produzindo (para você saber o que esperar)

- Tudo é gerado por scripts Python do Blender **5.2.3** (módulo `bpy`), que ficam dentro de cada pasta
  (`scripts/`). Nada é feito à mão no modelo; assim dá para refazer e ajustar com precisão.
- **Novas skins** chegam só como PNG 128x128 no mesmo layout. O jogo não precisa mudar nada.
- **Novas cores de cabelo** chegam só como PNG 64x64 no mesmo UV do corte. O jogo não precisa mudar nada.
- **Novos cortes** chegam como malha nova `Cabelo` com material e UV no mesmo padrão.
- **Novos tipos de rosto** aumentam o atlas para a direita (mais blocos de 240x240). A fórmula vira
  `offset.x = (tipo * 5 + quadro) / (5 * N_TIPOS)` e o UV base muda na mesma proporção. Leia `N_TIPOS` do
  `rostos.json` (campo `tipos`) em vez de fixar 5 no código.
- Toda entrega vem com prints de conferência (frente, 3/4, costas) e uma checagem automática (malha quebrada, peça
  solta, nada cobrindo os olhos). Se algo chegar diferente deste documento, peça para a Sofia antes de contornar no
  código.
- Regra do projeto: **nada é apagado nem sobrescrito sem o Samuel aprovar**. Versões novas chegam em pasta nova
  (`-v2`, `-v3`...). Aponte o jogo para a versão que o Samuel disser que é a atual.

## 9. O que ainda vai mudar

1. **Corpo 100% original** 11 peças originais, com a mesma interface.
2. **Esqueleto (rig)** para animar andar, correr, chutar e comemorar. Hoje as peças são rígidas e separadas; com o
   rig, o glb passa a trazer ossos e animações (glTF skins + animations). Escreva o controle do personagem
   pensando em trocar a animação por nome.
3. **Pacote modular**: `base.glb` + `cabelo_<corte>.glb` + texturas.

## 10. O que pode e o que não pode ir para o jogo

O BRASILERO tem que ser **só nosso**: nada de outro criador, empresa, clube ou marca.

**Pode (é nosso):**
- o mapa da skin (`layout.json`) e todas as skins pintadas pela Sofia ou pelo Samuel **sem marca de terceiros**;
- `rostos_atlas.png` e todo o sistema de rostos (desenhos originais);
- os 7 cortes de cabelo e as 35 texturas;
- `Cranio`, `Bermuda`, `Orelha.L/.R`, `Chuteira_Sola.L/.R`, `Chuteira_Cadarco.L/.R` (feitos do zero);
- o time inventado Capivara EC (`skins/skin_capivara*.png`).
- as 11 peças originais (`Cabeca`, `Pescoco`, `Camisa_Tronco`, `Braco.L/.R`, `Mao.L/.R`, `Perna.L/.R`, `Chuteira.L/.R`), e o `Rosto_Expressao`
- `skins/skin_*.png`: usa escudo e nome que os clubes mesmo disponibilizaram;

**Não pode:**
- 
- qualquer coisa da pasta `jogador-n64` (inclusive o zip original);

## 11. Checklist de implementação

- [ ] Carregar um glb de `cabelos-v4/web/` e mostrar o personagem em pé, olhando para +Z, na escala certa.
- [ ] Texturas sem borrão (Nearest, sem mipmaps, `flipY = false`, sRGB).
- [ ] Trocar a skin por um PNG externo e conferir costas, ombros e lateral da bermuda.
- [ ] Rosto: trocar `tipo` (0 a 4) e tocar as 5 animações a 10 fps; piscar sozinho.
- [ ] Dois jogadores lado a lado com rosto e skin diferentes, sem um interferir no outro (materiais clonados).
- [ ] Trocar a cor do cabelo (textura) e o corte (malha `Cabelo` presa na `Cabeca`).
- [ ] Validação da skin (128x128, sem transparência dentro das áreas usadas).
- [ ] Nenhum asset da lista "não pode" no build final.
